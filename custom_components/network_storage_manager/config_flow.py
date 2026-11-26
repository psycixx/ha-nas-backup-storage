"""Guided creation of Supervisor-managed network storage mounts."""
from __future__ import annotations

from pathlib import PurePath
from typing import Any

import voluptuous as vol
from aiohasupervisor.models.mounts import (
    CIFSMountRequest,
    MountState,
    MountUsage,
    MountsOptions,
    NFSMountRequest,
)
from homeassistant import config_entries
from homeassistant.components.hassio.handler import get_supervisor_client
from homeassistant.helpers import selector
from homeassistant.helpers.hassio import is_hassio

from .const import *
from .models import (
    mount_target_exists,
    prepare_mount_input,
    validate_mount_identity,
    validate_mount_input,
)


def _identity_schema(defaults: dict[str, Any] | None = None) -> vol.Schema:
    """Return the short, protocol-selection form."""
    defaults = defaults or {}
    return vol.Schema(
        {
            vol.Required(
                CONF_MOUNT_NAME, default=defaults.get(CONF_MOUNT_NAME, "nas_storage")
            ): selector.TextSelector(),
            vol.Required(
                CONF_USAGE, default=defaults.get(CONF_USAGE, USAGE_BACKUP)
            ): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=STORAGE_USAGES, translation_key="storage_usage"
                )
            ),
            vol.Required(
                CONF_PROTOCOL, default=defaults.get(CONF_PROTOCOL, PROTOCOL_CIFS)
            ): selector.SelectSelector(
                selector.SelectSelectorConfig(options=[PROTOCOL_CIFS, PROTOCOL_NFS])
            ),
            vol.Optional(
                CONF_WINDOWS_PATH, default=defaults.get(CONF_WINDOWS_PATH, "")
            ): selector.TextSelector(selector.TextSelectorConfig(autocomplete="off")),
        }
    )


def _default_backup_field(fields, defaults):
    """Only backup mounts can be selected as the default backup destination."""
    if defaults.get(CONF_USAGE, USAGE_BACKUP) == USAGE_BACKUP:
        fields[vol.Required(
            CONF_MAKE_DEFAULT, default=defaults.get(CONF_MAKE_DEFAULT, False)
        )] = selector.BooleanSelector()
    return vol.Schema(fields)


def _smb_schema(defaults: dict[str, Any] | None = None) -> vol.Schema:
    """Return the SMB fields appropriate to the selected storage usage."""
    defaults = defaults or {}
    return _default_backup_field(
        {
            vol.Required(CONF_SERVER, default=defaults.get(CONF_SERVER, "")): selector.TextSelector(),
            vol.Required(CONF_SHARE, default=defaults.get(CONF_SHARE, "")): selector.TextSelector(),
            vol.Required(CONF_USERNAME, default=defaults.get(CONF_USERNAME, "")): selector.TextSelector(),
            vol.Required(CONF_PASSWORD): selector.TextSelector(
                selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD)
            ),
        },
        defaults,
    )


def _nfs_schema(defaults: dict[str, Any] | None = None) -> vol.Schema:
    """Return the NFS fields appropriate to the selected storage usage."""
    defaults = defaults or {}
    return _default_backup_field(
        {
            vol.Required(CONF_SERVER, default=defaults.get(CONF_SERVER, "")): selector.TextSelector(),
            vol.Required(CONF_PATH, default=defaults.get(CONF_PATH, "")): selector.TextSelector(),
        },
        defaults,
    )


def _error_key_for_exception(err: Exception) -> str:
    """Map safe Supervisor failure categories to translated form messages."""
    detail = str(err).casefold()
    if any(value in detail for value in ("authentication", "logon", "login", "invalid credential")):
        return "authentication_failed"
    if any(value in detail for value in ("permission denied", "access denied", "not permitted")):
        return "permission_denied"
    if any(value in detail for value in ("not found", "no such", "does not exist")):
        return "path_not_found"
    if any(value in detail for value in ("timeout", "timed out", "connection refused", "network is unreachable")):
        return "cannot_connect"
    return "mount_failed"


class NasBackupStorageConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Configure one Supervisor-managed network storage location."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the in-progress configuration data."""
        super().__init__()
        self._identity_data: dict[str, Any] = {}

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        """Collect the short protocol-selection form."""
        if not is_hassio(self.hass):
            return self.async_abort(reason="supervisor_required")
        if user_input is None:
            return self.async_show_form(step_id="user", data_schema=_identity_schema())

        try:
            self._identity_data = prepare_mount_input(user_input)
        except ValueError as err:
            return self.async_show_form(
                step_id="user",
                data_schema=_identity_schema(user_input),
                errors={"base": str(err)},
            )

        if self._identity_data[CONF_PROTOCOL] == PROTOCOL_CIFS:
            return await self.async_step_smb()
        return await self.async_step_nfs()

    async def async_step_smb(self, user_input: dict[str, Any] | None = None):
        """Collect the SMB/CIFS-only fields."""
        defaults = prepare_mount_input(self._identity_data)
        if user_input is None:
            return self.async_show_form(step_id="smb", data_schema=_smb_schema(defaults))
        return await self._async_create_mount(
            {**self._identity_data, **user_input}, "smb", _smb_schema
        )

    async def async_step_nfs(self, user_input: dict[str, Any] | None = None):
        """Collect the NFS-only fields."""
        if user_input is None:
            return self.async_show_form(
                step_id="nfs", data_schema=_nfs_schema(self._identity_data)
            )
        return await self._async_create_mount(
            {**self._identity_data, **user_input}, "nfs", _nfs_schema
        )

    async def _async_create_mount(self, user_input, step_id, schema_factory):
        """Validate, create, activate and save one Supervisor mount."""
        created_mount = False
        data: dict[str, Any] | None = None
        try:
            data = validate_mount_input(user_input)
            await self.async_set_unique_id(data[CONF_MOUNT_NAME])
            self._abort_if_unique_id_configured()

            client = get_supervisor_client(self.hass)
            mounts = await client.mounts.info()
            if any(mount.name == data[CONF_MOUNT_NAME] for mount in mounts.mounts):
                raise ValueError("mount_name_exists")
            if mount_target_exists(mounts.mounts, data):
                raise ValueError("mount_target_exists")

            if data[CONF_PROTOCOL] == PROTOCOL_CIFS:
                request = CIFSMountRequest(
                    usage=MountUsage(data[CONF_USAGE]),
                    server=data[CONF_SERVER],
                    share=data[CONF_SHARE],
                    username=data[CONF_USERNAME],
                    password=data[CONF_PASSWORD],
                )
            else:
                request = NFSMountRequest(
                    usage=MountUsage(data[CONF_USAGE]),
                    server=data[CONF_SERVER],
                    path=PurePath(data[CONF_PATH]),
                )

            await client.mounts.create_mount(data[CONF_MOUNT_NAME], request)
            created_mount = True
            mounts = await client.mounts.info()
            mount = next(
                (mount for mount in mounts.mounts if mount.name == data[CONF_MOUNT_NAME]),
                None,
            )
            if mount is None or mount.state != MountState.ACTIVE:
                await client.mounts.delete_mount(data[CONF_MOUNT_NAME])
                raise ValueError("mount_not_active")

            if data[CONF_USAGE] == USAGE_BACKUP and data[CONF_MAKE_DEFAULT]:
                await client.mounts.options(
                    MountsOptions(default_backup_mount=data[CONF_MOUNT_NAME])
                )
        except ValueError as err:
            return self.async_show_form(
                step_id=step_id,
                data_schema=schema_factory(user_input),
                errors={"base": str(err)},
            )
        except Exception as err:
            if created_mount and data is not None:
                try:
                    await get_supervisor_client(self.hass).mounts.delete_mount(
                        data[CONF_MOUNT_NAME]
                    )
                except Exception:
                    pass
            return self.async_show_form(
                step_id=step_id,
                data_schema=schema_factory(user_input),
                errors={"base": _error_key_for_exception(err)},
            )

        entry_data = {
            CONF_MOUNT_NAME: data[CONF_MOUNT_NAME],
            CONF_PROTOCOL: data[CONF_PROTOCOL],
            CONF_USAGE: data[CONF_USAGE],
            CONF_SERVER: data[CONF_SERVER],
            CONF_MAKE_DEFAULT: data[CONF_MAKE_DEFAULT],
        }
        if data[CONF_PROTOCOL] == PROTOCOL_CIFS:
            entry_data[CONF_SHARE] = data[CONF_SHARE]
        else:
            entry_data[CONF_PATH] = data[CONF_PATH]

        return self.async_create_entry(
            title=f"Network Storage: {data[CONF_MOUNT_NAME]}",
            data=entry_data,
        )

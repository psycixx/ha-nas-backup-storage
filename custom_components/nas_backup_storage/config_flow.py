"""Guided creation of Supervisor backup mounts."""
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
from .models import validate_mount_input

def _schema(defaults: dict[str, Any] | None = None) -> vol.Schema:
    defaults = defaults or {}
    d = lambda key, fallback=None: defaults.get(key, fallback)
    return vol.Schema({
        vol.Required(CONF_MOUNT_NAME, default=d(CONF_MOUNT_NAME, "nas_backup")): selector.TextSelector(),
        vol.Required(CONF_PROTOCOL, default=d(CONF_PROTOCOL, PROTOCOL_CIFS)): selector.SelectSelector(
            selector.SelectSelectorConfig(options=[PROTOCOL_CIFS, PROTOCOL_NFS])
        ),
        vol.Required(CONF_SERVER, default=d(CONF_SERVER, "")): selector.TextSelector(),
        vol.Optional(CONF_SHARE, default=d(CONF_SHARE, "")): selector.TextSelector(),
        vol.Optional(CONF_PATH, default=d(CONF_PATH, "")): selector.TextSelector(),
        vol.Optional(CONF_USERNAME, default=d(CONF_USERNAME, "")): selector.TextSelector(),
        vol.Optional(CONF_PASSWORD, default=""): selector.TextSelector(
            selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD)
        ),
        vol.Required(CONF_MAKE_DEFAULT, default=d(CONF_MAKE_DEFAULT, False)): selector.BooleanSelector(),
    })

class NasBackupStorageConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Configure one Supervisor-managed network backup location."""
    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        if not is_hassio(self.hass):
            return self.async_abort(reason="supervisor_required")
        if user_input is None:
            return self.async_show_form(step_id="user", data_schema=_schema())

        created_mount = False
        try:
            data = validate_mount_input(user_input)
            await self.async_set_unique_id(data[CONF_MOUNT_NAME])
            self._abort_if_unique_id_configured()
            client = get_supervisor_client(self.hass)
            mounts = await client.mounts.info()
            if any(mount.name == data[CONF_MOUNT_NAME] for mount in mounts.mounts):
                raise ValueError("mount_name_exists")
            if data[CONF_PROTOCOL] == PROTOCOL_CIFS:
                request = CIFSMountRequest(
                    usage=MountUsage.BACKUP,
                    server=data[CONF_SERVER],
                    share=data[CONF_SHARE],
                    username=data[CONF_USERNAME],
                    password=data[CONF_PASSWORD],
                )
            else:
                request = NFSMountRequest(
                    usage=MountUsage.BACKUP,
                    server=data[CONF_SERVER],
                    path=PurePath(data[CONF_PATH]),
                )
            await client.mounts.create_mount(data[CONF_MOUNT_NAME], request)
            created_mount = True
            mounts = await client.mounts.info()
            mount = next(
                mount for mount in mounts.mounts if mount.name == data[CONF_MOUNT_NAME]
            )
            if mount.state is not MountState.ACTIVE:
                await client.mounts.delete_mount(data[CONF_MOUNT_NAME])
                raise ValueError("mount_failed")
            if data[CONF_MAKE_DEFAULT]:
                await client.mounts.options(
                    MountsOptions(default_backup_mount=data[CONF_MOUNT_NAME])
                )
        except ValueError as err:
            return self.async_show_form(
                step_id="user", data_schema=_schema(user_input), errors={"base": str(err)}
            )
        except Exception:
            if created_mount:
                try:
                    await get_supervisor_client(self.hass).mounts.delete_mount(data[CONF_MOUNT_NAME])
                except Exception:
                    pass
            return self.async_show_form(
                step_id="user", data_schema=_schema(user_input), errors={"base": "cannot_connect"}
            )

        return self.async_create_entry(
            title=f"NAS Backup: {data[CONF_MOUNT_NAME]}",
            data={CONF_MOUNT_NAME: data[CONF_MOUNT_NAME]},
        )

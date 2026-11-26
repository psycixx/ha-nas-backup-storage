"""Supervisor mount state sensors."""
from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity

from .const import (
    CONF_MAKE_DEFAULT,
    CONF_PATH,
    CONF_PROTOCOL,
    CONF_SERVER,
    CONF_SHARE,
    CONF_USAGE,
    DOMAIN,
    PROTOCOL_CIFS,
    STORAGE_USAGES,
    USAGE_BACKUP,
)
from .device import device_info


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the Supervisor mount state and configuration sensors."""
    status = hass.data[DOMAIN][entry.entry_id]["status"]
    entities = [
        MountStatusSensor(status, entry),
        StorageUsageSensor(status, entry),
        StorageProtocolSensor(status, entry),
        StorageServerSensor(status, entry),
        StoragePathSensor(status, entry),
    ]
    if entry.data.get(CONF_USAGE, USAGE_BACKUP) == USAGE_BACKUP:
        entities.append(StorageDefaultSensor(status, entry))
    async_add_entities(entities)


class MountStatusSensor(SensorEntity):
    """Expose the selected native storage's mount state."""

    _attr_has_entity_name = True
    _attr_translation_key = "backup_storage_status"
    _attr_icon = "mdi:nas"

    def __init__(self, status, entry) -> None:
        self._status = status
        self._entry = entry
        self._attr_device_info = device_info(entry)
        self._attr_unique_id = f"{entry.entry_id}_status"
        self._unsub = status.add_listener(self._handle_status_update)

    @property
    def native_value(self) -> str:
        return self._status.state

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return safe status diagnostics without exposing credentials."""
        data = self._entry.data
        attributes = {
            "mount_name": self._status.name,
            "protocol": data.get(CONF_PROTOCOL),
            "server": data.get(CONF_SERVER),
            "usage": data.get(CONF_USAGE, USAGE_BACKUP),
            "last_checked": self._status.last_updated,
        }
        if self._status.last_error:
            attributes["last_error"] = self._status.last_error
        if data.get(CONF_USAGE, USAGE_BACKUP) == USAGE_BACKUP:
            attributes["default_backup_location"] = data.get(CONF_MAKE_DEFAULT, False)
        if data.get(CONF_PROTOCOL) == PROTOCOL_CIFS:
            attributes["share"] = data.get(CONF_SHARE)
        else:
            attributes["nfs_export_path"] = data.get(CONF_PATH)
        return attributes

    def _handle_status_update(self) -> None:
        if self.hass is not None:
            self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        await self._status.async_refresh()

    async def async_will_remove_from_hass(self) -> None:
        self._unsub()
        await super().async_will_remove_from_hass()


class _StorageSettingSensor(SensorEntity):
    """Base entity for a visible, non-secret network storage setting."""

    _attr_has_entity_name = True

    def __init__(self, status, entry, suffix: str, translation_key: str, icon: str) -> None:
        self._status = status
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_{suffix}"
        self._attr_translation_key = translation_key
        self._attr_icon = icon
        self._attr_device_info = device_info(entry)
        self._unsub = status.add_listener(self._handle_status_update)

    def _data(self):
        return self._entry.data

    def _handle_status_update(self) -> None:
        if self.hass is not None:
            self.async_write_ha_state()

    async def async_will_remove_from_hass(self) -> None:
        self._unsub()
        await super().async_will_remove_from_hass()


class StorageUsageSensor(_StorageSettingSensor):
    """Expose the selected network storage purpose."""

    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = STORAGE_USAGES

    def __init__(self, status, entry) -> None:
        super().__init__(status, entry, "usage", "storage_usage", "mdi:folder-cog")

    @property
    def native_value(self):
        return self._data().get(CONF_USAGE, USAGE_BACKUP)


class StorageProtocolSensor(_StorageSettingSensor):
    def __init__(self, status, entry) -> None:
        super().__init__(status, entry, "protocol", "storage_protocol", "mdi:lan")

    @property
    def native_value(self):
        return self._data().get(CONF_PROTOCOL)


class StorageServerSensor(_StorageSettingSensor):
    def __init__(self, status, entry) -> None:
        super().__init__(status, entry, "server", "storage_server", "mdi:server-network")

    @property
    def native_value(self):
        return self._data().get(CONF_SERVER)


class StoragePathSensor(_StorageSettingSensor):
    def __init__(self, status, entry) -> None:
        super().__init__(status, entry, "path", "storage_path", "mdi:folder-network")

    @property
    def native_value(self):
        data = self._data()
        return (
            data.get(CONF_SHARE)
            if data.get(CONF_PROTOCOL) == PROTOCOL_CIFS
            else data.get(CONF_PATH)
        )


class StorageDefaultSensor(_StorageSettingSensor):
    def __init__(self, status, entry) -> None:
        super().__init__(
            status, entry, "is_default", "default_backup_location", "mdi:star"
        )

    @property
    def native_value(self):
        return "enabled" if self._data().get(CONF_MAKE_DEFAULT) else "disabled"

"""Supervisor mount state sensor."""
from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity

from .const import (
    CONF_MAKE_DEFAULT,
    CONF_PATH,
    CONF_PROTOCOL,
    CONF_SERVER,
    CONF_SHARE,
    DOMAIN,
    PROTOCOL_CIFS,
)
from .device import device_info


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the Supervisor mount status sensor."""
    async_add_entities(
        [MountStatusSensor(hass.data[DOMAIN][entry.entry_id]["status"], entry)]
    )


class MountStatusSensor(SensorEntity):
    """Expose the selected native backup storage's mount state."""

    _attr_has_entity_name = True
    _attr_translation_key = "backup_storage_status"
    _attr_icon = "mdi:nas"

    def __init__(self, status, entry) -> None:
        """Initialize the entity."""
        self._status = status
        self._entry = entry
        self._attr_device_info = device_info(entry)
        self._attr_unique_id = f"{entry.entry_id}_status"
        self._unsub = status.add_listener(self._handle_status_update)

    @property
    def native_value(self) -> str:
        """Return the Supervisor mount state."""
        return self._status.state

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return safe status diagnostics without exposing credentials."""
        data = self._entry.data
        attributes = {
            "mount_name": self._status.name,
            "protocol": data.get(CONF_PROTOCOL),
            "server": data.get(CONF_SERVER),
            "default_backup_location": data.get(CONF_MAKE_DEFAULT),
            "last_checked": self._status.last_updated,
        }
        if data.get(CONF_PROTOCOL) == PROTOCOL_CIFS:
            attributes["share"] = data.get(CONF_SHARE)
        else:
            attributes["nfs_export_path"] = data.get(CONF_PATH)
        return attributes

    def _handle_status_update(self) -> None:
        """Refresh only after Home Assistant has registered this entity."""
        if self.hass is not None:
            self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        """Refresh once the entity can safely publish a state."""
        await super().async_added_to_hass()
        await self._status.async_refresh()

    async def async_will_remove_from_hass(self) -> None:
        """Unsubscribe from mount status updates."""
        self._unsub()
        await super().async_will_remove_from_hass()

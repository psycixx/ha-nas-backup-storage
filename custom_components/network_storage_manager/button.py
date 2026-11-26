"""Reconnect button for a Supervisor mount."""
from __future__ import annotations

from homeassistant.components.button import ButtonEntity

from .const import DOMAIN
from .device import device_info


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the reconnect button."""
    async_add_entities(
        [ReconnectButton(hass.data[DOMAIN][entry.entry_id]["status"], entry)]
    )


class ReconnectButton(ButtonEntity):
    """Request an immediate Supervisor reload of the network mount."""

    _attr_has_entity_name = True
    _attr_translation_key = "reconnect_backup_storage"
    _attr_icon = "mdi:connection"

    def __init__(self, status, entry) -> None:
        """Initialize the entity."""
        self._status = status
        self._attr_device_info = device_info(entry)
        self._attr_unique_id = f"{entry.entry_id}_reconnect"

    async def async_press(self) -> None:
        """Reconnect the network mount."""
        await self._status.async_reload()

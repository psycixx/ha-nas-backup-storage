"""Reconnect button for a Supervisor backup mount."""
from homeassistant.components.button import ButtonEntity
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([ReconnectButton(hass.data[DOMAIN][entry.entry_id]["status"], entry)])

class ReconnectButton(ButtonEntity):
    _attr_has_entity_name = True
    _attr_name = "Reconnect backup storage"
    _attr_icon = "mdi:connection"
    def __init__(self, status, entry):
        self._status, self._attr_unique_id = status, f"{entry.entry_id}_reconnect"
    async def async_press(self): await self._status.async_reload()

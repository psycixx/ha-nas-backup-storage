"""Supervisor mount state sensor."""
from homeassistant.components.sensor import SensorEntity
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([MountStatusSensor(hass.data[DOMAIN][entry.entry_id]["status"], entry)])

class MountStatusSensor(SensorEntity):
    _attr_has_entity_name = True
    _attr_name = "Backup storage status"
    _attr_icon = "mdi:nas"
    def __init__(self, status, entry):
        self._status, self._attr_unique_id = status, f"{entry.entry_id}_status"
        self._unsub = status.add_listener(self.async_write_ha_state)
    @property
    def native_value(self): return self._status.state
    async def async_added_to_hass(self): await self._status.async_refresh()
    async def async_will_remove_from_hass(self): self._unsub()

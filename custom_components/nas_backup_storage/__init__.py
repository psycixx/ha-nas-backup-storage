"""NAS Backup Storage integration."""
from __future__ import annotations
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from .const import DOMAIN

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Keep a record of an integration-managed Supervisor backup mount."""
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = entry.data
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload without deleting the Supervisor mount or its backups."""
    hass.data[DOMAIN].pop(entry.entry_id, None)
    return True

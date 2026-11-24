"""NAS Backup Storage integration."""
from __future__ import annotations
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from .const import DOMAIN, CONF_MOUNT_NAME
from .status import MountStatus

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Keep a record of an integration-managed Supervisor backup mount."""
    status = MountStatus(hass, entry.data[CONF_MOUNT_NAME])
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {"status": status}
    await hass.config_entries.async_forward_entry_setups(entry, ["sensor", "button"])
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload without deleting the Supervisor mount or its backups."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, ["sensor", "button"])
    if unloaded: hass.data[DOMAIN].pop(entry.entry_id, None)
    return unloaded

"""Network Storage Manager integration."""
from __future__ import annotations

import logging

from homeassistant.components.hassio.handler import get_supervisor_client
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import CONF_MOUNT_NAME, DOMAIN
from .status import MountStatus

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up one integration-managed Supervisor mount."""
    status = MountStatus(hass, entry.data[CONF_MOUNT_NAME])
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {"status": status}
    try:
        await hass.config_entries.async_forward_entry_setups(entry, ["sensor", "button"])
    except Exception:
        status.async_stop()
        hass.data[DOMAIN].pop(entry.entry_id, None)
        raise
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload entities without changing the Supervisor mount."""
    unloaded = await hass.config_entries.async_unload_platforms(
        entry, ["sensor", "button"]
    )
    if unloaded:
        entry_data = hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
        if entry_data is not None:
            entry_data["status"].async_stop()
    return unloaded


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Remove the native storage location when its integration entry is deleted."""
    mount_name = entry.data[CONF_MOUNT_NAME]
    try:
        await get_supervisor_client(hass).mounts.delete_mount(mount_name)
    except Exception:
        _LOGGER.warning(
            "Could not remove Supervisor mount %s while removing the "
            "Network Storage Manager entry. Remove it manually under "
            "Settings > System > Storage if it still exists.",
            mount_name,
            exc_info=True,
        )

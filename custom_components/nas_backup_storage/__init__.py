"""NAS Backup Storage integration."""
from __future__ import annotations

import logging

from homeassistant.components.hassio.handler import get_supervisor_client
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import CONF_MOUNT_NAME, DOMAIN
from .status import MountStatus

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up one integration-managed Supervisor backup mount."""
    status = MountStatus(hass, entry.data[CONF_MOUNT_NAME])
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {"status": status}
    await hass.config_entries.async_forward_entry_setups(entry, ["sensor", "button"])
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload entities without changing the Supervisor mount."""
    unloaded = await hass.config_entries.async_unload_platforms(
        entry, ["sensor", "button"]
    )
    if unloaded:
        hass.data[DOMAIN][entry.entry_id]["status"].async_stop()
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unloaded


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Remove the native backup location when its integration entry is deleted."""
    mount_name = entry.data[CONF_MOUNT_NAME]
    try:
        await get_supervisor_client(hass).mounts.delete_mount(mount_name)
    except Exception:
        # Do not prevent the user from removing a stale integration entry. The
        # Supervisor may already have removed the mount manually.
        _LOGGER.warning(
            "Could not remove Supervisor backup mount %s while removing the "
            "NAS Backup Storage entry",
            mount_name,
            exc_info=True,
        )

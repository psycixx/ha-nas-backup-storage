"""Device metadata for NAS storage entities."""
from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo

from .const import CONF_PROTOCOL, DOMAIN


def device_info(entry) -> DeviceInfo:
    """Build the shared device entry for one native NAS backup location."""
    protocol = entry.data.get(CONF_PROTOCOL, "SMB/NFS")
    return DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name=entry.title,
        manufacturer="NAS Backup Storage",
        model=f"{protocol} backup location",
        configuration_url="https://github.com/psycixx/ha-nas-backup-storage",
    )

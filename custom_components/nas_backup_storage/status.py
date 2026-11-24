"""Shared Supervisor mount status."""
from __future__ import annotations

from collections.abc import Callable
from datetime import timedelta
import logging

from homeassistant.components.hassio.handler import get_supervisor_client
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.util import dt as dt_util

_LOGGER = logging.getLogger(__name__)


class MountStatus:
    """Keep the mount state current without changing the mount configuration."""

    def __init__(self, hass, name: str) -> None:
        self.hass = hass
        self.name = name
        self.state = "unknown"
        self.last_updated: str | None = None
        self._listeners: list[Callable[[], None]] = []
        self._unsub = async_track_time_interval(
            hass, self._async_periodic_refresh, timedelta(minutes=5)
        )

    async def _async_periodic_refresh(self, now) -> None:
        """Refresh the status on the scheduled polling interval."""
        await self.async_refresh()

    async def async_refresh(self) -> None:
        """Fetch the Supervisor mount state and notify registered entities."""
        try:
            mounts = await get_supervisor_client(self.hass).mounts.info()
            mount = next(
                (item for item in mounts.mounts if item.name == self.name), None
            )
            self.state = mount.state.value if mount and mount.state else "missing"
        except Exception:
            self.state = "unavailable"
            _LOGGER.exception("Could not refresh backup mount %s", self.name)
        self.last_updated = dt_util.utcnow().isoformat()
        for listener in tuple(self._listeners):
            try:
                listener()
            except Exception:
                _LOGGER.exception(
                    "Could not update an entity for backup mount %s", self.name
                )

    async def async_reload(self) -> None:
        """Ask the Supervisor to reconnect the mount, then refresh its state."""
        await get_supervisor_client(self.hass).mounts.reload_mount(self.name)
        await self.async_refresh()

    def async_stop(self) -> None:
        """Stop periodic refreshes."""
        self._unsub()

    def add_listener(self, listener: Callable[[], None]) -> Callable[[], None]:
        """Register a state-change listener."""
        self._listeners.append(listener)
        return lambda: self._listeners.remove(listener)

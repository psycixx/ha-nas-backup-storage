"""Shared Supervisor mount status."""
from __future__ import annotations

from collections.abc import Callable
from datetime import timedelta
import logging

from homeassistant.components.hassio.handler import get_supervisor_client
from homeassistant.exceptions import HomeAssistantError
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
        self.last_error: str | None = None
        self._listeners: list[Callable[[], None]] = []
        self._unsub = async_track_time_interval(
            hass, self._async_periodic_refresh, timedelta(minutes=5)
        )

    def _notify_listeners(self) -> None:
        """Notify entities while isolating listener failures."""
        for listener in tuple(self._listeners):
            try:
                listener()
            except Exception:
                _LOGGER.exception(
                    "Could not update an entity for backup mount %s", self.name
                )

    def _set_error(self, message: str) -> None:
        """Record a safe failure state and publish it."""
        self.state = "unavailable"
        self.last_error = message
        self.last_updated = dt_util.utcnow().isoformat()
        self._notify_listeners()

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
            self.last_error = None
        except Exception:
            _LOGGER.exception("Could not refresh backup mount %s", self.name)
            self._set_error("Could not contact the Supervisor to check this storage location.")
            return

        self.last_updated = dt_util.utcnow().isoformat()
        self._notify_listeners()

    async def async_reload(self) -> None:
        """Ask the Supervisor to reconnect the mount, then refresh its state."""
        try:
            await get_supervisor_client(self.hass).mounts.reload_mount(self.name)
        except Exception as err:
            _LOGGER.exception("Could not reconnect backup mount %s", self.name)
            self._set_error("The storage location could not be reconnected.")
            raise HomeAssistantError(
                "The storage location could not be reconnected. "
                "Check the server address, path and access permissions."
            ) from err
        await self.async_refresh()

    def async_stop(self) -> None:
        """Stop periodic refreshes."""
        self._unsub()

    def add_listener(self, listener: Callable[[], None]) -> Callable[[], None]:
        """Register a state-change listener."""
        self._listeners.append(listener)
        return lambda: self._listeners.remove(listener)

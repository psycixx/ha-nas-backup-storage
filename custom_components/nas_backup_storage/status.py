"""Shared Supervisor mount status."""
from __future__ import annotations
from collections.abc import Callable
from datetime import timedelta
from homeassistant.components.hassio.handler import get_supervisor_client
from homeassistant.helpers.event import async_track_time_interval

class MountStatus:
    """Keep the mount state current without changing the mount configuration."""
    def __init__(self, hass, name: str) -> None:
        self.hass, self.name, self.state, self._listeners = hass, name, "unknown", []
        self._unsub = async_track_time_interval(
            hass, self._async_periodic_refresh, timedelta(minutes=5)
        )
    async def _async_periodic_refresh(self, now) -> None:
        await self.async_refresh()
    async def async_refresh(self) -> None:
        try:
            mounts = await get_supervisor_client(self.hass).mounts.info()
            mount = next((item for item in mounts.mounts if item.name == self.name), None)
            self.state = mount.state.value if mount and mount.state else "missing"
        except Exception:
            self.state = "unavailable"
        for listener in tuple(self._listeners): listener()
    async def async_reload(self) -> None:
        await get_supervisor_client(self.hass).mounts.reload_mount(self.name)
        await self.async_refresh()
    def async_stop(self) -> None:
        self._unsub()
    def add_listener(self, listener: Callable[[], None]):
        self._listeners.append(listener)
        return lambda: self._listeners.remove(listener)

"""Shared Supervisor mount status."""
from __future__ import annotations
from collections.abc import Callable
from homeassistant.components.hassio.handler import get_supervisor_client

class MountStatus:
    def __init__(self, hass, name: str) -> None:
        self.hass, self.name, self.state, self._listeners = hass, name, "unknown", []
    async def async_refresh(self) -> None:
        mounts = await get_supervisor_client(self.hass).mounts.info()
        mount = next((item for item in mounts.mounts if item.name == self.name), None)
        self.state = mount.state.value if mount and mount.state else "missing"
        for listener in tuple(self._listeners): listener()
    async def async_reload(self) -> None:
        await get_supervisor_client(self.hass).mounts.reload_mount(self.name)
        await self.async_refresh()
    def add_listener(self, listener: Callable[[], None]):
        self._listeners.append(listener)
        return lambda: self._listeners.remove(listener)

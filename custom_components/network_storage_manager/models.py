"""Input validation and Supervisor-mount comparison helpers."""
from __future__ import annotations

import re
from typing import Any, Iterable

from .const import *

# The Supervisor only accepts letters, digits and underscores in a mount name.
_MOUNT_NAME = re.compile(r"^[A-Za-z0-9_]{1,64}$")


def validate_mount_identity(data: dict[str, Any]) -> dict[str, Any]:
    """Validate the values selected before showing the protocol-specific form."""
    result = dict(data)
    name = str(result.get(CONF_MOUNT_NAME, "")).strip()
    if not _MOUNT_NAME.fullmatch(name):
        raise ValueError("invalid_mount_name")
    result[CONF_MOUNT_NAME] = name

    protocol = result.get(CONF_PROTOCOL)
    if protocol not in (PROTOCOL_CIFS, PROTOCOL_NFS):
        raise ValueError("invalid_protocol")
    return result


def _apply_windows_path(result: dict[str, Any]) -> None:
    """Extract SMB server and remote share path from a copied UNC path."""
    windows_path = str(result.get(CONF_WINDOWS_PATH, "")).strip()
    if not windows_path:
        return
    if result.get(CONF_PROTOCOL) != PROTOCOL_CIFS:
        raise ValueError("windows_path_cifs_only")
    if not windows_path.startswith(("\\\\", "//")):
        raise ValueError("invalid_windows_path")

    parts = [part for part in windows_path.replace("\\", "/").split("/") if part]
    if len(parts) < 2:
        raise ValueError("windows_path_needs_share")
    if any(part in (".", "..") for part in parts):
        raise ValueError("invalid_remote_path")

    result[CONF_SERVER] = parts[0]
    result[CONF_SHARE] = "/".join(parts[1:])
    result[CONF_WINDOWS_PATH] = windows_path


def prepare_mount_input(data: dict[str, Any]) -> dict[str, Any]:
    """Normalize values that can be determined before protocol-specific input."""
    result = validate_mount_identity(data)
    _apply_windows_path(result)
    return result


def _mount_value(mount: Any, key: str) -> str:
    """Return a normalized Supervisor mount attribute."""
    value = mount.get(key) if isinstance(mount, dict) else getattr(mount, key, None)
    value = getattr(value, "value", value)
    return "" if value is None else str(value).strip()


def mount_target_exists(mounts: Iterable[Any], data: dict[str, Any]) -> bool:
    """Return whether a Supervisor mount already has this remote target."""
    protocol = data[CONF_PROTOCOL]
    server = str(data[CONF_SERVER]).casefold()
    target_key = CONF_SHARE if protocol == PROTOCOL_CIFS else CONF_PATH
    target = str(data[target_key]).strip().strip("/")
    if protocol == PROTOCOL_CIFS:
        target = target.casefold()

    for mount in mounts:
        if _mount_value(mount, "type").casefold() != protocol:
            continue
        if _mount_value(mount, "server").casefold() != server:
            continue
        existing = _mount_value(mount, target_key).strip().strip("/")
        if protocol == PROTOCOL_CIFS:
            existing = existing.casefold()
        if existing == target:
            return True
    return False


def validate_mount_input(data: dict[str, Any]) -> dict[str, Any]:
    """Normalize and validate input before the Supervisor mount call."""
    result = prepare_mount_input(data)
    server = str(result.get(CONF_SERVER, "")).strip()
    if not server:
        raise ValueError("server_required")
    if server in (".", "..") or "/" in server or "\\" in server:
        raise ValueError("invalid_server")
    result[CONF_SERVER] = server

    if result[CONF_PROTOCOL] == PROTOCOL_CIFS:
        share = str(result.get(CONF_SHARE, "")).strip().strip("/")
        if not share:
            raise ValueError("share_required")
        if any(part in (".", "..") for part in share.split("/")):
            raise ValueError("invalid_remote_path")
        result[CONF_SHARE] = share
        if not str(result.get(CONF_USERNAME, "")).strip():
            raise ValueError("username_required")
        if not result.get(CONF_PASSWORD):
            raise ValueError("password_required")
    else:
        path = str(result.get(CONF_PATH, "")).strip()
        if not path.startswith("/"):
            raise ValueError("invalid_nfs_path")
        if any(part == ".." for part in path.split("/")):
            raise ValueError("invalid_remote_path")
        result[CONF_PATH] = path
    return result

""""Pure validation for NAS backup storage setup."""
from __future__ import annotations
import re
from typing import Any
from .const import *

_MOUNT_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")

def _apply_windows_path(result: dict[str, Any]) -> None:
    """Extract SMB server and share from a copied Windows UNC path."""
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
    result[CONF_SERVER] = parts[0]
    # The Supervisor accepts a remote SMB share path, including a subfolder.
    result[CONF_SHARE] = "/".join(parts[1:])
    result[CONF_WINDOWS_PATH] = windows_path

def validate_mount_input(data: dict[str, Any]) -> dict[str, Any]:
    """Normalize and validate input before the Supervisor mount call."""
    result = dict(data)
    name = str(result.get(CONF_MOUNT_NAME, "")).strip()
    if not _MOUNT_NAME.fullmatch(name):
        raise ValueError("invalid_mount_name")
    result[CONF_MOUNT_NAME] = name
    protocol = result.get(CONF_PROTOCOL)
    if protocol not in (PROTOCOL_CIFS, PROTOCOL_NFS):
        raise ValueError("invalid_protocol")

    _apply_windows_path(result)
    server = str(result.get(CONF_SERVER, "")).strip()
    if not server:
        raise ValueError("server_required")
    result[CONF_SERVER] = server
    if protocol == PROTOCOL_CIFS:
        share = str(result.get(CONF_SHARE, "")).strip().strip("/")
        if not share:
            raise ValueError("share_required")
        result[CONF_SHARE] = share
        if not str(result.get(CONF_USERNAME, "")).strip():
            raise ValueError("username_required")
        if not result.get(CONF_PASSWORD):
            raise ValueError("password_required")
    else:
        path = str(result.get(CONF_PATH, "")).strip()
        if not path.startswith("/"):
            raise ValueError("invalid_nfs_path")
        result[CONF_PATH] = path
    return result

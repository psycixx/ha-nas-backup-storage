"""Pure validation for NAS backup storage setup."""
from __future__ import annotations
import re
from typing import Any
from .const import *

_MOUNT_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")

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

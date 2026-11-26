""""Constants for Network Storage Manager."""
from typing import Final

DOMAIN: Final = "network_storage_manager"

CONF_MOUNT_NAME: Final = "mount_name"
CONF_PROTOCOL: Final = "protocol"
CONF_SERVER: Final = "server"
CONF_SHARE: Final = "share"
CONF_PATH: Final = "path"
CONF_WINDOWS_PATH: Final = "windows_path"
CONF_USERNAME: Final = "username"
CONF_PASSWORD: Final = "password"
CONF_MAKE_DEFAULT: Final = "make_default"
CONF_USAGE: Final = "usage"

USAGE_BACKUP: Final = "backup"
USAGE_MEDIA: Final = "media"
USAGE_SHARE: Final = "share"
STORAGE_USAGES: Final = [USAGE_BACKUP, USAGE_MEDIA, USAGE_SHARE]

PROTOCOL_CIFS: Final = "cifs"
PROTOCOL_NFS: Final = "nfs"

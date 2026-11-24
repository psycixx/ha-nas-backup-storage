"""Constants for NAS Backup Storage."""
from typing import Final

DOMAIN: Final = "nas_backup_storage"

CONF_MOUNT_NAME: Final = "mount_name"
CONF_PROTOCOL: Final = "protocol"
CONF_SERVER: Final = "server"
CONF_SHARE: Final = "share"
CONF_PATH: Final = "path"
CONF_USERNAME: Final = "username"
CONF_PASSWORD: Final = "password"
CONF_MAKE_DEFAULT: Final = "make_default"

PROTOCOL_CIFS: Final = "cifs"
PROTOCOL_NFS: Final = "nfs"

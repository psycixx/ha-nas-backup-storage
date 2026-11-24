"""Tests which do not require Home Assistant."""
import importlib.util
import sys
import types
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1] / "custom_components" / "nas_backup_storage"
package = types.ModuleType("nas_backup_storage")
package.__path__ = [str(ROOT)]
sys.modules["nas_backup_storage"] = package
for name in ("const", "models"):
    spec = importlib.util.spec_from_file_location(f"nas_backup_storage.{name}", ROOT / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

from nas_backup_storage.const import *
from nas_backup_storage.models import validate_mount_input

class MountInputTests(unittest.TestCase):
    def test_cifs_input(self):
        result = validate_mount_input({CONF_MOUNT_NAME: "truenas_backups", CONF_PROTOCOL: PROTOCOL_CIFS, CONF_SERVER: "nas.local", CONF_SHARE: "/backups/", CONF_USERNAME: "ha", CONF_PASSWORD: "secret"})
        self.assertEqual(result[CONF_SHARE], "backups")
    def test_nfs_needs_absolute_path(self):
        with self.assertRaises(ValueError):
            validate_mount_input({CONF_MOUNT_NAME: "nas", CONF_PROTOCOL: PROTOCOL_NFS, CONF_SERVER: "nas.local", CONF_PATH: "mnt/pool/backups"})

"""Tests which do not require Home Assistant."""
import importlib.util
import sys
import types
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1] / "custom_components" / "network_storage_manager"
package = types.ModuleType("network_storage_manager")
package.__path__ = [str(ROOT)]
sys.modules["network_storage_manager"] = package
for name in ("const", "models"):
    spec = importlib.util.spec_from_file_location(f"network_storage_manager.{name}", ROOT / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

from network_storage_manager.const import *
from network_storage_manager.models import validate_mount_input


class MountInputTests(unittest.TestCase):
    def test_cifs_input(self):
        result = validate_mount_input({CONF_MOUNT_NAME: "truenas_backups", CONF_PROTOCOL: PROTOCOL_CIFS, CONF_SERVER: "nas.local", CONF_SHARE: "/backups/", CONF_USERNAME: "ha", CONF_PASSWORD: "secret"})
        self.assertEqual(result[CONF_SHARE], "backups")

    def test_windows_unc_path_populates_server_and_share(self):
        result = validate_mount_input({CONF_MOUNT_NAME: "truenas_backups", CONF_PROTOCOL: PROTOCOL_CIFS, CONF_WINDOWS_PATH: r"\\truenas\backups", CONF_USERNAME: "ha", CONF_PASSWORD: "secret"})
        self.assertEqual(result[CONF_SERVER], "truenas")
        self.assertEqual(result[CONF_SHARE], "backups")

    def test_windows_unc_path_allows_subfolder(self):
        result = validate_mount_input({CONF_MOUNT_NAME: "nas", CONF_PROTOCOL: PROTOCOL_CIFS, CONF_WINDOWS_PATH: r"\\truenas\backups\home-assistant", CONF_USERNAME: "ha", CONF_PASSWORD: "secret"})
        self.assertEqual(result[CONF_SERVER], "truenas")
        self.assertEqual(result[CONF_SHARE], "backups/home-assistant")

    def test_nfs_needs_absolute_path(self):
        with self.assertRaises(ValueError):
            validate_mount_input({CONF_MOUNT_NAME: "nas", CONF_PROTOCOL: PROTOCOL_NFS, CONF_SERVER: "nas.local", CONF_PATH: "mnt/pool/backups"})

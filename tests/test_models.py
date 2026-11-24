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
    spec = importlib.util.spec_from_file_location(
        f"network_storage_manager.{name}", ROOT / f"{name}.py"
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

from network_storage_manager.const import *
from network_storage_manager.models import (
    mount_target_exists,
    prepare_mount_input,
    validate_mount_identity,
    validate_mount_input,
)


class MountInputTests(unittest.TestCase):
    def test_cifs_input(self):
        result = validate_mount_input(
            {
                CONF_MOUNT_NAME: "truenas_backups",
                CONF_PROTOCOL: PROTOCOL_CIFS,
                CONF_SERVER: "nas.local",
                CONF_SHARE: "/backups/",
                CONF_USERNAME: "ha",
                CONF_PASSWORD: "secret",
            }
        )
        self.assertEqual(result[CONF_SHARE], "backups")

    def test_windows_unc_path_populates_server_and_subfolder(self):
        result = validate_mount_input(
            {
                CONF_MOUNT_NAME: "truenas_backups",
                CONF_PROTOCOL: PROTOCOL_CIFS,
                CONF_WINDOWS_PATH: r"\\truenas\backups\home-assistant",
                CONF_USERNAME: "ha",
                CONF_PASSWORD: "secret",
            }
        )
        self.assertEqual(result[CONF_SERVER], "truenas")
        self.assertEqual(result[CONF_SHARE], "backups/home-assistant")

    def test_mount_name_rejects_hyphen_for_supervisor_compatibility(self):
        with self.assertRaisesRegex(ValueError, "invalid_mount_name"):
            validate_mount_identity(
                {CONF_MOUNT_NAME: "truenas-backups", CONF_PROTOCOL: PROTOCOL_CIFS}
            )

    def test_windows_path_requires_two_leading_backslashes(self):
        with self.assertRaisesRegex(ValueError, "invalid_windows_path"):
            prepare_mount_input(
                {
                    CONF_MOUNT_NAME: "nas",
                    CONF_PROTOCOL: PROTOCOL_CIFS,
                    CONF_WINDOWS_PATH: r"\truenas\backups",
                }
            )

    def test_existing_cifs_target_is_detected(self):
        data = validate_mount_input(
            {
                CONF_MOUNT_NAME: "nas",
                CONF_PROTOCOL: PROTOCOL_CIFS,
                CONF_SERVER: "truenas",
                CONF_SHARE: "backups/home-assistant",
                CONF_USERNAME: "ha",
                CONF_PASSWORD: "secret",
            }
        )
        mount = types.SimpleNamespace(
            type="cifs", server="TRUENAS", share="BACKUPS/HOME-ASSISTANT"
        )
        self.assertTrue(mount_target_exists([mount], data))

    def test_other_target_is_not_detected_as_duplicate(self):
        data = validate_mount_input(
            {
                CONF_MOUNT_NAME: "nas",
                CONF_PROTOCOL: PROTOCOL_NFS,
                CONF_SERVER: "truenas",
                CONF_PATH: "/mnt/tank/backups/home-assistant",
            }
        )
        mount = types.SimpleNamespace(type="nfs", server="truenas", path="/mnt/tank/other")
        self.assertFalse(mount_target_exists([mount], data))

    def test_nfs_needs_absolute_path(self):
        with self.assertRaisesRegex(ValueError, "invalid_nfs_path"):
            validate_mount_input(
                {
                    CONF_MOUNT_NAME: "nas",
                    CONF_PROTOCOL: PROTOCOL_NFS,
                    CONF_SERVER: "nas.local",
                    CONF_PATH: "mnt/pool/backups",
                }
            )

    def test_remote_paths_reject_parent_segments(self):
        with self.assertRaisesRegex(ValueError, "invalid_remote_path"):
            validate_mount_input(
                {
                    CONF_MOUNT_NAME: "nas",
                    CONF_PROTOCOL: PROTOCOL_CIFS,
                    CONF_SERVER: "nas.local",
                    CONF_SHARE: "backups/../other",
                    CONF_USERNAME: "ha",
                    CONF_PASSWORD: "secret",
                }
            )

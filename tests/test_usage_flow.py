"""Storage purpose tests with real schemas and mocked Home Assistant services."""

from enum import StrEnum
import importlib.util
import json
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import AsyncMock, Mock, patch

import voluptuous as vol

ROOT = Path(__file__).parents[1] / "custom_components" / "network_storage_manager"


class Selector:
    def __init__(self, config=None):
        self.config = config or {}

    def __call__(self, value):
        if "options" in self.config and value not in self.config["options"]:
            raise vol.Invalid("Unsupported choice")
        return value


class ConfigFlow:
    def __init_subclass__(cls, **kwargs):
        pass

    def async_show_form(self, **kwargs):
        return {"type": "form", **kwargs}

    async def async_set_unique_id(self, value):
        self.unique_id = value

    def _abort_if_unique_id_configured(self):
        pass

    def async_create_entry(self, **kwargs):
        return {"type": "create_entry", **kwargs}


def load_modules():
    modules = {}
    package = types.ModuleType("usage_test_nsm")
    package.__path__ = [str(ROOT)]
    modules[package.__name__] = package
    try:
        from aiohasupervisor.models.mounts import MountUsage
        real_sdk = True
    except ImportError:
        real_sdk = False
        for name in ("aiohasupervisor", "aiohasupervisor.models", "aiohasupervisor.models.mounts"):
            modules[name] = types.ModuleType(name)

        class MountUsage(StrEnum):
            BACKUP = "backup"
            MEDIA = "media"
            SHARE = "share"

        class MountState(StrEnum):
            ACTIVE = "active"
            FAILED = "failed"

        sdk = modules["aiohasupervisor.models.mounts"]
        sdk.MountUsage = MountUsage
        sdk.MountState = MountState
        sdk.CIFSMountRequest = types.SimpleNamespace
        sdk.NFSMountRequest = types.SimpleNamespace
        sdk.MountsOptions = types.SimpleNamespace

    for name in ("homeassistant", "homeassistant.config_entries", "homeassistant.components",
                 "homeassistant.components.hassio", "homeassistant.components.hassio.handler",
                 "homeassistant.helpers", "homeassistant.helpers.selector",
                 "homeassistant.helpers.hassio", "homeassistant.components.sensor",
                 "homeassistant.helpers.device_registry"):
        modules[name] = types.ModuleType(name)
    modules["homeassistant"].config_entries = modules["homeassistant.config_entries"]
    modules["homeassistant.config_entries"].ConfigFlow = ConfigFlow
    modules["homeassistant.components.hassio.handler"].get_supervisor_client = Mock()
    modules["homeassistant.helpers.hassio"].is_hassio = lambda hass: True
    selectors = modules["homeassistant.helpers.selector"]
    for name in ("TextSelector", "SelectSelector", "BooleanSelector"):
        setattr(selectors, name, Selector)
    selectors.SelectSelectorConfig = dict
    selectors.TextSelectorConfig = dict
    selectors.TextSelectorType = types.SimpleNamespace(PASSWORD="password")
    modules["homeassistant.helpers"].selector = selectors
    modules["homeassistant.components.sensor"].SensorEntity = type("SensorEntity", (), {"hass": None})
    modules["homeassistant.components.sensor"].SensorDeviceClass = types.SimpleNamespace(ENUM="enum")
    modules["homeassistant.helpers.device_registry"].DeviceInfo = dict
    loaded = {}
    with patch.dict(sys.modules, modules):
        for name in ("const", "models", "device", "config_flow", "sensor"):
            spec = importlib.util.spec_from_file_location(f"usage_test_nsm.{name}", ROOT / f"{name}.py")
            module = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = module
            spec.loader.exec_module(module)
            loaded[name] = module
    return loaded, real_sdk


MODULES, REAL_SDK = load_modules()
flow_module = MODULES["config_flow"]
sensor_module = MODULES["sensor"]


def field_names(schema):
    return {str(marker.schema) for marker in schema.schema}


class FormTests(unittest.TestCase):
    def test_first_step_offers_all_purposes_and_defaults_to_backup(self):
        schema = flow_module._identity_schema()
        field = next(marker for marker in schema.schema if marker.schema == "usage")
        self.assertEqual(field.default(), "backup")
        self.assertEqual(schema.schema[field].config["options"], ["backup", "media", "share"])
        self.assertEqual(schema.schema[field].config["translation_key"], "storage_usage")

    def test_default_backup_control_only_appears_for_backups(self):
        for factory in (flow_module._smb_schema, flow_module._nfs_schema):
            for usage in ("backup", "media", "share"):
                with self.subTest(factory=factory.__name__, usage=usage):
                    fields = field_names(factory({"usage": usage}))
                    self.assertEqual("make_default" in fields, usage == "backup")

    def test_password_is_never_prefilled_after_form_error(self):
        schema = flow_module._smb_schema({"usage": "media", "password": "test-only-password"})
        field = next(marker for marker in schema.schema if marker.schema == "password")
        self.assertIs(field.default, vol.UNDEFINED)

    def test_translations_cover_all_usages_and_generic_entity_names(self):
        for filename in ("strings.json", "translations/en.json", "translations/de.json"):
            data = json.loads((ROOT / filename).read_text(encoding="utf-8"))
            self.assertIn("usage", data["config"]["step"]["user"]["data"])
            self.assertEqual(set(data["selector"]["storage_usage"]["options"]), {"backup", "media", "share"})
            self.assertEqual(set(data["entity"]["sensor"]["storage_usage"]["state"]), {"backup", "media", "share"})
            self.assertNotIn("backup", data["entity"]["sensor"]["backup_storage_status"]["name"].lower())


class MountCreationTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.flow = flow_module.NasBackupStorageConfigFlow()
        self.flow.hass = object()
        self.client = types.SimpleNamespace(mounts=types.SimpleNamespace(
            info=AsyncMock(), create_mount=AsyncMock(), delete_mount=AsyncMock(), options=AsyncMock()
        ))
        flow_module.get_supervisor_client.return_value = self.client

    def input(self, protocol, usage):
        data = {"mount_name": "nas_storage", "protocol": protocol, "usage": usage,
                "server": "nas.local", "make_default": True}
        return data | ({"share": "storage", "username": "test", "password": "test-only-password"}
                       if protocol == "cifs" else {"path": "/mnt/storage"})

    async def create(self, protocol, usage):
        self.client.mounts.info.side_effect = [
            types.SimpleNamespace(mounts=[]),
            types.SimpleNamespace(mounts=[types.SimpleNamespace(
                name="nas_storage", state=flow_module.MountState.ACTIVE
            )]),
        ]
        return await self.flow._async_create_mount(
            self.input(protocol, usage), "smb" if protocol == "cifs" else "nfs",
            flow_module._smb_schema if protocol == "cifs" else flow_module._nfs_schema,
        )

    async def test_both_protocols_forward_each_usage_and_store_only_safe_data(self):
        for protocol in ("cifs", "nfs"):
            for usage in ("backup", "media", "share"):
                with self.subTest(protocol=protocol, usage=usage):
                    self.client.mounts.create_mount.reset_mock()
                    self.client.mounts.options.reset_mock()
                    result = await self.create(protocol, usage)
                    self.assertEqual(result["type"], "create_entry")
                    request = self.client.mounts.create_mount.await_args.args[1]
                    self.assertEqual(request.usage.value, usage)
                    self.assertEqual(result["data"]["usage"], usage)
                    self.assertNotIn("password", result["data"])
                    self.assertNotIn("username", result["data"])
                    self.assertEqual(result["data"]["make_default"], usage == "backup")
                    self.assertEqual(self.client.mounts.options.await_count, int(usage == "backup"))

    async def test_protocol_step_preserves_usage(self):
        first = await self.flow.async_step_user({
            "mount_name": "nas_media", "protocol": "cifs", "usage": "media"
        })
        self.assertEqual(first["step_id"], "smb")
        self.assertNotIn("make_default", field_names(first["data_schema"]))
        self.assertEqual(self.flow._identity_data["usage"], "media")

    async def test_form_error_keeps_non_backup_purpose(self):
        data = self.input("nfs", "share") | {"server": ""}
        result = await self.flow._async_create_mount(data, "nfs", flow_module._nfs_schema)
        self.assertEqual(result["errors"], {"base": "server_required"})
        self.assertNotIn("make_default", field_names(result["data_schema"]))
        self.client.mounts.create_mount.assert_not_awaited()

    async def test_inactive_mount_is_cleaned_up_without_changing_defaults(self):
        self.client.mounts.info.side_effect = [types.SimpleNamespace(mounts=[]),
            types.SimpleNamespace(mounts=[types.SimpleNamespace(
                name="nas_storage", state=flow_module.MountState.FAILED
            )])]
        result = await self.flow._async_create_mount(
            self.input("nfs", "media"), "nfs", flow_module._nfs_schema
        )
        self.assertEqual(result["errors"], {"base": "mount_not_active"})
        self.client.mounts.delete_mount.assert_awaited_once_with("nas_storage")
        self.client.mounts.options.assert_not_awaited()

    @unittest.skipUnless(REAL_SDK, "SDK serialization is checked by Python 3.13 CI")
    async def test_actual_sdk_serializes_all_mount_purposes(self):
        for protocol in ("cifs", "nfs"):
            for usage in ("backup", "media", "share"):
                await self.create(protocol, usage)
                request = self.client.mounts.create_mount.await_args.args[1]
                self.assertEqual(request.to_dict()["usage"], usage)


class SensorTests(unittest.IsolatedAsyncioTestCase):
    async def test_non_backup_mounts_have_no_default_backup_sensor(self):
        status = types.SimpleNamespace(add_listener=Mock(return_value=lambda: None),
                                       name="nas", last_updated=None, last_error=None)
        for usage in ("backup", "media", "share", None):
            entry = types.SimpleNamespace(entry_id="entry", title="NAS", data={
                "protocol": "nfs", "server": "nas.local", "path": "/mnt/storage"
            })
            if usage is not None:
                entry.data["usage"] = usage
            hass = types.SimpleNamespace(data={"network_storage_manager": {"entry": {"status": status}}})
            entities = []
            await sensor_module.async_setup_entry(hass, entry, entities.extend)
            purposes = [e for e in entities if isinstance(e, sensor_module.StorageUsageSensor)]
            self.assertEqual(purposes[0].native_value, usage or "backup")
            defaults = [e for e in entities if isinstance(e, sensor_module.StorageDefaultSensor)]
            self.assertEqual(len(defaults), int(usage in ("backup", None)))
            attributes = entities[0].extra_state_attributes
            self.assertEqual("default_backup_location" in attributes, usage in ("backup", None))


if __name__ == "__main__":
    unittest.main()

import importlib
import json
import sys
import tempfile
import types
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
AGENT_ROOT = PROJECT_ROOT / "3d_agent"
if str(AGENT_ROOT) not in sys.path:
    sys.path.insert(0, str(AGENT_ROOT))


class FakeVector:
    def __init__(self, x: float, y: float, z: float) -> None:
        self.x = x
        self.y = y
        self.z = z


class FakeModifier:
    def __init__(self, name: str, type: str) -> None:
        self.name = name
        self.type = type
        self.width = 0.0
        self.segments = 0


class FakeModifiers:
    def __init__(self) -> None:
        self._items: list[FakeModifier] = []

    def __iter__(self):
        return iter(self._items)

    def get(self, name: str) -> FakeModifier | None:
        return next((modifier for modifier in self._items if modifier.name == name), None)

    def new(self, name: str, type: str) -> FakeModifier:
        modifier = FakeModifier(name, type)
        self._items.append(modifier)
        return modifier

    def remove(self, modifier: FakeModifier) -> None:
        self._items.remove(modifier)


class FakeObject:
    def __init__(self, name: str) -> None:
        self.name = name
        self.type = "MESH"
        self.data = types.SimpleNamespace(name=f"{name}_Mesh")
        self.dimensions = FakeVector(1.0, 2.0, 3.0)
        self.location = FakeVector(4.0, 5.0, 6.0)
        self.rotation_euler = FakeVector(0.1, 0.2, 0.3)
        self.scale = FakeVector(1.0, 1.0, 1.0)
        self.modifiers = FakeModifiers()


class FakeObjects:
    def __init__(self, objects: list[FakeObject]) -> None:
        self._objects = {blender_object.name: blender_object for blender_object in objects}

    def get(self, name: str) -> FakeObject | None:
        return self._objects.get(name)


class FakeWindowManagerOps:
    def __init__(self) -> None:
        self.saved_paths: list[str] = []

    def save_as_mainfile(self, filepath: str) -> None:
        self.saved_paths.append(filepath)


def make_fake_bpy(blender_object: FakeObject, source_file: Path):
    window_manager_ops = FakeWindowManagerOps()
    return types.SimpleNamespace(
        data=types.SimpleNamespace(objects=FakeObjects([blender_object]), filepath=str(source_file)),
        ops=types.SimpleNamespace(wm=window_manager_ops),
    )


class Phase2CoreGeometryApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.source_file = Path(self.temp_dir.name) / "source.blend"
        self.source_file.write_bytes(b"blend")
        self.blender_object = FakeObject("Body")
        self.fake_bpy = make_fake_bpy(self.blender_object, self.source_file)
        sys.modules["bpy"] = self.fake_bpy
        import core_api as core_geometry_api

        self.core_geometry_api = importlib.reload(core_geometry_api)
        self.core_geometry_api.reset_modification_report_state()

    def tearDown(self) -> None:
        sys.modules.pop("bpy", None)
        self.temp_dir.cleanup()

    def test_require_object_returns_existing_object(self) -> None:
        self.assertIs(self.core_geometry_api.require_object("Body"), self.blender_object)

        with self.assertRaises(LookupError):
            self.core_geometry_api.require_object("Missing")

    def test_object_snapshot_is_json_serializable(self) -> None:
        self.blender_object.modifiers.new(name="Existing", type="BEVEL")

        snapshot = self.core_geometry_api.object_snapshot(self.blender_object)

        self.assertEqual(snapshot["name"], "Body")
        self.assertEqual(snapshot["type"], "MESH")
        self.assertEqual(snapshot["dimensions"], [1.0, 2.0, 3.0])
        self.assertEqual(snapshot["location"], [4.0, 5.0, 6.0])
        self.assertEqual(snapshot["modifiers"][0]["name"], "Existing")
        json.dumps(snapshot)

    def test_add_bevel_modifier_replaces_named_modifier_and_records_report(self) -> None:
        self.blender_object.modifiers.new(name="AI_Bevel", type="BEVEL")

        modifier = self.core_geometry_api.add_bevel_modifier(self.blender_object, 0.02, 2, "AI_Bevel")
        report = self.core_geometry_api.build_modification_report()

        self.assertEqual(modifier.name, "AI_Bevel")
        self.assertEqual(modifier.type, "BEVEL")
        self.assertEqual(modifier.width, 0.02)
        self.assertEqual(modifier.segments, 2)
        self.assertEqual(len(list(self.blender_object.modifiers)), 1)
        self.assertEqual(report["modified_objects"][0]["change_type"], "modifier_added")
        self.assertEqual(report["removed_modifiers"][0]["modifier"]["name"], "AI_Bevel")
        self.assertFalse(report["saved_original_file"])

    def test_save_as_copy_only_refuses_source_and_records_output_copy(self) -> None:
        output_file = Path(self.temp_dir.name) / "copies" / "output.blend"

        saved_path = self.core_geometry_api.save_as_copy_only(self.source_file, output_file)
        report = self.core_geometry_api.build_modification_report()

        self.assertEqual(saved_path, str(output_file))
        self.assertEqual(self.fake_bpy.ops.wm.saved_paths, [str(output_file)])
        self.assertEqual(report["source_blend_file"], str(self.source_file))
        self.assertEqual(report["output_blend_copy"], str(output_file))

        with self.assertRaises(RuntimeError):
            self.core_geometry_api.save_as_copy_only(self.source_file, self.source_file)

    def test_write_modification_report_writes_json(self) -> None:
        self.core_geometry_api.add_bevel_modifier(self.blender_object, 0.01, 1, "AI_Test_Bevel")
        report_file = Path(self.temp_dir.name) / "reports" / "modification_report.json"

        written_path = self.core_geometry_api.write_modification_report(report_file)
        report = json.loads(report_file.read_text(encoding="utf-8"))

        self.assertEqual(written_path, str(report_file))
        self.assertEqual(report["report_version"], "core_geometry_api_v1")
        self.assertEqual(report["modified_objects"][0]["modifier_type"], "BEVEL")

    def test_write_modification_report_can_write_provided_user_report(self) -> None:
        report_file = Path(self.temp_dir.name) / "reports" / "user_report.json"
        user_report = {
            "operation": "edge_soften",
            "object_name": "Body",
            "implementation": {
                "method": "modifier",
                "modifier_name": "AI_PanelLine_Bevel",
                "modifier_type": "BEVEL",
            },
            "parameters": {"strength": 0.01},
            "mesh_data_applied": False,
        }

        self.core_geometry_api.write_modification_report(report_file, user_report)
        report = json.loads(report_file.read_text(encoding="utf-8"))

        self.assertEqual(report, user_report)

    def test_split_core_api_modules_are_used_by_compatibility_wrapper(self) -> None:
        import blender_ops.core_geometry_api as compatibility_wrapper

        wrapper_source = Path(compatibility_wrapper.__file__).read_text(encoding="utf-8")
        domain_source = (AGENT_ROOT / "blender_ops" / "domain_operations.py").read_text(encoding="utf-8")

        self.assertIs(compatibility_wrapper.require_object, self.core_geometry_api.require_object)
        self.assertIs(compatibility_wrapper.add_bevel_modifier, self.core_geometry_api.add_bevel_modifier)
        self.assertNotIn("import bpy", wrapper_source)
        self.assertNotIn("bpy.", wrapper_source)
        self.assertNotIn("from blender_ops import core_geometry_api", domain_source)
        self.assertIn("import core_api as core_geometry_api", domain_source)


if __name__ == "__main__":
    unittest.main()
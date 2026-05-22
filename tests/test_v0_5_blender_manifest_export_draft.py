import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
AGENT_ROOT = PROJECT_ROOT / "3d_agent"
if str(AGENT_ROOT) not in sys.path:
    sys.path.insert(0, str(AGENT_ROOT))

from agent.blender_manifest_export_draft import create_blender_manifest_export_draft


class V05BlenderManifestExportDraftTests(unittest.TestCase):
    def test_manifest_export_draft_contains_v0_5_contract_fields(self) -> None:
        script = create_blender_manifest_export_draft("exports/demo_manifest.json")

        self.assertIn('"manifest_version": "v0_5"', script)
        self.assertIn('"source_software": "blender"', script)
        self.assertIn('"objects": [object_manifest(scene_object)', script)
        self.assertIn('"object_name": target_object.name', script)
        self.assertIn('"object_type": target_object.type', script)
        self.assertIn('"collection_path": collection_path_for_object(target_object)', script)
        self.assertIn('"dimensions": vector3(target_object.dimensions)', script)
        self.assertIn('"custom_properties": safe_custom_properties(target_object)', script)

    def test_manifest_export_draft_uses_requested_output_path(self) -> None:
        script = create_blender_manifest_export_draft("exports/demo_manifest.json")

        self.assertIn("output_path = Path('exports/demo_manifest.json')", script)
        self.assertIn("output_path.write_text", script)

    def test_manifest_export_draft_is_read_only_for_blender_scene(self) -> None:
        script = create_blender_manifest_export_draft()

        self.assertIn("only reads scene object metadata", script)
        self.assertIn("It does not edit mesh geometry", script)
        self.assertNotIn("bpy.data.objects.new", script)
        self.assertNotIn("bpy.ops.object.modifier_apply", script)
        self.assertNotIn("bpy.ops.wm.save_as_mainfile", script)
        self.assertNotIn("bpy.ops.mesh", script)
        self.assertNotIn(".modifiers.new", script)

    def test_manifest_export_draft_reads_scene_objects(self) -> None:
        script = create_blender_manifest_export_draft()

        self.assertIn("for scene_object in bpy.context.scene.objects", script)
        self.assertIn("target_object.material_slots", script)
        self.assertIn("target_object.keys()", script)


if __name__ == "__main__":
    unittest.main()
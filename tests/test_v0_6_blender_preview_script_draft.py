import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
AGENT_ROOT = PROJECT_ROOT / "3d_agent"
if str(AGENT_ROOT) not in sys.path:
    sys.path.insert(0, str(AGENT_ROOT))

from agent.blender_preview_script_draft import create_blender_preview_script_draft
from agent.geometry_preview import create_geometry_preview_plan
from agent.safe_preview_session import create_safe_preview_session
from main import build_cli_result
from model.model_binding import create_model_binding_context, review_execution_package_with_binding
from model.scene_manifest import load_scene_manifest


SCENE_MANIFEST_PATH = PROJECT_ROOT / "examples" / "blender_scene_manifest.json"


class V06BlenderPreviewScriptDraftTests(unittest.TestCase):
    def _preview_script(self, user_input: str) -> str:
        result = build_cli_result(user_input, scene_manifest_path=str(SCENE_MANIFEST_PATH))
        plan = create_geometry_preview_plan(
            result["execution_package"],
            result["model_binding_context"],
            result["execution_package_review"],
        )
        session = create_safe_preview_session(plan)
        return create_blender_preview_script_draft(plan, session)

    def test_preview_script_contains_preview_contract_and_collection_creation(self) -> None:
        script = self._preview_script("给胸甲加一些锐利的分件线，适合 1/144 打印。")

        self.assertIn("V0.6 Blender Preview Script Draft", script)
        self.assertIn("preview-only generated visual guide objects", script)
        self.assertIn("geometry_preview_plan = json.loads", script)
        self.assertIn("safe_preview_session = json.loads", script)
        self.assertIn("collection_name = 'V06_chest_armor_preview'", script)
        self.assertIn("bpy.data.collections.new", script)
        self.assertIn("bpy.data.objects.new", script)
        self.assertIn("create_visual_guide_object", script)
        self.assertIn("generated_visual_guides", script)
        self.assertIn("preview_report", script)
        self.assertIn("report_path.write_text", script)

    def test_preview_script_tags_generated_objects_for_rollback(self) -> None:
        script = self._preview_script("把背包的推进器做得更高机动一点，加喷口和机械细节。")

        self.assertIn('preview_object["v0_6_preview_session_id"] = session_id', script)
        self.assertIn('preview_object["source_task_id"]', script)
        self.assertIn('preview_object["target_object"]', script)
        self.assertIn('preview_object["element_type"]', script)
        self.assertIn('preview_object["requires_user_confirmation"]', script)
        self.assertIn("generated_object_names.append", script)

    def test_preview_script_does_not_include_destructive_blender_ops(self) -> None:
        script = self._preview_script("给两条腿加同样的管线和液压杆，密度中等。")

        self.assertIn("does not edit bound mesh data", script)
        self.assertNotIn("bpy.ops", script)
        self.assertNotIn("modifier_apply", script)
        self.assertNotIn("save_as_mainfile", script)
        self.assertNotIn("bpy.ops.object.delete", script)
        self.assertNotIn("bpy.ops.mesh", script)
        self.assertNotIn(".modifiers.new", script)

    def test_blocked_preview_script_writes_report_only(self) -> None:
        result = build_cli_result("给胸甲加一些锐利的分件线，适合 1/144 打印。", include_execution_package=True)
        manifest = load_scene_manifest(SCENE_MANIFEST_PATH)
        binding_context = create_model_binding_context(manifest, "unknown_part", result["execution_package"])
        review = review_execution_package_with_binding(result["execution_package"], binding_context)
        plan = create_geometry_preview_plan(result["execution_package"], binding_context, review)
        session = create_safe_preview_session(plan)
        script = create_blender_preview_script_draft(plan, session)

        self.assertIn("Preview is blocked; this draft writes report data only", script)
        self.assertIn("preview_report", script)
        self.assertIn("report_path.write_text", script)
        self.assertNotIn("import bpy", script)
        self.assertNotIn("bpy.data.collections.new", script)
        self.assertNotIn("bpy.data.objects.new", script)


if __name__ == "__main__":
    unittest.main()
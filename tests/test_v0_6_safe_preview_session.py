import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
AGENT_ROOT = PROJECT_ROOT / "3d_agent"
if str(AGENT_ROOT) not in sys.path:
    sys.path.insert(0, str(AGENT_ROOT))

from agent.geometry_preview import create_geometry_preview_plan
from agent.safe_preview_session import create_safe_preview_session
from main import build_cli_result
from model.model_binding import create_model_binding_context, review_execution_package_with_binding
from model.scene_manifest import load_scene_manifest


SCENE_MANIFEST_PATH = PROJECT_ROOT / "examples" / "blender_scene_manifest.json"


class V06SafePreviewSessionTests(unittest.TestCase):
    def _preview_plan(self, user_input: str) -> dict:
        result = build_cli_result(user_input, scene_manifest_path=str(SCENE_MANIFEST_PATH))
        return create_geometry_preview_plan(
            result["execution_package"],
            result["model_binding_context"],
            result["execution_package_review"],
        )

    def test_safe_preview_session_outputs_contract_fields(self) -> None:
        plan = self._preview_plan("给胸甲加一些锐利的分件线，适合 1/144 打印。")
        session = create_safe_preview_session(plan)

        self.assertEqual(
            set(session),
            {
                "session_version",
                "session_id",
                "execution_mode",
                "target_software",
                "allowed_operations",
                "forbidden_operations",
                "preflight_checks",
                "generated_artifacts",
                "rollback_strategy",
            },
        )
        self.assertEqual(session["session_version"], "v0_6")
        self.assertEqual(session["session_id"], "v06_chest_armor_preview_001")
        self.assertEqual(session["execution_mode"], "preview_only")
        self.assertEqual(session["target_software"], "blender")

    def test_preview_ready_session_allows_only_preview_operations(self) -> None:
        plan = self._preview_plan("给胸甲加一些锐利的分件线，适合 1/144 打印。")
        session = create_safe_preview_session(plan)

        self.assertIn("create_preview_collection", session["allowed_operations"])
        self.assertIn("create_generated_preview_object", session["allowed_operations"])
        self.assertIn("tag_generated_preview_object", session["allowed_operations"])
        self.assertIn("write_preview_report_json", session["allowed_operations"])
        self.assertNotIn("edit_bound_mesh", session["allowed_operations"])
        self.assertIn("edit_bound_mesh", session["forbidden_operations"])
        self.assertIn("boolean_operation", session["forbidden_operations"])
        self.assertIn("save_blend_file", session["forbidden_operations"])

    def test_session_records_preflight_checks_and_artifacts(self) -> None:
        plan = self._preview_plan("把背包的推进器做得更高机动一点，加喷口和机械细节。")
        session = create_safe_preview_session(plan)

        self.assertIn("verify_preview_plan_version_v0_6", session["preflight_checks"])
        self.assertIn("verify_execution_mode_preview_only", session["preflight_checks"])
        self.assertIn("verify_bound_mesh_is_read_only", session["preflight_checks"])
        self.assertIn("verify_target_object_exists:Backpack_Block_01", session["preflight_checks"])
        self.assertIn("verify_user_confirmation_for_preview_elements", session["preflight_checks"])
        artifact_types = {artifact["artifact_type"] for artifact in session["generated_artifacts"]}
        self.assertIn("preview_collection", artifact_types)
        self.assertIn("generated_preview_object", artifact_types)
        self.assertIn("preview_report_json", artifact_types)

    def test_blocked_session_only_allows_preview_report(self) -> None:
        result = build_cli_result("给胸甲加一些锐利的分件线，适合 1/144 打印。", include_execution_package=True)
        manifest = load_scene_manifest(SCENE_MANIFEST_PATH)
        binding_context = create_model_binding_context(manifest, "unknown_part", result["execution_package"])
        review = review_execution_package_with_binding(result["execution_package"], binding_context)
        plan = create_geometry_preview_plan(result["execution_package"], binding_context, review)
        session = create_safe_preview_session(plan)

        self.assertEqual(session["session_id"], "v06_chest_armor_blocked_001")
        self.assertEqual(session["allowed_operations"], ["write_preview_report_json"])
        self.assertIn("stop_if_preview_status_blocked", session["preflight_checks"])
        artifact_types = [artifact["artifact_type"] for artifact in session["generated_artifacts"]]
        self.assertEqual(artifact_types, ["preview_report_json"])

    def test_rollback_strategy_targets_generated_session_objects_only(self) -> None:
        plan = self._preview_plan("给两条腿加同样的管线和液压杆，密度中等。")
        session = create_safe_preview_session(plan)

        self.assertTrue(any("v0_6_preview_session_id=v06_leg_preview_001" in step for step in session["rollback_strategy"]))
        self.assertTrue(any("保留用户原始对象" in step for step in session["rollback_strategy"]))
        self.assertTrue(any("目标 mesh" in step for step in session["rollback_strategy"]))


if __name__ == "__main__":
    unittest.main()
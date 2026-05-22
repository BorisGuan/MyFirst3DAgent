import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
AGENT_ROOT = PROJECT_ROOT / "3d_agent"
if str(AGENT_ROOT) not in sys.path:
    sys.path.insert(0, str(AGENT_ROOT))

from agent.geometry_preview import create_geometry_preview_plan
from main import build_cli_result
from model.model_binding import create_model_binding_context, review_execution_package_with_binding
from model.scene_manifest import load_scene_manifest, normalize_scene_manifest


SCENE_MANIFEST_PATH = PROJECT_ROOT / "examples" / "blender_scene_manifest.json"


class V06GeometryPreviewTests(unittest.TestCase):
    def _v05_result(self, user_input: str) -> dict:
        return build_cli_result(user_input, scene_manifest_path=str(SCENE_MANIFEST_PATH))

    def _preview_plan_from_result(self, result: dict) -> dict:
        return create_geometry_preview_plan(
            result["execution_package"],
            result["model_binding_context"],
            result["execution_package_review"],
        )

    def test_chest_preview_plan_outputs_contract_fields(self) -> None:
        result = self._v05_result("给胸甲加一些锐利的分件线，适合 1/144 打印。")
        plan = self._preview_plan_from_result(result)

        self.assertEqual(
            set(plan),
            {
                "preview_version",
                "source_package_ref",
                "source_binding_ref",
                "source_review_ref",
                "target_part",
                "preview_mode",
                "preview_status",
                "target_objects",
                "preview_elements",
                "required_confirmations",
                "blocked_by",
                "safety_rules",
                "rollback_plan",
                "preview_summary",
            },
        )
        self.assertEqual(plan["preview_version"], "v0_6")
        self.assertEqual(plan["source_package_ref"], "execution_package")
        self.assertEqual(plan["source_binding_ref"], "model_binding_context")
        self.assertEqual(plan["source_review_ref"], "execution_package_review")
        self.assertEqual(plan["target_part"], "chest_armor")
        self.assertEqual(plan["preview_status"], "preview_ready")
        self.assertEqual(plan["target_objects"], ["ChestArmor_Upper_01"])
        self.assertIn("no_surface_boundaries", plan["blocked_by"])
        self.assertIn("preview_only", plan["safety_rules"])
        self.assertIn("do_not_modify_bound_mesh", plan["safety_rules"])
        self.assertTrue(any("v0_6_preview_session_id" in step for step in plan["rollback_plan"]))
        self.assertTrue(
            any(
                element["element_type"] in {"panel_line_hint", "surface_detail_hint"}
                for element in plan["preview_elements"]
            )
        )

    def test_backpack_preview_uses_placeholder_or_mounting_hint(self) -> None:
        result = self._v05_result("把背包的推进器做得更高机动一点，加喷口和机械细节。")
        plan = self._preview_plan_from_result(result)

        self.assertEqual(plan["preview_status"], "preview_ready")
        self.assertEqual(plan["preview_mode"], "bounding_box_overlay")
        self.assertEqual(plan["target_objects"], ["Backpack_Block_01"])
        self.assertTrue(
            any(
                element["element_type"] in {"placeholder_volume", "mounting_point_hint"}
                for element in plan["preview_elements"]
            )
        )
        self.assertIn("no_mounting_surface", plan["blocked_by"])

    def test_leg_preview_keeps_joint_confirmation_for_multiple_objects(self) -> None:
        result = self._v05_result("给两条腿加同样的管线和液压杆，密度中等。")
        plan = self._preview_plan_from_result(result)

        self.assertEqual(plan["preview_status"], "preview_ready")
        self.assertEqual(set(plan["target_objects"]), {"LeftLeg_Armor_01", "RightLeg_Armor_01"})
        self.assertIn("no_joint_range_data", plan["blocked_by"])
        self.assertTrue(any("关节" in item for item in plan["required_confirmations"]))
        self.assertTrue(
            any(
                element["element_type"] in {"manual_review_note", "risk_marker"}
                for element in plan["preview_elements"]
            )
        )

    def test_candidate_binding_requires_user_confirmation(self) -> None:
        result = build_cli_result("给胸甲加一些锐利的分件线，适合 1/144 打印。", include_execution_package=True)
        candidate_manifest = normalize_scene_manifest(
            {
                "manifest_version": "v0_5",
                "source_software": "blender",
                "source_file": "candidate.blend",
                "objects": [
                    {
                        "object_name": "ChestArmor_Candidate",
                        "object_type": "MESH",
                        "collection_path": ["Gundam", "Body", "Chest"],
                        "material_names": ["armor_white"],
                    }
                ],
            }
        )
        binding_context = create_model_binding_context(
            candidate_manifest,
            "chest_armor",
            result["execution_package"],
        )
        review = review_execution_package_with_binding(result["execution_package"], binding_context)
        plan = create_geometry_preview_plan(result["execution_package"], binding_context, review)

        self.assertEqual(plan["preview_status"], "needs_user_confirmation")
        self.assertEqual(plan["target_objects"], ["ChestArmor_Candidate"])
        self.assertTrue(any("候选绑定对象" in item for item in plan["required_confirmations"]))
        self.assertTrue(all(element["requires_user_confirmation"] for element in plan["preview_elements"]))

    def test_blocked_review_does_not_generate_preview_elements(self) -> None:
        result = build_cli_result("给胸甲加一些锐利的分件线，适合 1/144 打印。", include_execution_package=True)
        manifest = load_scene_manifest(SCENE_MANIFEST_PATH)
        binding_context = create_model_binding_context(manifest, "unknown_part", result["execution_package"])
        review = review_execution_package_with_binding(result["execution_package"], binding_context)
        plan = create_geometry_preview_plan(result["execution_package"], binding_context, review)

        self.assertEqual(plan["preview_status"], "blocked")
        self.assertEqual(plan["preview_mode"], "blocked")
        self.assertEqual(plan["target_objects"], [])
        self.assertEqual(plan["preview_elements"], [])
        self.assertIn("no_trusted_bound_object", plan["blocked_by"])


if __name__ == "__main__":
    unittest.main()
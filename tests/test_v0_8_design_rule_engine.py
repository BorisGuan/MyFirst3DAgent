import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
AGENT_ROOT = PROJECT_ROOT / "3d_agent"
if str(AGENT_ROOT) not in sys.path:
    sys.path.insert(0, str(AGENT_ROOT))

from agent.design_rule_engine import load_mecha_design_rules, review_mecha_design_rules
from main import build_cli_result, parse_cli_args


SCENE_MANIFEST_PATH = PROJECT_ROOT / "examples" / "blender_scene_manifest.json"


class V08DesignRuleEngineTests(unittest.TestCase):
    def test_rule_pack_loads_v0_8_rules(self) -> None:
        rules = load_mecha_design_rules()

        self.assertEqual(rules["rule_pack_version"], "v0_8")
        self.assertIn("chest_armor", rules["part_rules"])
        self.assertIn("preview_before_mesh_edit", rules["default_geometry_constraints"])

    def test_chest_parting_lines_pass_with_chest_constraints(self) -> None:
        review = review_mecha_design_rules(
            {
                "operation": "add_parting_lines",
                "target_part": "chest_armor",
                "scale": "1/144",
                "density": "medium",
            },
            {"target_part": "chest_armor"},
            "给胸甲加一些锐利的分件线，适合 1/144 打印。",
        )

        self.assertEqual(review["review_version"], "v0_8")
        self.assertEqual(review["status"], "passed_with_warnings")
        self.assertEqual(review["requested_detail_type"], "parting_lines")
        self.assertIn("parting_lines", review["recommended_detail_types"])
        self.assertIn("keep_center_mass_readable", review["geometry_constraints"])
        self.assertIn("scale_rules.1/144", review["matched_rules"])

    def test_chest_thruster_request_is_blocked(self) -> None:
        review = review_mecha_design_rules(
            {
                "operation": "add_thrusters",
                "target_part": "chest_armor",
                "scale": "1/144",
                "density": "medium",
            },
            {"target_part": "chest_armor"},
            "给胸甲加大型推进器。",
        )

        self.assertEqual(review["status"], "blocked")
        self.assertIn("thrusters", review["blocked_detail_types"])
        self.assertIn("detail_type_not_recommended_for_chest_armor", review["blockers"])
        self.assertTrue(review["requires_user_confirmation"])

    def test_leg_single_target_request_warns_about_symmetry(self) -> None:
        review = review_mecha_design_rules(
            {
                "operation": "add_hydraulic_rods",
                "target_part": "leg_armor",
                "scale": "1/100",
                "density": "medium",
                "symmetry": "single_target",
            },
            {"target_part": "leg_armor"},
            "给腿部加液压杆。",
        )

        self.assertEqual(review["status"], "passed_with_warnings")
        self.assertIn("symmetry_rules.leg_armor", review["matched_rules"])
        self.assertTrue(any("symmetry" in item for item in review["requires_user_confirmation"]))

    def test_overwrite_source_blend_intent_is_blocked(self) -> None:
        review = review_mecha_design_rules(
            {
                "operation": "add_parting_lines",
                "target_part": "chest_armor",
                "scale": "1/144",
                "density": "medium",
            },
            {"target_part": "chest_armor"},
            "给胸甲加分件线并覆盖保存原文件。",
        )

        self.assertEqual(review["status"], "blocked")
        self.assertIn("overwrite_source_blend", review["blockers"])
        self.assertIn("blocked_user_intents.overwrite_source_blend", review["matched_rules"])

    def test_cli_can_include_design_rule_review_explicitly(self) -> None:
        result = build_cli_result(
            "给胸甲加一些锐利的分件线，适合 1/144 打印。",
            include_design_rule_review=True,
        )

        self.assertIn("execution_package", result)
        self.assertIn("design_rule_review", result)
        self.assertEqual(result["design_rule_review"]["review_version"], "v0_8")

    def test_cli_geometry_preview_includes_design_rule_review(self) -> None:
        result = build_cli_result(
            "给胸甲加一些锐利的分件线，适合 1/144 打印。",
            scene_manifest_path=str(SCENE_MANIFEST_PATH),
            include_geometry_preview=True,
        )

        self.assertIn("design_rule_review", result)
        self.assertIn("geometry_preview_plan", result)
        self.assertIn("preview_before_mesh_edit", result["design_rule_review"]["geometry_constraints"])

    def test_parse_cli_args_accepts_design_rule_review_flag(self) -> None:
        parsed = parse_cli_args(["给胸甲加分件线", "--design-rule-review"])

        self.assertEqual(tuple(parsed)[0], "给胸甲加分件线")
        self.assertTrue(parsed.include_design_rule_review)


if __name__ == "__main__":
    unittest.main()
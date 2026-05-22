import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
AGENT_ROOT = PROJECT_ROOT / "3d_agent"
if str(AGENT_ROOT) not in sys.path:
    sys.path.insert(0, str(AGENT_ROOT))

from agent.formatter import format_blueprint
from agent.intent_parser import parse_intent
from agent.loop import run_agent
from agent.planner import create_plan
from agent.risk_checker import evaluate_risks
from model.context_manager import ContextManager
from model.schemas import OperationPlan


class V02BlueprintTests(unittest.TestCase):
    def setUp(self) -> None:
        self.context_manager = ContextManager()
        self.model_context = self.context_manager.raw_model_context()
        self.planner_context = self.context_manager.summary_for_planner()

    def test_operation_plan_outputs_all_v2_fields(self) -> None:
        plan = OperationPlan(
            target_part="chest_armor",
            operation="add_parting_lines",
            detail_type="parting_lines",
            style="sharp_mechanical",
            density="medium",
            symmetry="single_target",
            scale="1/144",
            placement_zones=["upper_chest_plate"],
            constraints=["keep_line_density_readable"],
            steps=["确认胸甲主要可见面。"],
            risk_notes=["1/144 比例下刻线或分件线需要控制宽度和间距。"],
            reasoning="用户希望胸甲增加锐利分件线。",
            designer_brief="建议在胸甲添加锐利分件线。",
        ).to_dict()

        self.assertEqual(
            set(plan),
            {
                "target_part",
                "operation",
                "detail_type",
                "style",
                "density",
                "symmetry",
                "scale",
                "placement_zones",
                "constraints",
                "steps",
                "risk_notes",
                "reasoning",
                "designer_brief",
            },
        )

    def test_planner_accepts_valid_v2_plan(self) -> None:
        intent = parse_intent("给胸甲加一些锐利的分件线，适合 1/144 打印。", self.planner_context)
        plan = create_plan(intent, self.model_context)

        self.assertEqual(plan["target_part"], "chest_armor")
        self.assertEqual(plan["operation"], "add_parting_lines")
        self.assertEqual(plan["style"], "sharp_mechanical")
        self.assertEqual(plan["scale"], "1/144")

    def test_planner_rejects_invalid_enum(self) -> None:
        intent = parse_intent("给胸甲加一些锐利的分件线，适合 1/144 打印。", self.planner_context)
        intent["operation"] = "add_magic_detail"

        with self.assertRaisesRegex(ValueError, "operation must be one of"):
            create_plan(intent, self.model_context)

    def test_mock_parser_outputs_complete_v2_fields(self) -> None:
        intent = parse_intent("给两条腿加同样的管线和液压杆，密度中等。", self.planner_context)

        self.assertEqual(intent["target_part"], "leg")
        self.assertIn(intent["detail_type"], {"pipes", "hydraulic_rods"})
        self.assertIn(intent["symmetry"], {"left_right_mirror", "group_sync"})
        self.assertIsInstance(intent["placement_zones"], list)
        self.assertIsInstance(intent["steps"], list)
        self.assertTrue(intent["designer_brief"])

    def test_risk_checker_adds_high_risk_antenna_notes(self) -> None:
        intent = parse_intent("给 V 字天线加大量刻线，比例 1/144。", self.planner_context)
        plan = create_plan(intent, self.model_context)
        plan = evaluate_risks(plan, self.model_context)

        combined_notes = " ".join(plan["risk_notes"])
        self.assertIn("1/144", combined_notes)
        self.assertIn("天线", combined_notes)

    def test_formatter_adds_non_empty_display_fields(self) -> None:
        intent = parse_intent("给盾牌加少量战损和旧化，不要太脏。", self.planner_context)
        plan = create_plan(intent, self.model_context)
        plan = evaluate_risks(plan, self.model_context)
        formatted = format_blueprint(plan)

        self.assertTrue(formatted["designer_brief"])
        self.assertTrue(formatted["user_message"])
        self.assertIn("保持克制处理", formatted["designer_brief"])

    def test_run_agent_model_edit_outputs_complete_blueprint(self) -> None:
        result = run_agent("给胸甲加一些锐利的分件线，适合 1/144 打印。")

        self.assertEqual(result["command_type"], "model_edit")
        self.assertEqual(result["target_part"], "chest_armor")
        self.assertEqual(result["operation"], "add_parting_lines")
        self.assertGreaterEqual(len(result["steps"]), 3)
        self.assertGreaterEqual(len(result["risk_notes"]), 1)
        self.assertTrue(result["designer_brief"])
        self.assertTrue(result["user_message"])


if __name__ == "__main__":
    unittest.main()
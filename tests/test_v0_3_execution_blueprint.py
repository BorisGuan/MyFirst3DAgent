import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
AGENT_ROOT = PROJECT_ROOT / "3d_agent"
if str(AGENT_ROOT) not in sys.path:
    sys.path.insert(0, str(AGENT_ROOT))

from agent.execution_blueprint import create_execution_blueprint
from agent.intent_parser import parse_intent
from agent.loop import run_agent
from agent.planner import create_plan
from agent.risk_checker import evaluate_risks
from main import build_cli_result
from model.context_manager import ContextManager


class V03ExecutionBlueprintTests(unittest.TestCase):
    def setUp(self) -> None:
        self.context_manager = ContextManager()
        self.model_context = self.context_manager.raw_model_context()
        self.planner_context = self.context_manager.summary_for_planner()

    def _operation_plan_from_text(self, user_input: str) -> dict:
        intent = parse_intent(user_input, self.planner_context)
        plan = create_plan(intent, self.model_context)
        return evaluate_risks(plan, self.model_context)

    def test_execution_blueprint_outputs_contract_fields(self) -> None:
        operation_plan = self._operation_plan_from_text(
            "给胸甲加一些锐利的分件线，适合 1/144 打印。"
        )
        blueprint = create_execution_blueprint(operation_plan, self.model_context)

        self.assertEqual(
            set(blueprint),
            {
                "source_plan_ref",
                "target_part",
                "execution_intent",
                "operation_template",
                "zone_mapping",
                "automation_assessment",
                "risk_review",
                "execution_brief",
            },
        )
        self.assertEqual(blueprint["source_plan_ref"], "operation_plan_v2")
        self.assertEqual(blueprint["target_part"], "chest_armor")

    def test_parting_lines_maps_to_surface_detailing(self) -> None:
        operation_plan = self._operation_plan_from_text(
            "给胸甲加一些锐利的分件线，适合 1/144 打印。"
        )
        blueprint = create_execution_blueprint(operation_plan, self.model_context)

        self.assertEqual(blueprint["execution_intent"]["tool_family"], "surface_detailing")
        self.assertEqual(
            blueprint["execution_intent"]["recommended_method"],
            "parting_line_planning",
        )
        self.assertEqual(blueprint["automation_assessment"]["difficulty"], "medium")
        self.assertIn("no_real_mesh", blueprint["automation_assessment"]["blocked_by"])
        self.assertTrue(blueprint["automation_assessment"]["v0_4_candidate"])

    def test_thrusters_maps_to_propulsion_detailing(self) -> None:
        operation_plan = self._operation_plan_from_text(
            "把背包的推进器做得更高机动一点，加喷口和机械细节。"
        )
        blueprint = create_execution_blueprint(operation_plan, self.model_context)

        self.assertEqual(blueprint["execution_intent"]["tool_family"], "propulsion_detailing")
        self.assertEqual(
            blueprint["execution_intent"]["recommended_method"],
            "thruster_component_placement",
        )
        self.assertEqual(blueprint["automation_assessment"]["difficulty"], "high")
        self.assertIn("no_mounting_surface", blueprint["automation_assessment"]["blocked_by"])

    def test_leg_hydraulic_rods_include_joint_risk(self) -> None:
        operation_plan = self._operation_plan_from_text(
            "给两条腿加同样的管线和液压杆，密度中等。"
        )
        blueprint = create_execution_blueprint(operation_plan, self.model_context)

        self.assertEqual(blueprint["execution_intent"]["tool_family"], "mechanical_attachment")
        self.assertEqual(blueprint["execution_intent"]["recommended_method"], "piston_pair_layout")
        self.assertIn("no_joint_range_data", blueprint["automation_assessment"]["blocked_by"])
        self.assertTrue(any("关节" in reason for reason in blueprint["risk_review"]["risk_reasons"]))

    def test_shield_damage_uses_damage_weathering(self) -> None:
        operation_plan = self._operation_plan_from_text("给盾牌加少量战损和旧化，不要太脏。")
        blueprint = create_execution_blueprint(operation_plan, self.model_context)

        self.assertEqual(blueprint["execution_intent"]["tool_family"], "damage_weathering")
        self.assertEqual(
            blueprint["execution_intent"]["recommended_method"],
            "shallow_damage_marking",
        )
        self.assertEqual(blueprint["automation_assessment"]["difficulty"], "high")
        self.assertIn("浅表", " ".join(blueprint["risk_review"]["mitigation_steps"]))

    def test_v0_3_prompt_draft_renders(self) -> None:
        prompt_path = AGENT_ROOT / "prompts" / "v0_3_execution_blueprint_prompt_draft.txt"
        prompt = prompt_path.read_text(encoding="utf-8")
        rendered = prompt.format(
            model_context='{"model":{"name":"Gundam"}}',
            operation_plan='{"target_part":"chest_armor","operation":"add_parting_lines"}',
        )

        self.assertIn("Execution Blueprint", rendered)
        self.assertIn("operation_plan_v2", rendered)

    def test_run_agent_includes_execution_blueprint_by_default(self) -> None:
        result = run_agent("给胸甲加一些锐利的分件线，适合 1/144 打印。")

        self.assertEqual(result["command_type"], "model_edit")
        self.assertIn("execution_blueprint", result)
        self.assertEqual(
            result["execution_blueprint"]["execution_intent"]["tool_family"],
            "surface_detailing",
        )

    def test_cli_result_includes_execution_blueprint_by_default(self) -> None:
        result = build_cli_result("给胸甲加一些锐利的分件线，适合 1/144 打印。")

        self.assertEqual(result["command_type"], "model_edit")
        self.assertIn("execution_blueprint", result)
        self.assertEqual(
            result["execution_blueprint"]["execution_intent"]["tool_family"],
            "surface_detailing",
        )

    def test_cli_result_does_not_add_blueprint_to_context_queries(self) -> None:
        result = build_cli_result("现在有哪些部件？")

        self.assertEqual(result["command_type"], "inspect_context")
        self.assertNotIn("execution_blueprint", result)


if __name__ == "__main__":
    unittest.main()
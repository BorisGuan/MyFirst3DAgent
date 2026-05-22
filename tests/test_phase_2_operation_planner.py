import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
AGENT_ROOT = PROJECT_ROOT / "3d_agent"
if str(AGENT_ROOT) not in sys.path:
    sys.path.insert(0, str(AGENT_ROOT))

from operation_planner import LegacyExecutionPathError, create_simplified_operation_plan, execute_operation_request, plan_operation


class FakeDomainLayer:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def edge_soften(self, target_object: str, parameters: dict, implementation_hint: dict) -> dict:
        call = {
            "target_object": target_object,
            "parameters": parameters,
            "implementation_hint": implementation_hint,
        }
        self.calls.append(call)
        return call


class Phase2OperationPlannerTests(unittest.TestCase):
    def test_plan_operation_fills_default_parameters_for_structured_input(self) -> None:
        request = plan_operation(
            {
                "operation": "edge_soften",
                "target_object": "ChestArmor_Upper_01",
            }
        )

        self.assertEqual(
            request,
            {
                "operation": "edge_soften",
                "target_object": "ChestArmor_Upper_01",
                "parameters": {
                    "strength": 0.01,
                    "style": "mechanical",
                },
            },
        )

    def test_plan_operation_preserves_explicit_parameters(self) -> None:
        request = plan_operation(
            {
                "operation": "edge_soften",
                "target_object": "Body",
                "parameters": {"strength": 0.02},
            }
        )

        self.assertEqual(request["parameters"], {"strength": 0.02, "style": "mechanical"})

    def test_execute_operation_request_is_retired_and_does_not_call_domain(self) -> None:
        domain_layer = FakeDomainLayer()
        request = {
            "operation": "edge_soften",
            "target_object": "Body",
            "source_blend_file": "source.blend",
            "output_blend_copy": "output.blend",
            "report_file": "report.json",
        }

        with self.assertRaises(LegacyExecutionPathError):
            execute_operation_request(request, domain_layer=domain_layer)

        self.assertEqual(domain_layer.calls, [])

    def test_create_simplified_operation_plan_uses_planner_defaults(self) -> None:
        plan = create_simplified_operation_plan(
            "edge_soften",
            "Body",
            "source.blend",
            "output.blend",
        )

        self.assertEqual(plan["parameters"], {"strength": 0.01, "style": "mechanical"})
        self.assertNotIn("implementation_hint", plan)

    def test_planner_rejects_unsupported_operations(self) -> None:
        with self.assertRaises(ValueError):
            plan_operation({"operation": "add_panel_line", "target_object": "Body"})

    def test_planner_has_no_blender_or_core_api_dependency(self) -> None:
        source = (AGENT_ROOT / "operation_planner.py").read_text(encoding="utf-8")

        self.assertNotIn("import bpy", source)
        self.assertNotIn("bpy.", source)
        self.assertNotIn("from blender_ops", source)
        self.assertNotIn("core_geometry_api", source)


if __name__ == "__main__":
    unittest.main()
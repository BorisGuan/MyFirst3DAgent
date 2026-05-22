import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
AGENT_ROOT = PROJECT_ROOT / "3d_agent"
if str(AGENT_ROOT) not in sys.path:
    sys.path.insert(0, str(AGENT_ROOT))

from domain import OperationRegistry, OperationSpec
from planning import ParameterCompletionError, complete_parameters
from task_object import TaskIntent, TaskObject, TaskPlanning, TaskSource, TaskState, TaskTarget


def selected_bound_task(intent_parameters: dict | None = None) -> TaskObject:
    return TaskObject(
        state=TaskState.BOUND,
        source=TaskSource(user_input="给胸甲做机械风格边缘软化", channel="agent_layer"),
        task_type="surface_detail_enhancement",
        target=TaskTarget(
            semantic_part="chest_armor",
            bound_object="ChestArmor_Upper_01",
            binding_candidates=["ChestArmor_Upper_01"],
        ),
        intent=TaskIntent(
            desired_effect="armor_layers",
            style="mechanical",
            density="low",
            scale="1/144",
            parameters=intent_parameters or {},
        ),
        planning=TaskPlanning(
            selected_operation="edge_soften",
            reasoning=["Selected edge_soften through registry."],
        ),
    )


class PlanningParameterCompleterTests(unittest.TestCase):
    def test_completes_edge_soften_default_parameters_and_enters_planned(self) -> None:
        task = selected_bound_task()

        returned_task = complete_parameters(task)

        self.assertIs(returned_task, task)
        self.assertEqual(task.state, TaskState.PLANNED)
        self.assertEqual(task.planning.parameters, {"strength": 0.01, "style": "mechanical"})
        self.assertEqual(task.planning.selected_operation, "edge_soften")
        self.assertEqual(len(task.planning.reasoning), 2)
        self.assertIn("Completed parameters", task.planning.reasoning[-1])

    def test_explicit_intent_parameters_override_defaults(self) -> None:
        task = selected_bound_task({"strength": 0.02, "style": "clean"})

        complete_parameters(task)

        self.assertEqual(task.planning.parameters, {"strength": 0.02, "style": "clean"})

    def test_rejects_invalid_strength(self) -> None:
        for invalid_strength in (0.0, -0.1, "0.02", True):
            with self.subTest(invalid_strength=invalid_strength):
                with self.assertRaises(ParameterCompletionError):
                    complete_parameters(selected_bound_task({"strength": invalid_strength}))

    def test_rejects_invalid_style(self) -> None:
        for invalid_style in ("unknown", 10):
            with self.subTest(invalid_style=invalid_style):
                with self.assertRaises(ParameterCompletionError):
                    complete_parameters(selected_bound_task({"style": invalid_style}))

    def test_rejects_unsupported_explicit_parameter(self) -> None:
        with self.assertRaises(ParameterCompletionError) as error_context:
            complete_parameters(selected_bound_task({"segments": 3}))

        self.assertIn("Unsupported parameter", str(error_context.exception))

    def test_rejects_non_bound_task(self) -> None:
        task = selected_bound_task()
        task.state = TaskState.VALIDATED

        with self.assertRaises(ParameterCompletionError) as error_context:
            complete_parameters(task)

        self.assertIn("state must be 'bound'", str(error_context.exception))

    def test_rejects_missing_selected_operation(self) -> None:
        task = selected_bound_task()
        task.planning.selected_operation = None

        with self.assertRaises(ParameterCompletionError) as error_context:
            complete_parameters(task)

        self.assertIn("planning.selected_operation is required", str(error_context.exception))

    def test_rejects_unregistered_selected_operation(self) -> None:
        task = selected_bound_task()
        task.planning.selected_operation = "add_panel_line"

        with self.assertRaises(ParameterCompletionError) as error_context:
            complete_parameters(task)

        self.assertIn("Unsupported operation", str(error_context.exception))

    def test_uses_registry_parameter_schema(self) -> None:
        task = selected_bound_task({"width": 0.4})
        registry = OperationRegistry(
            (
                OperationSpec(
                    name="edge_soften",
                    supported_task_types=("surface_detail_enhancement",),
                    required_target_state="bound",
                    default_parameters={"width": 0.1},
                    parameter_schema={"width": {"type": "number", "exclusive_minimum": 0.0}},
                    safety_level="safe_non_destructive",
                    handler_name="edge_soften",
                ),
            )
        )

        complete_parameters(task, registry=registry)

        self.assertEqual(task.planning.parameters, {"width": 0.4})

    def test_completer_does_not_write_runtime_result_or_call_execution_layers(self) -> None:
        task = selected_bound_task()

        complete_parameters(task)

        self.assertIsNone(task.runtime.source_blend_file)
        self.assertIsNone(task.runtime.output_blend_copy)
        self.assertIsNone(task.runtime.report_file)
        self.assertIsNone(task.result.success)

    def test_completer_has_no_domain_core_runtime_or_blender_dependency(self) -> None:
        source = (AGENT_ROOT / "planning" / "parameter_completer.py").read_text(encoding="utf-8")

        self.assertNotIn("import bpy", source)
        self.assertNotIn("bpy.", source)
        self.assertNotIn("from blender_ops", source)
        self.assertNotIn("domain_operations", source)
        self.assertNotIn("core_geometry_api", source)
        self.assertNotIn("from runtime", source)
        self.assertNotIn("operation_planner", source)
        self.assertNotIn("modification_execution", source)
        self.assertNotIn("report_file", source)


if __name__ == "__main__":
    unittest.main()
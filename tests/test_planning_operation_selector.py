import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
AGENT_ROOT = PROJECT_ROOT / "3d_agent"
if str(AGENT_ROOT) not in sys.path:
    sys.path.insert(0, str(AGENT_ROOT))

from domain import OperationRegistry, OperationSpec
from planning import OperationSelectionError, select_operation
from task_object import TaskIntent, TaskObject, TaskSource, TaskState, TaskTarget


def bound_task() -> TaskObject:
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
        ),
    )


class PlanningOperationSelectorTests(unittest.TestCase):
    def test_selects_edge_soften_for_supported_bound_task(self) -> None:
        task = bound_task()

        returned_task = select_operation(task)

        self.assertIs(returned_task, task)
        self.assertEqual(task.state, TaskState.BOUND)
        self.assertEqual(task.planning.selected_operation, "edge_soften")
        self.assertEqual(task.planning.parameters, {})
        self.assertEqual(len(task.planning.reasoning), 1)
        self.assertIn("edge_soften", task.planning.reasoning[0])
        self.assertIn("operation registry", task.planning.reasoning[0])

    def test_rejects_non_bound_task(self) -> None:
        task = bound_task()
        task.state = TaskState.VALIDATED

        with self.assertRaises(OperationSelectionError) as error_context:
            select_operation(task)

        self.assertIn("state must be 'bound'", str(error_context.exception))

    def test_rejects_bound_state_without_bound_object(self) -> None:
        task = bound_task()
        task.target.bound_object = None

        with self.assertRaises(OperationSelectionError) as error_context:
            select_operation(task)

        self.assertIn("target.bound_object is required", str(error_context.exception))

    def test_rejects_unsupported_task_type(self) -> None:
        task = bound_task()
        task.task_type = "unsupported_task"

        with self.assertRaises(OperationSelectionError) as error_context:
            select_operation(task)

        self.assertIn("No registered operation supports task_type", str(error_context.exception))

    def test_rejects_incompatible_safety_policy(self) -> None:
        task = bound_task()
        task.execution_policy.mode = "unsafe_destructive"

        with self.assertRaises(OperationSelectionError) as error_context:
            select_operation(task)

        self.assertIn("execution_policy.mode", str(error_context.exception))

    def test_uses_registry_instead_of_hardcoded_unregistered_operations(self) -> None:
        task = bound_task()
        registry = OperationRegistry(
            (
                OperationSpec(
                    name="custom_safe_operation",
                    supported_task_types=("surface_detail_enhancement",),
                    required_target_state="bound",
                    safety_level="safe_non_destructive",
                    handler_name="custom_safe_operation",
                ),
            )
        )

        select_operation(task, registry=registry)

        self.assertEqual(task.planning.selected_operation, "custom_safe_operation")

    def test_selector_does_not_generate_modifier_or_execution_parameters(self) -> None:
        task = bound_task()

        select_operation(task)

        self.assertNotIn("modifier", " ".join(task.planning.reasoning).lower())
        self.assertEqual(task.planning.parameters, {})
        self.assertIsNone(task.runtime.source_blend_file)
        self.assertIsNone(task.result.success)

    def test_selector_has_no_domain_core_cli_or_blender_dependency(self) -> None:
        source = (AGENT_ROOT / "planning" / "operation_selector.py").read_text(encoding="utf-8")

        self.assertNotIn("import bpy", source)
        self.assertNotIn("bpy.", source)
        self.assertNotIn("from blender_ops", source)
        self.assertNotIn("domain_operations", source)
        self.assertNotIn("core_geometry_api", source)
        self.assertNotIn("operation_planner", source)
        self.assertNotIn("modification_execution", source)
        self.assertNotIn("argparse", source)
        self.assertNotIn("--operation", source)


if __name__ == "__main__":
    unittest.main()
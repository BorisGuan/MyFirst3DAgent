import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
AGENT_ROOT = PROJECT_ROOT / "3d_agent"
if str(AGENT_ROOT) not in sys.path:
    sys.path.insert(0, str(AGENT_ROOT))

from planning import PlanningValidationError, validate_draft_task
from task_object import TaskIntent, TaskObject, TaskSource, TaskState, TaskTarget


def valid_draft_task() -> TaskObject:
    return TaskObject(
        source=TaskSource(user_input="给胸甲做机械风格边缘软化", channel="agent_layer"),
        task_type="surface_detail_enhancement",
        target=TaskTarget(semantic_part="chest_armor"),
        intent=TaskIntent(
            desired_effect="armor_layers",
            action="add_armor_layers",
            detail_type="armor_layers",
            style="sharp_mechanical",
            density="low",
            scale="1/144",
        ),
    )


class PlanningValidatorTests(unittest.TestCase):
    def test_valid_draft_task_advances_to_validated(self) -> None:
        task = valid_draft_task()

        returned_task = validate_draft_task(task)

        self.assertIs(returned_task, task)
        self.assertEqual(task.state, TaskState.VALIDATED)

    def test_rejects_non_draft_task(self) -> None:
        task = valid_draft_task()
        task.state = TaskState.VALIDATED

        with self.assertRaises(PlanningValidationError) as error_context:
            validate_draft_task(task)

        self.assertIn("state must be 'draft'", str(error_context.exception))

    def test_rejects_missing_source_user_input(self) -> None:
        task = valid_draft_task()
        task.source.user_input = "  "

        with self.assertRaises(PlanningValidationError) as error_context:
            validate_draft_task(task)

        self.assertIn("source.user_input is required", str(error_context.exception))

    def test_rejects_unsupported_task_type(self) -> None:
        task = valid_draft_task()
        task.task_type = "model_edit"

        with self.assertRaises(PlanningValidationError) as error_context:
            validate_draft_task(task)

        self.assertIn("task_type must be one of", str(error_context.exception))

    def test_rejects_missing_target_semantic_part(self) -> None:
        task = valid_draft_task()
        task.target.semantic_part = ""

        with self.assertRaises(PlanningValidationError) as error_context:
            validate_draft_task(task)

        self.assertIn("target.semantic_part is required", str(error_context.exception))

    def test_rejects_missing_minimum_intent_fields(self) -> None:
        task = valid_draft_task()
        task.intent.desired_effect = ""
        task.intent.style = ""
        task.intent.density = ""
        task.intent.scale = ""

        with self.assertRaises(PlanningValidationError) as error_context:
            validate_draft_task(task)

        error_message = str(error_context.exception)
        self.assertIn("intent.desired_effect is required", error_message)
        self.assertIn("intent.style is required", error_message)
        self.assertIn("intent.density is required", error_message)
        self.assertIn("intent.scale is required", error_message)

    def test_validator_does_not_bind_select_operation_or_write_runtime_fields(self) -> None:
        task = valid_draft_task()

        validate_draft_task(task)

        self.assertIsNone(task.target.bound_object)
        self.assertEqual(task.target.binding_candidates, [])
        self.assertIsNone(task.planning.selected_operation)
        self.assertEqual(task.planning.parameters, {})
        self.assertIsNone(task.runtime.source_blend_file)
        self.assertIsNone(task.runtime.output_blend_copy)
        self.assertIsNone(task.result.success)

    def test_validator_has_no_domain_core_runtime_or_blender_dependency(self) -> None:
        source = (AGENT_ROOT / "planning" / "validator.py").read_text(encoding="utf-8")

        self.assertNotIn("import bpy", source)
        self.assertNotIn("bpy.", source)
        self.assertNotIn("from blender_ops", source)
        self.assertNotIn("from runtime", source)
        self.assertNotIn("from operation_planner", source)
        self.assertNotIn("from modification_execution", source)


if __name__ == "__main__":
    unittest.main()
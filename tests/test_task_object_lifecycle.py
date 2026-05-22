import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
AGENT_ROOT = PROJECT_ROOT / "3d_agent"
if str(AGENT_ROOT) not in sys.path:
    sys.path.insert(0, str(AGENT_ROOT))

from task_object import (
    TaskObject,
    TaskState,
    TaskStateTransitionError,
    allowed_next_states,
    can_transition,
    transition_task,
    validate_transition,
)


class TaskObjectLifecycleTests(unittest.TestCase):
    def test_allows_main_lifecycle_path(self) -> None:
        task = TaskObject()

        for next_state in (
            TaskState.VALIDATED,
            TaskState.BOUND,
            TaskState.PLANNED,
            TaskState.READY_TO_EXECUTE,
            TaskState.EXECUTING,
            TaskState.COMPLETED,
        ):
            returned_task = transition_task(task, next_state)
            self.assertIs(returned_task, task)
            self.assertEqual(task.state, next_state)

    def test_allows_failure_from_non_terminal_active_states(self) -> None:
        for current_state in (
            TaskState.VALIDATED,
            TaskState.BOUND,
            TaskState.PLANNED,
            TaskState.READY_TO_EXECUTE,
            TaskState.EXECUTING,
        ):
            task = TaskObject(state=current_state)

            transition_task(task, TaskState.FAILED)

            self.assertEqual(task.state, TaskState.FAILED)

    def test_rejects_documented_invalid_transitions(self) -> None:
        invalid_transitions = (
            (TaskState.DRAFT, TaskState.EXECUTING),
            (TaskState.DRAFT, TaskState.COMPLETED),
            (TaskState.COMPLETED, TaskState.PLANNED),
            (TaskState.COMPLETED, TaskState.FAILED),
            (TaskState.FAILED, TaskState.COMPLETED),
            (TaskState.READY_TO_EXECUTE, TaskState.BOUND),
            (TaskState.EXECUTING, TaskState.PLANNED),
        )

        for current_state, next_state in invalid_transitions:
            with self.subTest(current_state=current_state, next_state=next_state):
                with self.assertRaises(TaskStateTransitionError):
                    validate_transition(current_state, next_state)

    def test_terminal_states_cannot_be_silently_rewritten(self) -> None:
        completed_task = TaskObject(state=TaskState.COMPLETED)
        failed_task = TaskObject(state=TaskState.FAILED)

        with self.assertRaises(TaskStateTransitionError):
            transition_task(completed_task, TaskState.PLANNED)
        with self.assertRaises(TaskStateTransitionError):
            transition_task(failed_task, TaskState.COMPLETED)

        self.assertEqual(completed_task.state, TaskState.COMPLETED)
        self.assertEqual(failed_task.state, TaskState.FAILED)

    def test_supports_string_state_inputs(self) -> None:
        task = TaskObject()

        self.assertTrue(can_transition("draft", "validated"))
        transition_task(task, "validated")

        self.assertEqual(task.state, TaskState.VALIDATED)

    def test_reports_allowed_next_states(self) -> None:
        self.assertEqual(allowed_next_states(TaskState.DRAFT), (TaskState.VALIDATED,))
        self.assertEqual(allowed_next_states(TaskState.COMPLETED), ())

    def test_rejects_unknown_state_values(self) -> None:
        with self.assertRaises(TaskStateTransitionError):
            validate_transition("draft", "archived")

    def test_lifecycle_has_no_runtime_or_blender_dependency(self) -> None:
        source = (AGENT_ROOT / "task_object" / "lifecycle.py").read_text(encoding="utf-8")

        self.assertNotIn("import bpy", source)
        self.assertNotIn("bpy.", source)
        self.assertNotIn("from runtime", source)
        self.assertNotIn("from blender_ops", source)


if __name__ == "__main__":
    unittest.main()
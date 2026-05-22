import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
AGENT_ROOT = PROJECT_ROOT / "3d_agent"
if str(AGENT_ROOT) not in sys.path:
    sys.path.insert(0, str(AGENT_ROOT))

from planning import SafetyPolicyError, check_safety_policy
from task_object import (
    ExecutionPolicy,
    TaskConstraints,
    TaskIntent,
    TaskObject,
    TaskPlanning,
    TaskRuntime,
    TaskSource,
    TaskState,
    TaskTarget,
)


SOURCE_BLEND_FILE = r"D:\Models\rx78_source.blend"
OUTPUT_BLEND_COPY = r"D:\Models\rx78_source_preview_copy.blend"
REPORT_FILE = r"D:\Models\reports\rx78_source_preview_report.json"


def planned_task() -> TaskObject:
    return TaskObject(
        state=TaskState.PLANNED,
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
        constraints=TaskConstraints(
            preserve_source_file=True,
            non_destructive=True,
            mesh_edit_allowed=False,
        ),
        execution_policy=ExecutionPolicy(
            mode="safe_non_destructive",
            preserve_source_file=True,
            output_blend_copy=OUTPUT_BLEND_COPY,
            report_file=REPORT_FILE,
        ),
        planning=TaskPlanning(
            selected_operation="edge_soften",
            parameters={"strength": 0.01, "style": "mechanical"},
            reasoning=["Completed parameters for edge_soften."],
        ),
        runtime=TaskRuntime(source_blend_file=SOURCE_BLEND_FILE),
    )


class PlanningSafetyPolicyCheckerTests(unittest.TestCase):
    def test_safe_policy_enters_ready_to_execute(self) -> None:
        task = planned_task()

        returned_task = check_safety_policy(task)

        self.assertIs(returned_task, task)
        self.assertEqual(task.state, TaskState.READY_TO_EXECUTE)
        self.assertEqual(task.execution_policy.mode, "safe_non_destructive")
        self.assertTrue(task.execution_policy.preserve_source_file)
        self.assertEqual(task.execution_policy.output_blend_copy, OUTPUT_BLEND_COPY)
        self.assertEqual(task.execution_policy.report_file, REPORT_FILE)
        self.assertEqual(task.planning.selected_operation, "edge_soften")
        self.assertEqual(task.planning.parameters, {"strength": 0.01, "style": "mechanical"})
        self.assertIn("Safety policy approved", task.planning.reasoning[-1])

    def test_rejects_non_planned_task(self) -> None:
        task = planned_task()
        task.state = TaskState.BOUND

        with self.assertRaises(SafetyPolicyError) as error_context:
            check_safety_policy(task)

        self.assertIn("state must be 'planned'", str(error_context.exception))

    def test_rejects_missing_selected_operation(self) -> None:
        task = planned_task()
        task.planning.selected_operation = None

        with self.assertRaises(SafetyPolicyError) as error_context:
            check_safety_policy(task)

        self.assertIn("planning.selected_operation", str(error_context.exception))

    def test_rejects_missing_completed_parameters(self) -> None:
        task = planned_task()
        task.planning.parameters = {}

        with self.assertRaises(SafetyPolicyError) as error_context:
            check_safety_policy(task)

        self.assertIn("planning.parameters", str(error_context.exception))

    def test_rejects_unsafe_execution_mode(self) -> None:
        task = planned_task()
        task.execution_policy.mode = "unsafe_destructive"

        with self.assertRaises(SafetyPolicyError) as error_context:
            check_safety_policy(task)

        self.assertIn("execution_policy.mode", str(error_context.exception))

    def test_rejects_source_file_overwrite_policy(self) -> None:
        task = planned_task()
        task.constraints.preserve_source_file = False

        with self.assertRaises(SafetyPolicyError) as error_context:
            check_safety_policy(task)

        self.assertIn("constraints.preserve_source_file", str(error_context.exception))

    def test_rejects_destructive_policy(self) -> None:
        task = planned_task()
        task.constraints.non_destructive = False

        with self.assertRaises(SafetyPolicyError) as error_context:
            check_safety_policy(task)

        self.assertIn("constraints.non_destructive", str(error_context.exception))

    def test_rejects_mesh_edit_allowed_policy(self) -> None:
        task = planned_task()
        task.constraints.mesh_edit_allowed = True

        with self.assertRaises(SafetyPolicyError) as error_context:
            check_safety_policy(task)

        self.assertIn("mesh edit", str(error_context.exception).lower())

    def test_rejects_missing_output_copy_for_real_execution(self) -> None:
        task = planned_task()
        task.execution_policy.output_blend_copy = None

        with self.assertRaises(SafetyPolicyError) as error_context:
            check_safety_policy(task)

        self.assertIn("output_blend_copy", str(error_context.exception))

    def test_rejects_missing_report_artifact(self) -> None:
        task = planned_task()
        task.execution_policy.report_file = None

        with self.assertRaises(SafetyPolicyError) as error_context:
            check_safety_policy(task)

        self.assertIn("report_file", str(error_context.exception))

    def test_rejects_output_copy_overwriting_runtime_source_blend_file(self) -> None:
        task = planned_task()
        task.execution_policy.output_blend_copy = SOURCE_BLEND_FILE


        with self.assertRaises(SafetyPolicyError) as error_context:
            check_safety_policy(task)

        self.assertIn("must not overwrite", str(error_context.exception))

    def test_rejects_output_copy_overwriting_source_metadata_blend_file(self) -> None:
        task = planned_task()
        task.runtime.source_blend_file = None
        task.source.metadata["source_blend_file"] = SOURCE_BLEND_FILE
        task.execution_policy.output_blend_copy = SOURCE_BLEND_FILE

        with self.assertRaises(SafetyPolicyError) as error_context:
            check_safety_policy(task)

        self.assertIn("must not overwrite", str(error_context.exception))

    def test_checker_does_not_write_runtime_result_or_report_artifacts(self) -> None:
        task = planned_task()

        check_safety_policy(task)

        self.assertEqual(task.runtime.source_blend_file, SOURCE_BLEND_FILE)
        self.assertIsNone(task.runtime.output_blend_copy)
        self.assertIsNone(task.runtime.report_file)
        self.assertIsNone(task.result.success)
        self.assertEqual(task.result.report_file, None)
        self.assertEqual(task.artifact_refs, {})

    def test_checker_has_no_domain_core_or_blender_dependency(self) -> None:
        source = (AGENT_ROOT / "planning" / "safety_policy_checker.py").read_text(encoding="utf-8")

        self.assertNotIn("import bpy", source)
        self.assertNotIn("bpy.", source)
        self.assertNotIn("from blender_ops", source)
        self.assertNotIn("domain_operations", source)
        self.assertNotIn("core_geometry_api", source)
        self.assertNotIn("operation_planner", source)
        self.assertNotIn("modification_execution", source)
        self.assertNotIn("open(", source)
        self.assertNotIn("write_text", source)


if __name__ == "__main__":
    unittest.main()
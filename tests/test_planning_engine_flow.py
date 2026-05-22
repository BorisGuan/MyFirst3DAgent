import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
AGENT_ROOT = PROJECT_ROOT / "3d_agent"
if str(AGENT_ROOT) not in sys.path:
    sys.path.insert(0, str(AGENT_ROOT))

from domain import OperationRegistry, OperationSpec
from planning import PlanningEngineError, plan_task
from task_object import (
    ExecutionPolicy,
    TaskConstraints,
    TaskIntent,
    TaskObject,
    TaskSource,
    TaskState,
    TaskTarget,
)


SOURCE_BLEND_FILE = r"D:\Models\rx78_source.blend"
OUTPUT_BLEND_COPY = r"D:\Models\rx78_source_ready_copy.blend"
REPORT_FILE = r"D:\Models\reports\rx78_source_ready.json"


def draft_task(intent_parameters: dict | None = None) -> TaskObject:
    return TaskObject(
        state=TaskState.DRAFT,
        source=TaskSource(
            user_input="给胸甲做机械风格边缘软化",
            channel="agent_layer",
            metadata={"source_blend_file": SOURCE_BLEND_FILE},
        ),
        task_type="surface_detail_enhancement",
        target=TaskTarget(semantic_part="chest_armor"),
        intent=TaskIntent(
            desired_effect="armor_layers",
            style="mechanical",
            density="low",
            scale="1/144",
            parameters=intent_parameters or {},
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
    )


def fake_manifest() -> dict:
    return {
        "manifest_version": "v0_5",
        "source_software": "blender",
        "source_file": SOURCE_BLEND_FILE,
        "unit_system": "metric",
        "objects": [
            {
                "object_name": "ChestArmor_Upper_01",
                "object_type": "MESH",
                "collection_path": ["Gundam", "Body", "Chest"],
                "dimensions": [2.4, 0.8, 1.1],
                "location": [0.0, 0.0, 0.0],
                "rotation_euler": [0.0, 0.0, 0.0],
                "vertex_count": 1200,
                "material_names": ["armor_white"],
                "custom_properties": {"part_role": "chest_armor"},
            },
        ],
    }


def fake_registry(default_strength: float = 0.01) -> OperationRegistry:
    return OperationRegistry(
        (
            OperationSpec(
                name="edge_soften",
                supported_task_types=("surface_detail_enhancement",),
                required_target_state="bound",
                default_parameters={"strength": default_strength, "style": "mechanical"},
                parameter_schema={
                    "strength": {"type": "number", "exclusive_minimum": 0.0},
                    "style": {"type": "string", "enum": ["clean", "heavy", "mechanical"]},
                },
                safety_level="safe_non_destructive",
                handler_name="edge_soften",
            ),
        )
    )


class EmptyRegistry:
    def supported_for_task_type(self, task_type: str) -> tuple:
        return ()

    def get(self, operation_name: str) -> OperationSpec:
        raise AssertionError("get should not be called when selection fails")


class PlanningEngineFlowTests(unittest.TestCase):
    def test_plans_draft_task_to_ready_to_execute_with_fake_manifest_and_registry(self) -> None:
        task = draft_task({"style": "clean"})

        returned_task = plan_task(task, scene_manifest=fake_manifest(), registry=fake_registry())

        self.assertIs(returned_task, task)
        self.assertEqual(task.state, TaskState.READY_TO_EXECUTE)
        self.assertEqual(task.target.bound_object, "ChestArmor_Upper_01")
        self.assertEqual(task.target.binding_candidates, ["ChestArmor_Upper_01"])
        self.assertEqual(task.planning.selected_operation, "edge_soften")
        self.assertEqual(task.planning.parameters, {"strength": 0.01, "style": "clean"})
        self.assertGreaterEqual(len(task.planning.reasoning), 3)

    def test_validation_failure_stops_at_draft(self) -> None:
        task = draft_task()
        task.source.user_input = ""

        with self.assertRaises(PlanningEngineError) as error_context:
            plan_task(task, scene_manifest=fake_manifest(), registry=fake_registry())

        self.assertEqual(error_context.exception.stage, "validation")
        self.assertIn("source.user_input", str(error_context.exception))
        self.assertEqual(task.state, TaskState.DRAFT)
        self.assertIsNone(task.target.bound_object)
        self.assertIsNone(task.planning.selected_operation)

    def test_binding_failure_stops_before_operation_selection(self) -> None:
        task = draft_task()
        task.target.semantic_part = "shield"

        with self.assertRaises(PlanningEngineError) as error_context:
            plan_task(task, scene_manifest=fake_manifest(), registry=fake_registry())

        self.assertEqual(error_context.exception.stage, "binding")
        self.assertIn("No binding candidates", str(error_context.exception))
        self.assertEqual(task.state, TaskState.VALIDATED)
        self.assertIsNone(task.target.bound_object)
        self.assertIsNone(task.planning.selected_operation)

    def test_operation_selection_failure_stops_before_parameter_completion(self) -> None:
        task = draft_task()

        with self.assertRaises(PlanningEngineError) as error_context:
            plan_task(task, scene_manifest=fake_manifest(), registry=EmptyRegistry())

        self.assertEqual(error_context.exception.stage, "operation_selection")
        self.assertIn("No registered operation", str(error_context.exception))
        self.assertEqual(task.state, TaskState.BOUND)
        self.assertIsNone(task.planning.selected_operation)
        self.assertEqual(task.planning.parameters, {})

    def test_parameter_completion_failure_stops_before_safety_policy(self) -> None:
        task = draft_task({"style": "unsupported"})

        with self.assertRaises(PlanningEngineError) as error_context:
            plan_task(task, scene_manifest=fake_manifest(), registry=fake_registry())

        self.assertEqual(error_context.exception.stage, "parameter_completion")
        self.assertIn("style", str(error_context.exception))
        self.assertEqual(task.state, TaskState.BOUND)
        self.assertEqual(task.planning.selected_operation, "edge_soften")
        self.assertEqual(task.planning.parameters, {})

    def test_safety_policy_failure_stops_at_planned(self) -> None:
        task = draft_task()
        task.execution_policy.output_blend_copy = None

        with self.assertRaises(PlanningEngineError) as error_context:
            plan_task(task, scene_manifest=fake_manifest(), registry=fake_registry())

        self.assertEqual(error_context.exception.stage, "safety_policy")
        self.assertIn("output_blend_copy", str(error_context.exception))
        self.assertEqual(task.state, TaskState.PLANNED)
        self.assertEqual(task.planning.parameters, {"strength": 0.01, "style": "mechanical"})

    def test_engine_does_not_write_execution_outputs_or_results(self) -> None:
        task = draft_task()

        plan_task(task, scene_manifest=fake_manifest(), registry=fake_registry())

        self.assertIsNone(task.runtime.source_blend_file)
        self.assertIsNone(task.runtime.output_blend_copy)
        self.assertIsNone(task.runtime.report_file)
        self.assertIsNone(task.result.success)
        self.assertEqual(task.artifact_refs, {})

    def test_engine_has_no_domain_core_runtime_or_blender_dependency(self) -> None:
        source = (AGENT_ROOT / "planning" / "planning_engine.py").read_text(encoding="utf-8")

        self.assertNotIn("import bpy", source)
        self.assertNotIn("bpy.", source)
        self.assertNotIn("from blender_ops", source)
        self.assertNotIn("domain_operations", source)
        self.assertNotIn("core_geometry_api", source)
        self.assertNotIn("from domain", source)
        self.assertNotIn("import domain", source)
        self.assertNotIn("operation_planner", source)
        self.assertNotIn("modification_execution", source)
        self.assertNotIn("open(", source)
        self.assertNotIn("write_text", source)


if __name__ == "__main__":
    unittest.main()
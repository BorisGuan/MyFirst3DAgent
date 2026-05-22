import json
import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
AGENT_ROOT = PROJECT_ROOT / "3d_agent"
if str(AGENT_ROOT) not in sys.path:
    sys.path.insert(0, str(AGENT_ROOT))

from domain import DomainOperationContractError, DomainOperationInput, OperationOutcome
from task_object import (
    ExecutionPolicy,
    TaskIntent,
    TaskObject,
    TaskPlanning,
    TaskSource,
    TaskState,
    TaskTarget,
)


def ready_task() -> TaskObject:
    return TaskObject(
        task_id="task-001",
        state=TaskState.READY_TO_EXECUTE,
        source=TaskSource(
            user_input="给胸甲做机械风格边缘软化",
            channel="agent_layer",
            metadata={"source_blend_file": r"D:\Models\rx78_source.blend"},
        ),
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
        execution_policy=ExecutionPolicy(
            mode="safe_non_destructive",
            preserve_source_file=True,
            output_blend_copy=r"D:\Models\rx78_source_ready_copy.blend",
            report_file=r"D:\Models\reports\rx78_source_ready.json",
        ),
        planning=TaskPlanning(
            selected_operation="edge_soften",
            parameters={"strength": 0.01, "style": "mechanical"},
        ),
    )


class DomainOperationContractsTests(unittest.TestCase):
    def test_domain_operation_input_derives_from_ready_task_object(self) -> None:
        operation_input = DomainOperationInput.from_task_object(ready_task())

        self.assertEqual(operation_input.task_id, "task-001")
        self.assertEqual(operation_input.operation, "edge_soften")
        self.assertEqual(operation_input.target_object, "ChestArmor_Upper_01")
        self.assertEqual(operation_input.parameters, {"strength": 0.01, "style": "mechanical"})
        self.assertEqual(
            operation_input.execution_policy,
            {"mode": "safe_non_destructive", "preserve_source_file": True},
        )

    def test_domain_operation_input_to_dict_is_minimal_and_json_serializable(self) -> None:
        operation_input = DomainOperationInput.from_task_object(ready_task())

        encoded = json.dumps(operation_input.to_dict(), ensure_ascii=False)
        serialized = operation_input.to_dict()

        self.assertIn("edge_soften", encoded)
        self.assertEqual(
            set(serialized),
            {"task_id", "operation", "target_object", "parameters", "execution_policy"},
        )
        serialized_text = json.dumps(serialized, ensure_ascii=False)
        self.assertNotIn("给胸甲", serialized_text)
        self.assertNotIn("user_input", serialized_text)
        self.assertNotIn("output_blend_copy", serialized_text)
        self.assertNotIn("report_file", serialized_text)
        self.assertNotIn("preview", serialized_text)
        self.assertNotIn("logs", serialized_text)

    def test_domain_operation_input_rejects_non_ready_task(self) -> None:
        task = ready_task()
        task.state = TaskState.PLANNED

        with self.assertRaises(DomainOperationContractError) as error_context:
            DomainOperationInput.from_task_object(task)

        self.assertIn("ready_to_execute", str(error_context.exception))

    def test_domain_operation_input_rejects_missing_target_object(self) -> None:
        task = ready_task()
        task.target.bound_object = None

        with self.assertRaises(DomainOperationContractError) as error_context:
            DomainOperationInput.from_task_object(task)

        self.assertIn("bound_object", str(error_context.exception))

    def test_domain_operation_input_rejects_missing_operation(self) -> None:
        task = ready_task()
        task.planning.selected_operation = None

        with self.assertRaises(DomainOperationContractError) as error_context:
            DomainOperationInput.from_task_object(task)

        self.assertIn("selected_operation", str(error_context.exception))

    def test_domain_operation_input_rejects_artifact_paths_when_constructed_directly(self) -> None:
        for unsafe_field in ("output_blend_copy", "report_file", "preview", "logs"):
            with self.subTest(unsafe_field=unsafe_field):
                with self.assertRaises(DomainOperationContractError):
                    DomainOperationInput(
                        task_id="task-001",
                        operation="edge_soften",
                        target_object="ChestArmor_Upper_01",
                        parameters={"strength": 0.01},
                        execution_policy={"mode": "safe_non_destructive", unsafe_field: "blocked"},
                    )

    def test_operation_outcome_to_dict_is_json_serializable(self) -> None:
        outcome = OperationOutcome(
            operation="edge_soften",
            target_object="ChestArmor_Upper_01",
            success=True,
            changed_objects=["ChestArmor_Upper_01"],
            modifier_info={"modifier_name": "EdgeSoftening", "width": 0.01},
            mesh_data_applied=False,
            diagnostics=["bevel modifier added"],
        )

        encoded = json.dumps(outcome.to_dict(), ensure_ascii=False)

        self.assertIn("edge_soften", encoded)
        self.assertEqual(
            outcome.to_dict(),
            {
                "operation": "edge_soften",
                "target_object": "ChestArmor_Upper_01",
                "success": True,
                "changed_objects": ["ChestArmor_Upper_01"],
                "modifier_info": {"modifier_name": "EdgeSoftening", "width": 0.01},
                "mesh_data_applied": False,
                "diagnostics": ["bevel modifier added"],
            },
        )

    def test_operation_outcome_rejects_invalid_shapes(self) -> None:
        with self.assertRaises(DomainOperationContractError):
            OperationOutcome(operation="", target_object="ChestArmor_Upper_01", success=True)
        with self.assertRaises(DomainOperationContractError):
            OperationOutcome(operation="edge_soften", target_object="", success=True)
        with self.assertRaises(DomainOperationContractError):
            OperationOutcome(operation="edge_soften", target_object="ChestArmor_Upper_01", success="yes")
        with self.assertRaises(DomainOperationContractError):
            OperationOutcome(
                operation="edge_soften",
                target_object="ChestArmor_Upper_01",
                success=True,
                changed_objects=[1],
            )

    def test_contracts_do_not_import_task_object_or_execution_layers(self) -> None:
        source = (AGENT_ROOT / "domain" / "operation_contracts.py").read_text(encoding="utf-8")

        self.assertNotIn("from task_object", source)
        self.assertNotIn("import task_object", source)
        self.assertNotIn("import bpy", source)
        self.assertNotIn("bpy.", source)
        self.assertNotIn("from blender_ops", source)
        self.assertNotIn("domain_operations", source)
        self.assertNotIn("core_geometry_api", source)
        self.assertNotIn("modification_execution", source)
        self.assertNotIn("open(", source)
        self.assertNotIn("write_text", source)


if __name__ == "__main__":
    unittest.main()
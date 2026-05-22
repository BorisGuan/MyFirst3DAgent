import json
import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
AGENT_ROOT = PROJECT_ROOT / "3d_agent"
if str(AGENT_ROOT) not in sys.path:
    sys.path.insert(0, str(AGENT_ROOT))

from domain import OperationOutcome
from reporting import PersistenceResult, build_failure_report, build_operation_report, write_report
from task_object import TaskObject, TaskPlanning, TaskSource, TaskState, TaskTarget


def ready_task() -> TaskObject:
    return TaskObject(
        task_id="task-report-001",
        state=TaskState.COMPLETED,
        source=TaskSource(user_input="给胸甲做机械风格边缘软化", channel="agent_layer"),
        target=TaskTarget(semantic_part="chest_armor", bound_object="ChestArmor_Upper_01"),
        planning=TaskPlanning(
            selected_operation="edge_soften",
            parameters={"strength": 0.01, "style": "mechanical"},
        ),
    )


def operation_outcome() -> OperationOutcome:
    return OperationOutcome(
        operation="edge_soften",
        target_object="ChestArmor_Upper_01",
        success=True,
        changed_objects=["ChestArmor_Upper_01"],
        modifier_info={"modifier_name": "AI_PanelLine_Bevel", "width": 0.01},
        mesh_data_applied=False,
        diagnostics=["domain ok"],
    )


class ReportingTests(unittest.TestCase):
    def test_build_operation_report_contains_required_execution_facts(self) -> None:
        report = build_operation_report(
            ready_task(),
            operation_outcome(),
            PersistenceResult(
                source_blend_file="source.blend",
                output_blend_copy="output.blend",
                saved_original_file=False,
            ),
            execution_status="success",
        )

        self.assertEqual(report["task_id"], "task-report-001")
        self.assertEqual(report["operation"], "edge_soften")
        self.assertEqual(report["target_object"], "ChestArmor_Upper_01")
        self.assertEqual(report["parameters"], {"strength": 0.01, "style": "mechanical"})
        self.assertEqual(report["changed_objects"], ["ChestArmor_Upper_01"])
        self.assertEqual(report["source_blend_file"], "source.blend")
        self.assertEqual(report["output_blend_copy"], "output.blend")
        self.assertFalse(report["saved_original_file"])

    def test_write_report_writes_json_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            report_path = Path(temp_dir) / "reports" / "runtime_report.json"
            report = {"task_id": "task-report-001", "operation": "edge_soften"}

            written_path = write_report(report_path, report)
            loaded_report = json.loads(report_path.read_text(encoding="utf-8"))

        self.assertEqual(written_path, str(report_path))
        self.assertEqual(loaded_report, report)

    def test_report_builder_does_not_modify_task_planning_or_store_report_on_task(self) -> None:
        task = ready_task()
        selected_operation = task.planning.selected_operation
        parameters = dict(task.planning.parameters)

        report = build_operation_report(
            task,
            operation_outcome(),
            PersistenceResult(source_blend_file="source.blend", output_blend_copy="output.blend"),
            execution_status="success",
        )

        self.assertEqual(task.planning.selected_operation, selected_operation)
        self.assertEqual(task.planning.parameters, parameters)
        self.assertEqual(task.result.report_file, None)
        self.assertEqual(task.result.artifacts, {})
        self.assertNotIn("report", task.result.artifacts)
        self.assertEqual(report["operation"], "edge_soften")

    def test_build_failure_report_uses_runtime_supplied_failure_status(self) -> None:
        report = build_failure_report(
            ready_task(),
            error_stage="domain_operation",
            error=RuntimeError("domain failed"),
            execution_status="failed",
            persistence_result=PersistenceResult(source_blend_file="source.blend", output_blend_copy="output.blend"),
        )

        self.assertEqual(report["execution_status"], "failed")
        self.assertEqual(report["error_stage"], "domain_operation")
        self.assertEqual(report["operation"], "edge_soften")
        self.assertEqual(report["target_object"], "ChestArmor_Upper_01")

    def test_reporting_has_no_blender_domain_execution_or_planning_dependency(self) -> None:
        builder_source = (AGENT_ROOT / "reporting" / "report_builder.py").read_text(encoding="utf-8")
        writer_source = (AGENT_ROOT / "reporting" / "report_writer.py").read_text(encoding="utf-8")
        combined_source = builder_source + writer_source

        self.assertNotIn("import bpy", combined_source)
        self.assertNotIn("bpy.", combined_source)
        self.assertNotIn("select_operation", combined_source)
        self.assertNotIn("complete_parameters", combined_source)
        self.assertNotIn("edge_soften", builder_source)
        self.assertNotIn("save_as_copy_only", combined_source)


if __name__ == "__main__":
    unittest.main()
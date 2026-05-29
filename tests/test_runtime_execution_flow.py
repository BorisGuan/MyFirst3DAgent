import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
AGENT_ROOT = PROJECT_ROOT / "3d_agent"
if str(AGENT_ROOT) not in sys.path:
    sys.path.insert(0, str(AGENT_ROOT))

from domain import DomainOperationInput, OperationOutcome
from runtime import ExecutionContext, RuntimeExecutionError, default_execution_context, execute_ready_task
from task_object import (
    ExecutionPolicy,
    TaskConstraints,
    TaskIntent,
    TaskObject,
    TaskPlanning,
    TaskSource,
    TaskState,
    TaskTarget,
)


SOURCE_BLEND_FILE = r"D:\Models\rx78_source.blend"
OUTPUT_BLEND_COPY = r"D:\Models\rx78_runtime_copy.blend"
REPORT_FILE = r"D:\Models\reports\rx78_runtime_report.json"


class FakePersistenceApi:
    def __init__(self) -> None:
        self.save_calls: list[tuple[str, str]] = []

    def save_as_copy_only(self, source_file: str, output_file: str) -> str:
        self.save_calls.append((source_file, output_file))
        if Path(source_file).resolve() == Path(output_file).resolve():
            raise RuntimeError("Refusing to overwrite the source .blend file.")
        return output_file


class FakeReportWriter:
    def __init__(self) -> None:
        self.report_calls: list[tuple[str, dict]] = []

    def write_report(self, path: str, report: dict) -> str:
        self.report_calls.append((path, report))
        return path


class FakeClock:
    def __init__(self) -> None:
        self.index = 0

    def __call__(self) -> str:
        self.index += 1
        return f"2026-05-22T00:00:0{self.index}+00:00"


class RecordingDomainHandler:
    def __init__(self, should_fail: bool = False) -> None:
        self.should_fail = should_fail
        self.calls: list[DomainOperationInput] = []

    def __call__(self, operation_input: DomainOperationInput) -> OperationOutcome:
        self.calls.append(operation_input)
        if self.should_fail:
            raise RuntimeError("domain handler failed")
        return OperationOutcome(
            operation=operation_input.operation,
            target_object=operation_input.target_object,
            success=True,
            changed_objects=[operation_input.target_object],
            modifier_info={"modifier_name": "AI_PanelLine_Bevel", "width": operation_input.parameters["strength"]},
            mesh_data_applied=False,
            diagnostics=[],
        )


def ready_task() -> TaskObject:
    return TaskObject(
        task_id="task-runtime-001",
        state=TaskState.READY_TO_EXECUTE,
        source=TaskSource(
            user_input="给胸甲做机械风格边缘软化",
            channel="agent_layer",
            metadata={"source_blend_file": SOURCE_BLEND_FILE},
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
        ),
    )


def runtime_context(
    handler: RecordingDomainHandler | None = None,
    persistence_api: FakePersistenceApi | None = None,
    report_writer: FakeReportWriter | None = None,
) -> ExecutionContext:
    domain_handler = handler or RecordingDomainHandler()
    return ExecutionContext(
        domain_handlers={"edge_soften": domain_handler},
        persistence_api=persistence_api or FakePersistenceApi(),
        report_writer=report_writer or FakeReportWriter(),
        clock=FakeClock(),
    )


class RuntimeExecutionFlowTests(unittest.TestCase):
    def test_successful_execution_completes_task_and_writes_report(self) -> None:
        task = ready_task()
        handler = RecordingDomainHandler()
        persistence_api = FakePersistenceApi()
        report_writer = FakeReportWriter()
        context = runtime_context(handler, persistence_api, report_writer)

        returned_task = execute_ready_task(task, context=context)

        self.assertIs(returned_task, task)
        self.assertEqual(task.state, TaskState.COMPLETED)
        self.assertEqual(handler.calls[0].operation, "edge_soften")
        self.assertEqual(handler.calls[0].parameters, {"strength": 0.01, "style": "mechanical"})
        self.assertEqual(persistence_api.save_calls, [(SOURCE_BLEND_FILE, OUTPUT_BLEND_COPY)])
        self.assertEqual(report_writer.report_calls[0][0], REPORT_FILE)
        self.assertEqual(report_writer.report_calls[0][1]["execution_status"], "success")
        self.assertEqual(report_writer.report_calls[0][1]["task_id"], "task-runtime-001")
        self.assertEqual(report_writer.report_calls[0][1]["changed_objects"], ["ChestArmor_Upper_01"])
        self.assertEqual(task.runtime.source_blend_file, SOURCE_BLEND_FILE)
        self.assertEqual(task.runtime.output_blend_copy, OUTPUT_BLEND_COPY)
        self.assertEqual(task.runtime.report_file, REPORT_FILE)
        self.assertEqual(task.result.success, True)
        self.assertEqual(task.result.report_file, REPORT_FILE)
        self.assertEqual(task.result.artifacts, {"output_blend_copy": OUTPUT_BLEND_COPY})

    def test_runtime_uses_runtime_source_blend_file_when_present(self) -> None:
        task = ready_task()
        task.runtime.source_blend_file = r"D:\Models\runtime_source.blend"
        persistence_api = FakePersistenceApi()

        execute_ready_task(task, context=runtime_context(persistence_api=persistence_api))

        self.assertEqual(persistence_api.save_calls[0], (r"D:\Models\runtime_source.blend", OUTPUT_BLEND_COPY))

    def test_domain_failure_marks_task_failed_and_writes_failure_report(self) -> None:
        task = ready_task()
        handler = RecordingDomainHandler(should_fail=True)
        persistence_api = FakePersistenceApi()
        report_writer = FakeReportWriter()

        with self.assertRaises(RuntimeExecutionError) as error_context:
            execute_ready_task(task, context=runtime_context(handler, persistence_api, report_writer))

        self.assertEqual(error_context.exception.stage, "domain_operation")
        self.assertEqual(task.state, TaskState.FAILED)
        self.assertEqual(task.result.success, False)
        self.assertIn("domain handler failed", task.result.summary)
        self.assertEqual(persistence_api.save_calls, [])
        self.assertEqual(report_writer.report_calls[0][1]["execution_status"], "failed")
        self.assertEqual(report_writer.report_calls[0][1]["error_stage"], "domain_operation")

    def test_persistence_failure_marks_task_failed(self) -> None:
        task = ready_task()
        task.execution_policy.output_blend_copy = SOURCE_BLEND_FILE
        handler = RecordingDomainHandler()
        persistence_api = FakePersistenceApi()
        report_writer = FakeReportWriter()

        with self.assertRaises(RuntimeExecutionError) as error_context:
            execute_ready_task(task, context=runtime_context(handler, persistence_api, report_writer))

        self.assertEqual(error_context.exception.stage, "persistence_policy")
        self.assertEqual(task.state, TaskState.FAILED)
        self.assertEqual(task.result.success, False)
        self.assertEqual(handler.calls, [])
        self.assertEqual(persistence_api.save_calls, [])
        self.assertEqual(report_writer.report_calls[0][1]["execution_status"], "failed")

    def test_missing_domain_handler_marks_failed_without_choosing_another_operation(self) -> None:
        task = ready_task()
        persistence_api = FakePersistenceApi()
        context = ExecutionContext(domain_handlers={}, persistence_api=persistence_api, clock=FakeClock())

        with self.assertRaises(RuntimeExecutionError) as error_context:
            execute_ready_task(task, context=context)

        self.assertEqual(error_context.exception.stage, "domain_operation")
        self.assertEqual(task.state, TaskState.FAILED)
        self.assertEqual(persistence_api.save_calls, [])

    def test_default_execution_context_registers_supported_domain_handlers(self) -> None:
        context = default_execution_context()

        self.assertIn("armor_edge_lip_prepare", context.domain_handlers)
        self.assertIn("armor_layer_plate_prepare", context.domain_handlers)
        self.assertIn("edge_soften", context.domain_handlers)
        self.assertIn("hardpoint_socket_prepare", context.domain_handlers)
        self.assertIn("panel_line_bevel_prepare", context.domain_handlers)
        self.assertIn("solidify_thickness_preview", context.domain_handlers)
        self.assertIn("surface_inset_prepare", context.domain_handlers)
        self.assertIn("thruster_nozzle_prepare", context.domain_handlers)
        self.assertIn("vent_slot_prepare", context.domain_handlers)
        self.assertIn("weighted_normal_finish", context.domain_handlers)

    def test_non_ready_task_is_rejected_without_state_change(self) -> None:
        task = ready_task()
        task.state = TaskState.PLANNED

        with self.assertRaises(RuntimeExecutionError) as error_context:
            execute_ready_task(task, context=runtime_context())

        self.assertEqual(error_context.exception.stage, "state")
        self.assertEqual(task.state, TaskState.PLANNED)
        self.assertIsNone(task.result.success)

    def test_runtime_has_no_planning_core_geometry_or_blender_dependency(self) -> None:
        runtime_engine_source = (AGENT_ROOT / "runtime" / "runtime_engine.py").read_text(encoding="utf-8")
        execution_context_source = (AGENT_ROOT / "runtime" / "execution_context.py").read_text(encoding="utf-8")
        combined_source = runtime_engine_source + execution_context_source

        self.assertNotIn("import bpy", combined_source)
        self.assertNotIn("bpy.", combined_source)
        self.assertNotIn("select_operation", combined_source)
        self.assertNotIn("complete_parameters", combined_source)
        self.assertNotIn("add_bevel_modifier", runtime_engine_source)
        self.assertNotIn("require_object", runtime_engine_source)
        self.assertNotIn("user_input", runtime_engine_source)
        self.assertNotIn("desired_effect", runtime_engine_source)


if __name__ == "__main__":
    unittest.main()
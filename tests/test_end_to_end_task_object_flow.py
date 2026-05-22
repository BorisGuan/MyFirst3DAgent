import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
AGENT_ROOT = PROJECT_ROOT / "3d_agent"
if str(AGENT_ROOT) not in sys.path:
    sys.path.insert(0, str(AGENT_ROOT))

from agent_layer import create_draft_task
from domain import DomainOperationInput, OperationOutcome
from planning import plan_task
from runtime import ExecutionContext, execute_ready_task
from task_object import ExecutionPolicy, TaskState


SOURCE_BLEND_FILE = r"D:\Models\rx78_source.blend"
OUTPUT_BLEND_COPY = r"D:\Models\rx78_task_object_e2e.blend"
REPORT_FILE = r"D:\Models\reports\rx78_task_object_e2e.json"


class FakeContextManager:
    def summary_for_classifier(self) -> dict:
        return {"available_targets": ["chest_armor"]}

    def summary_for_planner(self) -> dict:
        return {"parts": [{"name": "chest_armor"}]}


class FakePersistenceApi:
    def __init__(self) -> None:
        self.save_calls: list[tuple[str, str]] = []

    def save_as_copy_only(self, source_file: str, output_file: str) -> str:
        self.save_calls.append((source_file, output_file))
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
        return f"2026-05-22T12:00:0{self.index}+00:00"


class RecordingDomainHandler:
    def __init__(self) -> None:
        self.calls: list[DomainOperationInput] = []

    def __call__(self, operation_input: DomainOperationInput) -> OperationOutcome:
        self.calls.append(operation_input)
        return OperationOutcome(
            operation=operation_input.operation,
            target_object=operation_input.target_object,
            success=True,
            changed_objects=[operation_input.target_object],
            modifier_info={
                "modifier_name": "AI_PanelLine_Bevel",
                "modifier_type": "BEVEL",
                "width": operation_input.parameters["strength"],
                "segments": 1,
            },
            mesh_data_applied=False,
            diagnostics=[],
        )


def fake_model_edit_classifier(user_input: str, context_summary: dict) -> dict[str, str]:
    return {
        "command_type": "model_edit",
        "confidence": "high",
        "reasoning": "e2e classifier fixture",
    }


def fake_intent_parser(user_input: str, model_context: dict) -> dict:
    return {
        "target_part": "chest_armor",
        "operation": "add_armor_layers",
        "detail_type": "armor_layers",
        "style": "mechanical",
        "density": "low",
        "symmetry": "single_target",
        "scale": "1/144",
        "placement_zones": ["upper_chest_plate"],
        "parameters": {"style": "mechanical"},
        "constraints": ["preserve silhouette"],
    }


def fake_scene_manifest() -> dict:
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


def runtime_context(
    handler: RecordingDomainHandler,
    persistence_api: FakePersistenceApi,
    report_writer: FakeReportWriter,
) -> ExecutionContext:
    return ExecutionContext(
        domain_handlers={"edge_soften": handler},
        persistence_api=persistence_api,
        report_writer=report_writer,
        clock=FakeClock(),
    )


class EndToEndTaskObjectFlowTests(unittest.TestCase):
    def test_natural_language_task_object_flow_completes_without_real_blender(self) -> None:
        task = create_draft_task(
            "给胸甲做机械风格边缘软化",
            context_manager=FakeContextManager(),
            classifier=fake_model_edit_classifier,
            intent_parser=fake_intent_parser,
        )
        task.source.metadata["source_blend_file"] = SOURCE_BLEND_FILE
        task.execution_policy = ExecutionPolicy(
            mode="safe_non_destructive",
            preserve_source_file=True,
            output_blend_copy=OUTPUT_BLEND_COPY,
            report_file=REPORT_FILE,
        )

        planned_task = plan_task(task, scene_manifest=fake_scene_manifest())
        handler = RecordingDomainHandler()
        persistence_api = FakePersistenceApi()
        report_writer = FakeReportWriter()

        completed_task = execute_ready_task(
            planned_task,
            context=runtime_context(handler, persistence_api, report_writer),
        )

        self.assertIs(completed_task, task)
        self.assertEqual(task.state, TaskState.COMPLETED)
        self.assertEqual(task.target.bound_object, "ChestArmor_Upper_01")
        self.assertEqual(task.planning.selected_operation, "edge_soften")
        self.assertEqual(task.planning.parameters, {"strength": 0.01, "style": "mechanical"})
        self.assertEqual(handler.calls[0].task_id, task.task_id)
        self.assertEqual(handler.calls[0].operation, "edge_soften")
        self.assertEqual(handler.calls[0].target_object, "ChestArmor_Upper_01")
        self.assertEqual(handler.calls[0].parameters, {"strength": 0.01, "style": "mechanical"})
        self.assertEqual(persistence_api.save_calls, [(SOURCE_BLEND_FILE, OUTPUT_BLEND_COPY)])
        self.assertEqual(report_writer.report_calls[0][0], REPORT_FILE)
        self.assertEqual(report_writer.report_calls[0][1]["execution_status"], "success")
        self.assertEqual(report_writer.report_calls[0][1]["task_id"], task.task_id)
        self.assertEqual(task.result.success, True)
        self.assertEqual(task.result.report_file, REPORT_FILE)
        self.assertEqual(task.result.artifacts, {"output_blend_copy": OUTPUT_BLEND_COPY})

    def test_e2e_test_does_not_use_legacy_operation_dict_or_real_blender(self) -> None:
        source = Path(__file__).read_text(encoding="utf-8")

        forbidden_fragments = [
            "import " + "bpy",
            "bpy" + ".",
            "execute_" + "modification_plan",
            "execute_" + "operation_request",
            "create_" + "simplified_operation_plan",
            "domain_operations" + ".edge_soften",
            "write_" + "bytes",
            "temp" + "file",
        ]
        for forbidden_fragment in forbidden_fragments:
            self.assertNotIn(forbidden_fragment, source)


if __name__ == "__main__":
    unittest.main()
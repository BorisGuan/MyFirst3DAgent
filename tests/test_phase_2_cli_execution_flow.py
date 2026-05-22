import json
import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
AGENT_ROOT = PROJECT_ROOT / "3d_agent"
if str(AGENT_ROOT) not in sys.path:
    sys.path.insert(0, str(AGENT_ROOT))

import cli as modification_cli
from modification_execution import LegacyModificationExecutionError, build_blender_background_command, execute_modification_plan
from task_object import TaskObject, TaskState


class FakeDomainLayer:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def edge_soften(self, target_object: str, parameters: dict, implementation_hint: dict) -> dict:
        call = {
            "target_object": target_object,
            "parameters": parameters,
            "implementation_hint": implementation_hint,
        }
        self.calls.append(call)
        return {
            "output_blend_copy": implementation_hint["output_blend_copy"],
            "modification_report_file": implementation_hint["report_file"],
            "saved_original_file": False,
        }


class RecordingPlanningEngine:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def __call__(self, task: TaskObject, **kwargs) -> TaskObject:
        self.calls.append({"task": task, "kwargs": kwargs})
        task.state = TaskState.READY_TO_EXECUTE
        task.target.bound_object = task.target.semantic_part
        task.planning.selected_operation = "edge_soften"
        task.planning.parameters = dict(task.intent.parameters)
        return task


class RecordingRuntimeEngine:
    def __init__(self) -> None:
        self.calls: list[TaskObject] = []

    def __call__(self, task: TaskObject) -> TaskObject:
        self.calls.append(task)
        if task.state != TaskState.READY_TO_EXECUTE:
            raise AssertionError(f"Runtime received non-ready task: {task.state.value}")
        task.state = TaskState.COMPLETED
        task.result.success = True
        task.result.report_file = task.execution_policy.report_file
        return task


class Phase2CliExecutionFlowTests(unittest.TestCase):
    def test_cli_args_create_task_object_draft(self) -> None:
        args = modification_cli.parse_cli_args(
            [
                "--modify-copy",
                "--operation",
                "edge_soften",
                "--target",
                "ChestArmor_Upper_01",
                "--source-blend",
                "source.blend",
                "--output-blend-copy",
                "output.blend",
                "--report-file",
                "report.json",
                "--strength",
                "0.02",
                "--style",
                "mechanical",
            ]
        )
        task = modification_cli.create_task_object_from_modify_copy_cli_args(args)

        self.assertEqual(task.state, TaskState.DRAFT)
        self.assertEqual(task.target.semantic_part, "ChestArmor_Upper_01")
        self.assertEqual(task.intent.parameters, {"strength": 0.02, "style": "mechanical"})
        self.assertEqual(task.source.metadata["source_blend_file"], "source.blend")

    def test_execution_flow_uses_task_object_planning_then_runtime(self) -> None:
        planner = RecordingPlanningEngine()
        runtime = RecordingRuntimeEngine()

        result = modification_cli.run_modify_copy_cli(
            [
                "--modify-copy",
                "--operation",
                "edge_soften",
                "--target",
                "ChestArmor_Upper_01",
                "--source-blend",
                "source.blend",
                "--output-blend-copy",
                "output.blend",
                "--report-file",
                "report.json",
                "--strength",
                "0.02",
                "--style",
                "clean",
            ],
            plan_task_fn=planner,
            execute_ready_task_fn=runtime,
        )

        self.assertEqual(result["state"], "completed")
        self.assertEqual(planner.calls[0]["task"].source.channel, "legacy_modify_copy_cli")
        self.assertEqual(planner.calls[0]["kwargs"]["binding_context"]["target_part"], "ChestArmor_Upper_01")
        self.assertEqual(runtime.calls[0].planning.selected_operation, "edge_soften")

    def test_operation_plan_execution_is_retired_and_writes_no_failure_report(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            report_file = Path(temp_dir) / "failure.json"
            plan = {"operation": "edge_soften", "report_file": str(report_file)}

            with self.assertRaises(LegacyModificationExecutionError):
                execute_modification_plan(plan, domain_layer=FakeDomainLayer())

            self.assertFalse(report_file.exists())

    def test_blender_background_command_opens_source_blend_before_running_cli(self) -> None:
        command = build_blender_background_command(
            blender_executable="blender",
            cli_script="3d_agent/cli.py",
            source_blend="source.blend",
            output_blend_copy="output.blend",
            target="Body",
            report_file="report.json",
            strength=0.01,
            style="mechanical",
        )

        self.assertEqual(command[:5], ["blender", "-b", "source.blend", "--python", "3d_agent/cli.py"])
        self.assertIn("--modify-copy", command)
        self.assertIn("--operation", command)
        self.assertIn("edge_soften", command)

    def test_new_cli_and_execution_modules_do_not_use_blender_api_or_core_api_directly(self) -> None:
        for relative_path in ["cli.py", "modification_execution.py", "operation_planner.py"]:
            source = (AGENT_ROOT / relative_path).read_text(encoding="utf-8")
            self.assertNotIn("import bpy", source)
            self.assertNotIn("bpy.", source)
            self.assertNotIn("from blender_ops", source)
            self.assertNotIn("core_geometry_api", source)
        modification_execution_source = (AGENT_ROOT / "modification_execution.py").read_text(encoding="utf-8")
        self.assertNotIn("execute_operation_request", modification_execution_source)


if __name__ == "__main__":
    unittest.main()
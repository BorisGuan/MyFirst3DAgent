import json
import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
AGENT_ROOT = PROJECT_ROOT / "3d_agent"
if str(AGENT_ROOT) not in sys.path:
    sys.path.insert(0, str(AGENT_ROOT))

import cli as task_cli
import main as agent_main
from task_object import (
    ExecutionPolicy,
    TaskIntent,
    TaskObject,
    TaskPlanning,
    TaskSource,
    TaskState,
    TaskTarget,
)


def draft_task(user_input: str = "soften chest armor") -> TaskObject:
    return TaskObject(
        state=TaskState.DRAFT,
        source=TaskSource(user_input=user_input, channel="agent_layer"),
        task_type="surface_detail_enhancement",
        target=TaskTarget(semantic_part="chest_armor"),
        intent=TaskIntent(
            desired_effect="armor_layers",
            style="mechanical",
            density="low",
            scale="1/144",
        ),
    )


def ready_task() -> TaskObject:
    task = draft_task()
    task.state = TaskState.READY_TO_EXECUTE
    task.source.metadata["source_blend_file"] = "source.blend"
    task.target.bound_object = "ChestArmor_Upper_01"
    task.execution_policy = ExecutionPolicy(
        mode="safe_non_destructive",
        preserve_source_file=True,
        output_blend_copy="output.blend",
        report_file="report.json",
    )
    task.planning = TaskPlanning(
        selected_operation="edge_soften",
        parameters={"strength": 0.01, "style": "mechanical"},
    )
    return task


class RecordingPlanningEngine:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    def __call__(self, task: TaskObject, **kwargs) -> TaskObject:
        self.calls.append({"task": task, "kwargs": kwargs})
        task.state = TaskState.READY_TO_EXECUTE
        task.target.bound_object = "ChestArmor_Upper_01"
        task.planning.selected_operation = "edge_soften"
        task.planning.parameters = {"strength": 0.01, "style": "mechanical"}
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
        task.result.artifacts = {"output_blend_copy": task.execution_policy.output_blend_copy or ""}
        return task


class TaskObjectCliFlowTests(unittest.TestCase):
    def test_input_entry_runs_agent_planning_and_runtime_chain(self) -> None:
        planner = RecordingPlanningEngine()
        runtime = RecordingRuntimeEngine()

        result = task_cli.run_task_object_cli(
            [
                "--input",
                "soften chest armor",
                "--scene-manifest",
                "scene_manifest.json",
                "--source-blend",
                "source.blend",
                "--output-blend-copy",
                "output.blend",
                "--report-file",
                "report.json",
            ],
            create_draft_task_fn=draft_task,
            plan_task_fn=planner,
            execute_ready_task_fn=runtime,
            load_scene_manifest_fn=lambda path: {"manifest_path": path},
        )

        self.assertEqual(result["state"], "completed")
        planned_task = planner.calls[0]["task"]
        self.assertEqual(planned_task.source.metadata["source_blend_file"], "source.blend")
        self.assertEqual(planner.calls[0]["kwargs"]["scene_manifest"], {"manifest_path": "scene_manifest.json"})
        self.assertEqual(runtime.calls[0].planning.selected_operation, "edge_soften")
        self.assertEqual(runtime.calls[0].planning.parameters, {"strength": 0.01, "style": "mechanical"})

    def test_task_file_entry_executes_ready_task_without_planning(self) -> None:
        runtime = RecordingRuntimeEngine()
        with tempfile.TemporaryDirectory() as temp_dir:
            task_file = Path(temp_dir) / "ready_task.json"
            task_file.write_text(json.dumps(ready_task().to_dict(), ensure_ascii=False), encoding="utf-8")

            result = task_cli.run_task_object_cli(
                ["--task-file", str(task_file)],
                plan_task_fn=lambda *args, **kwargs: self.fail("ready task-file must not run Planning Engine"),
                execute_ready_task_fn=runtime,
            )

        self.assertEqual(result["state"], "completed")
        self.assertEqual(runtime.calls[0].state, TaskState.COMPLETED)
        self.assertEqual(runtime.calls[0].planning.selected_operation, "edge_soften")

    def test_legacy_modify_copy_flags_are_converted_to_task_object_before_runtime(self) -> None:
        planner = RecordingPlanningEngine()
        runtime = RecordingRuntimeEngine()

        result = task_cli.run_modify_copy_cli(
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
        self.assertEqual(runtime.calls[0].source.metadata["source_blend_file"], "source.blend")

    def test_main_exposes_task_object_cli_result_builder(self) -> None:
        result = agent_main.build_task_object_cli_result(
            [
                "--input",
                "soften chest armor",
                "--scene-manifest",
                "scene_manifest.json",
                "--source-blend",
                "source.blend",
                "--output-blend-copy",
                "output.blend",
                "--report-file",
                "report.json",
            ],
            create_draft_task_fn=draft_task,
            plan_task_fn=RecordingPlanningEngine(),
            execute_ready_task_fn=RecordingRuntimeEngine(),
            load_scene_manifest_fn=lambda path: {},
        )

        self.assertEqual(result["state"], "completed")

    def test_real_cli_entry_does_not_directly_execute_operation_plan_domain_or_core(self) -> None:
        cli_source = (AGENT_ROOT / "cli.py").read_text(encoding="utf-8")

        self.assertNotIn("execute_modification_plan", cli_source)
        self.assertNotIn("from blender_ops", cli_source)
        self.assertNotIn("import core_api", cli_source)
        self.assertNotIn("from core_api", cli_source)
        self.assertIn("plan_task", cli_source)
        self.assertIn("execute_ready_task", cli_source)


if __name__ == "__main__":
    unittest.main()
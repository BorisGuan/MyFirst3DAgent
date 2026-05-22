"""Phase 2 real modification CLI entry point."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

AGENT_ROOT = Path(__file__).resolve().parent
if str(AGENT_ROOT) not in sys.path:
    sys.path.insert(0, str(AGENT_ROOT))

from agent_layer import create_draft_task
from model.scene_manifest import load_scene_manifest
from planning import plan_task
from runtime import execute_ready_task
from task_object import ExecutionPolicy, TaskIntent, TaskObject, TaskPlanning, TaskSource, TaskState, TaskTarget

SUPPORTED_OPERATION = "edge_soften"


@dataclass(frozen=True)
class ModifyCopyCliArgs:
    modify_copy: bool
    operation: str
    target: str
    source_blend: str
    output_blend_copy: str
    report_file: str
    strength: float | None
    style: str | None


@dataclass(frozen=True)
class TaskObjectCliArgs:
    user_input: str | None
    task_file: str | None
    scene_manifest: str | None
    source_blend: str | None
    output_blend_copy: str | None
    report_file: str | None


DraftTaskFactory = Callable[[str], TaskObject]
SceneManifestLoader = Callable[[str], dict[str, Any]]
PlanningEngine = Callable[..., TaskObject]
RuntimeEngine = Callable[[TaskObject], TaskObject]


def parse_cli_args(args: list[str]) -> ModifyCopyCliArgs:
    """Parse the Step 3 real modification CLI surface."""
    parser = argparse.ArgumentParser(description="Phase 2 real model modification CLI")
    parser.add_argument("--modify-copy", action="store_true", required=True)
    parser.add_argument("--operation", choices=[SUPPORTED_OPERATION], required=True)
    parser.add_argument("--target", required=True)
    parser.add_argument("--source-blend", required=True)
    parser.add_argument("--output-blend-copy", required=True)
    parser.add_argument("--report-file", default="outputs/modification_report.json")
    parser.add_argument("--strength", type=float, default=None)
    parser.add_argument("--style", choices=["clean", "heavy", "mechanical"], default=None)
    namespace = parser.parse_args(args)
    return ModifyCopyCliArgs(
        modify_copy=namespace.modify_copy,
        operation=namespace.operation,
        target=namespace.target,
        source_blend=namespace.source_blend,
        output_blend_copy=namespace.output_blend_copy,
        report_file=namespace.report_file,
        strength=namespace.strength,
        style=namespace.style,
    )


def is_task_object_cli_args(args: list[str]) -> bool:
    """Return whether raw CLI args request the TaskObject main chain."""
    return "--input" in args or "--task-file" in args


def parse_task_object_cli_args(args: list[str]) -> TaskObjectCliArgs:
    """Parse the TaskObject main-chain CLI surface."""
    parser = argparse.ArgumentParser(description="TaskObject real modification CLI")
    parser.add_argument("--input", dest="user_input", default=None)
    parser.add_argument("--task-file", default=None)
    parser.add_argument("--scene-manifest", default=None)
    parser.add_argument("--source-blend", default=None)
    parser.add_argument("--output-blend-copy", default=None)
    parser.add_argument("--report-file", default=None)
    namespace = parser.parse_args(args)
    if bool(namespace.user_input) == bool(namespace.task_file):
        raise ValueError("Provide exactly one of --input or --task-file.")
    return TaskObjectCliArgs(
        user_input=namespace.user_input,
        task_file=namespace.task_file,
        scene_manifest=namespace.scene_manifest,
        source_blend=namespace.source_blend,
        output_blend_copy=namespace.output_blend_copy,
        report_file=namespace.report_file,
    )


def run_task_object_cli(
    args: list[str],
    create_draft_task_fn: DraftTaskFactory = create_draft_task,
    plan_task_fn: PlanningEngine = plan_task,
    execute_ready_task_fn: RuntimeEngine = execute_ready_task,
    load_scene_manifest_fn: SceneManifestLoader = load_scene_manifest,
) -> dict:
    """Run the TaskObject main chain and return the final TaskObject dict."""
    cli_args = parse_task_object_cli_args(args)
    if cli_args.user_input:
        task = create_draft_task_fn(cli_args.user_input)
        _apply_execution_cli_overrides(task, cli_args, require_execution_inputs=True)
        scene_manifest = _required_scene_manifest(cli_args, load_scene_manifest_fn)
        _plan_if_needed(task, plan_task_fn, scene_manifest=scene_manifest, source_manifest_ref=cli_args.scene_manifest)
        execute_ready_task_fn(task)
        return task.to_dict()

    task = _load_task_file(cli_args.task_file)
    _apply_execution_cli_overrides(task, cli_args, require_execution_inputs=False)
    if task.state == TaskState.DRAFT:
        scene_manifest = _required_scene_manifest(cli_args, load_scene_manifest_fn)
        _plan_if_needed(task, plan_task_fn, scene_manifest=scene_manifest, source_manifest_ref=cli_args.scene_manifest)
    execute_ready_task_fn(task)
    return task.to_dict()


def run_modify_copy_cli(
    args: list[str],
    plan_task_fn: PlanningEngine = plan_task,
    execute_ready_task_fn: RuntimeEngine = execute_ready_task,
) -> dict:
    """Run legacy structured flags through the TaskObject main chain."""
    cli_args = parse_cli_args(args)
    task = create_task_object_from_modify_copy_cli_args(cli_args)
    binding_context = {
        "target_part": cli_args.target,
        "bindings": [{"object_name": cli_args.target, "binding_status": "bound"}],
    }
    _plan_if_needed(task, plan_task_fn, binding_context=binding_context, source_manifest_ref="legacy_modify_copy_cli")
    execute_ready_task_fn(task)
    return task.to_dict()


def main(argv: list[str] | None = None) -> int:
    """Callable script entry point for Blender background mode."""
    raw_args = _script_args(sys.argv if argv is None else argv)
    try:
        result = run_task_object_cli(raw_args) if is_task_object_cli_args(raw_args) else run_modify_copy_cli(raw_args)
    except Exception as error:
        print(json.dumps({"execution_status": "failed", "error": str(error)}, ensure_ascii=False), file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def _script_args(argv: list[str]) -> list[str]:
    if "--" in argv:
        return argv[argv.index("--") + 1 :]
    return argv[1:]


def _load_task_file(task_file: str | None) -> TaskObject:
    if not task_file:
        raise ValueError("--task-file is required.")
    return TaskObject.from_dict(json.loads(Path(task_file).read_text(encoding="utf-8")))


def _apply_execution_cli_overrides(
    task: TaskObject,
    cli_args: TaskObjectCliArgs,
    require_execution_inputs: bool,
) -> None:
    if cli_args.source_blend:
        task.source.metadata["source_blend_file"] = cli_args.source_blend
    if cli_args.output_blend_copy:
        task.execution_policy.output_blend_copy = cli_args.output_blend_copy
    if cli_args.report_file:
        task.execution_policy.report_file = cli_args.report_file
    if not require_execution_inputs:
        return
    missing_fields = []
    if not task.source.metadata.get("source_blend_file") and not task.runtime.source_blend_file:
        missing_fields.append("--source-blend")
    if not task.execution_policy.output_blend_copy:
        missing_fields.append("--output-blend-copy")
    if not task.execution_policy.report_file:
        missing_fields.append("--report-file")
    if missing_fields:
        raise ValueError("TaskObject execution requires " + ", ".join(missing_fields) + ".")


def _required_scene_manifest(
    cli_args: TaskObjectCliArgs,
    load_scene_manifest_fn: SceneManifestLoader,
) -> dict[str, Any]:
    if not cli_args.scene_manifest:
        raise ValueError("--scene-manifest is required before Planning Engine can bind a draft TaskObject.")
    return load_scene_manifest_fn(cli_args.scene_manifest)


def _plan_if_needed(
    task: TaskObject,
    plan_task_fn: PlanningEngine,
    scene_manifest: dict[str, Any] | None = None,
    binding_context: dict[str, Any] | None = None,
    source_manifest_ref: str | None = None,
) -> None:
    if task.state == TaskState.DRAFT:
        plan_task_fn(
            task,
            scene_manifest=scene_manifest,
            binding_context=binding_context,
            source_manifest_ref=source_manifest_ref or "scene_manifest",
        )
    if task.state != TaskState.READY_TO_EXECUTE:
        raise ValueError(f"TaskObject must be ready_to_execute before Runtime, got {task.state.value!r}.")


def create_task_object_from_modify_copy_cli_args(cli_args: ModifyCopyCliArgs) -> TaskObject:
    """Convert legacy structured CLI fields into a draft TaskObject."""
    parameters = {}
    if cli_args.strength is not None:
        parameters["strength"] = cli_args.strength
    if cli_args.style is not None:
        parameters["style"] = cli_args.style
    return TaskObject(
        state=TaskState.DRAFT,
        source=TaskSource(
            user_input=f"legacy structured {cli_args.operation} request for {cli_args.target}",
            channel="legacy_modify_copy_cli",
            metadata={"source_blend_file": cli_args.source_blend},
        ),
        task_type="surface_detail_enhancement",
        target=TaskTarget(semantic_part=cli_args.target),
        intent=TaskIntent(
            desired_effect="surface_detail_enhancement",
            style=cli_args.style or "mechanical",
            density="low",
            scale="legacy_cli",
            parameters=parameters,
        ),
        execution_policy=ExecutionPolicy(
            mode="safe_non_destructive",
            preserve_source_file=True,
            output_blend_copy=cli_args.output_blend_copy,
            report_file=cli_args.report_file,
        ),
        planning=TaskPlanning(),
    )


if __name__ == "__main__":
    raise SystemExit(main())
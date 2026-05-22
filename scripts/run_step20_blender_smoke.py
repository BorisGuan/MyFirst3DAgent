"""Run the Step 20 real Blender smoke test.

This is a manual smoke runner, not a unittest module. It enters through the
TaskObject task-file CLI path and verifies that Blender creates an output copy,
writes a Runtime report, and leaves the source .blend unchanged.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
AGENT_ROOT = PROJECT_ROOT / "3d_agent"
if str(AGENT_ROOT) not in sys.path:
    sys.path.insert(0, str(AGENT_ROOT))

from task_object import ExecutionPolicy, TaskIntent, TaskObject, TaskPlanning, TaskSource, TaskState, TaskTarget


DEFAULT_BLENDER_EXECUTABLE = Path(r"D:\tools\blender-5.1\blender.exe")
DEFAULT_SOURCE_BLEND = PROJECT_ROOT / "examples" / "BlendFile" / "Gundam" / "GF-Gundam.blend"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "outputs" / "step20_smoke"
DEFAULT_TARGET_OBJECT = "Body_Armor01"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Step 20 TaskObject Blender smoke test.")
    parser.add_argument("--blender-executable", default=str(DEFAULT_BLENDER_EXECUTABLE))
    parser.add_argument("--source-blend", default=str(DEFAULT_SOURCE_BLEND))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--target-object", default=DEFAULT_TARGET_OBJECT)
    parser.add_argument("--strength", type=float, default=0.01)
    parser.add_argument("--style", choices=["clean", "heavy", "mechanical"], default="mechanical")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    blender_executable = Path(args.blender_executable)
    source_blend = Path(args.source_blend)
    output_dir = Path(args.output_dir)
    output_blend_copy = output_dir / f"{source_blend.stem}.step20.edge_soften.blend"
    report_file = output_dir / f"{source_blend.stem}.step20.edge_soften.report.json"
    task_file = output_dir / f"{source_blend.stem}.step20.edge_soften.task.json"
    summary_file = output_dir / f"{source_blend.stem}.step20.edge_soften.summary.json"

    _require_file(blender_executable, "Blender executable")
    _require_file(source_blend, "Source .blend")
    if source_blend.resolve() == output_blend_copy.resolve():
        raise RuntimeError("Smoke output path must not overwrite the source .blend file.")

    output_dir.mkdir(parents=True, exist_ok=True)
    _remove_previous_outputs(output_blend_copy, report_file, summary_file)
    task = _ready_task(
        source_blend=source_blend,
        output_blend_copy=output_blend_copy,
        report_file=report_file,
        target_object=args.target_object,
        strength=args.strength,
        style=args.style,
    )
    task_file.write_text(json.dumps(task.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")

    source_hash_before = _sha256(source_blend)
    command = [
        str(blender_executable),
        "-b",
        str(source_blend),
        "--python",
        str(AGENT_ROOT / "cli.py"),
        "--",
        "--task-file",
        str(task_file),
    ]
    process = subprocess.run(
        command,
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    (output_dir / "blender_stdout.log").write_text(process.stdout, encoding="utf-8")
    (output_dir / "blender_stderr.log").write_text(process.stderr, encoding="utf-8")
    source_hash_after = _sha256(source_blend)

    cli_result = _extract_first_json_object(process.stdout) if process.stdout.strip() else {}
    report = json.loads(report_file.read_text(encoding="utf-8")) if report_file.exists() else {}
    checks = _checks(
        process_returncode=process.returncode,
        source_hash_before=source_hash_before,
        source_hash_after=source_hash_after,
        output_blend_copy=output_blend_copy,
        report_file=report_file,
        cli_result=cli_result,
        report=report,
    )
    summary = {
        "command": command,
        "paths": {
            "source_blend": str(source_blend),
            "output_blend_copy": str(output_blend_copy),
            "report_file": str(report_file),
            "task_file": str(task_file),
            "summary_file": str(summary_file),
        },
        "checks": checks,
        "task_state": cli_result.get("state"),
        "task_result": cli_result.get("result", {}),
        "report_execution_status": report.get("execution_status"),
        "target_object": args.target_object,
    }
    summary_file.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if all(checks.values()) else 1


def _ready_task(
    source_blend: Path,
    output_blend_copy: Path,
    report_file: Path,
    target_object: str,
    strength: float,
    style: str,
) -> TaskObject:
    return TaskObject(
        task_id="step20-smoke-edge-soften",
        state=TaskState.READY_TO_EXECUTE,
        source=TaskSource(
            user_input="Step 20 smoke: soften a real Blender mesh edge modifier.",
            channel="step20_smoke_task_file",
            metadata={"source_blend_file": str(source_blend)},
        ),
        task_type="surface_detail_enhancement",
        target=TaskTarget(
            semantic_part=target_object,
            bound_object=target_object,
            binding_candidates=[target_object],
        ),
        intent=TaskIntent(
            desired_effect="surface_detail_enhancement",
            action="edge_soften",
            detail_type="edge_soften",
            style=style,
            density="low",
            scale="smoke",
            parameters={"strength": strength, "style": style},
        ),
        execution_policy=ExecutionPolicy(
            mode="safe_non_destructive",
            preserve_source_file=True,
            output_blend_copy=str(output_blend_copy),
            report_file=str(report_file),
        ),
        planning=TaskPlanning(
            selected_operation="edge_soften",
            parameters={"strength": strength, "style": style},
            reasoning=["Step 20 smoke task is pre-planned as a ready_to_execute TaskObject."],
        ),
    )


def _checks(
    process_returncode: int,
    source_hash_before: str,
    source_hash_after: str,
    output_blend_copy: Path,
    report_file: Path,
    cli_result: dict[str, Any],
    report: dict[str, Any],
) -> dict[str, bool]:
    artifacts = cli_result.get("result", {}).get("artifacts", {}) if isinstance(cli_result.get("result"), dict) else {}
    return {
        "blender_exit_success": process_returncode == 0,
        "output_blend_copy_exists": output_blend_copy.exists() and output_blend_copy.stat().st_size > 0,
        "report_json_exists": report_file.exists() and report_file.stat().st_size > 0,
        "source_blend_unchanged": source_hash_before == source_hash_after,
        "task_completed": cli_result.get("state") == "completed",
        "task_result_artifact_points_to_output": artifacts.get("output_blend_copy") == str(output_blend_copy),
        "runtime_report_success": report.get("execution_status") == "success",
    }


def _extract_first_json_object(text: str) -> dict[str, Any]:
    decoder = json.JSONDecoder()
    for index, character in enumerate(text):
        if character != "{":
            continue
        try:
            value, _ = decoder.raw_decode(text[index:])
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            return value
    raise ValueError("No JSON object found in Blender stdout.")


def _remove_previous_outputs(*paths: Path) -> None:
    for path in paths:
        if path.exists():
            path.unlink()


def _require_file(path: Path, label: str) -> None:
    if not path.exists():
        raise FileNotFoundError(f"{label} does not exist: {path}")
    if not path.is_file():
        raise FileNotFoundError(f"{label} is not a file: {path}")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
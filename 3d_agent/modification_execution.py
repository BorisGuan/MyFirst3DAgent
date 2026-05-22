"""Legacy Phase 2 command helpers.

OperationPlan execution is retired. Real modification now enters through a
TaskObject and is executed by the Runtime layer.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from operation_planner import SUPPORTED_OPERATION


class LegacyModificationExecutionError(RuntimeError):
    """Raised when old OperationPlan execution is requested."""


def execute_modification_plan(
    operation_plan: dict[str, Any],
    domain_layer: Any | None = None,
) -> dict[str, Any]:
    """Reject the retired OperationPlan execution path."""
    raise LegacyModificationExecutionError(
        "OperationPlan execution is retired. Use --input or --task-file so Runtime receives a TaskObject."
    )


def build_blender_background_command(
    blender_executable: str,
    cli_script: str | Path,
    source_blend: str | Path,
    output_blend_copy: str | Path,
    target: str,
    report_file: str | Path,
    operation: str = SUPPORTED_OPERATION,
    strength: float | None = None,
    style: str | None = None,
) -> list[str]:
    """Build a legacy structured CLI command that cli.py converts to TaskObject."""
    command = [
        blender_executable,
        "-b",
        str(source_blend),
        "--python",
        str(cli_script),
        "--",
        "--modify-copy",
        "--operation",
        operation,
        "--target",
        target,
        "--source-blend",
        str(source_blend),
        "--output-blend-copy",
        str(output_blend_copy),
        "--report-file",
        str(report_file),
    ]
    if strength is not None:
        command.extend(["--strength", str(strength)])
    if style is not None:
        command.extend(["--style", style])
    return command

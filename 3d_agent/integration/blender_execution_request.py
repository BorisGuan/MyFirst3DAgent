"""Build V0.7 Blender execution requests."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def create_blender_execution_request(
    source_blend_file: str,
    script_file: str,
    output_report_file: str,
    blender_executable: str = "blender",
    save_copy: bool = False,
    output_blend_copy: str | None = None,
    safe_preview_session: dict[str, Any] | None = None,
    script_safety_scan: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create the machine-readable contract used before calling Blender."""
    output_copy = output_blend_copy or _default_output_blend_copy(source_blend_file)
    return {
        "request_version": "v0_7",
        "execution_mode": "preview_only",
        "target_software": "blender",
        "blender_executable": blender_executable,
        "source_blend_file": source_blend_file,
        "script_file": script_file,
        "output_report_file": output_report_file,
        "output_blend_copy": output_copy,
        "save_copy": save_copy,
        "allowed_operations": (safe_preview_session or {}).get("allowed_operations", []),
        "forbidden_operations": (safe_preview_session or {}).get("forbidden_operations", []),
        "preflight_checks": [
            {
                "check_id": "script_safety_scan",
                "status": (script_safety_scan or {}).get("safety_status", "not_run"),
            },
            {
                "check_id": "source_blend_file_exists",
                "status": "passed" if Path(source_blend_file).exists() else "failed",
            },
        ],
    }


def _default_output_blend_copy(source_blend_file: str) -> str:
    source_path = Path(source_blend_file)
    return str(Path("outputs") / f"{source_path.stem}.preview.blend")
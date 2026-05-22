"""Run V0.7 preview-only Blender execution requests."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from blender_ops.authoring_api import blender_authoring_api_source


def write_blender_preview_script(script_text: str, output_dir: str | Path = "outputs") -> str:
    """Write a generated preview script to disk and return its path."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    script_path = output_path / "v0_7_preview_script.py"
    script_path.write_text(script_text, encoding="utf-8")
    return str(script_path)


def write_blender_execution_script(
    script_text: str,
    output_report_file: str,
    save_copy: bool = False,
    output_blend_copy: str | None = None,
    output_dir: str | Path = "outputs",
) -> str:
    """Write a preview script adjusted to emit the V0.7 report path."""
    report_literal = f"Path({str(Path(output_report_file))!r})"
    adjusted_script = script_text.replace(
        'report_path = Path(f"{session_id}_preview_report.json")',
        f"report_path = {report_literal}",
    )
    if save_copy:
        if not output_blend_copy:
            raise ValueError("output_blend_copy is required when save_copy is enabled.")
        copy_literal = f"Path({str(Path(output_blend_copy))!r})"
        save_copy_block = f'''

output_blend_copy = {copy_literal}
output_blend_copy.parent.mkdir(parents=True, exist_ok=True)
if output_blend_copy.resolve() == Path(bpy.data.filepath).resolve():
    raise RuntimeError("Refusing to overwrite the source .blend file.")
bpy.ops.wm.save_as_mainfile(filepath=str(output_blend_copy))
preview_report["saved_preview_copy"] = True
preview_report["output_blend_copy"] = str(output_blend_copy)
report_path.write_text(json.dumps(preview_report, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"Saved V0.8C preview copy to {{output_blend_copy}}")
'''
        adjusted_script = adjusted_script.replace(
            'print(f"Wrote V0.6 preview report to {report_path}")',
            'print(f"Wrote V0.6 preview report to {report_path}")' + save_copy_block,
        )
    return write_blender_preview_script(adjusted_script, output_dir)


def write_blender_authoring_execution_script(
    script_text: str,
    output_report_file: str,
    save_copy: bool = False,
    output_blend_copy: str | None = None,
    output_dir: str | Path = "outputs",
) -> str:
    """Write the V0.9A authoring script and its Blender-side API module."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    api_path = output_path / "blender_authoring_api.py"
    api_path.write_text(blender_authoring_api_source(), encoding="utf-8")
    report_literal = f"Path({str(Path(output_report_file))!r})"
    adjusted_script = script_text.replace(
        'report_path = Path(f"{session_id}_authoring_report.json")',
        f"report_path = {report_literal}",
    )
    if save_copy:
        if not output_blend_copy:
            raise ValueError("output_blend_copy is required when save_copy is enabled.")
        copy_literal = f"Path({str(Path(output_blend_copy))!r})"
        save_copy_block = f'''

from blender_authoring_api import save_as_copy_only
output_blend_copy = {copy_literal}
saved_copy_path = save_as_copy_only(output_blend_copy)
authoring_report["saved_preview_copy"] = True
authoring_report["output_blend_copy"] = saved_copy_path
report_path.write_text(json.dumps(authoring_report, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"Saved V0.9A authoring copy to {{saved_copy_path}}")
'''
        adjusted_script = adjusted_script.replace(
            'print(f"Wrote V0.9A authoring report to {report_path}")',
            'print(f"Wrote V0.9A authoring report to {report_path}")' + save_copy_block,
        )
    script_path = output_path / "v0_9a_authoring_script.py"
    script_path.write_text(adjusted_script, encoding="utf-8")
    return str(script_path)


def run_blender_execution_request(request: dict[str, Any], timeout_seconds: int = 120) -> dict[str, Any]:
    """Execute a preview-only request with Blender background mode."""
    report_path = Path(request["output_report_file"])
    report_path.parent.mkdir(parents=True, exist_ok=True)
    blender_executable = request.get("blender_executable", "blender")
    command = [
        blender_executable,
        "--background",
        request["source_blend_file"],
        "--python",
        request["script_file"],
    ]
    if str(blender_executable).endswith(".py"):
        command.insert(0, sys.executable)
    completed = subprocess.run(command, capture_output=True, text=True, timeout=timeout_seconds, check=False)
    script_report = _load_json_if_exists(report_path)
    generated_objects = script_report.get("generated_objects", []) if isinstance(script_report, dict) else []
    generated_authoring_objects = (
        script_report.get("generated_authoring_objects", []) if isinstance(script_report, dict) else []
    )
    execution_report = {
        "report_version": "v0_7",
        "execution_status": "success" if completed.returncode == 0 and report_path.exists() else "failed",
        "execution_mode": request.get("execution_mode", "preview_only"),
        "blender_version": _extract_blender_version(completed.stdout),
        "source_blend_file": request["source_blend_file"],
        "saved_original_file": False,
        "saved_preview_copy": bool(script_report.get("saved_preview_copy")) if isinstance(script_report, dict) else False,
        "output_blend_copy": script_report.get("output_blend_copy", "") if isinstance(script_report, dict) else "",
        "created_collections": _created_collections(script_report),
        "generated_objects": generated_objects,
        "generated_authoring_objects": generated_authoring_objects,
        "modified_bound_mesh": False,
        "script_exit_code": completed.returncode,
        "stdout_excerpt": _excerpt(completed.stdout),
        "stderr_excerpt": _excerpt(completed.stderr),
        "script_report_file": str(report_path),
        "report_summary": _summary(completed.returncode, generated_objects, report_path.exists()),
    }
    return execution_report


def _load_json_if_exists(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def _extract_blender_version(stdout: str) -> str:
    for line in stdout.splitlines():
        if line.startswith("Blender "):
            return line.strip()
    return ""


def _created_collections(script_report: dict[str, Any]) -> list[str]:
    if not isinstance(script_report, dict):
        return []
    session_id = script_report.get("session_id")
    target_part = script_report.get("target_part")
    if session_id and target_part:
        return [f"preview_session:{session_id}"]
    return []


def _excerpt(value: str, limit: int = 2000) -> str:
    return value[-limit:] if len(value) > limit else value


def _summary(returncode: int, generated_objects: list[str], report_exists: bool) -> str:
    if returncode != 0:
        return f"Blender exited with code {returncode}."
    if not report_exists:
        return "Blender finished but no preview report was written."
    return f"Blender preview completed with {len(generated_objects)} generated preview objects."
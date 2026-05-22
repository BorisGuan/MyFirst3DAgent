"""Core persistence API: Blender save and low-level operation report helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


_REPORT_STATE: dict[str, Any] = {
    "source_blend_file": "",
    "output_blend_copy": "",
    "modified_objects": [],
    "removed_modifiers": [],
}


def reset_modification_report_state() -> None:
    """Reset low-level report state for a fresh execution context."""
    _REPORT_STATE["source_blend_file"] = ""
    _REPORT_STATE["output_blend_copy"] = ""
    _REPORT_STATE["modified_objects"] = []
    _REPORT_STATE["removed_modifiers"] = []


def record_modified_object(record: dict[str, Any]) -> None:
    """Record a low-level object modification fact."""
    _REPORT_STATE["modified_objects"].append(dict(record))


def record_removed_modifier(record: dict[str, Any]) -> None:
    """Record a low-level removed modifier fact."""
    _REPORT_STATE["removed_modifiers"].append(dict(record))


def save_as_copy_only(source_file: str | Path, output_file: str | Path) -> str:
    """Save the current Blender file to output_file without overwriting source_file."""
    blender = _get_bpy()
    source_path = Path(source_file)
    output_path = Path(output_file)
    current_file = getattr(blender.data, "filepath", "")

    if _same_path(source_path, output_path):
        raise RuntimeError("Refusing to overwrite the source .blend file.")
    if current_file and _same_path(Path(current_file), output_path):
        raise RuntimeError("Refusing to overwrite the currently opened .blend file.")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    blender.ops.wm.save_as_mainfile(filepath=str(output_path))
    _REPORT_STATE["source_blend_file"] = str(source_path)
    _REPORT_STATE["output_blend_copy"] = str(output_path)
    return str(output_path)


def build_modification_report() -> dict[str, Any]:
    """Build a report from low-level Core API operations."""
    blender = _get_bpy()
    return {
        "report_version": "core_geometry_api_v1",
        "report_type": "core_geometry_api_modification_report",
        "source_blend_file": _REPORT_STATE["source_blend_file"] or str(getattr(blender.data, "filepath", "")),
        "saved_original_file": False,
        "output_blend_copy": _REPORT_STATE["output_blend_copy"],
        "modified_objects": list(_REPORT_STATE["modified_objects"]),
        "removed_modifiers": list(_REPORT_STATE["removed_modifiers"]),
    }


def write_modification_report(path: str | Path, report: dict[str, Any] | None = None) -> str:
    """Write a modification report as JSON."""
    report_path = Path(path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_data = build_modification_report() if report is None else report
    report_path.write_text(json.dumps(report_data, ensure_ascii=False, indent=2), encoding="utf-8")
    return str(report_path)


def _get_bpy() -> Any:
    try:
        import bpy  # type: ignore[import-not-found]
    except ModuleNotFoundError as error:
        raise RuntimeError("Core persistence API requires Blender's bpy module.") from error
    return bpy


def _same_path(first_path: Path, second_path: Path) -> bool:
    return first_path.resolve() == second_path.resolve()
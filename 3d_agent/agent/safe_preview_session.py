"""Safe Preview Session creation for V0.6 Geometry Preview Plans.

This module creates a preview-only safety contract. It does not execute Blender,
create objects, modify mesh data, or save files.
"""

import re
from typing import Any


SESSION_VERSION = "v0_6"
TARGET_SOFTWARE = "blender"
EXECUTION_MODE = "preview_only"

ALLOWED_PREVIEW_OPERATIONS = [
    "create_preview_collection",
    "create_generated_preview_object",
    "tag_generated_preview_object",
    "write_preview_report_json",
]
BLOCKED_ALLOWED_OPERATIONS = ["write_preview_report_json"]
FORBIDDEN_OPERATIONS = [
    "edit_bound_mesh",
    "delete_user_objects",
    "save_blend_file",
    "apply_modifiers",
    "boolean_operation",
    "export_final_production_model",
]
BASE_PREFLIGHT_CHECKS = [
    "verify_preview_plan_version_v0_6",
    "verify_execution_mode_preview_only",
    "verify_bound_mesh_is_read_only",
    "verify_generated_objects_will_be_tagged",
    "verify_preview_collection_isolated",
]
CONFIRMATION_PREFLIGHT_CHECK = "verify_user_confirmation_for_preview_elements"
BLOCKED_PREFLIGHT_CHECK = "stop_if_preview_status_blocked"


def create_safe_preview_session(geometry_preview_plan: dict[str, Any]) -> dict[str, Any]:
    """Create a safe preview session contract from a V0.6 Geometry Preview Plan."""
    target_part = geometry_preview_plan.get("target_part", "unknown_part")
    preview_status = geometry_preview_plan.get("preview_status", "blocked")
    session_id = _session_id(target_part, preview_status)

    return {
        "session_version": SESSION_VERSION,
        "session_id": session_id,
        "execution_mode": EXECUTION_MODE,
        "target_software": TARGET_SOFTWARE,
        "allowed_operations": _allowed_operations(preview_status),
        "forbidden_operations": list(FORBIDDEN_OPERATIONS),
        "preflight_checks": _preflight_checks(geometry_preview_plan),
        "generated_artifacts": _generated_artifacts(geometry_preview_plan, session_id),
        "rollback_strategy": _rollback_strategy(geometry_preview_plan, session_id),
    }


def _session_id(target_part: str, preview_status: str) -> str:
    normalized_part = re.sub(r"[^a-z0-9]+", "_", target_part.lower()).strip("_") or "unknown_part"
    status_suffix = "blocked" if preview_status == "blocked" else "preview"
    return f"v06_{normalized_part}_{status_suffix}_001"


def _allowed_operations(preview_status: str) -> list[str]:
    if preview_status == "blocked":
        return list(BLOCKED_ALLOWED_OPERATIONS)
    return list(ALLOWED_PREVIEW_OPERATIONS)


def _preflight_checks(geometry_preview_plan: dict[str, Any]) -> list[str]:
    checks = list(BASE_PREFLIGHT_CHECKS)
    preview_status = geometry_preview_plan.get("preview_status", "blocked")
    if preview_status == "blocked":
        checks.append(BLOCKED_PREFLIGHT_CHECK)
    if geometry_preview_plan.get("required_confirmations") or _preview_elements_need_confirmation(geometry_preview_plan):
        checks.append(CONFIRMATION_PREFLIGHT_CHECK)
    for target_object in geometry_preview_plan.get("target_objects", []):
        checks.append(f"verify_target_object_exists:{target_object}")
    return _merge_unique(checks)


def _preview_elements_need_confirmation(geometry_preview_plan: dict[str, Any]) -> bool:
    return any(
        preview_element.get("requires_user_confirmation")
        for preview_element in geometry_preview_plan.get("preview_elements", [])
    )


def _generated_artifacts(geometry_preview_plan: dict[str, Any], session_id: str) -> list[dict[str, Any]]:
    artifacts = [
        {
            "artifact_type": "preview_report_json",
            "artifact_name": f"{session_id}_report.json",
            "description": "记录 V0.6 预览计划、安全规则和用户确认事项。",
        }
    ]
    if geometry_preview_plan.get("preview_status") == "blocked":
        return artifacts

    collection_name = f"V06_{geometry_preview_plan.get('target_part', 'unknown_part')}_preview"
    artifacts.insert(
        0,
        {
            "artifact_type": "preview_collection",
            "artifact_name": collection_name,
            "description": "独立 Blender preview collection，只存放 generated preview objects。",
        },
    )
    artifacts.extend(
        {
            "artifact_type": "generated_preview_object",
            "artifact_name": preview_element.get("element_id", "preview_element"),
            "description": _artifact_description(preview_element),
        }
        for preview_element in geometry_preview_plan.get("preview_elements", [])
    )
    return artifacts


def _artifact_description(preview_element: dict[str, Any]) -> str:
    element_type = preview_element.get("element_type", "manual_review_note")
    target_object = preview_element.get("target_object", "unknown_object")
    return f"{element_type} for {target_object}; generated object must be tagged with session metadata."


def _rollback_strategy(geometry_preview_plan: dict[str, Any], session_id: str) -> list[str]:
    rollback_steps = [f"删除带有 v0_6_preview_session_id={session_id} 的 generated preview objects。"]
    rollback_steps.extend(geometry_preview_plan.get("rollback_plan", []))
    rollback_steps.append("确认所有绑定目标 mesh、材质和用户已有对象保持不变。")
    return _merge_unique(rollback_steps)


def _merge_unique(items: list[str]) -> list[str]:
    merged = []
    for item in items:
        if item and item not in merged:
            merged.append(item)
    return merged
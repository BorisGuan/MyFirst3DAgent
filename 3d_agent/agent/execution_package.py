"""Rule-based Execution Package conversion for V0.4.

This module turns a V0.3 Execution Blueprint into a software-facing execution
package. It does not call an LLM, execute Blender, inspect mesh data, or modify
real model files.
"""

from typing import Any


TOOL_FAMILY_EXECUTION_RULES: dict[str, dict[str, Any]] = {
    "surface_detailing": {
        "execution_mode": "annotation_package",
        "task_types": ["create_annotation", "create_curve_guide"],
        "required_inputs": ["real_mesh_file", "target_part_object", "surface_boundary_reference"],
        "checkpoint": "确认标记路径不会穿过舱门、关节或关键结构。",
        "rollback": "删除生成的线条标记、曲线指导对象或注释集合。",
        "artifact": "blender_annotation_script.py",
    },
    "armor_composition": {
        "execution_mode": "annotation_package",
        "task_types": ["create_annotation", "mark_risk_zone"],
        "required_inputs": ["real_mesh_file", "target_part_object", "surface_boundary_reference", "thickness_reference"],
        "checkpoint": "确认装甲层级不会遮挡关节、接口或主要轮廓。",
        "rollback": "删除装甲层级标记和风险区域标记。",
        "artifact": "blender_annotation_script.py",
    },
    "mechanical_attachment": {
        "execution_mode": "annotation_package",
        "task_types": ["create_curve_guide", "manual_review"],
        "required_inputs": ["real_mesh_file", "target_part_object", "connection_point_reference", "joint_range_reference"],
        "checkpoint": "确认连接端点、避障路径和关节活动范围。",
        "rollback": "删除曲线指导对象和连接端点标记。",
        "artifact": "blender_curve_guide_script.py",
    },
    "propulsion_detailing": {
        "execution_mode": "placeholder_package",
        "task_types": ["place_placeholder", "manual_review"],
        "required_inputs": ["real_mesh_file", "target_part_object", "mounting_surface_reference", "orientation_reference"],
        "checkpoint": "确认喷口朝向、安装面和周边结构空间。",
        "rollback": "删除喷口占位对象和朝向标记。",
        "artifact": "blender_placeholder_script.py",
    },
    "sensor_detailing": {
        "execution_mode": "placeholder_package",
        "task_types": ["place_placeholder"],
        "required_inputs": ["real_mesh_file", "target_part_object", "orientation_reference"],
        "checkpoint": "确认传感器朝向、可见性和比例。",
        "rollback": "删除传感器占位对象和朝向标记。",
        "artifact": "blender_placeholder_script.py",
    },
    "damage_weathering": {
        "execution_mode": "annotation_package",
        "task_types": ["create_annotation", "mark_risk_zone"],
        "required_inputs": ["real_mesh_file", "target_part_object", "surface_boundary_reference", "thickness_reference"],
        "checkpoint": "确认战损只位于非承力表面，并保持浅表处理。",
        "rollback": "删除战损注释、风险区域标记和浅表处理提示。",
        "artifact": "blender_annotation_script.py",
    },
}

BLOCKER_REQUIRED_INPUTS = {
    "no_real_mesh": "real_mesh_file",
    "no_surface_boundaries": "surface_boundary_reference",
    "no_part_connection_points": "connection_point_reference",
    "no_joint_range_data": "joint_range_reference",
    "no_thickness_data": "thickness_reference",
    "no_mounting_surface": "mounting_surface_reference",
    "no_scale_parameters": "scale_parameters",
}

ZONE_ROLE_TASK_HINTS = {
    "primary_visible_surface": "在主要可见面创建清晰标记，先不修改真实几何。",
    "edge_detail_zone": "在边缘区域创建保守标记，避免削弱外轮廓。",
    "joint_sensitive_zone": "标记为关节敏感区，要求人工复核活动范围。",
    "mounting_zone": "创建安装面或连接点占位标记，等待真实连接面确认。",
    "damage_zone": "创建浅表战损注释，避免深切或布尔操作。",
    "sensor_orientation_zone": "创建带朝向提示的占位标记。",
    "unknown_zone": "创建保守人工复核任务，等待区域语义确认。",
}


def create_execution_package(
    execution_blueprint: dict[str, Any],
    target_software: str = "blender",
) -> dict[str, Any]:
    """Convert a V0.3 Execution Blueprint into a V0.4 Execution Package."""
    execution_intent = execution_blueprint.get("execution_intent", {})
    tool_family = execution_intent.get("tool_family")
    if tool_family not in TOOL_FAMILY_EXECUTION_RULES:
        raise ValueError(f"Unsupported tool family for Execution Package: {tool_family!r}")

    rule = TOOL_FAMILY_EXECUTION_RULES[tool_family]
    target_part = execution_blueprint.get("target_part", "unknown_part")
    blocked_by = _merge_unique(
        execution_blueprint.get("automation_assessment", {}).get("blocked_by", []),
        _required_blockers(execution_blueprint),
    )
    required_inputs = _required_inputs(rule, blocked_by)
    execution_tasks = _execution_tasks(execution_blueprint, rule)

    return {
        "package_version": "v0_4",
        "source_blueprint_ref": "execution_blueprint",
        "target_part": target_part,
        "target_software": target_software,
        "execution_mode": rule["execution_mode"],
        "execution_tasks": execution_tasks,
        "required_inputs": required_inputs,
        "blocked_by": blocked_by,
        "user_checkpoints": _user_checkpoints(execution_blueprint, rule),
        "rollback_plan": _rollback_plan(rule),
        "output_artifacts": _output_artifacts(rule),
        "execution_summary": _execution_summary(execution_blueprint, rule, len(execution_tasks)),
    }


def _required_blockers(execution_blueprint: dict[str, Any]) -> list[str]:
    blockers = []
    execution_intent = execution_blueprint.get("execution_intent", {})
    if execution_intent.get("requires_mesh_access"):
        blockers.append("no_real_mesh")
    if execution_intent.get("requires_part_boundaries"):
        blockers.append("no_surface_boundaries")
    return blockers


def _required_inputs(rule: dict[str, Any], blocked_by: list[str]) -> list[str]:
    blocker_inputs = [BLOCKER_REQUIRED_INPUTS[blocker] for blocker in blocked_by if blocker in BLOCKER_REQUIRED_INPUTS]
    return _merge_unique(rule["required_inputs"], blocker_inputs)


def _execution_tasks(execution_blueprint: dict[str, Any], rule: dict[str, Any]) -> list[dict[str, Any]]:
    zone_mapping = execution_blueprint.get("zone_mapping") or [
        {
            "input_zone": "unknown_zone",
            "zone_role": "unknown_zone",
            "execution_hint": "缺少区域语义，建议人工确认后再执行。",
        }
    ]
    tasks = []
    for index, zone in enumerate(zone_mapping, start=1):
        zone_role = zone.get("zone_role", "unknown_zone")
        tasks.append(
            {
                "task_id": f"task_{index:03d}",
                "task_type": _task_type_for_zone(rule, zone_role),
                "target_zone": zone.get("input_zone", "unknown_zone"),
                "instruction": _task_instruction(execution_blueprint, zone),
                "requires_user_confirmation": True,
                "status": "planned",
            }
        )
    if _requires_manual_review(execution_blueprint, rule):
        tasks.append(_manual_review_task(len(tasks) + 1, execution_blueprint))
    return tasks


def _task_type_for_zone(rule: dict[str, Any], zone_role: str) -> str:
    task_types = rule["task_types"]
    if zone_role in {"joint_sensitive_zone", "unknown_zone"} and "manual_review" in task_types:
        return "manual_review"
    if zone_role == "mounting_zone" and "place_placeholder" in task_types:
        return "place_placeholder"
    if zone_role == "sensor_orientation_zone" and "place_placeholder" in task_types:
        return "place_placeholder"
    if zone_role == "damage_zone" and "mark_risk_zone" in task_types:
        return "mark_risk_zone"
    return task_types[0]


def _task_instruction(execution_blueprint: dict[str, Any], zone: dict[str, str]) -> str:
    method = execution_blueprint.get("execution_intent", {}).get("recommended_method", "manual_review")
    target_part = execution_blueprint.get("target_part", "目标部件")
    zone_role = zone.get("zone_role", "unknown_zone")
    zone_hint = ZONE_ROLE_TASK_HINTS.get(zone_role, ZONE_ROLE_TASK_HINTS["unknown_zone"])
    execution_hint = zone.get("execution_hint", "保守处理该区域。")
    return f"针对 {target_part} 的 {zone.get('input_zone', 'unknown_zone')}，按 {method} 生成执行标记；{zone_hint}{execution_hint}"


def _requires_manual_review(execution_blueprint: dict[str, Any], rule: dict[str, Any]) -> bool:
    risk_level = execution_blueprint.get("risk_review", {}).get("risk_level")
    difficulty = execution_blueprint.get("automation_assessment", {}).get("difficulty")
    return risk_level == "high" or difficulty == "high" or "manual_review" in rule["task_types"]


def _manual_review_task(task_index: int, execution_blueprint: dict[str, Any]) -> dict[str, Any]:
    risk_reasons = execution_blueprint.get("risk_review", {}).get("risk_reasons", [])
    reason_text = "；".join(risk_reasons) if risk_reasons else "当前信息不足，需要人工复核。"
    return {
        "task_id": f"task_{task_index:03d}",
        "task_type": "manual_review",
        "target_zone": "global_review",
        "instruction": f"执行前人工复核风险：{reason_text}",
        "requires_user_confirmation": True,
        "status": "planned",
    }


def _user_checkpoints(execution_blueprint: dict[str, Any], rule: dict[str, Any]) -> list[str]:
    checkpoints = [
        "确认目标部件对象是否正确。",
        rule["checkpoint"],
    ]
    mitigation_steps = execution_blueprint.get("risk_review", {}).get("mitigation_steps", [])
    return _merge_unique(checkpoints, mitigation_steps)


def _rollback_plan(rule: dict[str, Any]) -> list[str]:
    return [rule["rollback"], "保留原始模型文件，不覆盖用户已有文件。"]


def _output_artifacts(rule: dict[str, Any]) -> list[str]:
    return ["execution_package.json", rule["artifact"]]


def _execution_summary(execution_blueprint: dict[str, Any], rule: dict[str, Any], task_count: int) -> str:
    target_part = execution_blueprint.get("target_part", "目标部件")
    method = execution_blueprint.get("execution_intent", {}).get("recommended_method", "manual_review")
    return (
        f"已为 {target_part} 生成 {rule['execution_mode']}，包含 {task_count} 个计划任务；"
        f"建议按 {method} 先创建标记或占位对象，当前不会修改真实几何。"
    )


def _merge_unique(first_items: list[str], second_items: list[str]) -> list[str]:
    merged: list[str] = []
    for item in [*first_items, *second_items]:
        if item and item not in merged:
            merged.append(item)
    return merged
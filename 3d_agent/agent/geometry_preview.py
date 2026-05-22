"""Rule-based Geometry Preview Plan creation for V0.6.

This module turns V0.4 Execution Packages and V0.5 binding reviews into a
preview-only plan. It does not execute Blender, inspect mesh topology, or
modify model files.
"""

from typing import Any


PREVIEW_VERSION = "v0_6"
BOUND_CONFIDENCE = 0.90

DEFAULT_SAFETY_RULES = [
    "preview_only",
    "do_not_modify_bound_mesh",
    "do_not_apply_modifiers",
    "do_not_save_blend_file",
    "generated_objects_must_be_tagged",
    "generated_objects_must_be_in_preview_collection",
    "visual_guides_must_be_generated_objects",
]

DEFAULT_ROLLBACK_PLAN = [
    "删除带有 v0_6_preview_session_id 的 generated preview objects。",
    "删除空的 V0.6 preview collection。",
    "保留用户原始对象和材质不变。",
]

TASK_ELEMENT_TYPES = {
    "create_annotation": "surface_detail_hint",
    "create_curve_guide": "panel_line_hint",
    "mark_risk_zone": "risk_marker",
    "place_placeholder": "placeholder_volume",
    "manual_review": "manual_review_note",
}

ELEMENT_VISUAL_STYLES = {
    "panel_line_hint": {"color": "warning_blue", "display": "curve_overlay"},
    "surface_detail_hint": {"color": "warning_blue", "display": "annotation_marker"},
    "placeholder_volume": {"color": "preview_orange", "display": "wireframe_placeholder"},
    "mounting_point_hint": {"color": "preview_orange", "display": "empty_anchor"},
    "risk_marker": {"color": "risk_red", "display": "risk_marker"},
    "manual_review_note": {"color": "review_yellow", "display": "text_note"},
    "symmetry_reference": {"color": "mirror_green", "display": "axis_marker"},
}

VISUAL_GUIDE_TYPES = {
    "panel_line_hint": "curve_line_overlay",
    "surface_detail_hint": "annotation_disc",
    "placeholder_volume": "transparent_blockout",
    "mounting_point_hint": "anchor_sphere",
    "risk_marker": "risk_sphere",
    "manual_review_note": "text_note",
    "symmetry_reference": "mirror_axis",
}

VISUAL_GUIDE_MATERIALS = {
    "panel_line_hint": "AI_Preview_Blue",
    "surface_detail_hint": "AI_Preview_Blue",
    "placeholder_volume": "AI_Preview_Orange",
    "mounting_point_hint": "AI_Preview_Orange",
    "risk_marker": "AI_Preview_Red",
    "manual_review_note": "AI_Preview_Yellow",
    "symmetry_reference": "AI_Preview_Green",
}

CONFIRMATION_BY_BLOCKER = {
    "no_surface_boundaries": "确认预览线条或区域没有穿过舱门、关节或关键表面边界。",
    "no_part_connection_points": "确认预览对象不会覆盖连接点、卡榫或装配接口。",
    "no_joint_range_data": "确认关节活动范围，预览对象不能影响可动结构。",
    "no_thickness_data": "确认目标部件厚度足够，预览细节不能暗示深切或穿透。",
    "no_mounting_surface": "确认安装面和朝向，再把占位预览转换成真实结构。",
}


def create_geometry_preview_plan(
    execution_package: dict[str, Any],
    model_binding_context: dict[str, Any],
    execution_package_review: dict[str, Any],
) -> dict[str, Any]:
    """Create a V0.6 Geometry Preview Plan from V0.4 and V0.5 outputs."""
    target_part = execution_package.get(
        "target_part",
        model_binding_context.get("target_part", execution_package_review.get("target_part", "unknown_part")),
    )
    bound_bindings = _bound_bindings(model_binding_context)
    candidate_bindings = _candidate_bindings(model_binding_context)
    preview_status = _preview_status(execution_package_review, bound_bindings, candidate_bindings)
    target_objects = _target_objects(preview_status, bound_bindings, candidate_bindings)
    blocked_by = _blocked_by(execution_package_review, preview_status)
    preview_elements = _preview_elements(execution_package, preview_status, target_objects)
    preview_mode = _preview_mode(preview_status, preview_elements)

    return {
        "preview_version": PREVIEW_VERSION,
        "source_package_ref": "execution_package",
        "source_binding_ref": "model_binding_context",
        "source_review_ref": "execution_package_review",
        "target_part": target_part,
        "preview_mode": preview_mode,
        "preview_status": preview_status,
        "target_objects": target_objects,
        "preview_elements": preview_elements,
        "required_confirmations": _required_confirmations(
            execution_package,
            execution_package_review,
            preview_status,
            candidate_bindings,
        ),
        "blocked_by": blocked_by,
        "safety_rules": list(DEFAULT_SAFETY_RULES),
        "rollback_plan": list(DEFAULT_ROLLBACK_PLAN),
        "preview_summary": _preview_summary(target_part, preview_status, target_objects, blocked_by),
    }


def _bound_bindings(model_binding_context: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        binding
        for binding in model_binding_context.get("bindings", [])
        if binding.get("binding_status") == "bound" and binding.get("confidence", 0.0) >= BOUND_CONFIDENCE
    ]


def _candidate_bindings(model_binding_context: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        binding
        for binding in model_binding_context.get("bindings", [])
        if binding.get("binding_status") in {"candidate", "ambiguous"}
    ]


def _preview_status(
    execution_package_review: dict[str, Any],
    bound_bindings: list[dict[str, Any]],
    candidate_bindings: list[dict[str, Any]],
) -> str:
    review_status = execution_package_review.get("review_status")
    if review_status == "blocked":
        return "blocked"
    if bound_bindings:
        return "preview_ready"
    if candidate_bindings:
        return "needs_user_confirmation"
    return "blocked"


def _target_objects(
    preview_status: str,
    bound_bindings: list[dict[str, Any]],
    candidate_bindings: list[dict[str, Any]],
) -> list[str]:
    if preview_status == "blocked":
        return []
    bindings = bound_bindings if bound_bindings else candidate_bindings
    return _merge_unique([binding.get("object_name", "") for binding in bindings])


def _blocked_by(execution_package_review: dict[str, Any], preview_status: str) -> list[str]:
    blockers = list(execution_package_review.get("remaining_blockers", []))
    if preview_status == "blocked" and "no_trusted_bound_object" not in blockers:
        blockers.insert(0, "no_trusted_bound_object")
    return _merge_unique(blockers)


def _preview_elements(
    execution_package: dict[str, Any],
    preview_status: str,
    target_objects: list[str],
) -> list[dict[str, Any]]:
    if preview_status == "blocked" or not target_objects:
        return []

    elements = []
    element_index = 1
    for task in execution_package.get("execution_tasks", []):
        for target_object in target_objects:
            elements.append(_preview_element(element_index, task, target_object))
            element_index += 1
    return elements


def _preview_element(element_index: int, task: dict[str, Any], target_object: str) -> dict[str, Any]:
    element_type = _element_type(task)
    target_zone = task.get("target_zone", "unknown_zone")
    return {
        "element_id": f"preview_{element_index:03d}",
        "source_task_id": task.get("task_id", ""),
        "element_type": element_type,
        "target_object": target_object,
        "target_zone": target_zone,
        "reference_frame": _reference_frame(element_type),
        "placement_hint": _placement_hint(element_type, target_zone),
        "visual_style": ELEMENT_VISUAL_STYLES[element_type],
        "visual_guide": _visual_guide(element_type),
        "intent": _element_intent(task, element_type),
        "requires_user_confirmation": True,
    }


def _visual_guide(element_type: str) -> dict[str, Any]:
    guide = {
        "guide_version": "v0_8b",
        "guide_type": VISUAL_GUIDE_TYPES.get(element_type, "text_note"),
        "material_name": VISUAL_GUIDE_MATERIALS.get(element_type, "AI_Preview_Yellow"),
        "preview_only": True,
        "non_destructive": True,
    }
    if element_type == "panel_line_hint":
        guide.update({"line_length_factor": 0.65, "bevel_depth": 0.01})
    elif element_type == "placeholder_volume":
        guide.update({"size_factor": [0.32, 0.12, 0.08], "alpha": 0.35})
    elif element_type == "mounting_point_hint":
        guide.update({"radius_factor": 0.08, "alpha": 0.45})
    elif element_type == "risk_marker":
        guide.update({"radius_factor": 0.1, "alpha": 0.55})
    elif element_type == "surface_detail_hint":
        guide.update({"radius_factor": 0.08, "alpha": 0.35})
    elif element_type == "manual_review_note":
        guide.update({"text_size": 0.18})
    return guide


def _element_type(task: dict[str, Any]) -> str:
    task_type = task.get("task_type", "manual_review")
    target_zone = task.get("target_zone", "")
    instruction = task.get("instruction", "")
    if task_type == "place_placeholder" and any(token in f"{target_zone}{instruction}" for token in ["安装", "mount"]):
        return "mounting_point_hint"
    return TASK_ELEMENT_TYPES.get(task_type, "manual_review_note")


def _reference_frame(element_type: str) -> str:
    if element_type in {"placeholder_volume", "mounting_point_hint"}:
        return "object_bounds"
    if element_type == "manual_review_note":
        return "manual_anchor"
    if element_type == "risk_marker":
        return "object_bounds"
    return "object_bounds"


def _placement_hint(element_type: str, target_zone: str) -> dict[str, Any]:
    placement_hint = {
        "target_zone": target_zone,
        "normalized_position": [0.0, 0.0, 0.5],
        "manual_adjustment_required": True,
    }
    if element_type in {"panel_line_hint", "surface_detail_hint"}:
        placement_hint["axis"] = "x"
    if element_type in {"placeholder_volume", "mounting_point_hint"}:
        placement_hint["axis"] = "z"
        placement_hint["normalized_size"] = [0.2, 0.2, 0.2]
    return placement_hint


def _element_intent(task: dict[str, Any], element_type: str) -> str:
    instruction = task.get("instruction", "Review this preview manually.")
    return f"{_element_type_label(element_type)}：{instruction}"


def _element_type_label(element_type: str) -> str:
    labels = {
        "panel_line_hint": "分件线预览",
        "surface_detail_hint": "表面细节预览",
        "placeholder_volume": "占位体预览",
        "mounting_point_hint": "安装点预览",
        "risk_marker": "风险区域预览",
        "manual_review_note": "人工复核注释",
        "symmetry_reference": "对称参考预览",
    }
    return labels.get(element_type, "预览提示")


def _preview_mode(preview_status: str, preview_elements: list[dict[str, Any]]) -> str:
    if preview_status == "blocked":
        return "blocked"
    element_types = {element.get("element_type") for element in preview_elements}
    if element_types & {"placeholder_volume", "mounting_point_hint"}:
        return "bounding_box_overlay"
    if element_types and element_types <= {"risk_marker"}:
        return "risk_marker_only"
    return "annotation_overlay"


def _required_confirmations(
    execution_package: dict[str, Any],
    execution_package_review: dict[str, Any],
    preview_status: str,
    candidate_bindings: list[dict[str, Any]],
) -> list[str]:
    confirmations = list(execution_package.get("user_checkpoints", []))
    for blocker in execution_package_review.get("remaining_blockers", []):
        confirmation = CONFIRMATION_BY_BLOCKER.get(blocker)
        if confirmation:
            confirmations.append(confirmation)
    if preview_status == "needs_user_confirmation":
        candidate_names = "、".join(binding.get("object_name", "候选对象") for binding in candidate_bindings)
        confirmations.append(f"确认候选绑定对象是否可以作为预览目标：{candidate_names}。")
    if preview_status == "blocked":
        confirmations.append("补充可信绑定对象后才能生成局部几何预览。")
    return _merge_unique(confirmations)


def _preview_summary(
    target_part: str,
    preview_status: str,
    target_objects: list[str],
    blocked_by: list[str],
) -> str:
    if preview_status == "blocked":
        return f"{target_part} 缺少可信绑定对象，V0.6 不能生成预览对象。"
    object_text = "、".join(target_objects)
    if preview_status == "needs_user_confirmation":
        return f"{target_part} 只有候选绑定对象 {object_text}，可生成需确认的预览草案。"
    blocker_text = "、".join(blocked_by) if blocked_by else "无剩余阻塞项"
    return f"已为 {target_part} 的绑定对象 {object_text} 生成 preview_only 预览计划；仍保留：{blocker_text}。"


def _merge_unique(items: list[str]) -> list[str]:
    merged = []
    for item in items:
        if item and item not in merged:
            merged.append(item)
    return merged
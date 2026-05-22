"""Presentation formatting for operation blueprints."""

from typing import Any


DETAIL_TEXT = {
    "panel_lines": "面板线",
    "parting_lines": "分件线",
    "armor_layers": "装甲分层",
    "vents": "散热口",
    "thrusters": "喷口/推进器",
    "pipes": "管线",
    "hydraulic_rods": "液压杆",
    "sensors": "传感器",
    "weapon_mounts": "武器挂点",
    "surface_damage": "战损",
    "weathering": "旧化效果",
}

OPERATION_TEXT = {
    "add_panel_lines": "添加",
    "add_parting_lines": "添加",
    "add_armor_layers": "增加",
    "add_vents": "添加",
    "add_thrusters": "添加",
    "add_pipes": "添加",
    "add_hydraulic_rods": "添加",
    "add_sensors": "添加",
    "add_weapon_mounts": "添加",
    "add_surface_damage": "添加",
    "refine_surface": "细化",
}


STYLE_TEXT = {
    "default_mecha": "标准机甲",
    "sharp_mechanical": "锐利机械",
    "heavy_armor": "厚重装甲",
    "military_realistic": "军武写实",
    "clean_anime": "干净动画风",
    "high_mobility": "高机动",
    "exposed_inner_frame": "内构外露",
}

DENSITY_TEXT = {
    "low": "少量",
    "medium": "中等密度",
    "high": "高密度",
}

SYMMETRY_TEXT = {
    "single_target": "",
    "left_right_mirror": "，保持左右镜像",
    "centerline_symmetry": "，保持中线对称",
    "group_sync": "，保持成组一致",
}


def format_blueprint(plan: dict[str, Any]) -> dict[str, Any]:
    """Return a plan copy with normalized user-facing text fields."""
    formatted_plan = dict(plan)
    formatted_plan["designer_brief"] = _build_designer_brief(formatted_plan)
    formatted_plan["user_message"] = _build_user_message(formatted_plan)
    return formatted_plan


def _build_designer_brief(plan: dict[str, Any]) -> str:
    target_part = plan.get("target_part", "unknown_part")
    operation = plan.get("operation", "")
    detail_type = plan.get("detail_type", "")
    style = plan.get("style", "default_mecha")
    density = plan.get("density", "medium")
    symmetry = plan.get("symmetry", "single_target")
    scale = plan.get("scale", "unknown")

    operation_text = OPERATION_TEXT.get(operation, "添加")
    detail_text = DETAIL_TEXT.get(detail_type, detail_type or "细节")
    style_text = STYLE_TEXT.get(style, style or "标准机甲")
    density_text = DENSITY_TEXT.get(density, density or "中等密度")
    symmetry_text = SYMMETRY_TEXT.get(symmetry, "")
    scale_text = "" if scale == "unknown" else f"，按 {scale} 比例控制细节"
    restraint_text = "，保持克制处理" if density == "low" else ""
    risk_text = _risk_summary(plan)

    return (
        f"建议在 {target_part} 上{operation_text}{density_text}{style_text}{detail_text}"
        f"{symmetry_text}{scale_text}{restraint_text}{risk_text}。"
    )


def _build_user_message(plan: dict[str, Any]) -> str:
    target_part = plan.get("target_part", "目标部件")
    operation = plan.get("operation", "")
    detail_type = plan.get("detail_type", "")
    density = plan.get("density", "medium")
    risk_count = len(plan.get("risk_notes", []))

    operation_text = OPERATION_TEXT.get(operation, "添加")
    detail_text = DETAIL_TEXT.get(detail_type, detail_type or "细节")
    density_text = DENSITY_TEXT.get(density, density or "中等密度")
    risk_text = f"，包含 {risk_count} 条风险提示" if risk_count else "，未发现明显抽象风险"
    return f"已生成 {target_part} 操作蓝图：{operation_text}{density_text}{detail_text}{risk_text}。"


def _risk_summary(plan: dict[str, Any]) -> str:
    risk_notes = plan.get("risk_notes", [])
    if not risk_notes:
        return ""
    return f"，需注意 {risk_notes[0].rstrip('。')}"
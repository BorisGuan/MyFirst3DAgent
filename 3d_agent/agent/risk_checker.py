"""Conservative manufacturability risk checks for operation blueprints.

The checker does not inspect real mesh data. It only adds conservative notes
based on abstract target part, detail type, density, and scale.
"""

from typing import Any


SMALL_PARTS = {"antenna", "camera_sensor"}
JOINT_RELATED_PARTS = {
    "waist",
    "arm",
    "left_arm",
    "right_arm",
    "hand",
    "leg",
    "left_leg",
    "right_leg",
    "knee_armor",
    "foot",
}
LINE_DETAIL_TYPES = {"panel_lines", "parting_lines"}
PROTRUDING_DETAIL_TYPES = {
    "pipes",
    "hydraulic_rods",
    "thrusters",
    "sensors",
    "weapon_mounts",
}


def evaluate_risks(plan: dict[str, Any], model_context: dict[str, Any]) -> dict[str, Any]:
    """Return a copy of the plan with conservative risk notes appended."""
    updated_plan = dict(plan)
    existing_notes = list(updated_plan.get("risk_notes", []))
    generated_notes = _generate_risk_notes(updated_plan, model_context)
    updated_plan["risk_notes"] = _merge_unique_notes(existing_notes, generated_notes)
    return updated_plan


def _generate_risk_notes(plan: dict[str, Any], model_context: dict[str, Any]) -> list[str]:
    target_part = plan.get("target_part", "")
    detail_type = plan.get("detail_type", "")
    density = plan.get("density", "medium")
    scale = plan.get("scale", "unknown")
    category = _part_category(target_part, model_context)

    notes: list[str] = []

    if scale == "1/144" and detail_type in LINE_DETAIL_TYPES:
        notes.append("1/144 比例下刻线或分件线需要控制宽度和间距。")

    if scale == "1/144" and density == "high":
        notes.append("1/144 比例下高密度细节可能降低打印清晰度。")

    if target_part in SMALL_PARTS and not (target_part == "antenna" and density == "high"):
        notes.append("小型细长部件需要避免过度削弱结构强度。")

    if target_part == "antenna" and density == "high":
        notes.append("V 字天线不适合承载高密度表面细节，建议降低密度或只保留主轮廓。")

    if target_part in JOINT_RELATED_PARTS and detail_type in PROTRUDING_DETAIL_TYPES - {"pipes", "hydraulic_rods"}:
        notes.append("突出细节需要避开关节活动范围，避免影响姿态或装配。")

    if detail_type in {"pipes", "hydraulic_rods"}:
        notes.append("管线和液压杆应预留连接端点，避免悬空或穿过装甲边界。")

    if detail_type == "thrusters" and target_part not in {"backpack", "booster", "thruster", "leg", "foot"}:
        notes.append("喷口细节需要确认推进方向和安装空间是否合理。")

    if detail_type == "weapon_mounts" and category not in {"equipment", "weapon", "weapon_accessory", "armor"}:
        notes.append("武器挂点需要确认承力位置和连接面是否合理。")

    if detail_type == "surface_damage" and target_part in SMALL_PARTS:
        notes.append("小型部件上的战损缺口容易削弱结构，建议只做浅表痕迹。")

    return notes


def _part_category(target_part: str, model_context: dict[str, Any]) -> str:
    for part in model_context.get("model", {}).get("parts", []):
        if part.get("name") == target_part:
            return part.get("category", "part")
    return "part"


def _merge_unique_notes(existing_notes: list[str], generated_notes: list[str]) -> list[str]:
    merged: list[str] = []
    for note in [*existing_notes, *generated_notes]:
        if note and note not in merged:
            merged.append(note)
    return merged
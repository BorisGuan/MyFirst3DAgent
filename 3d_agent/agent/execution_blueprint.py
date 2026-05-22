"""Rule-based Execution Blueprint conversion for V0.3.

This module converts a validated OperationPlan V2 into an execution-oriented
blueprint. It does not call an LLM, execute Blender, inspect mesh data, or
modify the main V0.2 agent flow.
"""

from typing import Any


OPERATION_TEMPLATES: dict[str, dict[str, Any]] = {
    "add_panel_lines": {
        "tool_family": "surface_detailing",
        "recommended_method": "engraved_line_layout",
        "automation_level": "semi_automatable",
        "difficulty": "medium",
        "v0_4_candidate": True,
        "blocked_by": ["no_real_mesh", "no_surface_boundaries"],
        "template_goal": "lay out readable panel lines on visible armor surfaces",
        "manual_first_step": "先在主要可见装甲面上标记刻线路径。",
        "execution_steps": [
            "识别主要可见装甲面和需要避开的边界。",
            "规划不穿过关键结构的刻线路径。",
            "根据比例控制刻线密度、宽度和间距。",
        ],
        "mitigation_steps": ["先降低线条密度，再确认比例下的可读性。"],
    },
    "add_parting_lines": {
        "tool_family": "surface_detailing",
        "recommended_method": "parting_line_planning",
        "automation_level": "semi_automatable",
        "difficulty": "medium",
        "v0_4_candidate": True,
        "blocked_by": ["no_real_mesh", "no_surface_boundaries"],
        "template_goal": "plan printable parting lines on armor plates",
        "manual_first_step": "先确认分件线是否符合装甲板块逻辑。",
        "execution_steps": [
            "识别装甲板块的主要轮廓和可见边。",
            "标记不破坏主体轮廓的分件线路径。",
            "按比例控制分件线宽度和相邻间距。",
        ],
        "mitigation_steps": ["先在宽阔装甲面试画主分件线，再补次级线条。"],
    },
    "add_armor_layers": {
        "tool_family": "armor_composition",
        "recommended_method": "layered_plate_blockout",
        "automation_level": "blocked_until_mesh",
        "difficulty": "high",
        "v0_4_candidate": False,
        "blocked_by": ["no_real_mesh", "no_surface_boundaries", "no_thickness_data"],
        "template_goal": "block out layered armor relationships before geometric execution",
        "manual_first_step": "先确定主装甲层和副装甲层的覆盖关系。",
        "execution_steps": [
            "划分主装甲面和附加装甲片区域。",
            "确认叠甲不会遮挡关节或连接口。",
            "根据比例控制装甲厚度和突出程度。",
        ],
        "mitigation_steps": ["先用浅层轮廓标记替代厚重几何叠加。"],
    },
    "add_vents": {
        "tool_family": "armor_composition",
        "recommended_method": "recessed_vent_layout",
        "automation_level": "semi_automatable",
        "difficulty": "medium",
        "v0_4_candidate": True,
        "blocked_by": ["no_real_mesh", "no_surface_boundaries", "no_thickness_data"],
        "template_goal": "place recessed vents on suitable flat or protected armor areas",
        "manual_first_step": "先选择不会削弱主承力区域的位置。",
        "execution_steps": [
            "确认散热口所在面有足够空间。",
            "确定散热口方向和排列密度。",
            "按比例避免过细开槽。",
        ],
        "mitigation_steps": ["优先使用浅浮雕或视觉标记，避免深开槽。"],
    },
    "add_thrusters": {
        "tool_family": "propulsion_detailing",
        "recommended_method": "thruster_component_placement",
        "automation_level": "blocked_until_mesh",
        "difficulty": "high",
        "v0_4_candidate": False,
        "blocked_by": ["no_real_mesh", "no_mounting_surface", "no_part_connection_points"],
        "template_goal": "prepare logical thruster placement and direction before component modeling",
        "manual_first_step": "先确认喷口方向和安装空间是否符合机体结构逻辑。",
        "execution_steps": [
            "确认喷口朝向和推进用途。",
            "选择背包、腿部或设备块上的安装区域。",
            "保留连接结构和周边维护空间。",
        ],
        "mitigation_steps": ["先放置低细节占位喷口，再确认比例和安装方向。"],
    },
    "add_pipes": {
        "tool_family": "mechanical_attachment",
        "recommended_method": "curve_pipe_routing",
        "automation_level": "semi_automatable",
        "difficulty": "medium",
        "v0_4_candidate": True,
        "blocked_by": ["no_real_mesh", "no_part_connection_points", "no_joint_range_data"],
        "template_goal": "route pipes between plausible mechanical connection points",
        "manual_first_step": "先标记管线的起点和终点。",
        "execution_steps": [
            "选择管线连接端点。",
            "规划避开关节和装甲边界的路径。",
            "按比例控制管径和弯曲半径。",
        ],
        "mitigation_steps": ["先用单条主路径验证避障，再增加次级管线。"],
    },
    "add_hydraulic_rods": {
        "tool_family": "mechanical_attachment",
        "recommended_method": "piston_pair_layout",
        "automation_level": "semi_automatable",
        "difficulty": "medium",
        "v0_4_candidate": True,
        "blocked_by": ["no_real_mesh", "no_part_connection_points", "no_joint_range_data"],
        "template_goal": "place paired piston rods around plausible moving structures",
        "manual_first_step": "先确认液压杆的上下连接端点和伸缩方向。",
        "execution_steps": [
            "确认关节或机械连接区的运动方向。",
            "标记液压杆两端连接点。",
            "避免液压杆穿过活动范围。",
        ],
        "mitigation_steps": ["先保留更大的关节活动间隙，再调整液压杆位置。"],
    },
    "add_sensors": {
        "tool_family": "sensor_detailing",
        "recommended_method": "sensor_module_placement",
        "automation_level": "automation_candidate",
        "difficulty": "low",
        "v0_4_candidate": True,
        "blocked_by": ["no_real_mesh"],
        "template_goal": "place sensor modules with clear orientation and visual purpose",
        "manual_first_step": "先确认传感器朝向和观察用途。",
        "execution_steps": [
            "选择可见且朝向合理的位置。",
            "确定传感器尺寸和外框形状。",
            "避免传感器遮挡已有头部或装甲特征。",
        ],
        "mitigation_steps": ["优先使用浅浮雕外框，避免小件过薄。"],
    },
    "add_weapon_mounts": {
        "tool_family": "mechanical_attachment",
        "recommended_method": "hardpoint_mount_layout",
        "automation_level": "blocked_until_mesh",
        "difficulty": "high",
        "v0_4_candidate": False,
        "blocked_by": ["no_real_mesh", "no_mounting_surface", "no_part_connection_points"],
        "template_goal": "plan hardpoints on plausible load-bearing surfaces",
        "manual_first_step": "先确认挂点是否位于合理承力结构上。",
        "execution_steps": [
            "选择承力面或设备挂载面。",
            "确认挂点不会影响姿态或装配。",
            "预留连接件和武器外形空间。",
        ],
        "mitigation_steps": ["先以占位接口标记承力位置，不直接生成挂架。"],
    },
    "add_surface_damage": {
        "tool_family": "damage_weathering",
        "recommended_method": "shallow_damage_marking",
        "automation_level": "manual_guided",
        "difficulty": "high",
        "v0_4_candidate": False,
        "blocked_by": ["no_real_mesh", "no_thickness_data", "no_surface_boundaries"],
        "template_goal": "mark shallow damage or weathering without weakening structure",
        "manual_first_step": "先标记浅表损伤区域，不直接切深缺口。",
        "execution_steps": [
            "选择非承力的表面区域。",
            "控制战损数量和深度。",
            "保持战损风格与整体机体一致。",
        ],
        "mitigation_steps": ["优先使用浅表划痕和掉漆表现，避免深切缺口。"],
    },
    "refine_surface": {
        "tool_family": "surface_detailing",
        "recommended_method": "surface_cleanup_pass",
        "automation_level": "manual_guided",
        "difficulty": "medium",
        "v0_4_candidate": False,
        "blocked_by": ["no_real_mesh", "no_surface_boundaries"],
        "template_goal": "clean up and rebalance existing surface detail language",
        "manual_first_step": "先区分需要保留的结构线和需要弱化的杂线。",
        "execution_steps": [
            "检查已有表面细节的密度和方向。",
            "保留关键结构线，弱化噪声细节。",
            "统一目标部件的视觉语言。",
        ],
        "mitigation_steps": ["先做局部清理示例，再扩展到整个部件。"],
    },
}

WEATHERING_METHOD = "weathering_pass_planning"

ZONE_ROLE_HINTS = {
    "primary_visible_surface": "优先作为主要视觉细节区域，保持结构清晰。",
    "edge_detail_zone": "适合边缘细节，但需要避免削弱轮廓。",
    "joint_sensitive_zone": "需要预留活动范围，暂不直接自动执行。",
    "mounting_zone": "需要确认连接面和承力逻辑。",
    "damage_zone": "只建议浅表处理，避免破坏结构。",
    "sensor_orientation_zone": "需要确认朝向和可见性。",
    "unknown_zone": "缺少区域语义，建议保守处理该区域。",
}


def create_execution_blueprint(
    operation_plan: dict[str, Any],
    model_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Convert an OperationPlan V2 dict into an Execution Blueprint dict."""
    operation = operation_plan.get("operation")
    if operation not in OPERATION_TEMPLATES:
        raise ValueError(f"Unsupported operation for Execution Blueprint: {operation!r}")

    template = dict(OPERATION_TEMPLATES[operation])
    recommended_method = _recommended_method(operation_plan, template)
    target_part = operation_plan.get("target_part", "unknown_part")
    blocked_by = _merge_unique(template["blocked_by"], _contextual_blockers(operation_plan))
    risk_reasons = _risk_reasons(operation_plan, template)
    risk_level = _risk_level(operation_plan, template, risk_reasons)

    return {
        "source_plan_ref": "operation_plan_v2",
        "target_part": target_part,
        "execution_intent": {
            "tool_family": template["tool_family"],
            "recommended_method": recommended_method,
            "automation_level": template["automation_level"],
            "requires_mesh_access": True,
            "requires_part_boundaries": template["difficulty"] in {"medium", "high"},
        },
        "operation_template": {
            "template_id": f"{template['tool_family']}.{operation}",
            "template_goal": template["template_goal"],
            "manual_first_step": template["manual_first_step"],
            "execution_steps": list(template["execution_steps"]),
        },
        "zone_mapping": _zone_mapping(operation_plan.get("placement_zones", [])),
        "automation_assessment": {
            "difficulty": template["difficulty"],
            "blocked_by": blocked_by,
            "v0_4_candidate": template["v0_4_candidate"],
        },
        "risk_review": {
            "risk_level": risk_level,
            "risk_reasons": risk_reasons,
            "mitigation_steps": _merge_unique(
                template["mitigation_steps"],
                _scale_mitigation_steps(operation_plan),
            ),
        },
        "execution_brief": _execution_brief(operation_plan, template, recommended_method, blocked_by),
    }


def _recommended_method(operation_plan: dict[str, Any], template: dict[str, Any]) -> str:
    if (
        operation_plan.get("operation") == "add_surface_damage"
        and operation_plan.get("detail_type") == "weathering"
    ):
        return WEATHERING_METHOD
    return template["recommended_method"]


def _contextual_blockers(operation_plan: dict[str, Any]) -> list[str]:
    blockers = []
    if operation_plan.get("scale") == "unknown":
        blockers.append("no_scale_parameters")
    if operation_plan.get("detail_type") in {"pipes", "hydraulic_rods"}:
        blockers.append("no_joint_range_data")
    return blockers


def _risk_reasons(operation_plan: dict[str, Any], template: dict[str, Any]) -> list[str]:
    risk_notes = list(operation_plan.get("risk_notes", []))
    if risk_notes:
        return risk_notes
    if template["difficulty"] == "high":
        return ["该操作依赖真实模型表面、厚度或连接关系，当前只能保守规划。"]
    return ["当前未发现明显抽象风险，仍需在真实模型中复核。"]


def _risk_level(
    operation_plan: dict[str, Any],
    template: dict[str, Any],
    risk_reasons: list[str],
) -> str:
    if template["difficulty"] == "high":
        return "high"
    if operation_plan.get("target_part") in {"antenna", "camera_sensor"}:
        return "high"
    if operation_plan.get("scale") == "1/144" or risk_reasons:
        return "medium"
    return "low"


def _scale_mitigation_steps(operation_plan: dict[str, Any]) -> list[str]:
    if operation_plan.get("scale") == "1/144":
        return ["按 1/144 比例先降低细节密度，确认可读性后再补充次级细节。"]
    return []


def _zone_mapping(placement_zones: list[str]) -> list[dict[str, str]]:
    return [
        {
            "input_zone": zone,
            "zone_role": _zone_role(zone),
            "execution_hint": ZONE_ROLE_HINTS[_zone_role(zone)],
        }
        for zone in placement_zones
    ]


def _zone_role(zone: str) -> str:
    if any(token in zone for token in ["joint", "root_connection", "lower_chest_edge"]):
        return "joint_sensitive_zone"
    if any(token in zone for token in ["edge", "outer", "rim", "tip"]):
        return "edge_detail_zone"
    if any(token in zone for token in ["mount", "back", "equipment", "connection"]):
        return "mounting_zone"
    if any(token in zone for token in ["damage", "front_plate"]):
        return "damage_zone"
    if any(token in zone for token in ["sensor", "camera", "fin", "antenna"]):
        return "sensor_orientation_zone"
    if any(token in zone for token in ["plate", "panel", "surface", "hatch"]):
        return "primary_visible_surface"
    return "unknown_zone"


def _execution_brief(
    operation_plan: dict[str, Any],
    template: dict[str, Any],
    recommended_method: str,
    blocked_by: list[str],
) -> str:
    target_part = operation_plan.get("target_part", "目标部件")
    blocker_text = "、".join(blocked_by)
    return (
        f"针对 {target_part}，建议采用 {recommended_method} 执行准备："
        f"{template['manual_first_step']} 当前缺少 {blocker_text}，暂不直接生成真实几何。"
    )


def _merge_unique(first_items: list[str], second_items: list[str]) -> list[str]:
    merged: list[str] = []
    for item in [*first_items, *second_items]:
        if item and item not in merged:
            merged.append(item)
    return merged
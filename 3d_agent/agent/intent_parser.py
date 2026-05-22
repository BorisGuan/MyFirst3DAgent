"""Intent parsing through an LLM or local mock.

The LLM is only used for understanding and decision-making. It receives natural
language plus abstract model metadata, never real 3D geometry.
"""

import json
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import config


PROMPT_PATH = Path(__file__).resolve().parents[1] / "prompts" / "intent_prompt.txt"


def parse_intent(user_input: str, model_context: dict[str, Any]) -> dict[str, Any]:
    """Parse user input into the required JSON intent format."""
    if config.AI_PROVIDER == "copilot_api":
        return _parse_with_copilot_api(user_input, model_context)
    if config.AI_PROVIDER == "openai":
        return _parse_with_openai(user_input, model_context)
    if config.AI_PROVIDER != "mock":
        raise ValueError(f"Unsupported AI_PROVIDER: {config.AI_PROVIDER}")
    return _parse_with_mock(user_input, model_context)


def _parse_with_copilot_api(user_input: str, model_context: dict[str, Any]) -> dict[str, Any]:
    """Call local copilot-api through the OpenAI-compatible chat API."""
    prompt = _build_prompt(user_input, model_context)
    payload = {
        "model": config.COPILOT_API_MODEL,
        "temperature": 0,
        "response_format": {"type": "json_object"},
        "messages": [{"role": "user", "content": prompt}],
    }
    response = _post_json(
        f"{config.COPILOT_API_BASE_URL}/v1/chat/completions",
        payload,
        {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {config.COPILOT_API_AUTH_TOKEN}",
        },
    )
    content = _extract_chat_completion_text(response)
    return json.loads(_strip_json_markdown(content))


def _parse_with_openai(user_input: str, model_context: dict[str, Any]) -> dict[str, Any]:
    """Call OpenAI when explicitly enabled by configuration."""
    if not config.OPENAI_API_KEY:
        raise RuntimeError("USE_OPENAI=true requires OPENAI_API_KEY to be set.")

    try:
        from openai import OpenAI
    except ImportError as exc:
        raise RuntimeError("Install the openai package to enable OpenAI mode.") from exc

    prompt = _build_prompt(user_input, model_context)
    client = OpenAI(api_key=config.OPENAI_API_KEY)
    response = client.chat.completions.create(
        model=config.OPENAI_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        response_format={"type": "json_object"},
    )

    content = response.choices[0].message.content
    if not content:
        raise ValueError("LLM returned empty content.")
    return json.loads(content)


def _build_prompt(user_input: str, model_context: dict[str, Any]) -> str:
    """Render the prompt template with abstract model metadata."""
    template = PROMPT_PATH.read_text(encoding="utf-8")
    return template.format(
        model_context=json.dumps(model_context, ensure_ascii=False, indent=2),
        user_input=user_input,
    )


def _post_json(url: str, payload: dict[str, Any], headers: dict[str, str]) -> dict[str, Any]:
    request = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with urlopen(request, timeout=config.COPILOT_API_TIMEOUT_SECONDS) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"copilot-api request failed: HTTP {exc.code}: {body}") from exc
    except URLError as exc:
        raise RuntimeError(
            "copilot-api is not reachable. Start it with: copilot-api start"
        ) from exc


def _extract_chat_completion_text(response: dict[str, Any]) -> str:
    choices = response.get("choices", [])
    if not choices:
        raise ValueError(f"copilot-api returned no choices: {response}")
    content = choices[0].get("message", {}).get("content", "").strip()
    if not content:
        raise ValueError(f"copilot-api returned no text content: {response}")
    return content


def _strip_json_markdown(content: str) -> str:
    stripped = content.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        stripped = "\n".join(lines).strip()
    return stripped


def _parse_with_mock(user_input: str, model_context: dict[str, Any]) -> dict[str, Any]:
    """Deterministic fallback parser for local testing and demos."""
    lowered_input = user_input.lower()
    target_part = _detect_target_part(lowered_input, model_context)
    operation, detail_type = _detect_operation_and_detail_type(lowered_input)
    style = _detect_style(lowered_input)
    density = _detect_density(lowered_input)
    symmetry = _detect_symmetry(lowered_input)
    scale = _detect_scale(lowered_input)
    placement_zones = _build_placement_zones(target_part, detail_type)
    constraints = _build_constraints(target_part, detail_type, scale)
    steps = _build_steps(target_part, operation, detail_type, style, density, scale)
    risk_notes = _build_initial_risk_notes(target_part, detail_type, density, scale)
    reasoning = _build_reasoning(operation, detail_type, style, density, scale)
    designer_brief = _build_designer_brief(
        target_part,
        operation,
        detail_type,
        style,
        density,
        symmetry,
        scale,
    )

    return {
        "target_part": target_part,
        "operation": operation,
        "detail_type": detail_type,
        "style": style,
        "density": density,
        "symmetry": symmetry,
        "scale": scale,
        "placement_zones": placement_zones,
        "constraints": constraints,
        "steps": steps,
        "risk_notes": risk_notes,
        "reasoning": reasoning,
        "designer_brief": designer_brief,
    }


def _detect_target_part(user_input: str, model_context: dict[str, Any]) -> str:
    parts = model_context["model"]["parts"]
    for part in parts:
        part_name = part["name"]
        aliases = [
            alias
            for alias in [part_name, part.get("display_name", ""), *part.get("aliases", [])]
            if alias
        ]
        if any(alias in user_input for alias in aliases):
            return part_name
    return parts[0]["name"]


def _detect_operation_and_detail_type(user_input: str) -> tuple[str, str]:
    if any(keyword in user_input for keyword in ["分件线", "分割线", "分色线", "parting line", "seam line"]):
        return "add_parting_lines", "parting_lines"
    if any(keyword in user_input for keyword in ["刻线", "面板线", "装甲线", "panel line", "armor line"]):
        return "add_panel_lines", "panel_lines"
    if any(keyword in user_input for keyword in ["散热口", "散热片", "进气口", "排气口", "格栅", "vent"]):
        return "add_vents", "vents"
    if any(keyword in user_input for keyword in ["喷口", "喷嘴", "推进器", "助推器", "vernier", "thruster", "booster"]):
        return "add_thrusters", "thrusters"
    if any(keyword in user_input for keyword in ["液压杆", "液压缸", "活塞", "hydraulic", "piston"]):
        return "add_hydraulic_rods", "hydraulic_rods"
    if any(keyword in user_input for keyword in ["管线", "线缆", "电缆", "软管", "pipe", "cable", "hose"]):
        return "add_pipes", "pipes"
    if any(keyword in user_input for keyword in ["传感器", "摄像头", "监视器", "镜头", "sensor", "camera"]):
        return "add_sensors", "sensors"
    if any(keyword in user_input for keyword in ["武器挂点", "挂点", "接口", "挂架", "weapon mount", "hardpoint"]):
        return "add_weapon_mounts", "weapon_mounts"
    if any(keyword in user_input for keyword in ["战损", "划痕", "刮痕", "缺口", "破损", "damage", "scratches"]):
        return "add_surface_damage", "surface_damage"
    if any(keyword in user_input for keyword in ["旧化", "磨损", "掉漆", "生锈", "weathering", "wear", "rust"]):
        return "add_surface_damage", "weathering"
    if any(keyword in user_input for keyword in ["优化", "精修", "平滑", "调整表面", "refine"]):
        return "refine_surface", "panel_lines"
    if any(keyword in user_input for keyword in ["装甲分层", "装甲层次", "叠甲", "外甲", "机械", "零件", "结构", "greeble"]):
        return "add_armor_layers", "armor_layers"
    return "add_panel_lines", "panel_lines"


def _detect_style(user_input: str) -> str:
    if any(keyword in user_input for keyword in ["锐利", "尖锐", "棱角", "斜切", "硬朗", "sharp", "angular"]):
        return "sharp_mechanical"
    if any(keyword in user_input for keyword in ["厚重", "重甲", "重装", "heavy armor"]):
        return "heavy_armor"
    if any(keyword in user_input for keyword in ["军武", "写实", "军事", "实战", "military", "realistic"]):
        return "military_realistic"
    if any(keyword in user_input for keyword in ["动画风", "干净", "简洁", "清爽", "anime", "clean"]):
        return "clean_anime"
    if any(keyword in user_input for keyword in ["高机动", "高速", "推进", "机动", "high mobility"]):
        return "high_mobility"
    if any(keyword in user_input for keyword in ["内构外露", "露内构", "骨架外露", "inner frame"]):
        return "exposed_inner_frame"
    return "default_mecha"


def _detect_density(user_input: str) -> str:
    if any(keyword in user_input for keyword in ["大量", "很多", "密集", "high"]):
        return "high"
    if any(keyword in user_input for keyword in ["少量", "轻微", "克制", "不要太", "low"]):
        return "low"
    return "medium"


def _detect_symmetry(user_input: str) -> str:
    if any(keyword in user_input for keyword in ["左右", "两侧", "镜像", "左边和右边", "left right", "mirror"]):
        return "left_right_mirror"
    if any(keyword in user_input for keyword in ["中线", "中心对称", "沿中线", "centerline"]):
        return "centerline_symmetry"
    if any(keyword in user_input for keyword in ["全部", "所有", "同样", "统一", "成组", "group", "sync"]):
        return "group_sync"
    return "single_target"


def _detect_scale(user_input: str) -> str:
    if "1/144" in user_input or "hg" in user_input or "rg" in user_input:
        return "1/144"
    if "1/100" in user_input or "mg" in user_input:
        return "1/100"
    if "1/60" in user_input or "pg" in user_input:
        return "1/60"
    if "无比例" in user_input or "non scale" in user_input or "non-scale" in user_input:
        return "non_scale"
    return "unknown"


def _build_placement_zones(target_part: str, detail_type: str) -> list[str]:
    if target_part == "chest_armor":
        return ["upper_chest_plate", "around_cockpit_hatch"]
    if target_part in {"backpack", "booster", "thruster"}:
        return ["rear_equipment_block", "thruster_surrounds"]
    if target_part in {"leg", "left_leg", "right_leg", "knee_armor"}:
        return ["outer_armor_surface", "joint_surrounds"]
    if target_part == "shield":
        return ["front_plate", "outer_edges"]
    if target_part == "antenna":
        return ["main_fin_surface"]
    if detail_type in {"pipes", "hydraulic_rods"}:
        return ["joint_surrounds"]
    return ["primary_visible_surface"]


def _build_constraints(target_part: str, detail_type: str, scale: str) -> list[str]:
    constraints = []
    if scale == "1/144":
        constraints.append("keep_details_printable_at_1_144")
    if target_part in {"waist", "arm", "left_arm", "right_arm", "leg", "left_leg", "right_leg", "knee_armor"}:
        constraints.append("avoid_joint_interference")
    if target_part in {"antenna", "camera_sensor"}:
        constraints.append("avoid_over_thinning_small_parts")
    if detail_type in {"panel_lines", "parting_lines"}:
        constraints.append("keep_line_density_readable")
    return constraints


def _build_steps(
    target_part: str,
    operation: str,
    detail_type: str,
    style: str,
    density: str,
    scale: str,
) -> list[str]:
    detail_text = _detail_text(detail_type)
    style_text = _style_text(style)
    density_text = _density_text(density)
    steps = [
        f"确认 {target_part} 的主要可见面和边界。",
        f"以{style_text}风格添加{density_text}{detail_text}。",
        "保留原有轮廓和关键结构，不穿过关节或连接区域。",
    ]
    if scale == "1/144":
        steps.append("按 1/144 比例控制细节宽度和间距，避免过密。")
    if operation == "refine_surface":
        steps[1] = "清理表面层次，统一已有细节的方向和密度。"
    return steps


def _build_initial_risk_notes(target_part: str, detail_type: str, density: str, scale: str) -> list[str]:
    risk_notes = []
    if scale == "1/144" and detail_type in {"panel_lines", "parting_lines"}:
        risk_notes.append("1/144 比例下刻线或分件线需要控制宽度和间距。")
    if scale == "1/144" and density == "high":
        risk_notes.append("1/144 比例下高密度细节可能降低打印清晰度。")
    if target_part == "antenna":
        risk_notes.append("天线属于细长部件，过多细节可能削弱结构强度。")
    if detail_type in {"pipes", "hydraulic_rods"}:
        risk_notes.append("管线和液压杆需要避开关节活动范围。")
    return risk_notes


def _build_reasoning(
    operation: str,
    detail_type: str,
    style: str,
    density: str,
    scale: str,
) -> str:
    operation_text = _operation_text(operation)
    detail_text = _detail_text(detail_type)
    style_text = _style_text(style)
    density_text = {"low": "少量", "medium": "适量", "high": "大量"}[density]
    scale_text = "" if scale == "unknown" else f"，并考虑 {scale} 比例"
    return f"用户希望{operation_text}{density_text}{style_text}{detail_text}{scale_text}。"


def _build_designer_brief(
    target_part: str,
    operation: str,
    detail_type: str,
    style: str,
    density: str,
    symmetry: str,
    scale: str,
) -> str:
    operation_text = _operation_text(operation)
    detail_text = _detail_text(detail_type)
    style_text = _style_text(style)
    density_text = _density_text(density)
    symmetry_text = _symmetry_text(symmetry)
    scale_text = "" if scale == "unknown" else f"，按 {scale} 比例控制细节"
    restraint_text = "，保持克制处理" if density == "low" else ""
    return f"建议在 {target_part} 上{operation_text}{density_text}{style_text}{detail_text}{symmetry_text}{scale_text}{restraint_text}。"


def _operation_text(operation: str) -> str:
    return {
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
    }[operation]


def _detail_text(detail_type: str) -> str:
    return {
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
    }[detail_type]


def _style_text(style: str) -> str:
    return {
        "default_mecha": "标准机甲",
        "sharp_mechanical": "锐利机械",
        "heavy_armor": "厚重装甲",
        "military_realistic": "军武写实",
        "clean_anime": "干净动画风",
        "high_mobility": "高机动",
        "exposed_inner_frame": "内构外露",
    }[style]


def _density_text(density: str) -> str:
    return {"low": "少量", "medium": "中等密度", "high": "高密度"}[density]


def _symmetry_text(symmetry: str) -> str:
    return {
        "single_target": "",
        "left_right_mirror": "，保持左右镜像",
        "centerline_symmetry": "，保持中线对称",
        "group_sync": "，保持成组一致",
    }[symmetry]

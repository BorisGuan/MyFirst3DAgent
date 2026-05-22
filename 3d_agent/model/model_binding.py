"""Rule-based model binding for V0.5.

This module maps abstract target parts to objects from a normalized Scene
Manifest. It is read-only: it does not inspect mesh geometry, execute Blender,
or modify model files.
"""

import re
from typing import Any


BINDING_VERSION = "v0_5"
REVIEW_VERSION = "v0_5"
BOUND_CONFIDENCE = 0.90
CANDIDATE_CONFIDENCE = 0.60
AMBIGUOUS_CONFIDENCE = 0.30

TARGET_MATCH_RULES = {
    "chest_armor": {
        "name_tokens": ["chestarmor", "chest"],
        "collection_tokens": ["chest", "bodychest"],
        "material_tokens": ["armor"],
    },
    "backpack": {
        "name_tokens": ["backpack"],
        "collection_tokens": ["backpack", "equipmentbackpack"],
        "material_tokens": ["mechanical", "armor"],
    },
    "leg": {
        "name_tokens": ["leg", "leftleg", "rightleg"],
        "collection_tokens": ["leg", "legs", "leftleg", "rightleg"],
        "material_tokens": ["armor", "joint"],
    },
    "shield": {
        "name_tokens": ["shield"],
        "collection_tokens": ["shield", "weaponsshield"],
        "material_tokens": ["armor"],
    },
    "camera_sensor": {
        "name_tokens": ["camerasensor", "camera", "sensor"],
        "collection_tokens": ["sensor", "sensors", "headsensor", "headsensors"],
        "material_tokens": ["sensor", "lens"],
    },
    "thruster": {
        "name_tokens": ["thruster", "vernier"],
        "collection_tokens": ["thruster", "thrusters"],
        "material_tokens": ["thruster", "burnt", "metal"],
    },
}

BLOCKER_RESOLUTIONS = {
    "no_real_mesh": "real_mesh_file",
    "no_scale_parameters": "scale_parameters",
}
GEOMETRY_BLOCKERS = {
    "no_surface_boundaries",
    "no_part_connection_points",
    "no_joint_range_data",
    "no_thickness_data",
    "no_mounting_surface",
}


def create_model_binding_context(
    scene_manifest: dict[str, Any],
    target_part: str,
    execution_package: dict[str, Any] | None = None,
    source_manifest_ref: str = "scene_manifest",
) -> dict[str, Any]:
    """Create a V0.5 Model Binding Context for one abstract target part."""
    if not isinstance(target_part, str) or not target_part.strip():
        raise ValueError("target_part must be a non-empty string.")

    scored_objects = [_score_scene_object(scene_object, target_part) for scene_object in scene_manifest.get("objects", [])]
    bindings = [
        _binding_for_scored_object(scored_object, scene_manifest, target_part, execution_package)
        for scored_object in scored_objects
        if scored_object["score"] >= AMBIGUOUS_CONFIDENCE and scored_object["object"]["object_type"] == "MESH"
    ]
    bound_bindings = [binding for binding in bindings if binding["binding_status"] == "bound"]
    matched_object_names = {binding["object_name"] for binding in bindings}
    unmatched_objects = [
        scored_object["object"]["object_name"]
        for scored_object in scored_objects
        if scored_object["object"]["object_name"] not in matched_object_names
    ]

    return {
        "binding_version": BINDING_VERSION,
        "source_manifest_ref": source_manifest_ref,
        "target_part": target_part,
        "bindings": bindings,
        "unbound_parts": [] if bound_bindings else [target_part],
        "unmatched_objects": unmatched_objects,
        "binding_summary": _binding_summary(target_part, bound_bindings, bindings),
    }


def review_execution_package_with_binding(
    execution_package: dict[str, Any],
    binding_context: dict[str, Any],
) -> dict[str, Any]:
    """Review V0.4 package inputs and blockers against a V0.5 binding context."""
    bound_bindings = [
        binding
        for binding in binding_context.get("bindings", [])
        if binding.get("binding_status") == "bound"
    ]
    candidate_bindings = [
        binding
        for binding in binding_context.get("bindings", [])
        if binding.get("binding_status") in {"candidate", "ambiguous"}
    ]
    resolved_inputs = _merge_unique(
        [resolved_input for binding in bound_bindings for resolved_input in binding.get("resolved_inputs", [])]
    )
    required_inputs = list(execution_package.get("required_inputs", []))
    unresolved_inputs = [required_input for required_input in required_inputs if required_input not in resolved_inputs]
    resolved_blockers, remaining_blockers = _review_blockers(
        execution_package.get("blocked_by", []),
        resolved_inputs,
    )
    review_status = _review_status(
        bound_bindings,
        candidate_bindings,
        unresolved_inputs,
        remaining_blockers,
    )

    return {
        "review_version": REVIEW_VERSION,
        "source_package_ref": "execution_package",
        "source_binding_ref": "model_binding_context",
        "target_part": execution_package.get("target_part", binding_context.get("target_part", "unknown_part")),
        "binding_status": _aggregate_binding_status(bound_bindings, candidate_bindings),
        "bound_objects": [binding["object_name"] for binding in bound_bindings],
        "resolved_inputs": resolved_inputs,
        "unresolved_inputs": unresolved_inputs,
        "resolved_blockers": resolved_blockers,
        "remaining_blockers": remaining_blockers,
        "review_status": review_status,
        "review_notes": _review_notes(review_status, candidate_bindings, remaining_blockers),
        "review_summary": _review_summary(
            execution_package.get("target_part", binding_context.get("target_part", "unknown_part")),
            review_status,
            bound_bindings,
            remaining_blockers,
        ),
    }


def _score_scene_object(scene_object: dict[str, Any], target_part: str) -> dict[str, Any]:
    custom_properties = scene_object.get("custom_properties", {})
    explicit_part_role = custom_properties.get("part_role")
    if explicit_part_role and explicit_part_role != target_part:
        return {"object": scene_object, "score": 0.0, "evidence": []}

    rules = TARGET_MATCH_RULES.get(target_part, _default_rules(target_part))
    score = 0.0
    evidence = []

    if explicit_part_role == target_part:
        score += 0.75
        evidence.append("custom_property:part_role")

    object_name_text = _normalize_text(scene_object.get("object_name", ""))
    matched_name_token = _first_matching_token(object_name_text, rules["name_tokens"])
    if matched_name_token:
        score += 0.45
        evidence.append(f"name:{matched_name_token}")

    collection_text = _normalize_text("/".join(scene_object.get("collection_path", [])))
    matched_collection_token = _first_matching_token(collection_text, rules["collection_tokens"])
    if matched_collection_token:
        score += 0.25
        evidence.append(f"collection_path:{'/'.join(scene_object.get('collection_path', []))}")

    material_text = _normalize_text("/".join(scene_object.get("material_names", [])))
    matched_material_token = _first_matching_token(material_text, rules["material_tokens"])
    if matched_material_token:
        score += 0.05
        evidence.append(f"material:{matched_material_token}")

    return {"object": scene_object, "score": min(score, 1.0), "evidence": evidence}


def _binding_for_scored_object(
    scored_object: dict[str, Any],
    scene_manifest: dict[str, Any],
    target_part: str,
    execution_package: dict[str, Any] | None,
) -> dict[str, Any]:
    scene_object = scored_object["object"]
    binding_status = _binding_status(scored_object["score"])
    resolved_inputs = _resolved_inputs(binding_status, scene_manifest, execution_package)
    return {
        "target_part": target_part,
        "object_name": scene_object["object_name"],
        "binding_status": binding_status,
        "confidence": round(scored_object["score"], 2),
        "evidence": scored_object["evidence"],
        "object_summary": {
            "object_type": scene_object["object_type"],
            "dimensions": scene_object.get("dimensions", []),
            "vertex_count": scene_object.get("vertex_count", 0),
        },
        "resolved_inputs": resolved_inputs,
        "remaining_blockers": _remaining_blockers(resolved_inputs, execution_package),
    }


def _binding_status(score: float) -> str:
    if score >= BOUND_CONFIDENCE:
        return "bound"
    if score >= CANDIDATE_CONFIDENCE:
        return "candidate"
    if score >= AMBIGUOUS_CONFIDENCE:
        return "ambiguous"
    return "unbound"


def _resolved_inputs(
    binding_status: str,
    scene_manifest: dict[str, Any],
    execution_package: dict[str, Any] | None,
) -> list[str]:
    if binding_status != "bound":
        return []

    resolved_inputs = ["real_mesh_file", "target_part_object"]
    if scene_manifest.get("unit_system") != "unknown":
        resolved_inputs.append("scale_parameters")
    if execution_package:
        required_inputs = execution_package.get("required_inputs", [])
        return [item for item in resolved_inputs if item in required_inputs or item == "target_part_object"]
    return resolved_inputs


def _remaining_blockers(
    resolved_inputs: list[str],
    execution_package: dict[str, Any] | None,
) -> list[str]:
    if not execution_package:
        return []

    remaining_blockers = []
    for blocker in execution_package.get("blocked_by", []):
        resolved_input = BLOCKER_RESOLUTIONS.get(blocker)
        if blocker in GEOMETRY_BLOCKERS or resolved_input not in resolved_inputs:
            remaining_blockers.append(blocker)
    return remaining_blockers


def _review_blockers(blocked_by: list[str], resolved_inputs: list[str]) -> tuple[list[str], list[str]]:
    resolved_blockers = []
    remaining_blockers = []
    for blocker in blocked_by:
        resolved_input = BLOCKER_RESOLUTIONS.get(blocker)
        if blocker not in GEOMETRY_BLOCKERS and resolved_input in resolved_inputs:
            resolved_blockers.append(blocker)
        else:
            remaining_blockers.append(blocker)
    return resolved_blockers, remaining_blockers


def _review_status(
    bound_bindings: list[dict[str, Any]],
    candidate_bindings: list[dict[str, Any]],
    unresolved_inputs: list[str],
    remaining_blockers: list[str],
) -> str:
    if not bound_bindings and candidate_bindings:
        return "needs_user_confirmation"
    if not bound_bindings:
        return "blocked"
    if unresolved_inputs or remaining_blockers:
        return "partially_resolved"
    return "resolved"


def _aggregate_binding_status(
    bound_bindings: list[dict[str, Any]],
    candidate_bindings: list[dict[str, Any]],
) -> str:
    if bound_bindings:
        return "bound"
    if candidate_bindings:
        return "candidate"
    return "unbound"


def _review_notes(
    review_status: str,
    candidate_bindings: list[dict[str, Any]],
    remaining_blockers: list[str],
) -> list[str]:
    notes = []
    if review_status == "needs_user_confirmation":
        candidate_names = "、".join(binding["object_name"] for binding in candidate_bindings)
        notes.append(f"候选对象需要用户确认后才能作为执行目标：{candidate_names}。")
    if review_status == "blocked":
        notes.append("未找到可信绑定对象，不能解除执行包输入。")
    if remaining_blockers:
        notes.append("仍需保留阻塞项：" + "、".join(remaining_blockers) + "。")
    if not notes:
        notes.append("当前执行包输入已由绑定上下文满足，仍需用户在建模软件内确认。")
    return notes


def _review_summary(
    target_part: str,
    review_status: str,
    bound_bindings: list[dict[str, Any]],
    remaining_blockers: list[str],
) -> str:
    if review_status == "blocked":
        return f"未找到可信绑定对象：{target_part} 的 V0.4 执行包仍被阻塞。"
    if review_status == "needs_user_confirmation":
        return f"{target_part} 只有候选绑定，需要用户确认后才能复核执行包输入。"
    object_names = "、".join(binding["object_name"] for binding in bound_bindings)
    if remaining_blockers:
        return f"已将 {target_part} 绑定到 {object_names}，对象级输入已部分解决，仍保留 {len(remaining_blockers)} 个阻塞项。"
    return f"已将 {target_part} 绑定到 {object_names}，当前执行包阻塞项已解除。"


def _binding_summary(target_part: str, bound_bindings: list[dict[str, Any]], bindings: list[dict[str, Any]]) -> str:
    if bound_bindings:
        object_names = "、".join(binding["object_name"] for binding in bound_bindings)
        return f"已将 {target_part} 绑定到 {object_names}，但仍需检查剩余几何级阻塞项。"
    if bindings:
        return f"{target_part} 只有候选或模糊匹配，需要用户确认后才能作为执行目标。"
    return f"未能在 Scene Manifest 中为 {target_part} 找到可信对象。"


def _default_rules(target_part: str) -> dict[str, list[str]]:
    normalized_target = _normalize_text(target_part)
    return {
        "name_tokens": [normalized_target],
        "collection_tokens": [normalized_target],
        "material_tokens": [],
    }


def _normalize_text(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def _first_matching_token(text: str, tokens: list[str]) -> str:
    for token in tokens:
        normalized_token = _normalize_text(token)
        if normalized_token and normalized_token in text:
            return token
    return ""


def _merge_unique(items: list[str]) -> list[str]:
    merged: list[str] = []
    for item in items:
        if item and item not in merged:
            merged.append(item)
    return merged
"""V0.8 mecha design rule review.

The rule engine evaluates a planned edit before any real geometry authoring. It
does not execute Blender or modify model data.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


RULE_PACK_PATH = Path(__file__).resolve().parents[1] / "context" / "mecha_design_rules.json"


def load_mecha_design_rules(path: str | Path = RULE_PACK_PATH) -> dict[str, Any]:
    """Load the machine-readable V0.8 design rule pack."""
    return json.loads(Path(path).read_text(encoding="utf-8"))


def review_mecha_design_rules(
    operation_plan: dict[str, Any],
    execution_package: dict[str, Any],
    user_input: str = "",
    rule_pack: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Review a planned mecha edit against part, scale, symmetry, and safety rules."""
    rules = rule_pack or load_mecha_design_rules()
    operation = operation_plan.get("operation", "unknown_operation")
    target_part = execution_package.get("target_part", operation_plan.get("target_part", "unknown_part"))
    canonical_part = _canonical_part(target_part)
    requested_detail_type = _requested_detail_type(operation_plan, rules, operation)
    part_rule = rules.get("part_rules", {}).get(canonical_part, {})
    matched_rules: list[str] = []
    warnings: list[str] = []
    blockers: list[str] = []
    required_confirmations: list[str] = []
    recommended_detail_types = list(part_rule.get("recommended_detail_types", []))
    blocked_detail_types = list(part_rule.get("blocked_detail_types", []))
    geometry_constraints = list(rules.get("default_geometry_constraints", []))
    geometry_constraints.extend(part_rule.get("geometry_constraints", []))

    if part_rule:
        matched_rules.append(f"part_rules.{canonical_part}")
        warnings.extend(part_rule.get("warnings", []))

    if requested_detail_type:
        matched_rules.append(f"operation_detail_types.{operation}")
        if requested_detail_type in blocked_detail_types or f"large_{requested_detail_type}" in blocked_detail_types:
            blockers.append(f"detail_type_not_recommended_for_{canonical_part}")
            required_confirmations.append(
                f"Confirm whether {requested_detail_type} is really intended for {canonical_part}."
            )
        elif requested_detail_type not in recommended_detail_types and recommended_detail_types:
            warnings.append(f"{requested_detail_type} is not a primary recommended detail type for {canonical_part}.")

    scale = operation_plan.get("scale", "unknown")
    density = operation_plan.get("density", "medium")
    scale_rule = rules.get("scale_rules", {}).get(scale)
    if scale_rule:
        matched_rules.append(f"scale_rules.{scale}")
        geometry_constraints.extend(scale_rule.get("geometry_constraints", []))
        if density == scale_rule.get("density_warning_threshold"):
            warnings.extend(scale_rule.get("warnings", []))
            required_confirmations.append(f"Confirm that {scale} detail density remains printable and readable.")

    symmetry_rule = rules.get("symmetry_rules", {}).get(canonical_part)
    if symmetry_rule:
        matched_rules.append(f"symmetry_rules.{canonical_part}")
        requested_symmetry = operation_plan.get("symmetry", "single_target")
        if requested_symmetry == "single_target":
            warnings.append(symmetry_rule.get("warning", "Review symmetry before geometry changes."))
            required_confirmations.append(
                f"Confirm whether this {canonical_part} edit should use {symmetry_rule.get('recommended_symmetry', 'mirror')} symmetry."
            )

    for intent_id, intent_rule in rules.get("blocked_user_intents", {}).items():
        if _contains_any(user_input, intent_rule.get("keywords", [])):
            matched_rules.append(f"blocked_user_intents.{intent_id}")
            blockers.append(intent_id)
            warnings.append(intent_rule.get("warning", intent_id))

    status = _status(blockers, warnings)
    return {
        "review_version": "v0_8",
        "source_package_ref": "execution_package",
        "rule_pack_version": rules.get("rule_pack_version", "unknown"),
        "status": status,
        "target_part": target_part,
        "canonical_part": canonical_part,
        "operation": operation,
        "requested_detail_type": requested_detail_type,
        "recommended_detail_types": recommended_detail_types,
        "blocked_detail_types": blocked_detail_types,
        "matched_rules": _merge_unique(matched_rules),
        "warnings": _merge_unique(warnings),
        "blockers": _merge_unique(blockers),
        "geometry_constraints": _merge_unique(geometry_constraints),
        "requires_user_confirmation": _merge_unique(required_confirmations),
        "review_summary": _review_summary(status, canonical_part, requested_detail_type, blockers, warnings),
    }


def _canonical_part(target_part: str) -> str:
    value = target_part.lower()
    if "chest" in value or "胸" in value:
        return "chest_armor"
    if "backpack" in value or "背包" in value:
        return "backpack"
    if "leg" in value or "腿" in value:
        return "leg_armor"
    if "shield" in value or "盾" in value:
        return "shield"
    if "head" in value or "头" in value:
        return "head"
    return value or "unknown_part"


def _requested_detail_type(operation_plan: dict[str, Any], rules: dict[str, Any], operation: str) -> str:
    detail_type = operation_plan.get("detail_type")
    if detail_type:
        return detail_type
    return rules.get("operation_detail_types", {}).get(operation, "")


def _contains_any(value: str, keywords: list[str]) -> bool:
    normalized = value.lower()
    return any(keyword.lower() in normalized for keyword in keywords)


def _status(blockers: list[str], warnings: list[str]) -> str:
    if blockers:
        return "blocked"
    if warnings:
        return "passed_with_warnings"
    return "passed"


def _review_summary(
    status: str,
    canonical_part: str,
    requested_detail_type: str,
    blockers: list[str],
    warnings: list[str],
) -> str:
    detail_text = requested_detail_type or "requested detail"
    if status == "blocked":
        return f"{detail_text} on {canonical_part} is blocked by {len(blockers)} design rule issue(s)."
    if status == "passed_with_warnings":
        return f"{detail_text} on {canonical_part} can proceed with {len(warnings)} design warning(s)."
    return f"{detail_text} on {canonical_part} passed the V0.8 mecha design rule review."


def _merge_unique(items: list[str]) -> list[str]:
    merged: list[str] = []
    for item in items:
        if item and item not in merged:
            merged.append(item)
    return merged
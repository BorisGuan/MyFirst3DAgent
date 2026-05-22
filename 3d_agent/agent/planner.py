"""Plan normalization and validation.

The planner keeps the final output predictable. It does not execute tools or
modify any 3D model; it only validates a structured operation plan.
"""

from typing import Any

from model.schemas import (
    ALLOWED_ACTIONS,
    ALLOWED_DENSITIES,
    ALLOWED_DETAIL_TYPES,
    ALLOWED_OPERATIONS,
    ALLOWED_SCALES,
    ALLOWED_STYLES,
    ALLOWED_SYMMETRIES,
    OperationPlan,
)


REQUIRED_FIELDS = {
    "target_part",
    "operation",
    "detail_type",
    "style",
    "density",
    "symmetry",
    "scale",
    "placement_zones",
    "constraints",
    "steps",
    "risk_notes",
    "reasoning",
    "designer_brief",
}
LIST_FIELDS = {"placement_zones", "constraints", "steps", "risk_notes"}

LEGACY_ACTION_TO_OPERATION = {
    "add_detail": "add_panel_lines",
    "enhance_detail": "add_armor_layers",
    "refine_surface": "refine_surface",
}
LEGACY_DETAIL_TYPE_MAP = {
    "mechanical_greeble": "armor_layers",
    "surface_scratches": "surface_damage",
}


def create_plan(intent: dict[str, Any], model_context: dict[str, Any]) -> dict[str, Any]:
    """Validate parsed intent and return the final JSON-compatible plan."""
    intent = _normalize_intent(intent)
    missing_fields = REQUIRED_FIELDS - set(intent)
    if missing_fields:
        raise ValueError(f"Intent is missing required fields: {sorted(missing_fields)}")

    valid_parts = {part["name"] for part in model_context["model"]["parts"]}
    if intent["target_part"] not in valid_parts:
        raise ValueError(
            f"target_part must be one of {sorted(valid_parts)}, got {intent['target_part']!r}"
        )

    if intent["operation"] not in ALLOWED_OPERATIONS:
        raise ValueError(f"operation must be one of {sorted(ALLOWED_OPERATIONS)}")

    if intent["detail_type"] not in ALLOWED_DETAIL_TYPES:
        raise ValueError(f"detail_type must be one of {sorted(ALLOWED_DETAIL_TYPES)}")

    if intent["style"] not in ALLOWED_STYLES:
        raise ValueError(f"style must be one of {sorted(ALLOWED_STYLES)}")

    if intent["density"] not in ALLOWED_DENSITIES:
        raise ValueError(f"density must be one of {sorted(ALLOWED_DENSITIES)}")

    if intent["symmetry"] not in ALLOWED_SYMMETRIES:
        raise ValueError(f"symmetry must be one of {sorted(ALLOWED_SYMMETRIES)}")

    if intent["scale"] not in ALLOWED_SCALES:
        raise ValueError(f"scale must be one of {sorted(ALLOWED_SCALES)}")

    for field in LIST_FIELDS:
        if not isinstance(intent[field], list):
            raise ValueError(f"{field} must be a list of strings")
        if not all(isinstance(item, str) for item in intent[field]):
            raise ValueError(f"{field} must be a list of strings")

    plan = OperationPlan(
        target_part=intent["target_part"],
        operation=intent["operation"],
        detail_type=intent["detail_type"],
        style=intent["style"],
        density=intent["density"],
        symmetry=intent["symmetry"],
        scale=intent["scale"],
        placement_zones=intent["placement_zones"],
        constraints=intent["constraints"],
        steps=intent["steps"],
        risk_notes=intent["risk_notes"],
        reasoning=intent["reasoning"],
        designer_brief=intent["designer_brief"],
    )
    return plan.to_dict()


def _normalize_intent(intent: dict[str, Any]) -> dict[str, Any]:
    """Normalize legacy V0.1 intent into the V0.2 blueprint contract."""
    normalized = dict(intent)

    if "operation" not in normalized and "action" in normalized:
        action = normalized["action"]
        if action not in ALLOWED_ACTIONS:
            raise ValueError(f"action must be one of {sorted(ALLOWED_ACTIONS)}")
        normalized["operation"] = LEGACY_ACTION_TO_OPERATION[action]

    if normalized.get("detail_type") in LEGACY_DETAIL_TYPE_MAP:
        normalized["detail_type"] = LEGACY_DETAIL_TYPE_MAP[normalized["detail_type"]]

    normalized.setdefault("style", "default_mecha")
    normalized.setdefault("symmetry", "single_target")
    normalized.setdefault("scale", "unknown")
    normalized.setdefault("placement_zones", [])
    normalized.setdefault("constraints", [])
    normalized.setdefault("steps", [])
    normalized.setdefault("risk_notes", [])
    normalized.setdefault("reasoning", "")
    normalized.setdefault("designer_brief", "")

    return normalized

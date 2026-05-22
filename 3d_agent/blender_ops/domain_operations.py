"""Domain Operation Layer for interface operations.

This module exposes domain verbs and delegates geometry work to the Core
Geometry API. Upstream orchestration, persistence, and intent reasoning stay
outside this layer.
"""

from __future__ import annotations

from typing import Any

import core_api as core_geometry_api
from domain import DomainOperationInput, OperationOutcome


EDGE_SOFTEN_MODIFIER_NAME = "AI_PanelLine_Bevel"
DEFAULT_EDGE_SOFTEN_STRENGTH = 0.01
EDGE_SOFTEN_SEGMENTS = 1

_STYLE_WIDTH_MULTIPLIERS = {
    "clean": 0.75,
    "mechanical": 1.0,
    "heavy": 1.5,
}


def edge_soften(
    operation_input: DomainOperationInput,
) -> OperationOutcome:
    """Soften a target object's edges through the Core Geometry API."""
    if operation_input.operation != "edge_soften":
        raise ValueError(f"edge_soften cannot handle operation {operation_input.operation!r}.")

    width = _bevel_width_from_parameters(operation_input.parameters)
    resolved_object = core_geometry_api.require_object(operation_input.target_object)
    modifier = core_geometry_api.add_bevel_modifier(
        resolved_object,
        width=width,
        segments=EDGE_SOFTEN_SEGMENTS,
        modifier_name=EDGE_SOFTEN_MODIFIER_NAME,
    )
    return OperationOutcome(
        operation="edge_soften",
        target_object=operation_input.target_object,
        success=True,
        changed_objects=[operation_input.target_object],
        modifier_info={
            "modifier_name": _modifier_value(modifier, "name", "modifier_name"),
            "modifier_type": _modifier_value(modifier, "type", "modifier_type"),
            "width": width,
            "segments": EDGE_SOFTEN_SEGMENTS,
        },
        mesh_data_applied=False,
        diagnostics=[],
    )


def _bevel_width_from_parameters(parameters: dict[str, Any]) -> float:
    strength = float(parameters.get("strength", DEFAULT_EDGE_SOFTEN_STRENGTH))
    if strength <= 0:
        raise ValueError("strength must be greater than 0.")

    style = parameters.get("style", "mechanical")
    if style not in _STYLE_WIDTH_MULTIPLIERS:
        raise ValueError("style must be one of: clean, heavy, mechanical.")

    return strength * _STYLE_WIDTH_MULTIPLIERS[style]


def _modifier_value(modifier: Any, attribute_name: str, mapping_key: str) -> str:
    if isinstance(modifier, dict):
        return str(modifier.get(mapping_key) or modifier.get(attribute_name) or "")
    return str(getattr(modifier, attribute_name, ""))
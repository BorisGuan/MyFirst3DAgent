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
PANEL_LINE_BEVEL_PREPARE_MODIFIER_NAME = "AI_PanelLine_Prepare"
DEFAULT_PANEL_LINE_WIDTH = 0.006
DEFAULT_PANEL_LINE_SEGMENTS = 1
VENT_SLOT_PREPARE_MODIFIER_NAME = "AI_VentSlot_Prepare"
DEFAULT_VENT_SLOT_WIDTH = 0.004
DEFAULT_VENT_SLOT_SEGMENTS = 1
THRUSTER_NOZZLE_PREPARE_MODIFIER_NAME = "AI_ThrusterNozzle_Prepare"
DEFAULT_THRUSTER_NOZZLE_WIDTH = 0.008
DEFAULT_THRUSTER_NOZZLE_SEGMENTS = 2
HARDPOINT_SOCKET_PREPARE_MODIFIER_NAME = "AI_HardpointSocket_Prepare"
DEFAULT_HARDPOINT_SOCKET_WIDTH = 0.006
DEFAULT_HARDPOINT_SOCKET_SEGMENTS = 2
SURFACE_INSET_PREPARE_MODIFIER_NAME = "AI_SurfaceInset_Prepare"
DEFAULT_SURFACE_INSET_DEPTH = 0.006
DEFAULT_SURFACE_INSET_OFFSET = -1.0
ARMOR_EDGE_LIP_PREPARE_MODIFIER_NAME = "AI_ArmorEdgeLip_Prepare"
DEFAULT_ARMOR_EDGE_LIP_WIDTH = 0.008
DEFAULT_ARMOR_EDGE_LIP_SEGMENTS = 2
WEIGHTED_NORMAL_MODIFIER_NAME = "AI_WeightedNormal_Finish"
DEFAULT_WEIGHTED_NORMAL_WEIGHT = 50.0
DEFAULT_WEIGHTED_NORMAL_KEEP_SHARP = True
SOLIDIFY_THICKNESS_PREVIEW_MODIFIER_NAME = "AI_Solidify_ThicknessPreview"
DEFAULT_SOLIDIFY_THICKNESS = 0.015
DEFAULT_SOLIDIFY_OFFSET = 0.0
ARMOR_LAYER_PLATE_PREPARE_MODIFIER_NAME = "AI_ArmorLayer_PlatePrepare"
DEFAULT_ARMOR_LAYER_DEPTH = 0.01
DEFAULT_ARMOR_LAYER_OFFSET = 1.0

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


def weighted_normal_finish(
    operation_input: DomainOperationInput,
) -> OperationOutcome:
    """Improve target object shading through a Weighted Normal modifier."""
    if operation_input.operation != "weighted_normal_finish":
        raise ValueError(f"weighted_normal_finish cannot handle operation {operation_input.operation!r}.")

    weight = _weighted_normal_weight_from_parameters(operation_input.parameters)
    keep_sharp = _keep_sharp_from_parameters(operation_input.parameters)
    modifier_name = _modifier_name_from_parameters(operation_input.parameters, WEIGHTED_NORMAL_MODIFIER_NAME)
    resolved_object = core_geometry_api.require_object(operation_input.target_object)
    modifier = core_geometry_api.add_weighted_normal_modifier(
        resolved_object,
        weight=weight,
        keep_sharp=keep_sharp,
        modifier_name=modifier_name,
    )
    return OperationOutcome(
        operation="weighted_normal_finish",
        target_object=operation_input.target_object,
        success=True,
        changed_objects=[operation_input.target_object],
        modifier_info={
            "modifier_name": _modifier_value(modifier, "name", "modifier_name"),
            "modifier_type": _modifier_value(modifier, "type", "modifier_type"),
            "weight": weight,
            "keep_sharp": keep_sharp,
        },
        mesh_data_applied=False,
        diagnostics=[],
    )


def solidify_thickness_preview(
    operation_input: DomainOperationInput,
) -> OperationOutcome:
    """Preview armor thickness through a non-applied Solidify modifier."""
    if operation_input.operation != "solidify_thickness_preview":
        raise ValueError(f"solidify_thickness_preview cannot handle operation {operation_input.operation!r}.")

    thickness = _solidify_thickness_from_parameters(operation_input.parameters)
    offset = _solidify_offset_from_parameters(operation_input.parameters)
    modifier_name = _modifier_name_from_parameters(operation_input.parameters, SOLIDIFY_THICKNESS_PREVIEW_MODIFIER_NAME)
    resolved_object = core_geometry_api.require_object(operation_input.target_object)
    modifier = core_geometry_api.add_solidify_modifier(
        resolved_object,
        thickness=thickness,
        offset=offset,
        modifier_name=modifier_name,
    )
    return OperationOutcome(
        operation="solidify_thickness_preview",
        target_object=operation_input.target_object,
        success=True,
        changed_objects=[operation_input.target_object],
        modifier_info={
            "modifier_name": _modifier_value(modifier, "name", "modifier_name"),
            "modifier_type": _modifier_value(modifier, "type", "modifier_type"),
            "thickness": thickness,
            "offset": offset,
        },
        mesh_data_applied=False,
        diagnostics=[],
    )


def panel_line_bevel_prepare(
    operation_input: DomainOperationInput,
) -> OperationOutcome:
    """Prepare panel or parting line detail through a named Bevel modifier."""
    if operation_input.operation != "panel_line_bevel_prepare":
        raise ValueError(f"panel_line_bevel_prepare cannot handle operation {operation_input.operation!r}.")

    width = _panel_line_width_from_parameters(operation_input.parameters)
    segments = _panel_line_segments_from_parameters(operation_input.parameters)
    modifier_name = _modifier_name_from_parameters(operation_input.parameters, PANEL_LINE_BEVEL_PREPARE_MODIFIER_NAME)
    resolved_object = core_geometry_api.require_object(operation_input.target_object)
    modifier = core_geometry_api.add_bevel_modifier(
        resolved_object,
        width=width,
        segments=segments,
        modifier_name=modifier_name,
    )
    return OperationOutcome(
        operation="panel_line_bevel_prepare",
        target_object=operation_input.target_object,
        success=True,
        changed_objects=[operation_input.target_object],
        modifier_info={
            "modifier_name": _modifier_value(modifier, "name", "modifier_name"),
            "modifier_type": _modifier_value(modifier, "type", "modifier_type"),
            "width": width,
            "segments": segments,
        },
        mesh_data_applied=False,
        diagnostics=[],
    )


def armor_layer_plate_prepare(
    operation_input: DomainOperationInput,
) -> OperationOutcome:
    """Prepare an armor layer plate preview through a non-applied Solidify modifier."""
    if operation_input.operation != "armor_layer_plate_prepare":
        raise ValueError(f"armor_layer_plate_prepare cannot handle operation {operation_input.operation!r}.")

    layer_depth = _armor_layer_depth_from_parameters(operation_input.parameters)
    offset = _armor_layer_offset_from_parameters(operation_input.parameters)
    modifier_name = _modifier_name_from_parameters(operation_input.parameters, ARMOR_LAYER_PLATE_PREPARE_MODIFIER_NAME)
    resolved_object = core_geometry_api.require_object(operation_input.target_object)
    modifier = core_geometry_api.add_solidify_modifier(
        resolved_object,
        thickness=layer_depth,
        offset=offset,
        modifier_name=modifier_name,
    )
    return OperationOutcome(
        operation="armor_layer_plate_prepare",
        target_object=operation_input.target_object,
        success=True,
        changed_objects=[operation_input.target_object],
        modifier_info={
            "modifier_name": _modifier_value(modifier, "name", "modifier_name"),
            "modifier_type": _modifier_value(modifier, "type", "modifier_type"),
            "layer_depth": layer_depth,
            "offset": offset,
        },
        mesh_data_applied=False,
        diagnostics=[],
    )


def vent_slot_prepare(
    operation_input: DomainOperationInput,
) -> OperationOutcome:
    """Prepare vent or grille detail through a named Bevel modifier."""
    if operation_input.operation != "vent_slot_prepare":
        raise ValueError(f"vent_slot_prepare cannot handle operation {operation_input.operation!r}.")

    width = _vent_slot_width_from_parameters(operation_input.parameters)
    segments = _vent_slot_segments_from_parameters(operation_input.parameters)
    modifier_name = _modifier_name_from_parameters(operation_input.parameters, VENT_SLOT_PREPARE_MODIFIER_NAME)
    resolved_object = core_geometry_api.require_object(operation_input.target_object)
    modifier = core_geometry_api.add_bevel_modifier(
        resolved_object,
        width=width,
        segments=segments,
        modifier_name=modifier_name,
    )
    return OperationOutcome(
        operation="vent_slot_prepare",
        target_object=operation_input.target_object,
        success=True,
        changed_objects=[operation_input.target_object],
        modifier_info={
            "modifier_name": _modifier_value(modifier, "name", "modifier_name"),
            "modifier_type": _modifier_value(modifier, "type", "modifier_type"),
            "width": width,
            "segments": segments,
        },
        mesh_data_applied=False,
        diagnostics=[],
    )


def thruster_nozzle_prepare(
    operation_input: DomainOperationInput,
) -> OperationOutcome:
    """Prepare thruster or nozzle detail through a named Bevel modifier."""
    if operation_input.operation != "thruster_nozzle_prepare":
        raise ValueError(f"thruster_nozzle_prepare cannot handle operation {operation_input.operation!r}.")

    width = _thruster_nozzle_width_from_parameters(operation_input.parameters)
    segments = _thruster_nozzle_segments_from_parameters(operation_input.parameters)
    modifier_name = _modifier_name_from_parameters(operation_input.parameters, THRUSTER_NOZZLE_PREPARE_MODIFIER_NAME)
    resolved_object = core_geometry_api.require_object(operation_input.target_object)
    modifier = core_geometry_api.add_bevel_modifier(
        resolved_object,
        width=width,
        segments=segments,
        modifier_name=modifier_name,
    )
    return OperationOutcome(
        operation="thruster_nozzle_prepare",
        target_object=operation_input.target_object,
        success=True,
        changed_objects=[operation_input.target_object],
        modifier_info={
            "modifier_name": _modifier_value(modifier, "name", "modifier_name"),
            "modifier_type": _modifier_value(modifier, "type", "modifier_type"),
            "width": width,
            "segments": segments,
        },
        mesh_data_applied=False,
        diagnostics=[],
    )


def hardpoint_socket_prepare(
    operation_input: DomainOperationInput,
) -> OperationOutcome:
    """Prepare hardpoint or weapon socket detail through a named Bevel modifier."""
    if operation_input.operation != "hardpoint_socket_prepare":
        raise ValueError(f"hardpoint_socket_prepare cannot handle operation {operation_input.operation!r}.")

    width = _hardpoint_socket_width_from_parameters(operation_input.parameters)
    segments = _hardpoint_socket_segments_from_parameters(operation_input.parameters)
    modifier_name = _modifier_name_from_parameters(operation_input.parameters, HARDPOINT_SOCKET_PREPARE_MODIFIER_NAME)
    resolved_object = core_geometry_api.require_object(operation_input.target_object)
    modifier = core_geometry_api.add_bevel_modifier(
        resolved_object,
        width=width,
        segments=segments,
        modifier_name=modifier_name,
    )
    return OperationOutcome(
        operation="hardpoint_socket_prepare",
        target_object=operation_input.target_object,
        success=True,
        changed_objects=[operation_input.target_object],
        modifier_info={
            "modifier_name": _modifier_value(modifier, "name", "modifier_name"),
            "modifier_type": _modifier_value(modifier, "type", "modifier_type"),
            "width": width,
            "segments": segments,
        },
        mesh_data_applied=False,
        diagnostics=[],
    )


def surface_inset_prepare(
    operation_input: DomainOperationInput,
) -> OperationOutcome:
    """Prepare recessed or inset surface detail through a non-applied Solidify modifier."""
    if operation_input.operation != "surface_inset_prepare":
        raise ValueError(f"surface_inset_prepare cannot handle operation {operation_input.operation!r}.")

    inset_depth = _surface_inset_depth_from_parameters(operation_input.parameters)
    offset = _surface_inset_offset_from_parameters(operation_input.parameters)
    modifier_name = _modifier_name_from_parameters(operation_input.parameters, SURFACE_INSET_PREPARE_MODIFIER_NAME)
    resolved_object = core_geometry_api.require_object(operation_input.target_object)
    modifier = core_geometry_api.add_solidify_modifier(
        resolved_object,
        thickness=inset_depth,
        offset=offset,
        modifier_name=modifier_name,
    )
    return OperationOutcome(
        operation="surface_inset_prepare",
        target_object=operation_input.target_object,
        success=True,
        changed_objects=[operation_input.target_object],
        modifier_info={
            "modifier_name": _modifier_value(modifier, "name", "modifier_name"),
            "modifier_type": _modifier_value(modifier, "type", "modifier_type"),
            "inset_depth": inset_depth,
            "offset": offset,
        },
        mesh_data_applied=False,
        diagnostics=[],
    )


def armor_edge_lip_prepare(
    operation_input: DomainOperationInput,
) -> OperationOutcome:
    """Prepare armor edge lip detail through a named Bevel modifier."""
    if operation_input.operation != "armor_edge_lip_prepare":
        raise ValueError(f"armor_edge_lip_prepare cannot handle operation {operation_input.operation!r}.")

    width = _armor_edge_lip_width_from_parameters(operation_input.parameters)
    segments = _armor_edge_lip_segments_from_parameters(operation_input.parameters)
    modifier_name = _modifier_name_from_parameters(operation_input.parameters, ARMOR_EDGE_LIP_PREPARE_MODIFIER_NAME)
    resolved_object = core_geometry_api.require_object(operation_input.target_object)
    modifier = core_geometry_api.add_bevel_modifier(
        resolved_object,
        width=width,
        segments=segments,
        modifier_name=modifier_name,
    )
    return OperationOutcome(
        operation="armor_edge_lip_prepare",
        target_object=operation_input.target_object,
        success=True,
        changed_objects=[operation_input.target_object],
        modifier_info={
            "modifier_name": _modifier_value(modifier, "name", "modifier_name"),
            "modifier_type": _modifier_value(modifier, "type", "modifier_type"),
            "width": width,
            "segments": segments,
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


def _weighted_normal_weight_from_parameters(parameters: dict[str, Any]) -> float:
    weight = float(parameters.get("weight", DEFAULT_WEIGHTED_NORMAL_WEIGHT))
    if weight <= 0:
        raise ValueError("weight must be greater than 0.")
    return weight


def _keep_sharp_from_parameters(parameters: dict[str, Any]) -> bool:
    keep_sharp = parameters.get("keep_sharp", DEFAULT_WEIGHTED_NORMAL_KEEP_SHARP)
    if isinstance(keep_sharp, bool):
        return keep_sharp
    if keep_sharp == "true":
        return True
    if keep_sharp == "false":
        return False
    raise ValueError("keep_sharp must be one of: true, false.")


def _solidify_thickness_from_parameters(parameters: dict[str, Any]) -> float:
    thickness = float(parameters.get("thickness", DEFAULT_SOLIDIFY_THICKNESS))
    if thickness <= 0:
        raise ValueError("thickness must be greater than 0.")
    return thickness


def _solidify_offset_from_parameters(parameters: dict[str, Any]) -> float:
    return float(parameters.get("offset", DEFAULT_SOLIDIFY_OFFSET))


def _panel_line_width_from_parameters(parameters: dict[str, Any]) -> float:
    width = float(parameters.get("width", DEFAULT_PANEL_LINE_WIDTH))
    if width <= 0:
        raise ValueError("width must be greater than 0.")
    return width


def _panel_line_segments_from_parameters(parameters: dict[str, Any]) -> int:
    segments = int(parameters.get("segments", DEFAULT_PANEL_LINE_SEGMENTS))
    if segments < 1:
        raise ValueError("segments must be at least 1.")
    return segments


def _armor_layer_depth_from_parameters(parameters: dict[str, Any]) -> float:
    layer_depth = float(parameters.get("layer_depth", DEFAULT_ARMOR_LAYER_DEPTH))
    if layer_depth <= 0:
        raise ValueError("layer_depth must be greater than 0.")
    return layer_depth


def _armor_layer_offset_from_parameters(parameters: dict[str, Any]) -> float:
    return float(parameters.get("offset", DEFAULT_ARMOR_LAYER_OFFSET))


def _vent_slot_width_from_parameters(parameters: dict[str, Any]) -> float:
    width = float(parameters.get("width", DEFAULT_VENT_SLOT_WIDTH))
    if width <= 0:
        raise ValueError("width must be greater than 0.")
    return width


def _vent_slot_segments_from_parameters(parameters: dict[str, Any]) -> int:
    segments = int(parameters.get("segments", DEFAULT_VENT_SLOT_SEGMENTS))
    if segments < 1:
        raise ValueError("segments must be at least 1.")
    return segments


def _thruster_nozzle_width_from_parameters(parameters: dict[str, Any]) -> float:
    width = float(parameters.get("width", DEFAULT_THRUSTER_NOZZLE_WIDTH))
    if width <= 0:
        raise ValueError("width must be greater than 0.")
    return width


def _thruster_nozzle_segments_from_parameters(parameters: dict[str, Any]) -> int:
    segments = int(parameters.get("segments", DEFAULT_THRUSTER_NOZZLE_SEGMENTS))
    if segments < 1:
        raise ValueError("segments must be at least 1.")
    return segments


def _hardpoint_socket_width_from_parameters(parameters: dict[str, Any]) -> float:
    width = float(parameters.get("width", DEFAULT_HARDPOINT_SOCKET_WIDTH))
    if width <= 0:
        raise ValueError("width must be greater than 0.")
    return width


def _hardpoint_socket_segments_from_parameters(parameters: dict[str, Any]) -> int:
    segments = int(parameters.get("segments", DEFAULT_HARDPOINT_SOCKET_SEGMENTS))
    if segments < 1:
        raise ValueError("segments must be at least 1.")
    return segments


def _surface_inset_depth_from_parameters(parameters: dict[str, Any]) -> float:
    inset_depth = float(parameters.get("inset_depth", DEFAULT_SURFACE_INSET_DEPTH))
    if inset_depth <= 0:
        raise ValueError("inset_depth must be greater than 0.")
    return inset_depth


def _surface_inset_offset_from_parameters(parameters: dict[str, Any]) -> float:
    return float(parameters.get("offset", DEFAULT_SURFACE_INSET_OFFSET))


def _armor_edge_lip_width_from_parameters(parameters: dict[str, Any]) -> float:
    width = float(parameters.get("width", DEFAULT_ARMOR_EDGE_LIP_WIDTH))
    if width <= 0:
        raise ValueError("width must be greater than 0.")
    return width


def _armor_edge_lip_segments_from_parameters(parameters: dict[str, Any]) -> int:
    segments = int(parameters.get("segments", DEFAULT_ARMOR_EDGE_LIP_SEGMENTS))
    if segments < 1:
        raise ValueError("segments must be at least 1.")
    return segments


def _modifier_name_from_parameters(parameters: dict[str, Any], default_modifier_name: str) -> str:
    modifier_name = str(parameters.get("modifier_name", default_modifier_name)).strip()
    if not modifier_name:
        raise ValueError("modifier_name is required.")
    return modifier_name


def _modifier_value(modifier: Any, attribute_name: str, mapping_key: str) -> str:
    if isinstance(modifier, dict):
        return str(modifier.get(mapping_key) or modifier.get(attribute_name) or "")
    return str(getattr(modifier, attribute_name, ""))
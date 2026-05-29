"""Static registry for supported Domain Operations.

The registry is a Planning-facing capability list. It has no Blender API,
Core API, or Domain Operation handler dependency, and it does not execute
operations.
"""

from __future__ import annotations

from domain.operation_contracts import OperationSpec


EDGE_SOFTEN_OPERATION = "edge_soften"
WEIGHTED_NORMAL_FINISH_OPERATION = "weighted_normal_finish"
SOLIDIFY_THICKNESS_PREVIEW_OPERATION = "solidify_thickness_preview"
PANEL_LINE_BEVEL_PREPARE_OPERATION = "panel_line_bevel_prepare"
ARMOR_LAYER_PLATE_PREPARE_OPERATION = "armor_layer_plate_prepare"
VENT_SLOT_PREPARE_OPERATION = "vent_slot_prepare"
THRUSTER_NOZZLE_PREPARE_OPERATION = "thruster_nozzle_prepare"
HARDPOINT_SOCKET_PREPARE_OPERATION = "hardpoint_socket_prepare"
SURFACE_INSET_PREPARE_OPERATION = "surface_inset_prepare"
ARMOR_EDGE_LIP_PREPARE_OPERATION = "armor_edge_lip_prepare"

EDGE_SOFTEN_SPEC = OperationSpec(
    name=EDGE_SOFTEN_OPERATION,
    supported_task_types=("surface_detail_enhancement",),
    required_target_state="bound",
    default_parameters={
        "strength": 0.01,
        "style": "mechanical",
    },
    parameter_schema={
        "strength": {
            "type": "number",
            "exclusive_minimum": 0.0,
            "default": 0.01,
        },
        "style": {
            "type": "string",
            "enum": ["clean", "heavy", "mechanical"],
            "default": "mechanical",
        },
    },
    safety_level="safe_non_destructive",
    handler_name="edge_soften",
    report_schema={
        "required_fields": [
            "operation",
            "target_object",
            "success",
            "changed_objects",
            "modifier_info",
            "mesh_data_applied",
            "diagnostics",
        ],
    },
    intent_actions=(
        "refine_edges",
        "soften_edges",
        "add_surface_detail",
        "add_panel_lines",
        "add_parting_lines",
        "add_armor_layers",
    ),
    intent_detail_types=("edge_soften", "bevel", "panel_line", "panel_lines", "parting_lines", "armor_layers"),
    intent_effects=(
        "softened_mechanical_edges",
        "panel_lines",
        "parting_lines",
        "armor_layers",
        "non_destructive_surface_detail",
    ),
    priority=100,
)

WEIGHTED_NORMAL_FINISH_SPEC = OperationSpec(
    name=WEIGHTED_NORMAL_FINISH_OPERATION,
    supported_task_types=("surface_detail_enhancement",),
    required_target_state="bound",
    default_parameters={
        "weight": 50.0,
        "keep_sharp": "true",
        "modifier_name": "AI_WeightedNormal_Finish",
    },
    parameter_schema={
        "weight": {
            "type": "number",
            "exclusive_minimum": 0.0,
            "default": 50.0,
        },
        "keep_sharp": {
            "type": "string",
            "enum": ["true", "false"],
            "default": "true",
        },
        "modifier_name": {
            "type": "string",
            "default": "AI_WeightedNormal_Finish",
        },
    },
    safety_level="safe_non_destructive",
    handler_name="weighted_normal_finish",
    report_schema={
        "required_fields": [
            "operation",
            "target_object",
            "success",
            "changed_objects",
            "modifier_info",
            "mesh_data_applied",
            "diagnostics",
        ],
    },
    intent_actions=("improve_shading", "refine_surface", "finish_surface"),
    intent_detail_types=("weighted_normal", "shading_finish", "surface_finish", "hard_surface_finish"),
    intent_effects=("hard_surface_shading_finish", "cleaner_highlight_flow"),
    priority=90,
)

SOLIDIFY_THICKNESS_PREVIEW_SPEC = OperationSpec(
    name=SOLIDIFY_THICKNESS_PREVIEW_OPERATION,
    supported_task_types=("surface_detail_enhancement",),
    required_target_state="bound",
    default_parameters={
        "thickness": 0.015,
        "offset": 0.0,
        "modifier_name": "AI_Solidify_ThicknessPreview",
    },
    parameter_schema={
        "thickness": {
            "type": "number",
            "exclusive_minimum": 0.0,
            "default": 0.015,
        },
        "offset": {
            "type": "number",
            "default": 0.0,
        },
        "modifier_name": {
            "type": "string",
            "default": "AI_Solidify_ThicknessPreview",
        },
    },
    safety_level="safe_non_destructive",
    handler_name="solidify_thickness_preview",
    report_schema={
        "required_fields": [
            "operation",
            "target_object",
            "success",
            "changed_objects",
            "modifier_info",
            "mesh_data_applied",
            "diagnostics",
        ],
    },
    intent_actions=("preview_thickness", "add_thickness_preview", "enhance_armor_thickness"),
    intent_detail_types=("thickness_preview", "armor_thickness", "solidify_preview"),
    intent_effects=("armor_thickness_preview", "heavy_armor_feel", "printable_armor_thickness_preview"),
    priority=95,
)

PANEL_LINE_BEVEL_PREPARE_SPEC = OperationSpec(
    name=PANEL_LINE_BEVEL_PREPARE_OPERATION,
    supported_task_types=("surface_detail_enhancement",),
    required_target_state="bound",
    default_parameters={
        "width": 0.006,
        "segments": 1,
        "modifier_name": "AI_PanelLine_Prepare",
    },
    parameter_schema={
        "width": {
            "type": "number",
            "exclusive_minimum": 0.0,
            "default": 0.006,
        },
        "segments": {
            "type": "number",
            "exclusive_minimum": 0.0,
            "default": 1,
        },
        "modifier_name": {
            "type": "string",
            "default": "AI_PanelLine_Prepare",
        },
    },
    safety_level="safe_non_destructive",
    handler_name="panel_line_bevel_prepare",
    report_schema={
        "required_fields": [
            "operation",
            "target_object",
            "success",
            "changed_objects",
            "modifier_info",
            "mesh_data_applied",
            "diagnostics",
        ],
    },
    intent_actions=("add_panel_lines", "add_parting_lines", "prepare_panel_lines", "add_panel_line_base"),
    intent_detail_types=("panel_lines", "parting_lines", "panel_line", "parting_line"),
    intent_effects=("panel_line_preparation", "panel_lines", "parting_lines"),
    priority=80,
)

ARMOR_LAYER_PLATE_PREPARE_SPEC = OperationSpec(
    name=ARMOR_LAYER_PLATE_PREPARE_OPERATION,
    supported_task_types=("surface_detail_enhancement",),
    required_target_state="bound",
    default_parameters={
        "layer_depth": 0.01,
        "offset": 1.0,
        "modifier_name": "AI_ArmorLayer_PlatePrepare",
    },
    parameter_schema={
        "layer_depth": {
            "type": "number",
            "exclusive_minimum": 0.0,
            "default": 0.01,
        },
        "offset": {
            "type": "number",
            "default": 1.0,
        },
        "modifier_name": {
            "type": "string",
            "default": "AI_ArmorLayer_PlatePrepare",
        },
    },
    safety_level="safe_non_destructive",
    handler_name="armor_layer_plate_prepare",
    report_schema={
        "required_fields": [
            "operation",
            "target_object",
            "success",
            "changed_objects",
            "modifier_info",
            "mesh_data_applied",
            "diagnostics",
        ],
    },
    intent_actions=("prepare_armor_layers", "enhance_armor_layering", "add_layer_plate"),
    intent_detail_types=("armor_layer_plate", "layered_armor", "plate_offset"),
    intent_effects=("armor_layer_preparation", "layered_armor_structure", "outer_armor_plate_preview"),
    priority=85,
)

VENT_SLOT_PREPARE_SPEC = OperationSpec(
    name=VENT_SLOT_PREPARE_OPERATION,
    supported_task_types=("surface_detail_enhancement",),
    required_target_state="bound",
    default_parameters={
        "width": 0.004,
        "segments": 1,
        "modifier_name": "AI_VentSlot_Prepare",
    },
    parameter_schema={
        "width": {
            "type": "number",
            "exclusive_minimum": 0.0,
            "default": 0.004,
        },
        "segments": {
            "type": "number",
            "exclusive_minimum": 0.0,
            "default": 1,
        },
        "modifier_name": {
            "type": "string",
            "default": "AI_VentSlot_Prepare",
        },
    },
    safety_level="safe_non_destructive",
    handler_name="vent_slot_prepare",
    report_schema={
        "required_fields": [
            "operation",
            "target_object",
            "success",
            "changed_objects",
            "modifier_info",
            "mesh_data_applied",
            "diagnostics",
        ],
    },
    intent_actions=("add_vents", "prepare_vent_slots", "add_vent_slot_base"),
    intent_detail_types=("vents", "vent_slot", "vent_slots", "grille"),
    intent_effects=("vent_slot_preparation", "mechanical_vent_detail", "functional_vent_preview"),
    priority=82,
)

THRUSTER_NOZZLE_PREPARE_SPEC = OperationSpec(
    name=THRUSTER_NOZZLE_PREPARE_OPERATION,
    supported_task_types=("surface_detail_enhancement",),
    required_target_state="bound",
    default_parameters={
        "width": 0.008,
        "segments": 2,
        "modifier_name": "AI_ThrusterNozzle_Prepare",
    },
    parameter_schema={
        "width": {
            "type": "number",
            "exclusive_minimum": 0.0,
            "default": 0.008,
        },
        "segments": {
            "type": "number",
            "exclusive_minimum": 0.0,
            "default": 2,
        },
        "modifier_name": {
            "type": "string",
            "default": "AI_ThrusterNozzle_Prepare",
        },
    },
    safety_level="safe_non_destructive",
    handler_name="thruster_nozzle_prepare",
    report_schema={
        "required_fields": [
            "operation",
            "target_object",
            "success",
            "changed_objects",
            "modifier_info",
            "mesh_data_applied",
            "diagnostics",
        ],
    },
    intent_actions=("add_thrusters", "prepare_thruster_nozzles", "add_thruster_nozzle_base"),
    intent_detail_types=("thrusters", "thruster_nozzle", "thruster_nozzles", "nozzle", "vernier"),
    intent_effects=("thruster_nozzle_preparation", "high_mobility_detail", "propulsion_detail"),
    priority=82,
)

HARDPOINT_SOCKET_PREPARE_SPEC = OperationSpec(
    name=HARDPOINT_SOCKET_PREPARE_OPERATION,
    supported_task_types=("surface_detail_enhancement",),
    required_target_state="bound",
    default_parameters={
        "width": 0.006,
        "segments": 2,
        "modifier_name": "AI_HardpointSocket_Prepare",
    },
    parameter_schema={
        "width": {
            "type": "number",
            "exclusive_minimum": 0.0,
            "default": 0.006,
        },
        "segments": {
            "type": "number",
            "exclusive_minimum": 0.0,
            "default": 2,
        },
        "modifier_name": {
            "type": "string",
            "default": "AI_HardpointSocket_Prepare",
        },
    },
    safety_level="safe_non_destructive",
    handler_name="hardpoint_socket_prepare",
    report_schema={
        "required_fields": [
            "operation",
            "target_object",
            "success",
            "changed_objects",
            "modifier_info",
            "mesh_data_applied",
            "diagnostics",
        ],
    },
    intent_actions=("add_weapon_mounts", "prepare_hardpoint_socket", "add_mount_socket_base"),
    intent_detail_types=("weapon_mounts", "hardpoint_socket", "hardpoint", "socket", "weapon_mount"),
    intent_effects=("hardpoint_socket_preparation", "equipment_mount_interface", "weapon_mount_preview"),
    priority=83,
)

SURFACE_INSET_PREPARE_SPEC = OperationSpec(
    name=SURFACE_INSET_PREPARE_OPERATION,
    supported_task_types=("surface_detail_enhancement",),
    required_target_state="bound",
    default_parameters={
        "inset_depth": 0.006,
        "offset": -1.0,
        "modifier_name": "AI_SurfaceInset_Prepare",
    },
    parameter_schema={
        "inset_depth": {
            "type": "number",
            "exclusive_minimum": 0.0,
            "default": 0.006,
        },
        "offset": {
            "type": "number",
            "default": -1.0,
        },
        "modifier_name": {
            "type": "string",
            "default": "AI_SurfaceInset_Prepare",
        },
    },
    safety_level="safe_non_destructive",
    handler_name="surface_inset_prepare",
    report_schema={
        "required_fields": [
            "operation",
            "target_object",
            "success",
            "changed_objects",
            "modifier_info",
            "mesh_data_applied",
            "diagnostics",
        ],
    },
    intent_actions=("prepare_surface_inset", "add_surface_inset", "inset_surface"),
    intent_detail_types=("surface_inset", "inset_panel", "recessed_panel"),
    intent_effects=("surface_inset_preparation", "recessed_surface_preview", "inset_panel_preview"),
    priority=84,
)

ARMOR_EDGE_LIP_PREPARE_SPEC = OperationSpec(
    name=ARMOR_EDGE_LIP_PREPARE_OPERATION,
    supported_task_types=("surface_detail_enhancement",),
    required_target_state="bound",
    default_parameters={
        "width": 0.008,
        "segments": 2,
        "modifier_name": "AI_ArmorEdgeLip_Prepare",
    },
    parameter_schema={
        "width": {
            "type": "number",
            "exclusive_minimum": 0.0,
            "default": 0.008,
        },
        "segments": {
            "type": "number",
            "exclusive_minimum": 0.0,
            "default": 2,
        },
        "modifier_name": {
            "type": "string",
            "default": "AI_ArmorEdgeLip_Prepare",
        },
    },
    safety_level="safe_non_destructive",
    handler_name="armor_edge_lip_prepare",
    report_schema={
        "required_fields": [
            "operation",
            "target_object",
            "success",
            "changed_objects",
            "modifier_info",
            "mesh_data_applied",
            "diagnostics",
        ],
    },
    intent_actions=("prepare_armor_edge_lip", "add_armor_edge_lip", "prepare_edge_lip"),
    intent_detail_types=("armor_edge_lip", "edge_lip", "armor_lip", "edge_trim"),
    intent_effects=("armor_edge_lip_preparation", "armor_lip_preview", "mechanical_edge_lip"),
    priority=86,
)

DEFAULT_OPERATION_SPECS = (
    EDGE_SOFTEN_SPEC,
    WEIGHTED_NORMAL_FINISH_SPEC,
    SOLIDIFY_THICKNESS_PREVIEW_SPEC,
    PANEL_LINE_BEVEL_PREPARE_SPEC,
    ARMOR_LAYER_PLATE_PREPARE_SPEC,
    VENT_SLOT_PREPARE_SPEC,
    THRUSTER_NOZZLE_PREPARE_SPEC,
    HARDPOINT_SOCKET_PREPARE_SPEC,
    SURFACE_INSET_PREPARE_SPEC,
    ARMOR_EDGE_LIP_PREPARE_SPEC,
)


class OperationRegistryError(LookupError):
    """Raised when an operation registry lookup or registration fails."""


class OperationRegistry:
    """Small static registry for operation capability lookup."""

    def __init__(self, operation_specs: tuple[OperationSpec, ...] | None = None) -> None:
        self._operation_specs: dict[str, OperationSpec] = {}
        for operation_spec in operation_specs or DEFAULT_OPERATION_SPECS:
            self.register(operation_spec)

    def register(self, operation_spec: OperationSpec) -> None:
        """Register a static operation contract."""
        _validate_operation_spec(operation_spec)
        if operation_spec.name in self._operation_specs:
            raise OperationRegistryError(f"Operation {operation_spec.name!r} is already registered.")
        self._operation_specs[operation_spec.name] = operation_spec

    def get(self, operation_name: str) -> OperationSpec:
        """Return the operation spec for operation_name or fail clearly."""
        try:
            return self._operation_specs[operation_name]
        except KeyError as error:
            raise OperationRegistryError(f"Unsupported operation: {operation_name!r}.") from error

    def has(self, operation_name: str) -> bool:
        """Return whether operation_name is registered."""
        return operation_name in self._operation_specs

    def all_specs(self) -> tuple[OperationSpec, ...]:
        """Return all registered operation specs."""
        return tuple(self._operation_specs.values())

    def supported_for_task_type(self, task_type: str) -> tuple[OperationSpec, ...]:
        """Return operation specs that support a TaskObject task_type."""
        return tuple(
            operation_spec
            for operation_spec in self._operation_specs.values()
            if operation_spec.supports_task_type(task_type)
        )


def default_operation_registry() -> OperationRegistry:
    """Return the default registry for the current architecture step."""
    return OperationRegistry()


def _validate_operation_spec(operation_spec: OperationSpec) -> None:
    if not operation_spec.name:
        raise OperationRegistryError("OperationSpec.name is required.")
    if not operation_spec.supported_task_types:
        raise OperationRegistryError(f"Operation {operation_spec.name!r} must support at least one task_type.")
    if not operation_spec.required_target_state:
        raise OperationRegistryError(f"Operation {operation_spec.name!r} must define required_target_state.")
    if not operation_spec.handler_name:
        raise OperationRegistryError(f"Operation {operation_spec.name!r} must define handler_name.")
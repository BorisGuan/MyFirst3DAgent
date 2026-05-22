"""Data structures used by the minimal planning layer.

These schemas describe abstract model metadata and operation plans only. They do
not represent mesh, geometry, material, rigging, or rendering data.
"""

from dataclasses import asdict, dataclass
from typing import Any


ALLOWED_ACTIONS = {"add_detail", "enhance_detail", "refine_surface"}
ALLOWED_OPERATIONS = {
    "add_panel_lines",
    "add_parting_lines",
    "add_armor_layers",
    "add_vents",
    "add_thrusters",
    "add_pipes",
    "add_hydraulic_rods",
    "add_sensors",
    "add_weapon_mounts",
    "add_surface_damage",
    "refine_surface",
}
ALLOWED_DETAIL_TYPES = {
    "panel_lines",
    "parting_lines",
    "armor_layers",
    "vents",
    "thrusters",
    "pipes",
    "hydraulic_rods",
    "sensors",
    "weapon_mounts",
    "surface_damage",
    "weathering",
}
LEGACY_DETAIL_TYPES = {"mechanical_greeble", "surface_scratches"}
ALLOWED_STYLES = {
    "default_mecha",
    "sharp_mechanical",
    "heavy_armor",
    "military_realistic",
    "clean_anime",
    "high_mobility",
    "exposed_inner_frame",
}
ALLOWED_DENSITIES = {"low", "medium", "high"}
ALLOWED_SYMMETRIES = {
    "single_target",
    "left_right_mirror",
    "centerline_symmetry",
    "group_sync",
}
ALLOWED_SCALES = {"unknown", "non_scale", "1/144", "1/100", "1/60"}


@dataclass(frozen=True)
class ModelPart:
    """A high-level model part visible to the agent."""

    name: str
    detail_level: str
    display_name: str = ""
    category: str = "part"
    aliases: list[str] | None = None


@dataclass(frozen=True)
class AbstractModel:
    """Abstract model description passed to the LLM."""

    name: str
    parts: list[ModelPart]


@dataclass(frozen=True)
class OperationPlan:
    """Machine-readable mecha design operation blueprint returned by the agent."""

    target_part: str
    operation: str
    detail_type: str
    style: str
    density: str
    symmetry: str
    scale: str
    placement_zones: list[str]
    constraints: list[str]
    steps: list[str]
    risk_notes: list[str]
    reasoning: str
    designer_brief: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

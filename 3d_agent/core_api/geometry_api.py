"""Core geometry API: low-level Blender modifier helpers."""

from __future__ import annotations

from typing import Any

from core_api.persistence_api import record_modified_object, record_removed_modifier
from core_api.scene_object_api import modifier_snapshot


def add_bevel_modifier(object: Any, width: float, segments: int, modifier_name: str) -> Any:
    """Add a named BEVEL modifier to an object and return the modifier."""
    if not modifier_name:
        raise ValueError("modifier_name is required.")
    width_value = float(width)
    if width_value <= 0:
        raise ValueError("width must be greater than 0.")
    segment_count = int(segments)
    if segment_count < 1:
        raise ValueError("segments must be at least 1.")

    _require_modifier_collection(object)
    remove_or_replace_named_modifier(object, modifier_name)
    modifier = object.modifiers.new(name=modifier_name, type="BEVEL")
    modifier.width = width_value
    modifier.segments = segment_count
    record_modified_object(
        {
            "object_name": str(getattr(object, "name", "")),
            "change_type": "modifier_added",
            "modifier_name": modifier_name,
            "modifier_type": "BEVEL",
            "parameters": {
                "width": width_value,
                "segments": segment_count,
            },
            "mesh_data_applied": False,
        }
    )
    return modifier


def remove_or_replace_named_modifier(object: Any, modifier_name: str) -> dict[str, Any] | None:
    """Remove an existing modifier by name and return its previous snapshot."""
    if not modifier_name:
        raise ValueError("modifier_name is required.")
    modifiers = _require_modifier_collection(object)
    existing_modifier = modifiers.get(modifier_name) if hasattr(modifiers, "get") else None
    if existing_modifier is None:
        return None

    removed_snapshot = {
        "object_name": str(getattr(object, "name", "")),
        "modifier": modifier_snapshot(existing_modifier),
    }
    modifiers.remove(existing_modifier)
    record_removed_modifier(removed_snapshot)
    return removed_snapshot


def _require_modifier_collection(object: Any) -> Any:
    modifiers = getattr(object, "modifiers", None)
    if modifiers is None:
        raise TypeError("object must expose a Blender modifiers collection.")
    if not hasattr(modifiers, "new") or not hasattr(modifiers, "remove"):
        raise TypeError("object.modifiers must support new() and remove().")
    return modifiers
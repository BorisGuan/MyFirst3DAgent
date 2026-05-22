"""Core scene object API: low-level Blender object access helpers."""

from __future__ import annotations

from typing import Any


def require_object(object_name: str) -> Any:
    """Return a Blender object by name or fail loudly."""
    if not object_name:
        raise ValueError("object_name is required.")
    blender = _get_bpy()
    blender_object = blender.data.objects.get(object_name)
    if blender_object is None:
        raise LookupError(f"Blender object not found: {object_name}")
    return blender_object


def object_snapshot(object: Any) -> dict[str, Any]:
    """Return a JSON-serializable snapshot of a Blender object."""
    return {
        "name": str(getattr(object, "name", "")),
        "type": str(getattr(object, "type", "")),
        "data_name": str(getattr(getattr(object, "data", None), "name", "")),
        "dimensions": _vector3(getattr(object, "dimensions", None)),
        "location": _vector3(getattr(object, "location", None)),
        "rotation_euler": _vector3(getattr(object, "rotation_euler", None)),
        "scale": _vector3(getattr(object, "scale", None)),
        "modifiers": [modifier_snapshot(modifier) for modifier in getattr(object, "modifiers", [])],
    }


def modifier_snapshot(modifier: Any) -> dict[str, Any]:
    """Return a JSON-serializable snapshot of a Blender modifier."""
    snapshot = {
        "name": str(getattr(modifier, "name", "")),
        "type": str(getattr(modifier, "type", "")),
    }
    if hasattr(modifier, "width"):
        snapshot["width"] = float(modifier.width)
    if hasattr(modifier, "segments"):
        snapshot["segments"] = int(modifier.segments)
    return snapshot


def _get_bpy() -> Any:
    try:
        import bpy  # type: ignore[import-not-found]
    except ModuleNotFoundError as error:
        raise RuntimeError("Core scene object API requires Blender's bpy module.") from error
    return bpy


def _vector3(value: Any) -> list[float]:
    if value is None:
        return [0.0, 0.0, 0.0]
    if all(hasattr(value, attribute) for attribute in ("x", "y", "z")):
        return [float(value.x), float(value.y), float(value.z)]
    return [float(value[index]) for index in range(3)]
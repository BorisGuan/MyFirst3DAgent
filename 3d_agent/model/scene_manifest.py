"""Scene Manifest loading and validation for V0.5.

The Scene Manifest is a read-only object directory exported from Blender. This
module validates and normalizes that JSON shape only; it does not inspect mesh
geometry, bind parts, or execute Blender.
"""

import json
from pathlib import Path
from typing import Any


MANIFEST_VERSION = "v0_5"
SUPPORTED_SOURCE_SOFTWARE = {"blender"}
ALLOWED_UNIT_SYSTEMS = {"metric", "imperial", "blender_default", "unknown"}
ALLOWED_OBJECT_TYPES = {"MESH", "EMPTY", "CURVE", "ARMATURE", "CAMERA", "LIGHT", "UNKNOWN"}
VECTOR_FIELDS = {"dimensions", "location", "rotation_euler"}


def load_scene_manifest(path: str | Path) -> dict[str, Any]:
    """Load, validate, and normalize a V0.5 Scene Manifest JSON file."""
    manifest_path = Path(path)
    try:
        raw_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValueError(f"Invalid Scene Manifest JSON: {error.msg}") from error
    return normalize_scene_manifest(raw_manifest)


def normalize_scene_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    """Validate and normalize a Scene Manifest dict."""
    if not isinstance(manifest, dict):
        raise ValueError("Scene Manifest must be a JSON object.")

    manifest_version = _required_string(manifest, "manifest_version")
    if manifest_version != MANIFEST_VERSION:
        raise ValueError(f"manifest_version must be {MANIFEST_VERSION!r}.")

    source_software = _required_string(manifest, "source_software")
    if source_software not in SUPPORTED_SOURCE_SOFTWARE:
        raise ValueError("source_software must be 'blender' for V0.5.")

    source_file = _required_string(manifest, "source_file")
    unit_system = manifest.get("unit_system", "unknown")
    if not isinstance(unit_system, str) or unit_system not in ALLOWED_UNIT_SYSTEMS:
        raise ValueError("unit_system must be one of metric, imperial, blender_default, unknown.")

    objects = manifest.get("objects")
    if not isinstance(objects, list):
        raise ValueError("objects must be a list.")

    return {
        "manifest_version": manifest_version,
        "source_software": source_software,
        "source_file": source_file,
        "unit_system": unit_system,
        "objects": [_normalize_object(scene_object, index) for index, scene_object in enumerate(objects)],
    }


def _normalize_object(scene_object: Any, index: int) -> dict[str, Any]:
    if not isinstance(scene_object, dict):
        raise ValueError(f"objects[{index}] must be an object.")

    object_name = _required_string(scene_object, "object_name", prefix=f"objects[{index}].")
    object_type = scene_object.get("object_type", "UNKNOWN")
    if not isinstance(object_type, str) or object_type not in ALLOWED_OBJECT_TYPES:
        raise ValueError(f"objects[{index}].object_type must be a supported object type.")

    return {
        "object_name": object_name,
        "object_type": object_type,
        "collection_path": _string_list(scene_object.get("collection_path", []), f"objects[{index}].collection_path"),
        "dimensions": _vector(scene_object.get("dimensions", []), f"objects[{index}].dimensions"),
        "location": _vector(scene_object.get("location", []), f"objects[{index}].location"),
        "rotation_euler": _vector(scene_object.get("rotation_euler", []), f"objects[{index}].rotation_euler"),
        "vertex_count": _non_negative_int(scene_object.get("vertex_count", 0), f"objects[{index}].vertex_count"),
        "material_names": _string_list(scene_object.get("material_names", []), f"objects[{index}].material_names"),
        "custom_properties": _dict(scene_object.get("custom_properties", {}), f"objects[{index}].custom_properties"),
    }


def _required_string(data: dict[str, Any], field: str, prefix: str = "") -> str:
    value = data.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{prefix}{field} must be a non-empty string.")
    return value


def _string_list(value: Any, field_path: str) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValueError(f"{field_path} must be a list of strings.")
    return list(value)


def _vector(value: Any, field_path: str) -> list[float]:
    if value == []:
        return []
    if (
        not isinstance(value, list)
        or len(value) != 3
        or not all(isinstance(item, int | float) for item in value)
    ):
        raise ValueError(f"{field_path} must be an empty list or a 3-number list.")
    return [float(item) for item in value]


def _non_negative_int(value: Any, field_path: str) -> int:
    if not isinstance(value, int) or value < 0:
        raise ValueError(f"{field_path} must be a non-negative integer.")
    return value


def _dict(value: Any, field_path: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field_path} must be an object.")
    return dict(value)
"""Blender Scene Manifest export script draft for V0.5.

The generated script is intended to be reviewed and run inside Blender by the
user. It only reads scene object metadata and writes a JSON manifest; it does
not modify objects, mesh data, modifiers, or the .blend file.
"""


def create_blender_manifest_export_draft(output_path: str = "blender_scene_manifest.json") -> str:
    """Create a read-only Blender Python script draft for exporting a Scene Manifest."""
    return f'''# V0.5 Blender Scene Manifest export draft
# This draft only reads scene object metadata and writes a JSON manifest.
# It does not edit mesh geometry, create objects, run booleans, apply modifiers, or save .blend files.

import json
from pathlib import Path

import bpy


output_path = Path({output_path!r})


def vector3(values):
    return [float(values[0]), float(values[1]), float(values[2])]


def collection_path_for_object(target_object):
    def walk(collection, path):
        if target_object.name in collection.objects:
            return [*path, collection.name]
        for child_collection in collection.children:
            found_path = walk(child_collection, [*path, collection.name])
            if found_path:
                return found_path
        return []

    return walk(bpy.context.scene.collection, []) or [
        collection.name for collection in target_object.users_collection
    ]


def safe_custom_properties(target_object):
    custom_properties = {{}}
    for key in target_object.keys():
        if key.startswith("_"):
            continue
        value = target_object[key]
        if isinstance(value, (str, int, float, bool)) or value is None:
            custom_properties[key] = value
        else:
            custom_properties[key] = str(value)
    return custom_properties


def object_manifest(target_object):
    vertex_count = 0
    if target_object.type == "MESH" and hasattr(target_object.data, "vertices"):
        vertex_count = len(target_object.data.vertices)
    material_names = [
        slot.material.name
        for slot in target_object.material_slots
        if slot.material is not None
    ]
    return {{
        "object_name": target_object.name,
        "object_type": target_object.type,
        "collection_path": collection_path_for_object(target_object),
        "dimensions": vector3(target_object.dimensions),
        "location": vector3(target_object.location),
        "rotation_euler": vector3(target_object.rotation_euler),
        "vertex_count": vertex_count,
        "material_names": material_names,
        "custom_properties": safe_custom_properties(target_object),
    }}


manifest = {{
    "manifest_version": "v0_5",
    "source_software": "blender",
    "source_file": bpy.data.filepath or "unsaved_blender_scene.blend",
    "unit_system": bpy.context.scene.unit_settings.system.lower()
    if bpy.context.scene.unit_settings.system
    else "unknown",
    "objects": [object_manifest(scene_object) for scene_object in bpy.context.scene.objects],
}}

output_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"Wrote V0.5 Scene Manifest to {{output_path}}")
'''
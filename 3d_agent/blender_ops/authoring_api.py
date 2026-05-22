"""Generate Blender-side authoring helper module source.

The returned source is written next to generated Blender execution scripts and
imported inside Blender. It is intentionally plain Python text because `bpy` is
available only in the Blender process.
"""

from __future__ import annotations


def blender_authoring_api_source() -> str:
    """Return the Blender Python source for safe non-destructive authoring helpers."""
    return r'''"""V0.9A Blender Authoring API.

This module runs inside Blender. Helpers create generated authoring objects only;
they do not edit existing mesh data or overwrite source files.
"""

from pathlib import Path

import bpy


def find_object(object_name):
    return bpy.data.objects.get(object_name)


def ensure_collection(collection_name):
    collection = bpy.data.collections.get(collection_name)
    if collection is None:
        collection = bpy.data.collections.new(collection_name)
        bpy.context.scene.collection.children.link(collection)
    return collection


def ensure_authoring_material(material_name="AI_Authoring_PanelLine", color=(0.05, 0.25, 1.0, 0.75)):
    material = bpy.data.materials.get(material_name)
    if material is None:
        material = bpy.data.materials.new(material_name)
        material.use_nodes = True
    material.diffuse_color = color
    principled = material.node_tree.nodes.get("Principled BSDF") if material.use_nodes else None
    if principled is not None:
        principled.inputs["Base Color"].default_value = color
        principled.inputs["Alpha"].default_value = color[3]
    material.blend_method = "BLEND"
    return material


def object_dimensions(target_object):
    if target_object is None:
        return (1.0, 1.0, 1.0)
    return (
        max(float(target_object.dimensions.x), 0.1),
        max(float(target_object.dimensions.y), 0.1),
        max(float(target_object.dimensions.z), 0.1),
    )


def preview_location(target_object, normalized_position=(0.0, 0.0, 0.5)):
    if target_object is None:
        return (0.0, 0.0, 0.0)
    return (
        target_object.location.x + (float(normalized_position[0]) - 0.5) * target_object.dimensions.x,
        target_object.location.y + (float(normalized_position[1]) - 0.5) * target_object.dimensions.y,
        target_object.location.z + (float(normalized_position[2]) - 0.5) * target_object.dimensions.z,
    )


def tag_generated_object(generated_object, session_id, preview_element, target_object_name, authoring_type):
    generated_object["v0_9_authoring_session_id"] = session_id
    generated_object["v0_9_authoring_type"] = authoring_type
    generated_object["source_task_id"] = preview_element.get("source_task_id", "")
    generated_object["target_object"] = target_object_name
    generated_object["element_type"] = preview_element.get("element_type", "manual_review_note")
    generated_object["target_zone"] = preview_element.get("target_zone", "unknown_zone")
    generated_object["intent"] = preview_element.get("intent", "Review this generated authoring object manually.")
    generated_object["non_destructive"] = True
    generated_object["requires_user_confirmation"] = bool(preview_element.get("requires_user_confirmation", True))


def create_panel_line_curve_guide(collection, session_id, preview_element, target_object, target_object_name):
    visual_guide = preview_element.get("visual_guide", {})
    dimensions = object_dimensions(target_object)
    placement_hint = preview_element.get("placement_hint", {})
    normalized_position = placement_hint.get("normalized_position", [0.0, 0.0, 0.5])
    line_length = max(dimensions[0], dimensions[1]) * float(visual_guide.get("line_length_factor", 0.65))
    bevel_depth = float(visual_guide.get("bevel_depth", 0.01))
    object_name = f"{session_id}_{preview_element.get('element_id', 'panel_line')}_authoring_curve"
    curve = bpy.data.curves.new(object_name, "CURVE")
    curve.dimensions = "3D"
    curve.resolution_u = 1
    curve.bevel_depth = bevel_depth
    curve["v0_9_curve_role"] = "panel_line_curve_guide"
    spline = curve.splines.new("POLY")
    spline.points.add(1)
    spline.points[0].co = (-line_length / 2, 0.0, 0.0, 1.0)
    spline.points[1].co = (line_length / 2, 0.0, 0.0, 1.0)
    generated_object = bpy.data.objects.new(object_name, curve)
    generated_object.location = preview_location(target_object, normalized_position)
    generated_object.data.materials.append(ensure_authoring_material())
    tag_generated_object(generated_object, session_id, preview_element, target_object_name, "panel_line_curve_guide")
    collection.objects.link(generated_object)
    return generated_object


def save_as_copy_only(output_blend_copy):
    output_path = Path(output_blend_copy)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.resolve() == Path(bpy.data.filepath).resolve():
        raise RuntimeError("Refusing to overwrite the source .blend file.")
    bpy.ops.wm.save_as_mainfile(filepath=str(output_path))
    return str(output_path)
'''
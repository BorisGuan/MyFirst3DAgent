"""Blender preview script draft formatter for V0.6.

The generated script is a draft for user review. It creates preview-only
generated objects in an isolated collection when the safe preview session allows
it. It does not modify bound mesh data, delete user objects, apply modifiers,
run Blender operations, or save .blend files.
"""

import json
import re
from typing import Any


def create_blender_preview_script_draft(
    geometry_preview_plan: dict[str, Any],
    safe_preview_session: dict[str, Any],
) -> str:
    """Create a conservative Blender Python preview script draft."""
    if "create_generated_preview_object" not in safe_preview_session.get("allowed_operations", []):
        return _blocked_preview_script(geometry_preview_plan, safe_preview_session)

    collection_name = _preview_collection_name(geometry_preview_plan, safe_preview_session)
    return f'''# V0.6 Blender Preview Script Draft
# This draft creates preview-only generated visual guide objects in an isolated collection.
# It does not edit bound mesh data, delete user objects, run booleans, apply modifiers, or save .blend files.
# Generated objects are tagged for review and rollback before any real modeling operation.

import json
from pathlib import Path

import bpy


geometry_preview_plan = json.loads({_json_literal(geometry_preview_plan)})
safe_preview_session = json.loads({_json_literal(safe_preview_session)})
session_id = safe_preview_session["session_id"]
collection_name = {collection_name!r}
report_path = Path(f"{{session_id}}_preview_report.json")


def preview_material(material_name):
    material = bpy.data.materials.get(material_name)
    if material is None:
        material = bpy.data.materials.new(material_name)
        material.use_nodes = True
    colors = {{
        "AI_Preview_Blue": (0.1, 0.45, 1.0, 0.55),
        "AI_Preview_Orange": (1.0, 0.48, 0.1, 0.45),
        "AI_Preview_Red": (1.0, 0.08, 0.05, 0.6),
        "AI_Preview_Yellow": (1.0, 0.85, 0.12, 0.65),
        "AI_Preview_Green": (0.15, 0.85, 0.35, 0.55),
    }}
    color = colors.get(material_name, colors["AI_Preview_Yellow"])
    material.diffuse_color = color
    principled = material.node_tree.nodes.get("Principled BSDF")
    if principled is not None:
        principled.inputs["Base Color"].default_value = color
        principled.inputs["Alpha"].default_value = color[3]
    material.blend_method = "BLEND"
    material.use_screen_refraction = True
    return material


def empty_display_type(element_type):
    display_types = {{
        "panel_line_hint": "SINGLE_ARROW",
        "surface_detail_hint": "PLAIN_AXES",
        "placeholder_volume": "CUBE",
        "mounting_point_hint": "SPHERE",
        "risk_marker": "SPHERE",
        "manual_review_note": "PLAIN_AXES",
        "symmetry_reference": "ARROWS",
    }}
    return display_types.get(element_type, "PLAIN_AXES")


def empty_display_size(element_type):
    if element_type in {{"placeholder_volume", "mounting_point_hint"}}:
        return 0.35
    if element_type == "risk_marker":
        return 0.3
    return 0.2


def preview_location(target_object, preview_element):
    if target_object is None:
        return (0.0, 0.0, 0.0)
    placement_hint = preview_element.get("placement_hint", {{}})
    normalized_position = placement_hint.get("normalized_position", [0.0, 0.0, 0.5])
    return (
        target_object.location.x + (float(normalized_position[0]) - 0.5) * target_object.dimensions.x,
        target_object.location.y + (float(normalized_position[1]) - 0.5) * target_object.dimensions.y,
        target_object.location.z + (float(normalized_position[2]) - 0.5) * target_object.dimensions.z,
    )


def guide_dimensions(target_object):
    if target_object is None:
        return (1.0, 1.0, 1.0)
    return (
        max(float(target_object.dimensions.x), 0.1),
        max(float(target_object.dimensions.y), 0.1),
        max(float(target_object.dimensions.z), 0.1),
    )


def tag_preview_object(preview_object, preview_element, target_object_name):
    preview_object["v0_6_preview_session_id"] = session_id
    preview_object["v0_8b_visual_guide"] = True
    preview_object["source_task_id"] = preview_element.get("source_task_id", "")
    preview_object["target_object"] = target_object_name
    preview_object["element_type"] = preview_element.get("element_type", "manual_review_note")
    preview_object["target_zone"] = preview_element.get("target_zone", "unknown_zone")
    preview_object["intent"] = preview_element.get("intent", "Review this generated preview object manually.")
    preview_object["requires_user_confirmation"] = bool(preview_element.get("requires_user_confirmation", True))


def create_curve_line_guide(preview_name, location, target_object, preview_element):
    visual_guide = preview_element.get("visual_guide", {{}})
    dimensions = guide_dimensions(target_object)
    line_length = max(dimensions[0], dimensions[1]) * float(visual_guide.get("line_length_factor", 0.65))
    curve = bpy.data.curves.new(preview_name, "CURVE")
    curve.dimensions = "3D"
    curve.resolution_u = 1
    curve.bevel_depth = float(visual_guide.get("bevel_depth", 0.01))
    spline = curve.splines.new("POLY")
    spline.points.add(1)
    spline.points[0].co = (-line_length / 2, 0.0, 0.0, 1.0)
    spline.points[1].co = (line_length / 2, 0.0, 0.0, 1.0)
    preview_object = bpy.data.objects.new(preview_name, curve)
    preview_object.location = location
    return preview_object


def create_blockout_guide(preview_name, location, target_object, preview_element):
    visual_guide = preview_element.get("visual_guide", {{}})
    dimensions = guide_dimensions(target_object)
    size_factor = visual_guide.get("size_factor", [0.25, 0.12, 0.08])
    mesh = bpy.data.meshes.new(f"{{preview_name}}_mesh")
    sx = dimensions[0] * float(size_factor[0])
    sy = dimensions[1] * float(size_factor[1])
    sz = dimensions[2] * float(size_factor[2])
    vertices = [
        (-sx, -sy, -sz), (sx, -sy, -sz), (sx, sy, -sz), (-sx, sy, -sz),
        (-sx, -sy, sz), (sx, -sy, sz), (sx, sy, sz), (-sx, sy, sz),
    ]
    faces = [(0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    preview_object = bpy.data.objects.new(preview_name, mesh)
    preview_object.location = location
    preview_object.display_type = "WIRE"
    return preview_object


def create_sphere_guide(preview_name, location, target_object, preview_element):
    visual_guide = preview_element.get("visual_guide", {{}})
    dimensions = guide_dimensions(target_object)
    radius = max(dimensions) * float(visual_guide.get("radius_factor", 0.08))
    mesh = bpy.data.meshes.new(f"{{preview_name}}_mesh")
    vertices = [
        (0.0, 0.0, radius), (radius, 0.0, 0.0), (0.0, radius, 0.0),
        (-radius, 0.0, 0.0), (0.0, -radius, 0.0), (0.0, 0.0, -radius),
    ]
    faces = [(0, 1, 2), (0, 2, 3), (0, 3, 4), (0, 4, 1), (5, 2, 1), (5, 3, 2), (5, 4, 3), (5, 1, 4)]
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    preview_object = bpy.data.objects.new(preview_name, mesh)
    preview_object.location = location
    preview_object.display_type = "WIRE"
    return preview_object


def create_text_guide(preview_name, location, preview_element):
    visual_guide = preview_element.get("visual_guide", {{}})
    curve = bpy.data.curves.new(preview_name, "FONT")
    curve.body = preview_element.get("element_type", "review")
    curve.size = float(visual_guide.get("text_size", 0.18))
    preview_object = bpy.data.objects.new(preview_name, curve)
    preview_object.location = location
    return preview_object


def create_visual_guide_object(preview_name, location, target_object, preview_element):
    guide_type = preview_element.get("visual_guide", {{}}).get("guide_type", "text_note")
    if guide_type == "curve_line_overlay":
        return create_curve_line_guide(preview_name, location, target_object, preview_element)
    if guide_type == "transparent_blockout":
        return create_blockout_guide(preview_name, location, target_object, preview_element)
    if guide_type in {{"annotation_disc", "anchor_sphere", "risk_sphere"}}:
        return create_sphere_guide(preview_name, location, target_object, preview_element)
    return create_text_guide(preview_name, location, preview_element)


collection = bpy.data.collections.get(collection_name)
if collection is None:
    collection = bpy.data.collections.new(collection_name)
    bpy.context.scene.collection.children.link(collection)

generated_object_names = []
generated_visual_guides = []
for preview_element in geometry_preview_plan.get("preview_elements", []):
    target_object_name = preview_element.get("target_object", "")
    target_object = bpy.data.objects.get(target_object_name)
    preview_name = f"{{session_id}}_{{preview_element.get('element_id', 'preview_element')}}"
    location = preview_location(target_object, preview_element)
    preview_object = create_visual_guide_object(preview_name, location, target_object, preview_element)
    material = preview_material(preview_element.get("visual_guide", {{}}).get("material_name", "AI_Preview_Yellow"))
    if hasattr(preview_object.data, "materials"):
        preview_object.data.materials.append(material)
    tag_preview_object(preview_object, preview_element, target_object_name)
    collection.objects.link(preview_object)
    generated_object_names.append(preview_object.name)
    generated_visual_guides.append({{
        "object_name": preview_object.name,
        "guide_type": preview_element.get("visual_guide", {{}}).get("guide_type", "text_note"),
        "target_object": target_object_name,
        "element_type": preview_element.get("element_type", "manual_review_note"),
    }})

preview_report = {{
    "session_id": session_id,
    "preview_status": geometry_preview_plan.get("preview_status"),
    "target_part": geometry_preview_plan.get("target_part"),
    "target_objects": geometry_preview_plan.get("target_objects", []),
    "generated_objects": generated_object_names,
    "generated_visual_guides": generated_visual_guides,
    "required_confirmations": geometry_preview_plan.get("required_confirmations", []),
    "safety_rules": geometry_preview_plan.get("safety_rules", []),
    "rollback_strategy": safe_preview_session.get("rollback_strategy", []),
}}
report_path.write_text(json.dumps(preview_report, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"Created {{len(generated_object_names)}} V0.6 preview objects in {{collection_name}}")
print(f"Wrote V0.6 preview report to {{report_path}}")
'''


def _blocked_preview_script(
    geometry_preview_plan: dict[str, Any],
    safe_preview_session: dict[str, Any],
) -> str:
    return f'''# V0.6 Blender Preview Script Draft
# Preview is blocked; this draft writes report data only.
# It does not create Blender objects, edit bound mesh data, run booleans, apply modifiers, or save .blend files.

import json
from pathlib import Path


geometry_preview_plan = json.loads({_json_literal(geometry_preview_plan)})
safe_preview_session = json.loads({_json_literal(safe_preview_session)})
session_id = safe_preview_session["session_id"]
report_path = Path(f"{{session_id}}_preview_report.json")

preview_report = {{
    "session_id": session_id,
    "preview_status": geometry_preview_plan.get("preview_status"),
    "target_part": geometry_preview_plan.get("target_part"),
    "blocked_by": geometry_preview_plan.get("blocked_by", []),
    "required_confirmations": geometry_preview_plan.get("required_confirmations", []),
    "rollback_strategy": safe_preview_session.get("rollback_strategy", []),
}}
report_path.write_text(json.dumps(preview_report, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"V0.6 preview blocked; wrote report to {{report_path}}")
'''


def _preview_collection_name(
    geometry_preview_plan: dict[str, Any],
    safe_preview_session: dict[str, Any],
) -> str:
    for artifact in safe_preview_session.get("generated_artifacts", []):
        if artifact.get("artifact_type") == "preview_collection" and artifact.get("artifact_name"):
            return artifact["artifact_name"]
    target_part = geometry_preview_plan.get("target_part", "unknown_part")
    return f"V06_{_safe_identifier(target_part)}_preview"


def _safe_identifier(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_]+", "_", value).strip("_") or "unknown_part"


def _json_literal(value: dict[str, Any]) -> str:
    return repr(json.dumps(value, ensure_ascii=False, indent=2))
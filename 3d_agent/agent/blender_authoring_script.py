"""Blender authoring script generator for V0.9A."""

from __future__ import annotations

import json
import re
from typing import Any


def create_blender_authoring_script(
    geometry_preview_plan: dict[str, Any],
    safe_preview_session: dict[str, Any],
) -> str:
    """Create a Blender script that uses the V0.9 authoring API for curve guides."""
    collection_name = _authoring_collection_name(geometry_preview_plan, safe_preview_session)
    return f'''# V0.9A Blender Authoring Script
# Creates non-destructive authoring curve guides for panel line preview elements.
# Does not edit target mesh data, apply modifiers, run booleans, or overwrite source files.

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from blender_authoring_api import create_panel_line_curve_guide, ensure_collection, find_object


geometry_preview_plan = json.loads({_json_literal(geometry_preview_plan)})
safe_preview_session = json.loads({_json_literal(safe_preview_session)})
session_id = safe_preview_session["session_id"]
collection_name = {collection_name!r}
report_path = Path(f"{{session_id}}_authoring_report.json")

collection = ensure_collection(collection_name)

generated_authoring_objects = []
skipped_preview_elements = []
for preview_element in geometry_preview_plan.get("preview_elements", []):
    if preview_element.get("element_type") not in {"panel_line_hint", "surface_detail_hint"}:
        skipped_preview_elements.append({{
            "element_id": preview_element.get("element_id", ""),
            "element_type": preview_element.get("element_type", "manual_review_note"),
            "reason": "v0_9a_only_authors_panel_line_curve_guides",
        }})
        continue
    target_object_name = preview_element.get("target_object", "")
    target_object = find_object(target_object_name)
    generated_object = create_panel_line_curve_guide(
        collection,
        session_id,
        preview_element,
        target_object,
        target_object_name,
    )
    generated_authoring_objects.append({{
        "object_name": generated_object.name,
        "authoring_type": "panel_line_curve_guide",
        "target_object": target_object_name,
        "element_id": preview_element.get("element_id", ""),
        "non_destructive": True,
    }})

authoring_report = {{
    "report_version": "v0_9a",
    "session_id": session_id,
    "authoring_status": "success",
    "target_part": geometry_preview_plan.get("target_part"),
    "target_objects": geometry_preview_plan.get("target_objects", []),
    "generated_authoring_objects": generated_authoring_objects,
    "skipped_preview_elements": skipped_preview_elements,
    "modified_bound_mesh": False,
    "saved_original_file": False,
}}
report_path.write_text(json.dumps(authoring_report, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"Created {{len(generated_authoring_objects)}} V0.9A authoring curve guide objects in {{collection_name}}")
print(f"Wrote V0.9A authoring report to {{report_path}}")
'''


def _authoring_collection_name(
    geometry_preview_plan: dict[str, Any],
    safe_preview_session: dict[str, Any],
) -> str:
    target_part = geometry_preview_plan.get("target_part", "unknown_part")
    session_id = safe_preview_session.get("session_id", "authoring")
    return f"V09_{_safe_identifier(target_part)}_{_safe_identifier(session_id)}_authoring"


def _safe_identifier(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_]+", "_", value).strip("_") or "unknown"


def _json_literal(value: dict[str, Any]) -> str:
    return repr(json.dumps(value, ensure_ascii=False, indent=2))
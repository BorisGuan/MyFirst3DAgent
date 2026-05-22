"""Blender script draft formatter for V0.4 Execution Packages.

The generated script is a draft for user review. It creates marker objects only
when a user deliberately runs it in Blender, and it does not modify mesh data.
"""

from typing import Any


def create_blender_script_draft(execution_package: dict[str, Any]) -> str:
    """Create a conservative Blender Python script draft from an Execution Package."""
    target_part = execution_package.get("target_part", "unknown_part")
    collection_name = f"V04_{target_part}_execution_markers"
    task_lines = []
    for task in execution_package.get("execution_tasks", []):
        task_lines.extend(_task_script_lines(task, collection_name))

    body = "\n".join(task_lines) if task_lines else "# No planned tasks were provided."
    return f'''# V0.4 Blender script draft
# This draft only creates marker empties and text notes.
# It does not edit mesh geometry, run booleans, apply modifiers, or save files.
# Review every marker before converting it into real modeling operations.

import bpy

collection_name = {collection_name!r}
collection = bpy.data.collections.get(collection_name)
if collection is None:
    collection = bpy.data.collections.new(collection_name)
    bpy.context.scene.collection.children.link(collection)

{body}
'''


def _task_script_lines(task: dict[str, Any], collection_name: str) -> list[str]:
    task_id = task.get("task_id", "task_unknown")
    task_type = task.get("task_type", "manual_review")
    target_zone = task.get("target_zone", "unknown_zone")
    instruction = task.get("instruction", "Review this task manually.")
    marker_name = f"{task_id}_{task_type}_{target_zone}"
    return [
        f"# {task_id}: {instruction}",
        f"empty = bpy.data.objects.new({marker_name!r}, None)",
        "empty.empty_display_type = 'PLAIN_AXES'",
        "empty.empty_display_size = 0.25",
        "empty.location = (0, 0, 0)",
        f"empty['v0_4_task_type'] = {task_type!r}",
        f"empty['target_zone'] = {target_zone!r}",
        f"empty['instruction'] = {instruction!r}",
        f"bpy.data.collections[{collection_name!r}].objects.link(empty)",
        "",
    ]
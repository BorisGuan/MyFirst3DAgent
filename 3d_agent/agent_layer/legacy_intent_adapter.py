"""Adapt legacy parsed intent into a TaskObject draft.

The adapter only writes Agent-owned TaskObject fields. It does not select a
Domain Operation, bind Blender objects, write runtime paths, or execute tools.
"""

from __future__ import annotations

from typing import Any

from task_object import OwnershipLayer, TaskObject, apply_owned_patch


def create_task_draft_from_legacy_intent(
    user_input: str,
    command: dict[str, str],
    legacy_intent: dict[str, Any],
) -> TaskObject:
    """Create a draft TaskObject from legacy classifier and parser output."""
    task = TaskObject()
    apply_owned_patch(
        task,
        OwnershipLayer.AGENT,
        {
            "source": {
                "user_input": user_input,
                "channel": "agent_layer",
                "metadata": {
                    "command_type": command.get("command_type", "model_edit"),
                    "confidence": command.get("confidence", "low"),
                    "reasoning": command.get("reasoning", ""),
                },
            },
            "task_type": _task_type_from_legacy_intent(legacy_intent),
            "target": {
                "semantic_part": str(legacy_intent.get("target_part", "")),
            },
            "intent": {
                "desired_effect": _desired_effect_from_legacy_intent(legacy_intent),
                "action": str(legacy_intent.get("operation") or legacy_intent.get("action") or ""),
                "detail_type": str(legacy_intent.get("detail_type", "")),
                "style": str(legacy_intent.get("style", "")),
                "density": str(legacy_intent.get("density", "")),
                "scale": str(legacy_intent.get("scale", "")),
                "symmetry": str(legacy_intent.get("symmetry", "")),
                "placement_zones": list(legacy_intent.get("placement_zones") or []),
                "parameters": {},
            },
            "constraints": {
                "notes": list(legacy_intent.get("constraints") or []),
            },
        },
    )
    return task


def _task_type_from_legacy_intent(legacy_intent: dict[str, Any]) -> str:
    detail_type = str(legacy_intent.get("detail_type", ""))
    if detail_type in {"panel_lines", "parting_lines", "armor_layers", "surface_damage", "weathering"}:
        return "surface_detail_enhancement"
    if detail_type in {"vents", "thrusters", "pipes", "hydraulic_rods", "sensors", "weapon_mounts"}:
        return "surface_detail_enhancement"
    return "model_edit"


def _desired_effect_from_legacy_intent(legacy_intent: dict[str, Any]) -> str:
    return str(
        legacy_intent.get("desired_effect")
        or legacy_intent.get("detail_type")
        or legacy_intent.get("operation")
        or legacy_intent.get("action")
        or ""
    )
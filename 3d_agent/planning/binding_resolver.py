"""Planning Binding Resolver for TaskObject targets.

The resolver maps a validated TaskObject semantic target to object names from a
read-only scene manifest or binding context. It does not open .blend files,
call bpy, modify models, select operations, or complete parameters.
"""

from __future__ import annotations

from typing import Any

from model.model_binding import create_model_binding_context
from model.scene_manifest import normalize_scene_manifest
from task_object import OwnershipLayer, TaskObject, TaskState, apply_owned_patch


class BindingResolutionError(ValueError):
    """Raised when a TaskObject target cannot be bound to a real object."""


def resolve_task_binding(
    task: TaskObject,
    scene_manifest: dict[str, Any] | None = None,
    binding_context: dict[str, Any] | None = None,
    source_manifest_ref: str = "scene_manifest",
) -> TaskObject:
    """Resolve a validated TaskObject target against a manifest or binding context."""
    if task.state != TaskState.VALIDATED:
        raise BindingResolutionError(f"TaskObject state must be 'validated', got {task.state.value!r}.")
    if not task.target.semantic_part.strip():
        raise BindingResolutionError("target.semantic_part is required for binding.")

    context = _binding_context_for(task, scene_manifest, binding_context, source_manifest_ref)
    if context.get("target_part") != task.target.semantic_part:
        raise BindingResolutionError(
            f"Binding context target_part {context.get('target_part')!r} does not match "
            f"TaskObject target.semantic_part {task.target.semantic_part!r}."
        )

    bound_names = _object_names_for_status(context, {"bound"})
    candidate_names = _object_names_for_status(context, {"bound", "candidate", "ambiguous"})
    if not bound_names:
        if candidate_names:
            raise BindingResolutionError(
                "No confirmed binding found; candidate objects: " + ", ".join(candidate_names)
            )
        raise BindingResolutionError(f"No binding candidates found for target {task.target.semantic_part!r}.")

    return apply_owned_patch(
        task,
        OwnershipLayer.PLANNING,
        {
            "state": TaskState.BOUND,
            "target": {
                "bound_object": bound_names[0],
                "binding_candidates": candidate_names,
            },
        },
    )


def _binding_context_for(
    task: TaskObject,
    scene_manifest: dict[str, Any] | None,
    binding_context: dict[str, Any] | None,
    source_manifest_ref: str,
) -> dict[str, Any]:
    if binding_context is not None:
        return binding_context
    if scene_manifest is None:
        raise BindingResolutionError("scene_manifest or binding_context is required for binding.")
    normalized_manifest = normalize_scene_manifest(scene_manifest)
    return create_model_binding_context(
        normalized_manifest,
        task.target.semantic_part,
        source_manifest_ref=source_manifest_ref,
    )


def _object_names_for_status(binding_context: dict[str, Any], statuses: set[str]) -> list[str]:
    names: list[str] = []
    for binding in binding_context.get("bindings", []):
        if binding.get("binding_status") in statuses:
            object_name = binding.get("object_name")
            if isinstance(object_name, str) and object_name:
                names.append(object_name)
    return names
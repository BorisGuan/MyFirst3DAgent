"""Planning Validator for TaskObject drafts.

The validator checks minimum draft completeness and advances the lifecycle from
draft to validated. It does not bind targets, select operations, complete
parameters, call Domain/Core/Runtime, or import Blender APIs.
"""

from __future__ import annotations

from task_object import OwnershipLayer, TaskObject, TaskState, apply_owned_patch


SUPPORTED_TASK_TYPES = frozenset({"surface_detail_enhancement"})


class PlanningValidationError(ValueError):
    """Raised when a draft TaskObject is not valid for Planning."""


def validate_draft_task(task: TaskObject) -> TaskObject:
    """Validate a draft TaskObject and advance it to validated."""
    errors = _collect_validation_errors(task)
    if errors:
        raise PlanningValidationError("Invalid TaskObject draft: " + "; ".join(errors))
    return apply_owned_patch(task, OwnershipLayer.PLANNING, {"state": TaskState.VALIDATED})


def _collect_validation_errors(task: TaskObject) -> list[str]:
    errors: list[str] = []
    if task.state != TaskState.DRAFT:
        errors.append(f"state must be 'draft', got {task.state.value!r}")
    if not task.source.user_input.strip():
        errors.append("source.user_input is required")
    if task.task_type not in SUPPORTED_TASK_TYPES:
        errors.append(f"task_type must be one of {sorted(SUPPORTED_TASK_TYPES)}, got {task.task_type!r}")
    if not task.target.semantic_part.strip():
        errors.append("target.semantic_part is required")

    intent_errors = _collect_intent_errors(task)
    errors.extend(intent_errors)
    return errors


def _collect_intent_errors(task: TaskObject) -> list[str]:
    required_fields = {
        "desired_effect": task.intent.desired_effect,
        "style": task.intent.style,
        "density": task.intent.density,
        "scale": task.intent.scale,
    }
    return [f"intent.{field_name} is required" for field_name, value in required_fields.items() if not str(value).strip()]
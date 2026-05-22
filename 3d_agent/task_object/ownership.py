"""TaskObject field ownership guard.

This module checks which architecture layer may patch which TaskObject fields.
It does not call Agent, Planning, Domain, Core, Runtime, Blender, or report
systems.
"""

from __future__ import annotations

from dataclasses import is_dataclass
from enum import Enum
from typing import Any

from task_object.lifecycle import validate_transition
from task_object.schema import TaskObject, TaskState


class OwnershipLayer(str, Enum):
    AGENT = "agent"
    PLANNING = "planning"
    RUNTIME = "runtime"
    REPORTING = "reporting"
    DOMAIN = "domain"


class TaskOwnershipError(PermissionError):
    """Raised when a layer attempts to modify a field it does not own."""


_OWNED_FIELD_PREFIXES: dict[OwnershipLayer, tuple[str, ...]] = {
    OwnershipLayer.AGENT: (
        "source",
        "task_type",
        "target.semantic_part",
        "intent",
        "constraints",
    ),
    OwnershipLayer.PLANNING: (
        "target.bound_object",
        "target.binding_candidates",
        "planning",
        "execution_policy",
    ),
    OwnershipLayer.RUNTIME: (
        "runtime",
        "result",
    ),
    OwnershipLayer.REPORTING: (
        "artifact_refs",
    ),
    OwnershipLayer.DOMAIN: (),
}

_OWNED_STATE_VALUES: dict[OwnershipLayer, frozenset[TaskState]] = {
    OwnershipLayer.AGENT: frozenset({TaskState.DRAFT}),
    OwnershipLayer.PLANNING: frozenset(
        {
            TaskState.VALIDATED,
            TaskState.BOUND,
            TaskState.PLANNED,
            TaskState.READY_TO_EXECUTE,
            TaskState.FAILED,
        }
    ),
    OwnershipLayer.RUNTIME: frozenset({TaskState.EXECUTING, TaskState.COMPLETED, TaskState.FAILED}),
    OwnershipLayer.REPORTING: frozenset(),
    OwnershipLayer.DOMAIN: frozenset(),
}


def owned_paths(owner: OwnershipLayer | str) -> tuple[str, ...]:
    """Return direct field prefixes owned by a layer."""
    layer = _coerce_owner(owner)
    return _OWNED_FIELD_PREFIXES[layer]


def validate_patch_owner(
    owner: OwnershipLayer | str,
    patch: dict[str, Any],
    task: TaskObject | None = None,
) -> None:
    """Validate that owner may modify every field path in patch."""
    layer = _coerce_owner(owner)
    for field_path, value in _flatten_patch(patch):
        if field_path == "state":
            _validate_state_owner(layer, value, task)
            continue
        if not _owns_field_path(layer, field_path):
            raise TaskOwnershipError(
                f"{layer.value} layer cannot modify TaskObject field {field_path!r}."
            )


def apply_owned_patch(
    task: TaskObject,
    owner: OwnershipLayer | str,
    patch: dict[str, Any],
) -> TaskObject:
    """Validate and apply an owned patch to a TaskObject."""
    validate_patch_owner(owner, patch, task=task)
    for field_path, value in _flatten_patch(patch):
        if field_path == "state":
            task.state = _coerce_state(value)
        else:
            _assign_path(task, field_path, value)
    return task


def _coerce_owner(owner: OwnershipLayer | str) -> OwnershipLayer:
    if isinstance(owner, OwnershipLayer):
        return owner
    normalized = str(owner).strip().lower().replace(" layer", "").replace("_layer", "")
    try:
        return OwnershipLayer(normalized)
    except ValueError as error:
        raise TaskOwnershipError(f"Unknown TaskObject owner: {owner!r}.") from error


def _flatten_patch(patch: dict[str, Any], prefix: str = "") -> list[tuple[str, Any]]:
    if not isinstance(patch, dict):
        raise TypeError("TaskObject patch must be a dictionary.")
    items: list[tuple[str, Any]] = []
    for key, value in patch.items():
        field_path = f"{prefix}.{key}" if prefix else str(key)
        if isinstance(value, dict) and value and not _is_dict_leaf(field_path):
            items.extend(_flatten_patch(value, field_path))
        else:
            items.append((field_path, value))
    return items


def _is_dict_leaf(field_path: str) -> bool:
    return field_path in {
        "source.metadata",
        "intent.parameters",
        "planning.parameters",
        "result.artifacts",
        "artifact_refs",
    }


def _owns_field_path(layer: OwnershipLayer, field_path: str) -> bool:
    return any(
        field_path == prefix or field_path.startswith(f"{prefix}.")
        for prefix in _OWNED_FIELD_PREFIXES[layer]
    )


def _validate_state_owner(
    layer: OwnershipLayer,
    value: Any,
    task: TaskObject | None,
) -> None:
    next_state = _coerce_state(value)
    if next_state not in _OWNED_STATE_VALUES[layer]:
        raise TaskOwnershipError(
            f"{layer.value} layer cannot modify TaskObject field 'state' to {next_state.value!r}."
        )
    if task is not None:
        validate_transition(task.state, next_state)


def _coerce_state(value: Any) -> TaskState:
    if isinstance(value, TaskState):
        return value
    try:
        return TaskState(str(value))
    except ValueError as error:
        raise TaskOwnershipError(f"Unknown TaskState for ownership patch: {value!r}.") from error


def _assign_path(target: Any, field_path: str, value: Any) -> None:
    parts = field_path.split(".")
    current = target
    for part in parts[:-1]:
        if isinstance(current, dict):
            current = current[part]
        else:
            current = getattr(current, part)
    final_part = parts[-1]
    if isinstance(current, dict):
        current[final_part] = value
    elif is_dataclass(current):
        setattr(current, final_part, value)
    else:
        setattr(current, final_part, value)
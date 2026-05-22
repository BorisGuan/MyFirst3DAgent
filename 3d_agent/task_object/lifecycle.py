"""Lifecycle state transition rules for TaskObject.

This module validates state movement only. It does not implement TaskStore,
retry behavior, Runtime orchestration, or external side effects.
"""

from __future__ import annotations

from typing import Any

from task_object.schema import TaskObject, TaskState


class TaskStateTransitionError(ValueError):
    """Raised when a TaskObject state transition is not allowed."""


_ALLOWED_TRANSITIONS: dict[TaskState, frozenset[TaskState]] = {
    TaskState.DRAFT: frozenset({TaskState.VALIDATED}),
    TaskState.VALIDATED: frozenset({TaskState.BOUND, TaskState.FAILED}),
    TaskState.BOUND: frozenset({TaskState.PLANNED, TaskState.FAILED}),
    TaskState.PLANNED: frozenset({TaskState.READY_TO_EXECUTE, TaskState.FAILED}),
    TaskState.READY_TO_EXECUTE: frozenset({TaskState.EXECUTING, TaskState.FAILED}),
    TaskState.EXECUTING: frozenset({TaskState.COMPLETED, TaskState.FAILED}),
    TaskState.COMPLETED: frozenset(),
    TaskState.FAILED: frozenset(),
}


def allowed_next_states(current_state: TaskState | str) -> tuple[TaskState, ...]:
    """Return the states that may directly follow current_state."""
    state = _coerce_state(current_state)
    return tuple(_ALLOWED_TRANSITIONS[state])


def can_transition(current_state: TaskState | str, next_state: TaskState | str) -> bool:
    """Return whether a direct state transition is allowed."""
    current = _coerce_state(current_state)
    next_value = _coerce_state(next_state)
    return next_value in _ALLOWED_TRANSITIONS[current]


def validate_transition(current_state: TaskState | str, next_state: TaskState | str) -> None:
    """Raise a clear error if a direct state transition is invalid."""
    current = _coerce_state(current_state)
    next_value = _coerce_state(next_state)
    if next_value not in _ALLOWED_TRANSITIONS[current]:
        allowed_values = sorted(state.value for state in _ALLOWED_TRANSITIONS[current])
        allowed_text = ", ".join(allowed_values) if allowed_values else "no next states"
        raise TaskStateTransitionError(
            f"Cannot transition TaskObject from {current.value!r} to {next_value.value!r}; "
            f"allowed: {allowed_text}."
        )


def transition_task(task: TaskObject, next_state: TaskState | str) -> TaskObject:
    """Validate and apply a state transition to a TaskObject."""
    validate_transition(task.state, next_state)
    task.state = _coerce_state(next_state)
    return task


def _coerce_state(value: TaskState | str | Any) -> TaskState:
    if isinstance(value, TaskState):
        return value
    try:
        return TaskState(str(value))
    except ValueError as error:
        raise TaskStateTransitionError(f"Unknown TaskState: {value!r}.") from error
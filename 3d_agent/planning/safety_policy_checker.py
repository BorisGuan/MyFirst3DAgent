"""Planning Safety Policy Checker for TaskObject execution readiness.

The checker validates that a planned TaskObject can only proceed under the
current safe, non-destructive policy. It does not execute operations, call
Domain handlers, call Core API, write files, or call Blender APIs.
"""

from __future__ import annotations

from pathlib import Path

from task_object import OwnershipLayer, TaskObject, TaskState, apply_owned_patch


SAFE_EXECUTION_MODE = "safe_non_destructive"


class SafetyPolicyError(ValueError):
    """Raised when a TaskObject does not satisfy execution safety policy."""


def check_safety_policy(task: TaskObject) -> TaskObject:
    """Validate safety policy and advance a planned TaskObject to ready_to_execute."""
    if task.state != TaskState.PLANNED:
        raise SafetyPolicyError(f"TaskObject state must be 'planned', got {task.state.value!r}.")
    if not task.planning.selected_operation:
        raise SafetyPolicyError("planning.selected_operation is required before safety policy approval.")
    if not task.planning.parameters:
        raise SafetyPolicyError("planning.parameters are required before safety policy approval.")

    _validate_safe_constraints(task)
    _validate_execution_policy(task)
    _validate_output_copy_does_not_overwrite_source(task)

    reasoning = list(task.planning.reasoning)
    reasoning.append("Safety policy approved for safe_non_destructive execution with output copy and report artifact.")
    return apply_owned_patch(
        task,
        OwnershipLayer.PLANNING,
        {
            "state": TaskState.READY_TO_EXECUTE,
            "execution_policy": {
                "mode": SAFE_EXECUTION_MODE,
                "preserve_source_file": True,
            },
            "planning": {
                "reasoning": reasoning,
            },
        },
    )


def _validate_safe_constraints(task: TaskObject) -> None:
    if not task.constraints.preserve_source_file:
        raise SafetyPolicyError("constraints.preserve_source_file must be true.")
    if not task.constraints.non_destructive:
        raise SafetyPolicyError("constraints.non_destructive must be true.")
    if task.constraints.mesh_edit_allowed:
        raise SafetyPolicyError("Destructive mesh edit is not allowed by the current safety policy.")


def _validate_execution_policy(task: TaskObject) -> None:
    if task.execution_policy.mode != SAFE_EXECUTION_MODE:
        raise SafetyPolicyError(
            f"execution_policy.mode must be {SAFE_EXECUTION_MODE!r}, got {task.execution_policy.mode!r}."
        )
    if not task.execution_policy.preserve_source_file:
        raise SafetyPolicyError("execution_policy.preserve_source_file must be true.")
    if not task.execution_policy.output_blend_copy:
        raise SafetyPolicyError("execution_policy.output_blend_copy is required for real execution.")
    if not task.execution_policy.report_file:
        raise SafetyPolicyError("execution_policy.report_file is required for report artifact tracking.")


def _validate_output_copy_does_not_overwrite_source(task: TaskObject) -> None:
    source_blend_file = _source_blend_file(task)
    if not source_blend_file:
        return
    if _path_key(task.execution_policy.output_blend_copy) == _path_key(source_blend_file):
        raise SafetyPolicyError("execution_policy.output_blend_copy must not overwrite the source .blend file.")


def _source_blend_file(task: TaskObject) -> str | None:
    if task.runtime.source_blend_file:
        return task.runtime.source_blend_file
    source_metadata = task.source.metadata
    for key in ("source_blend_file", "blend_file", "input_blend_file"):
        value = source_metadata.get(key)
        if value:
            return str(value)
    return None


def _path_key(path_value: str | None) -> str:
    if not path_value:
        return ""
    return str(Path(path_value).expanduser().resolve(strict=False)).rstrip("\\/").casefold()
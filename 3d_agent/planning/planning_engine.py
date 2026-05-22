"""Planning Engine for TaskObject lifecycle preparation.

The engine composes the Planning Layer stages. It does not execute model
changes, call Core APIs, write artifacts, or call Blender APIs.
"""

from __future__ import annotations

from typing import Any

from planning.binding_resolver import BindingResolutionError, resolve_task_binding
from planning.operation_selector import OperationSelectionError, select_operation
from planning.parameter_completer import ParameterCompletionError, complete_parameters
from planning.safety_policy_checker import SafetyPolicyError, check_safety_policy
from planning.validator import PlanningValidationError, validate_draft_task
from task_object import TaskObject


class PlanningEngineError(ValueError):
    """Raised when a Planning Engine stage fails."""

    def __init__(self, stage: str, original_error: Exception) -> None:
        self.stage = stage
        self.original_error = original_error
        super().__init__(f"Planning Engine failed during {stage}: {original_error}")


def plan_task(
    task: TaskObject,
    scene_manifest: dict[str, Any] | None = None,
    binding_context: dict[str, Any] | None = None,
    registry: Any | None = None,
    source_manifest_ref: str = "scene_manifest",
) -> TaskObject:
    """Run a draft TaskObject through Planning until it is ready_to_execute."""
    try:
        validate_draft_task(task)
    except PlanningValidationError as error:
        raise PlanningEngineError("validation", error) from error

    try:
        resolve_task_binding(
            task,
            scene_manifest=scene_manifest,
            binding_context=binding_context,
            source_manifest_ref=source_manifest_ref,
        )
    except BindingResolutionError as error:
        raise PlanningEngineError("binding", error) from error

    try:
        select_operation(task, registry=registry)
    except OperationSelectionError as error:
        raise PlanningEngineError("operation_selection", error) from error

    try:
        complete_parameters(task, registry=registry)
    except ParameterCompletionError as error:
        raise PlanningEngineError("parameter_completion", error) from error

    try:
        check_safety_policy(task)
    except SafetyPolicyError as error:
        raise PlanningEngineError("safety_policy", error) from error

    return task
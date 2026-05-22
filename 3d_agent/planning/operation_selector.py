"""Planning Operation Selector for TaskObject.

The selector chooses a registered Domain Operation for a bound TaskObject. It
does not call Domain handlers, create Blender modifier names, complete
parameters, read CLI arguments, call Core API, or import Blender APIs.
"""

from __future__ import annotations

from domain import OperationRegistry, default_operation_registry
from task_object import OwnershipLayer, TaskObject, TaskState, apply_owned_patch


class OperationSelectionError(ValueError):
    """Raised when Planning cannot select a supported operation."""


def select_operation(
    task: TaskObject,
    registry: OperationRegistry | None = None,
) -> TaskObject:
    """Select a Domain Operation for a bound TaskObject through the registry."""
    if task.state != TaskState.BOUND:
        raise OperationSelectionError(f"TaskObject state must be 'bound', got {task.state.value!r}.")
    if not task.target.bound_object:
        raise OperationSelectionError("target.bound_object is required before operation selection.")

    operation_registry = registry or default_operation_registry()
    supported_specs = operation_registry.supported_for_task_type(task.task_type)
    if not supported_specs:
        raise OperationSelectionError(f"No registered operation supports task_type {task.task_type!r}.")

    compatible_specs = [
        operation_spec
        for operation_spec in supported_specs
        if operation_spec.required_target_state == task.state.value
        and operation_spec.safety_level == task.execution_policy.mode
    ]
    if not compatible_specs:
        raise OperationSelectionError(
            f"No registered operation supports task_type {task.task_type!r}, "
            f"state {task.state.value!r}, and execution_policy.mode {task.execution_policy.mode!r}."
        )

    selected_spec = compatible_specs[0]
    return apply_owned_patch(
        task,
        OwnershipLayer.PLANNING,
        {
            "planning": {
                "selected_operation": selected_spec.name,
                "reasoning": [
                    f"Selected {selected_spec.name} because task_type={task.task_type}, "
                    f"state={task.state.value}, and execution_policy.mode={task.execution_policy.mode} "
                    "match the operation registry."
                ],
            },
        },
    )
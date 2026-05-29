"""Planning Parameter Completer for TaskObject operations.

The completer fills operation parameters from the selected operation contract
and explicit intent parameters. It does not call Domain handlers, Core API,
Runtime, report systems, or Blender APIs.
"""

from __future__ import annotations

from typing import Any

from domain import OperationRegistry, OperationRegistryError, OperationSpec, default_operation_registry
from task_object import OwnershipLayer, TaskObject, TaskState, apply_owned_patch


class ParameterCompletionError(ValueError):
    """Raised when Planning cannot complete valid operation parameters."""


_PLANNING_ONLY_INTENT_PARAMETERS = frozenset({"operation"})


def complete_parameters(
    task: TaskObject,
    registry: OperationRegistry | None = None,
) -> TaskObject:
    """Complete selected operation parameters and advance TaskObject to planned."""
    if task.state != TaskState.BOUND:
        raise ParameterCompletionError(f"TaskObject state must be 'bound', got {task.state.value!r}.")
    if not task.planning.selected_operation:
        raise ParameterCompletionError("planning.selected_operation is required before parameter completion.")

    operation_registry = registry or default_operation_registry()
    operation_spec = _operation_spec(operation_registry, task.planning.selected_operation)
    if operation_spec.required_target_state != task.state.value:
        raise ParameterCompletionError(
            f"Operation {operation_spec.name!r} requires target state {operation_spec.required_target_state!r}, "
            f"got {task.state.value!r}."
        )

    parameters = _complete_parameters(operation_spec, task.intent.parameters)
    reasoning = list(task.planning.reasoning)
    reasoning.append(f"Completed parameters for {operation_spec.name}: {sorted(parameters)}.")
    return apply_owned_patch(
        task,
        OwnershipLayer.PLANNING,
        {
            "state": TaskState.PLANNED,
            "planning": {
                "parameters": parameters,
                "reasoning": reasoning,
            },
        },
    )


def _operation_spec(registry: OperationRegistry, operation_name: str) -> OperationSpec:
    try:
        return registry.get(operation_name)
    except OperationRegistryError as error:
        raise ParameterCompletionError(str(error)) from error


def _complete_parameters(operation_spec: OperationSpec, explicit_parameters: dict[str, Any]) -> dict[str, Any]:
    parameters = dict(operation_spec.default_parameters)
    for name, value in (explicit_parameters or {}).items():
        if name in _PLANNING_ONLY_INTENT_PARAMETERS:
            continue
        if name not in operation_spec.parameter_schema:
            raise ParameterCompletionError(f"Unsupported parameter for {operation_spec.name!r}: {name!r}.")
        parameters[name] = value

    for name, schema in operation_spec.parameter_schema.items():
        if name not in parameters:
            raise ParameterCompletionError(f"Missing required parameter for {operation_spec.name!r}: {name!r}.")
        _validate_parameter(operation_spec.name, name, parameters[name], schema)
    return parameters


def _validate_parameter(operation_name: str, name: str, value: Any, schema: dict[str, Any]) -> None:
    parameter_type = schema.get("type")
    if parameter_type == "number":
        _validate_number(operation_name, name, value, schema)
        return
    if parameter_type == "string":
        _validate_string(operation_name, name, value, schema)
        return
    raise ParameterCompletionError(f"Unsupported parameter schema type for {operation_name!r}.{name}: {parameter_type!r}.")


def _validate_number(operation_name: str, name: str, value: Any, schema: dict[str, Any]) -> None:
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise ParameterCompletionError(f"Parameter {operation_name!r}.{name} must be a number.")
    minimum = schema.get("exclusive_minimum")
    if minimum is not None and float(value) <= float(minimum):
        raise ParameterCompletionError(f"Parameter {operation_name!r}.{name} must be greater than {minimum}.")


def _validate_string(operation_name: str, name: str, value: Any, schema: dict[str, Any]) -> None:
    if not isinstance(value, str):
        raise ParameterCompletionError(f"Parameter {operation_name!r}.{name} must be a string.")
    allowed_values = schema.get("enum")
    if allowed_values and value not in allowed_values:
        raise ParameterCompletionError(
            f"Parameter {operation_name!r}.{name} must be one of {list(allowed_values)}, got {value!r}."
        )
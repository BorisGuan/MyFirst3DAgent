"""Planning Operation Selector for TaskObject.

The selector chooses a registered Domain Operation for a bound TaskObject. It
does not call Domain handlers, create Blender modifier names, complete
parameters, read CLI arguments, call Core API, or import Blender APIs.
"""

from __future__ import annotations

from domain import OperationRegistry, OperationSpec, default_operation_registry
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

    compatible_specs = _compatible_specs(task, supported_specs)
    if not compatible_specs:
        raise OperationSelectionError(
            f"No registered operation supports task_type {task.task_type!r}, "
            f"state {task.state.value!r}, and execution_policy.mode {task.execution_policy.mode!r}."
        )

    selected_spec, reasoning = _select_from_compatible_specs(task, compatible_specs)
    return apply_owned_patch(
        task,
        OwnershipLayer.PLANNING,
        {
            "planning": {
                "selected_operation": selected_spec.name,
                "reasoning": [reasoning],
            },
        },
    )


def _compatible_specs(task: TaskObject, supported_specs: tuple[OperationSpec, ...]) -> list[OperationSpec]:
    return [
        operation_spec
        for operation_spec in supported_specs
        if operation_spec.required_target_state == task.state.value
        and operation_spec.safety_level == task.execution_policy.mode
    ]


def _select_from_compatible_specs(
    task: TaskObject,
    compatible_specs: list[OperationSpec],
) -> tuple[OperationSpec, str]:
    explicit_operation = _explicit_operation_name(task)
    if explicit_operation:
        return _select_explicit_operation(task, compatible_specs, explicit_operation)

    if len(compatible_specs) == 1:
        selected_spec = compatible_specs[0]
        return selected_spec, _compatibility_reason(task, selected_spec)

    scored_specs = [(_score_operation(task, operation_spec), operation_spec) for operation_spec in compatible_specs]
    best_score = max(score for score, _operation_spec in scored_specs)
    if best_score <= 0:
        operation_names = ", ".join(operation_spec.name for operation_spec in compatible_specs)
        raise OperationSelectionError(
            "Operation selection is ambiguous because intent did not match any compatible operation: "
            f"{operation_names}."
        )

    best_specs = [operation_spec for score, operation_spec in scored_specs if score == best_score]
    sorted_best_specs = sorted(best_specs, key=lambda operation_spec: (operation_spec.priority, operation_spec.name))
    selected_spec = sorted_best_specs[0]
    tied_specs = [
        operation_spec
        for operation_spec in sorted_best_specs
        if operation_spec.priority == selected_spec.priority
    ]
    if len(tied_specs) > 1:
        operation_names = ", ".join(operation_spec.name for operation_spec in tied_specs)
        raise OperationSelectionError(
            "Operation selection is ambiguous because multiple compatible operations have the same intent score "
            f"and priority: {operation_names}."
        )

    return selected_spec, _scored_reason(task, selected_spec, best_score)


def _select_explicit_operation(
    task: TaskObject,
    compatible_specs: list[OperationSpec],
    explicit_operation: str,
) -> tuple[OperationSpec, str]:
    for operation_spec in compatible_specs:
        if operation_spec.name == explicit_operation:
            return operation_spec, _explicit_reason(task, operation_spec)
    operation_names = ", ".join(operation_spec.name for operation_spec in compatible_specs)
    raise OperationSelectionError(
        f"Explicit operation {explicit_operation!r} is not compatible with task_type {task.task_type!r}, "
        f"state {task.state.value!r}, and execution_policy.mode {task.execution_policy.mode!r}. "
        f"Compatible operations: {operation_names}."
    )


def _explicit_operation_name(task: TaskObject) -> str | None:
    operation_name = task.intent.parameters.get("operation")
    if operation_name is None:
        return None
    normalized_name = str(operation_name).strip()
    return normalized_name or None


def _score_operation(task: TaskObject, operation_spec: OperationSpec) -> int:
    score = 0
    if _matches(task.intent.action, operation_spec.intent_actions):
        score += 40
    if _matches(task.intent.detail_type, operation_spec.intent_detail_types):
        score += 30
    if _matches(task.intent.desired_effect, operation_spec.intent_effects):
        score += 20
    return score


def _matches(value: str, candidates: tuple[str, ...]) -> bool:
    return bool(value and value in candidates)


def _compatibility_reason(task: TaskObject, operation_spec: OperationSpec) -> str:
    return (
        f"Selected {operation_spec.name} because task_type={task.task_type}, "
        f"state={task.state.value}, and execution_policy.mode={task.execution_policy.mode} "
        "match the operation registry."
    )


def _explicit_reason(task: TaskObject, operation_spec: OperationSpec) -> str:
    return (
        f"Selected {operation_spec.name} because task.intent.parameters['operation'] explicitly requested it "
        f"and task_type={task.task_type}, state={task.state.value}, and "
        f"execution_policy.mode={task.execution_policy.mode} match the operation registry."
    )


def _scored_reason(task: TaskObject, operation_spec: OperationSpec, score: int) -> str:
    matched_fields = _matched_intent_fields(task, operation_spec)
    return (
        f"Selected {operation_spec.name} with intent score {score} because "
        f"{', '.join(matched_fields)} matched the operation registry."
    )


def _matched_intent_fields(task: TaskObject, operation_spec: OperationSpec) -> list[str]:
    matched_fields = []
    if _matches(task.intent.action, operation_spec.intent_actions):
        matched_fields.append(f"intent.action={task.intent.action}")
    if _matches(task.intent.detail_type, operation_spec.intent_detail_types):
        matched_fields.append(f"intent.detail_type={task.intent.detail_type}")
    if _matches(task.intent.desired_effect, operation_spec.intent_effects):
        matched_fields.append(f"intent.desired_effect={task.intent.desired_effect}")
    return matched_fields
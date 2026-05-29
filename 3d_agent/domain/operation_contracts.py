"""Static Domain Operation contracts.

These contracts describe available operations and the minimal data exchanged
with Domain Operations. They do not import or call Blender, Core API, Runtime,
or Domain Operation handlers.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


class DomainOperationContractError(ValueError):
    """Raised when Domain Operation contract data is incomplete or unsafe."""


@dataclass(frozen=True)
class OperationSpec:
    name: str
    supported_task_types: tuple[str, ...]
    required_target_state: str
    default_parameters: dict[str, Any] = field(default_factory=dict)
    parameter_schema: dict[str, Any] = field(default_factory=dict)
    safety_level: str = "safe_non_destructive"
    handler_name: str = ""
    report_schema: dict[str, Any] = field(default_factory=dict)
    intent_actions: tuple[str, ...] = ()
    intent_detail_types: tuple[str, ...] = ()
    intent_effects: tuple[str, ...] = ()
    priority: int = 100

    def supports_task_type(self, task_type: str) -> bool:
        """Return whether this operation supports task_type."""
        return task_type in self.supported_task_types

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable operation contract."""
        return {
            "name": self.name,
            "supported_task_types": list(self.supported_task_types),
            "required_target_state": self.required_target_state,
            "default_parameters": dict(self.default_parameters),
            "parameter_schema": dict(self.parameter_schema),
            "safety_level": self.safety_level,
            "handler_name": self.handler_name,
            "report_schema": dict(self.report_schema),
            "intent_actions": list(self.intent_actions),
            "intent_detail_types": list(self.intent_detail_types),
            "intent_effects": list(self.intent_effects),
            "priority": self.priority,
        }


@dataclass(frozen=True)
class DomainOperationInput:
    task_id: str
    operation: str
    target_object: str
    parameters: dict[str, Any] = field(default_factory=dict)
    execution_policy: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _require_non_empty_string("task_id", self.task_id)
        _require_non_empty_string("operation", self.operation)
        _require_non_empty_string("target_object", self.target_object)
        _require_dict("parameters", self.parameters)
        _require_dict("execution_policy", self.execution_policy)
        _reject_execution_artifact_fields(self.execution_policy)
        object.__setattr__(self, "parameters", dict(self.parameters))
        object.__setattr__(self, "execution_policy", dict(self.execution_policy))

    @classmethod
    def from_task_object(cls, task: Any) -> "DomainOperationInput":
        """Build minimal Domain Operation input from a ready planning result."""
        if _state_value(getattr(task, "state", None)) != "ready_to_execute":
            raise DomainOperationContractError("Task state must be 'ready_to_execute' for DomainOperationInput.")

        target = _required_attr(task, "target")
        planning = _required_attr(task, "planning")
        return cls(
            task_id=str(_required_attr(task, "task_id")),
            operation=str(_required_attr(planning, "selected_operation")),
            target_object=str(_required_attr(target, "bound_object")),
            parameters=dict(_required_attr(planning, "parameters")),
            execution_policy=_domain_execution_policy(_required_attr(task, "execution_policy")),
        )

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable minimal Domain Operation input."""
        return {
            "task_id": self.task_id,
            "operation": self.operation,
            "target_object": self.target_object,
            "parameters": dict(self.parameters),
            "execution_policy": dict(self.execution_policy),
        }


@dataclass(frozen=True)
class OperationOutcome:
    operation: str
    target_object: str
    success: bool
    changed_objects: list[str] = field(default_factory=list)
    modifier_info: dict[str, Any] = field(default_factory=dict)
    mesh_data_applied: bool = False
    diagnostics: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        _require_non_empty_string("operation", self.operation)
        _require_non_empty_string("target_object", self.target_object)
        if not isinstance(self.success, bool):
            raise DomainOperationContractError("success must be a boolean.")
        if not isinstance(self.mesh_data_applied, bool):
            raise DomainOperationContractError("mesh_data_applied must be a boolean.")
        _require_string_list("changed_objects", self.changed_objects)
        _require_dict("modifier_info", self.modifier_info)
        _require_string_list("diagnostics", self.diagnostics)
        object.__setattr__(self, "changed_objects", list(self.changed_objects))
        object.__setattr__(self, "modifier_info", dict(self.modifier_info))
        object.__setattr__(self, "diagnostics", list(self.diagnostics))

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable Domain Operation outcome."""
        return {
            "operation": self.operation,
            "target_object": self.target_object,
            "success": self.success,
            "changed_objects": list(self.changed_objects),
            "modifier_info": dict(self.modifier_info),
            "mesh_data_applied": self.mesh_data_applied,
            "diagnostics": list(self.diagnostics),
        }


def _domain_execution_policy(execution_policy: Any) -> dict[str, Any]:
    return {
        "mode": _required_attr(execution_policy, "mode"),
        "preserve_source_file": _required_attr(execution_policy, "preserve_source_file"),
    }


def _required_attr(source: Any, name: str) -> Any:
    value = getattr(source, name, None)
    if value is None or value == "" or value == {}:
        raise DomainOperationContractError(f"{name} is required for DomainOperationInput.")
    return value


def _state_value(value: Any) -> str:
    return str(getattr(value, "value", value))


def _require_non_empty_string(field_name: str, value: Any) -> None:
    if not isinstance(value, str) or not value.strip():
        raise DomainOperationContractError(f"{field_name} must be a non-empty string.")


def _require_dict(field_name: str, value: Any) -> None:
    if not isinstance(value, dict):
        raise DomainOperationContractError(f"{field_name} must be a dictionary.")


def _require_string_list(field_name: str, value: Any) -> None:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise DomainOperationContractError(f"{field_name} must be a list of strings.")


def _reject_execution_artifact_fields(execution_policy: dict[str, Any]) -> None:
    disallowed_fields = {
        "output_blend_copy",
        "output_blend_path",
        "output_file",
        "report_file",
        "report_path",
        "preview",
        "preview_file",
        "log_file",
        "logs",
    }
    unsafe_fields = sorted(field for field in execution_policy if field in disallowed_fields)
    if unsafe_fields:
        raise DomainOperationContractError(
            "DomainOperationInput.execution_policy cannot include artifact paths: " + ", ".join(unsafe_fields)
        )
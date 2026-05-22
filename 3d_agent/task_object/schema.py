"""TaskObject schema for the state-based agent architecture.

This module defines data containers only. It does not call Agent, Planning,
Domain, Core, Runtime, Blender, or report systems.
"""

from __future__ import annotations

from dataclasses import dataclass, field, fields, is_dataclass
from enum import Enum
from typing import Any, TypeVar
from uuid import uuid4


class TaskState(str, Enum):
    """Supported TaskObject lifecycle states."""

    DRAFT = "draft"
    VALIDATED = "validated"
    BOUND = "bound"
    PLANNED = "planned"
    READY_TO_EXECUTE = "ready_to_execute"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class TaskSource:
    user_input: str = ""
    channel: str = "unknown"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class TaskTarget:
    semantic_part: str = ""
    bound_object: str | None = None
    binding_candidates: list[str] = field(default_factory=list)


@dataclass
class TaskIntent:
    desired_effect: str = ""
    action: str = ""
    detail_type: str = ""
    style: str = ""
    density: str = ""
    scale: str = ""
    symmetry: str = ""
    placement_zones: list[str] = field(default_factory=list)
    parameters: dict[str, Any] = field(default_factory=dict)


@dataclass
class TaskConstraints:
    preserve_source_file: bool = True
    non_destructive: bool = True
    mesh_edit_allowed: bool = False
    notes: list[str] = field(default_factory=list)


@dataclass
class ExecutionPolicy:
    mode: str = "safe_non_destructive"
    preserve_source_file: bool = True
    output_blend_copy: str | None = None
    report_file: str | None = None


@dataclass
class TaskPlanning:
    selected_operation: str | None = None
    parameters: dict[str, Any] = field(default_factory=dict)
    reasoning: list[str] = field(default_factory=list)


@dataclass
class TaskRuntime:
    source_blend_file: str | None = None
    output_blend_copy: str | None = None
    report_file: str | None = None
    started_at: str | None = None
    finished_at: str | None = None


@dataclass
class TaskResult:
    success: bool | None = None
    summary: str = ""
    report_file: str | None = None
    artifacts: dict[str, str] = field(default_factory=dict)


@dataclass
class TaskObject:
    task_id: str = field(default_factory=lambda: str(uuid4()))
    task_version: str = "task_object_v1"
    state: TaskState = TaskState.DRAFT
    source: TaskSource = field(default_factory=TaskSource)
    task_type: str = "model_edit"
    target: TaskTarget = field(default_factory=TaskTarget)
    intent: TaskIntent = field(default_factory=TaskIntent)
    constraints: TaskConstraints = field(default_factory=TaskConstraints)
    execution_policy: ExecutionPolicy = field(default_factory=ExecutionPolicy)
    planning: TaskPlanning = field(default_factory=TaskPlanning)
    runtime: TaskRuntime = field(default_factory=TaskRuntime)
    result: TaskResult = field(default_factory=TaskResult)
    diagnostics: list[str] = field(default_factory=list)
    artifact_refs: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable representation of the task."""
        return _to_plain_data(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TaskObject":
        """Build a TaskObject from a dictionary produced by to_dict()."""
        target_data = _normalize_target_data(data.get("target"))
        return cls(
            task_id=str(data.get("task_id") or uuid4()),
            task_version=str(data.get("task_version", "task_object_v1")),
            state=_coerce_task_state(data.get("state", TaskState.DRAFT)),
            source=_coerce_dataclass(TaskSource, data.get("source")),
            task_type=str(data.get("task_type", "model_edit")),
            target=_coerce_dataclass(TaskTarget, target_data),
            intent=_coerce_dataclass(TaskIntent, data.get("intent")),
            constraints=_coerce_dataclass(TaskConstraints, data.get("constraints")),
            execution_policy=_coerce_dataclass(ExecutionPolicy, data.get("execution_policy")),
            planning=_coerce_dataclass(TaskPlanning, data.get("planning")),
            runtime=_coerce_dataclass(TaskRuntime, data.get("runtime")),
            result=_coerce_dataclass(TaskResult, data.get("result")),
            diagnostics=list(data.get("diagnostics") or []),
            artifact_refs=dict(data.get("artifact_refs") or {}),
        )


SchemaType = TypeVar("SchemaType")


def _to_plain_data(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return {field.name: _to_plain_data(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, list):
        return [_to_plain_data(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _to_plain_data(item) for key, item in value.items()}
    return value


def _coerce_task_state(value: Any) -> TaskState:
    if isinstance(value, TaskState):
        return value
    return TaskState(str(value))


def _normalize_target_data(value: Any) -> Any:
    if not isinstance(value, dict):
        return value
    if "candidates" not in value or "binding_candidates" in value:
        return value
    normalized = dict(value)
    normalized["binding_candidates"] = normalized.pop("candidates")
    return normalized


def _coerce_dataclass(schema_type: type[SchemaType], value: Any) -> SchemaType:
    if isinstance(value, schema_type):
        return value
    if value is None:
        return schema_type()
    if not isinstance(value, dict):
        raise TypeError(f"{schema_type.__name__} data must be a dictionary.")
    allowed_fields = {field.name for field in fields(schema_type)}
    return schema_type(**{key: item for key, item in value.items() if key in allowed_fields})
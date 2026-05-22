"""Report data builders for Runtime-coordinated execution."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from domain import OperationOutcome


@dataclass(frozen=True)
class PersistenceResult:
    source_blend_file: str
    output_blend_copy: str
    saved_original_file: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable persistence summary."""
        return {
            "source_blend_file": self.source_blend_file,
            "output_blend_copy": self.output_blend_copy,
            "saved_original_file": self.saved_original_file,
        }


def build_operation_report(
    task: Any,
    operation_outcome: OperationOutcome,
    persistence_result: PersistenceResult,
    execution_status: str,
) -> dict[str, Any]:
    """Build a JSON-serializable report from Runtime execution facts."""
    return {
        "report_version": "runtime_execution_v1",
        "execution_status": execution_status,
        "task_id": str(task.task_id),
        "operation": operation_outcome.operation,
        "target_object": operation_outcome.target_object,
        "parameters": dict(task.planning.parameters),
        "changed_objects": list(operation_outcome.changed_objects),
        "operation_outcome": operation_outcome.to_dict(),
        **persistence_result.to_dict(),
    }


def build_failure_report(
    task: Any,
    error_stage: str,
    error: Exception,
    execution_status: str = "failed",
    persistence_result: PersistenceResult | None = None,
) -> dict[str, Any]:
    """Build a JSON-serializable report from Runtime failure facts."""
    report = {
        "report_version": "runtime_execution_v1",
        "execution_status": execution_status,
        "task_id": str(task.task_id),
        "operation": task.planning.selected_operation or "unknown_operation",
        "target_object": task.target.bound_object or "unknown_target",
        "parameters": dict(task.planning.parameters),
        "error_stage": error_stage,
        "error_type": type(error).__name__,
        "error_message": str(error),
        "saved_original_file": False,
    }
    if persistence_result is not None:
        report.update(persistence_result.to_dict())
    return report
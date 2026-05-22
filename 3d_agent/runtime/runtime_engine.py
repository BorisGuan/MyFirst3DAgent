"""Runtime Engine for ready TaskObject execution.

Runtime coordinates execution side effects. It does not select operations,
complete parameters, modify geometry directly, or inspect natural language.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from domain import DomainOperationInput, OperationOutcome
from reporting import PersistenceResult, build_failure_report, build_operation_report, report_writer
from runtime.execution_context import ExecutionContext, default_execution_context
from task_object import OwnershipLayer, TaskObject, TaskState, apply_owned_patch


class RuntimeExecutionError(RuntimeError):
    """Raised when Runtime execution fails after a clear stage boundary."""

    def __init__(self, stage: str, original_error: Exception) -> None:
        self.stage = stage
        self.original_error = original_error
        super().__init__(f"Runtime execution failed during {stage}: {original_error}")


def execute_ready_task(
    task: TaskObject,
    context: ExecutionContext | None = None,
) -> TaskObject:
    """Execute a ready_to_execute TaskObject through Domain and persistence side effects."""
    if task.state != TaskState.READY_TO_EXECUTE:
        raise RuntimeExecutionError("state", ValueError(f"TaskObject state must be 'ready_to_execute', got {task.state.value!r}."))

    runtime_context = context or default_execution_context()
    source_blend_file: str | None = None
    output_blend_copy: str | None = None
    report_file: str | None = None
    operation_input: DomainOperationInput | None = None

    try:
        operation_input = _domain_operation_input(task)
        source_blend_file = _source_blend_file(task)
        output_blend_copy = _required_text(task.execution_policy.output_blend_copy, "execution_policy.output_blend_copy")
        report_file = _required_text(task.execution_policy.report_file, "execution_policy.report_file")
        _validate_output_copy_path(source_blend_file, output_blend_copy)
        _mark_executing(task, runtime_context, source_blend_file, output_blend_copy, report_file)

        outcome = _call_domain_operation(runtime_context, operation_input)
        saved_copy = _save_output_copy(runtime_context, source_blend_file, output_blend_copy)
        written_report = _write_success_report(
            runtime_context,
            report_file,
            task,
            outcome,
            source_blend_file,
            saved_copy,
        )
        _mark_completed(task, runtime_context, outcome, saved_copy, written_report)
        return task
    except RuntimeExecutionError as error:
        _mark_failed(task, runtime_context, error, report_file, operation_input, source_blend_file, output_blend_copy)
        raise
    except Exception as error:
        runtime_error = RuntimeExecutionError("execution", error)
        _mark_failed(task, runtime_context, runtime_error, report_file, operation_input, source_blend_file, output_blend_copy)
        raise runtime_error from error


def _domain_operation_input(task: TaskObject) -> DomainOperationInput:
    try:
        return DomainOperationInput.from_task_object(task)
    except Exception as error:
        raise RuntimeExecutionError("domain_input", error) from error


def _source_blend_file(task: TaskObject) -> str:
    if task.runtime.source_blend_file:
        return task.runtime.source_blend_file
    for key in ("source_blend_file", "blend_file", "input_blend_file"):
        value = task.source.metadata.get(key)
        if value:
            return str(value)
    raise RuntimeExecutionError("persistence_policy", ValueError("source_blend_file is required before Runtime execution."))


def _required_text(value: str | None, field_name: str) -> str:
    if not value:
        raise RuntimeExecutionError("persistence_policy", ValueError(f"{field_name} is required before Runtime execution."))
    return value


def _validate_output_copy_path(source_blend_file: str, output_blend_copy: str) -> None:
    if _path_key(source_blend_file) == _path_key(output_blend_copy):
        raise RuntimeExecutionError(
            "persistence_policy",
            RuntimeError("output_blend_copy must be separate from the source .blend file."),
        )


def _mark_executing(
    task: TaskObject,
    context: ExecutionContext,
    source_blend_file: str,
    output_blend_copy: str,
    report_file: str,
) -> None:
    apply_owned_patch(
        task,
        OwnershipLayer.RUNTIME,
        {
            "state": TaskState.EXECUTING,
            "runtime": {
                "source_blend_file": source_blend_file,
                "output_blend_copy": output_blend_copy,
                "report_file": report_file,
                "started_at": context.clock(),
            },
        },
    )


def _call_domain_operation(context: ExecutionContext, operation_input: DomainOperationInput) -> OperationOutcome:
    handler = context.domain_handlers.get(operation_input.operation)
    if handler is None:
        raise RuntimeExecutionError(
            "domain_operation",
            LookupError(f"No Runtime domain handler registered for operation {operation_input.operation!r}."),
        )
    try:
        outcome = handler(operation_input)
    except Exception as error:
        raise RuntimeExecutionError("domain_operation", error) from error
    if not isinstance(outcome, OperationOutcome):
        raise RuntimeExecutionError("domain_operation", TypeError("Domain operation must return OperationOutcome."))
    if not outcome.success:
        raise RuntimeExecutionError("domain_operation", RuntimeError("Domain operation returned success=false."))
    return outcome


def _save_output_copy(context: ExecutionContext, source_blend_file: str, output_blend_copy: str) -> str:
    try:
        return context.persistence_api.save_as_copy_only(source_blend_file, output_blend_copy)
    except Exception as error:
        raise RuntimeExecutionError("persistence", error) from error


def _write_success_report(
    context: ExecutionContext,
    report_file: str,
    task: TaskObject,
    outcome: OperationOutcome,
    source_blend_file: str,
    output_blend_copy: str,
) -> str:
    try:
        persistence_result = PersistenceResult(
            source_blend_file=source_blend_file,
            output_blend_copy=output_blend_copy,
            saved_original_file=False,
        )
        return _report_writer(context).write_report(
            report_file,
            build_operation_report(task, outcome, persistence_result, execution_status="success"),
        )
    except Exception as error:
        raise RuntimeExecutionError("report_writer", error) from error


def _mark_completed(
    task: TaskObject,
    context: ExecutionContext,
    outcome: OperationOutcome,
    output_blend_copy: str,
    report_file: str,
) -> None:
    apply_owned_patch(
        task,
        OwnershipLayer.RUNTIME,
        {
            "state": TaskState.COMPLETED,
            "runtime": {
                "output_blend_copy": output_blend_copy,
                "report_file": report_file,
                "finished_at": context.clock(),
            },
            "result": {
                "success": True,
                "summary": f"Operation {outcome.operation} completed for {outcome.target_object}.",
                "report_file": report_file,
                "artifacts": {"output_blend_copy": output_blend_copy},
            },
        },
    )


def _mark_failed(
    task: TaskObject,
    context: ExecutionContext,
    error: RuntimeExecutionError,
    report_file: str | None,
    operation_input: DomainOperationInput | None,
    source_blend_file: str | None,
    output_blend_copy: str | None,
) -> None:
    if task.state not in {TaskState.READY_TO_EXECUTE, TaskState.EXECUTING}:
        return

    written_report = _try_write_failure_report(
        context,
        report_file,
        task,
        error,
        operation_input,
        source_blend_file,
        output_blend_copy,
    )
    runtime_patch: dict[str, Any] = {"finished_at": context.clock()}
    if written_report:
        runtime_patch["report_file"] = written_report

    apply_owned_patch(
        task,
        OwnershipLayer.RUNTIME,
        {
            "state": TaskState.FAILED,
            "runtime": runtime_patch,
            "result": {
                "success": False,
                "summary": f"Runtime execution failed during {error.stage}: {error.original_error}",
                "report_file": written_report,
            },
        },
    )


def _try_write_failure_report(
    context: ExecutionContext,
    report_file: str | None,
    task: TaskObject,
    error: RuntimeExecutionError,
    operation_input: DomainOperationInput | None,
    source_blend_file: str | None,
    output_blend_copy: str | None,
) -> str | None:
    if not report_file:
        return None
    try:
        persistence_result = None
        if source_blend_file or output_blend_copy:
            persistence_result = PersistenceResult(
                source_blend_file=source_blend_file or "",
                output_blend_copy=output_blend_copy or "",
                saved_original_file=False,
            )
        return _report_writer(context).write_report(
            report_file,
            build_failure_report(
                task,
                error_stage=error.stage,
                error=error.original_error,
                persistence_result=persistence_result,
            ),
        )
    except Exception:
        return None


def _report_writer(context: ExecutionContext) -> Any:
    return context.report_writer or report_writer


def _path_key(path_value: str) -> str:
    return str(Path(path_value).expanduser().resolve(strict=False)).rstrip("\\/").casefold()
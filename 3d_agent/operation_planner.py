"""Legacy Phase 2 operation-shaping helpers.

These helpers may still shape legacy preview data, but they are no longer a
real modification execution path. TaskObject Planning and Runtime own real
operation selection and execution.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


SUPPORTED_OPERATION = "edge_soften"
DEFAULT_REPORT_FILE = "outputs/modification_report.json"
DEFAULT_PARAMETERS = {
    "strength": 0.01,
    "style": "mechanical",
}


class LegacyExecutionPathError(RuntimeError):
    """Raised when old operation-dict execution is requested."""


def plan_operation(structured_input: dict[str, Any]) -> dict[str, Any]:
    """Map structured input into a complete domain-level operation request."""
    operation = structured_input.get("operation")
    target_object = structured_input.get("target_object")
    if operation != SUPPORTED_OPERATION:
        raise ValueError("Only edge_soften is supported in this step.")
    if not target_object:
        raise ValueError("target_object is required.")

    parameters = dict(DEFAULT_PARAMETERS)
    parameters.update(structured_input.get("parameters") or {})
    return {
        "operation": SUPPORTED_OPERATION,
        "target_object": target_object,
        "parameters": parameters,
    }


def execute_operation_request(
    operation_request: dict[str, Any],
    domain_layer: Any | None = None,
) -> Any:
    """Reject the retired operation-dict execution path."""
    raise LegacyExecutionPathError(
        "Operation dict execution is retired. Use TaskObject Planning and Runtime instead."
    )


def create_simplified_operation_plan(
    operation: str,
    target: str,
    source_blend: str,
    output_blend_copy: str,
    parameters: dict[str, Any] | None = None,
    report_file: str | None = None,
) -> dict[str, Any]:
    """Create the Step 3 operation plan for the single supported operation."""
    if not source_blend:
        raise ValueError("source_blend is required.")
    if not output_blend_copy:
        raise ValueError("output_blend_copy is required.")
    operation_request = plan_operation(
        {
            "operation": operation,
            "target_object": target,
            "parameters": parameters,
        }
    )

    return {
        "plan_version": "phase2_step3_v1",
        "execution_mode": "modify_copy",
        **operation_request,
        "source_blend_file": str(Path(source_blend)),
        "output_blend_copy": str(Path(output_blend_copy)),
        "report_file": report_file or DEFAULT_REPORT_FILE,
    }

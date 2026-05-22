"""Static registry for supported Domain Operations.

The registry is a Planning-facing capability list. It has no Blender API,
Core API, or Domain Operation handler dependency, and it does not execute
operations.
"""

from __future__ import annotations

from domain.operation_contracts import OperationSpec


EDGE_SOFTEN_OPERATION = "edge_soften"

EDGE_SOFTEN_SPEC = OperationSpec(
    name=EDGE_SOFTEN_OPERATION,
    supported_task_types=("surface_detail_enhancement",),
    required_target_state="bound",
    default_parameters={
        "strength": 0.01,
        "style": "mechanical",
    },
    parameter_schema={
        "strength": {
            "type": "number",
            "exclusive_minimum": 0.0,
            "default": 0.01,
        },
        "style": {
            "type": "string",
            "enum": ["clean", "heavy", "mechanical"],
            "default": "mechanical",
        },
    },
    safety_level="safe_non_destructive",
    handler_name="edge_soften",
    report_schema={
        "required_fields": [
            "operation",
            "target_object",
            "success",
            "changed_objects",
            "modifier_info",
            "mesh_data_applied",
            "diagnostics",
        ],
    },
)


class OperationRegistryError(LookupError):
    """Raised when an operation registry lookup or registration fails."""


class OperationRegistry:
    """Small static registry for operation capability lookup."""

    def __init__(self, operation_specs: tuple[OperationSpec, ...] | None = None) -> None:
        self._operation_specs: dict[str, OperationSpec] = {}
        for operation_spec in operation_specs or (EDGE_SOFTEN_SPEC,):
            self.register(operation_spec)

    def register(self, operation_spec: OperationSpec) -> None:
        """Register a static operation contract."""
        _validate_operation_spec(operation_spec)
        if operation_spec.name in self._operation_specs:
            raise OperationRegistryError(f"Operation {operation_spec.name!r} is already registered.")
        self._operation_specs[operation_spec.name] = operation_spec

    def get(self, operation_name: str) -> OperationSpec:
        """Return the operation spec for operation_name or fail clearly."""
        try:
            return self._operation_specs[operation_name]
        except KeyError as error:
            raise OperationRegistryError(f"Unsupported operation: {operation_name!r}.") from error

    def has(self, operation_name: str) -> bool:
        """Return whether operation_name is registered."""
        return operation_name in self._operation_specs

    def all_specs(self) -> tuple[OperationSpec, ...]:
        """Return all registered operation specs."""
        return tuple(self._operation_specs.values())

    def supported_for_task_type(self, task_type: str) -> tuple[OperationSpec, ...]:
        """Return operation specs that support a TaskObject task_type."""
        return tuple(
            operation_spec
            for operation_spec in self._operation_specs.values()
            if operation_spec.supports_task_type(task_type)
        )


def default_operation_registry() -> OperationRegistry:
    """Return the default registry for the current architecture step."""
    return OperationRegistry()


def _validate_operation_spec(operation_spec: OperationSpec) -> None:
    if not operation_spec.name:
        raise OperationRegistryError("OperationSpec.name is required.")
    if not operation_spec.supported_task_types:
        raise OperationRegistryError(f"Operation {operation_spec.name!r} must support at least one task_type.")
    if not operation_spec.required_target_state:
        raise OperationRegistryError(f"Operation {operation_spec.name!r} must define required_target_state.")
    if not operation_spec.handler_name:
        raise OperationRegistryError(f"Operation {operation_spec.name!r} must define handler_name.")
"""Runtime execution dependencies."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from domain import DomainOperationInput, OperationOutcome


DomainOperationHandler = Callable[[DomainOperationInput], OperationOutcome]


@dataclass(frozen=True)
class ExecutionContext:
    domain_handlers: Mapping[str, DomainOperationHandler]
    persistence_api: Any
    report_writer: Any = None
    clock: Callable[[], str] = lambda: datetime.now(UTC).isoformat()


def default_execution_context() -> ExecutionContext:
    """Return Runtime dependencies for the current supported operation set."""
    import core_api
    from blender_ops.domain_operations import edge_soften
    from reporting import report_writer

    return ExecutionContext(
        domain_handlers={"edge_soften": edge_soften},
        persistence_api=core_api,
        report_writer=report_writer,
    )
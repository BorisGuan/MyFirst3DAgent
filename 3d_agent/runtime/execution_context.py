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
    from blender_ops.domain_operations import (
        armor_edge_lip_prepare,
        armor_layer_plate_prepare,
        edge_soften,
        hardpoint_socket_prepare,
        panel_line_bevel_prepare,
        solidify_thickness_preview,
        surface_inset_prepare,
        thruster_nozzle_prepare,
        vent_slot_prepare,
        weighted_normal_finish,
    )
    from reporting import report_writer

    return ExecutionContext(
        domain_handlers={
            "armor_edge_lip_prepare": armor_edge_lip_prepare,
            "armor_layer_plate_prepare": armor_layer_plate_prepare,
            "edge_soften": edge_soften,
            "hardpoint_socket_prepare": hardpoint_socket_prepare,
            "panel_line_bevel_prepare": panel_line_bevel_prepare,
            "solidify_thickness_preview": solidify_thickness_preview,
            "surface_inset_prepare": surface_inset_prepare,
            "thruster_nozzle_prepare": thruster_nozzle_prepare,
            "vent_slot_prepare": vent_slot_prepare,
            "weighted_normal_finish": weighted_normal_finish,
        },
        persistence_api=core_api,
        report_writer=report_writer,
    )
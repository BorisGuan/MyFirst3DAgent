# Current TaskObject Architecture Status

This document captures the state after completing Steps 0-22 of the state-based TaskObject architecture migration.

## Milestone Summary

The project now has a complete modifier-only operation lifecycle:

```text
natural language or task file
-> TaskObject
-> Planning Engine
-> Runtime Engine
-> DomainOperationInput
-> Domain Operation
-> Core API
-> bpy
-> output .blend copy + Runtime report
```

The lifecycle has been validated at three levels:

```text
unit tests: python -m unittest discover -s tests
fake E2E: python -m unittest tests.test_end_to_end_task_object_flow
real smoke: python scripts\run_step20_blender_smoke.py
```

Latest known validation result:

```text
python -m unittest discover -s tests
Ran 366 tests: OK
```

## Layer Ownership

Agent Layer:

- Creates `TaskObject(state=draft)` from natural language.
- Reuses the legacy classifier and intent parser behind the Agent boundary.
- Does not call Planning, Runtime, Domain, Core, or Blender.

Planning Layer:

- Validates draft tasks.
- Resolves target binding from scene manifest or binding context.
- Selects a supported operation from the operation registry with intent-aware scoring when multiple compatible specs exist.
- Completes parameters from operation specs and intent parameters.
- Applies safety policy and moves the task to `ready_to_execute`.
- Does not call Domain, Runtime, Core, or Blender.

Runtime Layer:

- Accepts only `TaskObject(state=ready_to_execute)`.
- Derives `DomainOperationInput` from TaskObject.
- Calls the registered Domain handler.
- Coordinates persistence and report writing.
- Marks TaskObject `completed` or `failed`.
- Does not choose operations or complete parameters.

Domain Operation Layer:

- Implements operation behavior using `DomainOperationInput`.
- Returns `OperationOutcome`.
- Does not write reports, save files, or mutate TaskObject state.

Core API Layer:

- Owns raw `bpy` access.
- Resolves Blender objects, adds/removes modifiers, and saves output copies.

Reporting Side System:

- Builds and writes Runtime reports.
- Does not decide execution success and does not store large report objects in TaskObject.

## Entrypoints

Preferred real modification entry:

```text
3d_agent/cli.py --task-file path/to/task.json
```

Natural-language entry:

```text
3d_agent/cli.py --input "..." --scene-manifest path --source-blend path --output-blend-copy path --report-file path
```

Legacy structured entry remains as compatibility input:

```text
3d_agent/cli.py --modify-copy --operation edge_soften ...
```

The legacy structured entry is converted to TaskObject before Planning and Runtime.

## Retired Execution Sources

The following can remain for legacy preview or explanatory outputs, but they are not executable real modification inputs:

```text
OperationPlan
Execution Blueprint
Execution Package
preview / authoring script path
operation dict
```

`modification_execution.execute_modification_plan()` and `operation_planner.execute_operation_request()` fail fast to prevent old operation-plan execution from becoming a second Runtime path.

## Current Real Operations

Ten operations are available in the default registry and Runtime context:

```text
edge_soften
weighted_normal_finish
solidify_thickness_preview
panel_line_bevel_prepare
armor_layer_plate_prepare
vent_slot_prepare
thruster_nozzle_prepare
hardpoint_socket_prepare
surface_inset_prepare
armor_edge_lip_prepare
```

Implementation shapes:

```text
OperationRegistry -> OperationSpec(edge_soften)
Planning -> selected_operation=edge_soften
Runtime -> DomainOperationInput.from_task_object()
Domain -> blender_ops.domain_operations.edge_soften()
Core -> add_bevel_modifier()

OperationRegistry -> OperationSpec(weighted_normal_finish)
Planning -> selected_operation=weighted_normal_finish
Runtime -> DomainOperationInput.from_task_object()
Domain -> blender_ops.domain_operations.weighted_normal_finish()
Core -> add_weighted_normal_modifier()

OperationRegistry -> OperationSpec(solidify_thickness_preview)
Planning -> selected_operation=solidify_thickness_preview
Runtime -> DomainOperationInput.from_task_object()
Domain -> blender_ops.domain_operations.solidify_thickness_preview()
Core -> add_solidify_modifier()

OperationRegistry -> OperationSpec(panel_line_bevel_prepare)
Planning -> selected_operation=panel_line_bevel_prepare
Runtime -> DomainOperationInput.from_task_object()
Domain -> blender_ops.domain_operations.panel_line_bevel_prepare()
Core -> add_bevel_modifier()

OperationRegistry -> OperationSpec(armor_layer_plate_prepare)
Planning -> selected_operation=armor_layer_plate_prepare
Runtime -> DomainOperationInput.from_task_object()
Domain -> blender_ops.domain_operations.armor_layer_plate_prepare()
Core -> add_solidify_modifier()

OperationRegistry -> OperationSpec(vent_slot_prepare)
Planning -> selected_operation=vent_slot_prepare
Runtime -> DomainOperationInput.from_task_object()
Domain -> blender_ops.domain_operations.vent_slot_prepare()
Core -> add_bevel_modifier()

OperationRegistry -> OperationSpec(thruster_nozzle_prepare)
Planning -> selected_operation=thruster_nozzle_prepare
Runtime -> DomainOperationInput.from_task_object()
Domain -> blender_ops.domain_operations.thruster_nozzle_prepare()
Core -> add_bevel_modifier()

OperationRegistry -> OperationSpec(hardpoint_socket_prepare)
Planning -> selected_operation=hardpoint_socket_prepare
Runtime -> DomainOperationInput.from_task_object()
Domain -> blender_ops.domain_operations.hardpoint_socket_prepare()
Core -> add_bevel_modifier()

OperationRegistry -> OperationSpec(surface_inset_prepare)
Planning -> selected_operation=surface_inset_prepare
Runtime -> DomainOperationInput.from_task_object()
Domain -> blender_ops.domain_operations.surface_inset_prepare()
Core -> add_solidify_modifier()

OperationRegistry -> OperationSpec(armor_edge_lip_prepare)
Planning -> selected_operation=armor_edge_lip_prepare
Runtime -> DomainOperationInput.from_task_object()
Domain -> blender_ops.domain_operations.armor_edge_lip_prepare()
Core -> add_bevel_modifier()
```

The selector can now rank multiple compatible `OperationSpec` candidates by explicit operation request, `intent.action`, `intent.detail_type`, `intent.desired_effect`, and `priority`. The explicit `intent.parameters["operation"]` control field is consumed by Planning and is not forwarded as a Domain parameter.

## Known Gaps

- Fake E2E coverage still focuses on `edge_soften`; dedicated multi-operation fake E2E coverage is deferred while the core designer operation library is expanded.
- `TaskPlanning` stores one `selected_operation`, not a multi-step operation sequence.
- Parameter schema validation supports number and string only.
- Runtime handler registration is still a static mapping in `default_execution_context()`.
- The real smoke enters through a ready task file; a full natural-language real Blender smoke is still future work.
- Generated smoke artifacts live under `outputs/step20_smoke/` and should remain generated output, not source.

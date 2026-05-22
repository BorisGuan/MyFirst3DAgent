# Current TaskObject Architecture Status

This document captures the state after completing Steps 0-20 of the state-based TaskObject architecture migration.

## Milestone Summary

The project now has a complete single-operation lifecycle:

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
Ran 258 tests: OK
```

## Layer Ownership

Agent Layer:

- Creates `TaskObject(state=draft)` from natural language.
- Reuses the legacy classifier and intent parser behind the Agent boundary.
- Does not call Planning, Runtime, Domain, Core, or Blender.

Planning Layer:

- Validates draft tasks.
- Resolves target binding from scene manifest or binding context.
- Selects a supported operation from the operation registry.
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

## Current Real Operation

Only one operation is available in the default registry and Runtime context:

```text
edge_soften
```

Implementation shape:

```text
OperationRegistry -> OperationSpec(edge_soften)
Planning -> selected_operation=edge_soften
Runtime -> DomainOperationInput.from_task_object()
Domain -> blender_ops.domain_operations.edge_soften()
Core -> add_bevel_modifier()
```

## Known Gaps

- The operation selector chooses the first compatible operation; it does not yet rank by intent action, detail type, or desired effect.
- `TaskPlanning` stores one `selected_operation`, not a multi-step operation sequence.
- Parameter schema validation supports number and string only.
- Runtime handler registration is a static mapping in `default_execution_context()`.
- The real smoke enters through a ready task file; a full natural-language real Blender smoke is still future work.
- Generated smoke artifacts live under `outputs/step20_smoke/` and should remain generated output, not source.

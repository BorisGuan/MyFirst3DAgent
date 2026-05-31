# Step 18 Legacy Fact Source Cleanup

Step 18 retires old real-modification fact sources from the executable main chain.

## Current Real Modification Chain

```text
CLI --input / --task-file
or legacy --modify-copy converted to TaskObject
-> TaskObject
-> Planning Engine
-> Runtime Engine
-> DomainOperationInput.from_task_object()
-> Domain Operation
-> Core API
```

Runtime receives a `TaskObject` only. A task file is an external serialized form
of the same object and is loaded back into `TaskObject` before Runtime starts.

## Retired Execution Sources

These structures may remain for legacy preview, explanation, or historical tests,
but they are not executable real-modification inputs:

```text
OperationPlan
Execution Blueprint
Execution Package
preview / authoring script path
operation dict
```

`modification_execution.execute_modification_plan()` and
`operation_planner.execute_operation_request()` are retired execution APIs. They
fail fast instead of adapting operation dicts into Runtime, because that would
reintroduce a second source of truth.

## Legacy Preview Boundary

`3d_agent/main.py` can still build V0.x preview and authoring artifacts for the
legacy path. Those artifacts are side outputs only. They do not write TaskObject
state and they are not a real modification entry point.

## Test Contract

The Step 18 tests protect these rules:

1. CLI real modification no longer constructs an operation plan.
2. Old operation-dict execution APIs are disabled.
3. Runtime does not reference OperationPlan, Execution Blueprint, or Execution Package.
4. The documented main chain names TaskObject as the single executable truth.
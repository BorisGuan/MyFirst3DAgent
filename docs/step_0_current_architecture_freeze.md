# Step 0 Current Architecture Freeze

This document freezes the current implementation state before introducing the TaskObject architecture. It records facts only. It does not change runtime behavior, migrate code, or introduce TaskObject.

## Scope

Step 0 covers these implementation surfaces:

```text
3d_agent/main.py
3d_agent/cli.py
3d_agent/operation_planner.py
3d_agent/modification_execution.py
3d_agent/model/schemas.py
3d_agent/blender_ops/domain_operations.py
3d_agent/blender_ops/core_geometry_api.py
tests/test_phase_2_*.py
```

## Current Legacy AI Chain

The old natural-language workflow starts from `3d_agent/main.py` and routes through the agent loop:

```text
3d_agent/main.py
-> build_cli_result()
-> agent.loop.run_agent()
-> command_classifier.classify_command()
-> intent_parser.parse_intent()
-> agent.planner.create_plan()
-> risk_checker.evaluate_risks()
-> formatter.format_blueprint()
-> execution_blueprint.create_execution_blueprint()
-> optional execution_package / preview / authoring outputs
```

For model-edit commands, `agent.planner.create_plan()` validates intent and constructs `model.schemas.OperationPlan`, then returns a dict through `OperationPlan.to_dict()`.

Legacy optional outputs from `main.py` include:

```text
execution_package
design_rule_review
model_binding_context
execution_package_review
geometry_preview_plan
safe_preview_session
blender_preview_script_draft
blender_execution_request
blender_execution_report
blender_authoring_script
blender_authoring_request
blender_authoring_report
```

Freeze decision: this chain is legacy for real modification. Its reusable parts are natural-language understanding, context loading, and selected binding/manifest helpers. `OperationPlan`, execution blueprint, and execution package must not become the new real-modification source of truth.

## Current Real Modification Chain

The current Phase 2 real-modification path starts from the dedicated CLI module:

```text
3d_agent/cli.py
-> parse_cli_args()
-> build_operation_plan_from_cli()
-> operation_planner.create_simplified_operation_plan()
-> modification_execution.execute_modification_plan()
-> operation_planner.execute_operation_request()
-> blender_ops.domain_operations.edge_soften()
-> blender_ops.core_geometry_api.require_object()
-> blender_ops.core_geometry_api.add_bevel_modifier()
-> optional save_as_copy_only() / write_modification_report()
-> bpy
```

The Blender background command is assembled by `modification_execution.build_blender_background_command()`. It runs `3d_agent/cli.py` inside Blender with arguments after `--`.

## Current Real Modification Entry Points

These call sites can currently trigger or coordinate real modification behavior:

1. `3d_agent/cli.py::main()` is the Blender background-mode script entry point.
2. `3d_agent/cli.py::run_modify_copy_cli()` parses structured CLI input and executes a plan.
3. `3d_agent/modification_execution.py::execute_modification_plan()` validates a modify-copy operation plan and delegates execution.
4. `3d_agent/operation_planner.py::execute_operation_request()` delegates a planned operation to the Domain Operation Layer.
5. `3d_agent/blender_ops/domain_operations.py::edge_soften()` directly applies the supported domain operation.
6. `3d_agent/main.py` can run legacy preview/authoring Blender flows through generated scripts when preview/authoring flags are enabled. This remains a legacy path, not the new real-modification main chain.

## Where `bpy` Is Reached

For the current Phase 2 real-modification path, raw `bpy` is imported only through:

```text
3d_agent/blender_ops/core_geometry_api.py::_get_bpy()
```

The Core Geometry API then uses `bpy` to:

```text
lookup Blender objects
add / remove modifiers
save a .blend copy
build low-level modification report data
```

Freeze decision: future code should preserve the rule that raw `bpy` belongs behind the Core API boundary.

## Where Files Are Saved Or Reports Are Written

Current file/report side effects are not yet cleanly layered:

```text
modification_execution._write_failure_report()
domain_operations.edge_soften()
core_geometry_api.save_as_copy_only()
core_geometry_api.write_modification_report()
```

Important current violation to fix later: `domain_operations.edge_soften()` can save a `.blend` copy and write a report when `implementation_hint` includes `source_blend_file`, `output_blend_copy`, and `report_file`. This is intentionally frozen here, not fixed in Step 0.

## Current Main-Chain Semantic Objects

Current legacy semantic objects:

```text
model.schemas.OperationPlan
execution_blueprint dict
execution_package dict
geometry_preview_plan dict
safe_preview_session dict
blender_execution_request dict
```

Current Phase 2 structured execution objects:

```text
ModifyCopyCliArgs dataclass
operation_plan dict
operation_request dict
implementation_hint dict
domain_result dict
report dict
core report state dict
```

The Phase 2 `operation_plan` currently contains:

```text
plan_version
execution_mode
operation
target_object
parameters
source_blend_file
output_blend_copy
report_file
```

Freeze decision: these structures are overlapping partial facts. The new architecture should replace them as the main-chain truth with TaskObject, then derive layer-specific inputs from TaskObject.

## Reusable Modules

These modules are reusable with boundary changes:

```text
agent.command_classifier
agent.intent_parser
model.context_manager
model.scene_manifest
model.model_binding
blender_ops.domain_operations.edge_soften
blender_ops.core_geometry_api low-level bpy wrappers
tests/test_phase_2_* fake and mock patterns
```

Reusable does not mean source of truth. For example, `edge_soften` remains the only allowed Domain Operation, but its file/report side effects must move out in a later step.

## Legacy Or Migration-Only Modules

These structures should not drive the new real-modification main chain:

```text
model.schemas.OperationPlan
execution_blueprint as source of truth
execution_package as execution input
preview / authoring script path as real modification path
operation dict as the final main-chain input
```

They may remain temporarily for existing tests, preview behavior, or compatibility while the TaskObject path is introduced.

## Duplicate Truth Points

The main duplication to remove over later steps is:

```text
Natural-language intent -> OperationPlan / execution_blueprint / execution_package
Structured CLI input -> operation_plan / operation_request / implementation_hint
```

Both chains express target, operation intent, parameters, safety assumptions, and artifact paths, but they do so with incompatible dict shapes. Step 1 and later steps should introduce TaskObject as the single main-chain truth and then derive narrower layer inputs from it.

## Step 0 Freeze Result

No business logic should change in Step 0. The next steps can proceed using these frozen conclusions:

1. The current true Phase 2 real-modification chain starts at `3d_agent/cli.py` and reaches `bpy` through `core_geometry_api._get_bpy()`.
2. The current real-modification save path is `domain_operations.edge_soften()` -> `core_geometry_api.save_as_copy_only()`.
3. The current report write path is `domain_operations.edge_soften()` -> `core_geometry_api.write_modification_report()` plus failure reports in `modification_execution._write_failure_report()`.
4. The old AI chain can provide reusable understanding and context capabilities, but its `OperationPlan`, blueprint, and package are legacy real-modification facts.
5. The next implementation step should add TaskObject schema without connecting it to old Agent, Planner, Domain, Core, Runtime, or Blender flows.
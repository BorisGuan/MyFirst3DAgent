# 3D Model Modification Agent System - Architecture Introduction

Review basis: this document is grounded in the current repository implementation, including `3d_agent/task_object`, `agent_layer`, `planning`, `domain`, `runtime`, `blender_ops`, `core_api`, `reporting`, CLI entry points, context JSON files, tests, and the existing architecture documents. Where implementation and documents differ, the implementation is treated as authoritative.

Key evidence inspected:

```text
3d_agent/task_object/schema.py
3d_agent/task_object/ownership.py
3d_agent/task_object/lifecycle.py
3d_agent/agent_layer/agent_service.py
3d_agent/agent_layer/legacy_intent_adapter.py
3d_agent/model/context_manager.py
3d_agent/model/scene_manifest.py
3d_agent/model/model_binding.py
3d_agent/planning/*.py
3d_agent/domain/operation_contracts.py
3d_agent/domain/operation_registry.py
3d_agent/runtime/runtime_engine.py
3d_agent/runtime/execution_context.py
3d_agent/blender_ops/domain_operations.py
3d_agent/core_api/*.py
3d_agent/reporting/*.py
3d_agent/cli.py
3d_agent/main.py
3d_agent/context/*.json
3d_agent/model_contexts/00_base_gundam.json
3d_agent/session/*.json
tests/test_*.py
docs/02_task_object_architecture/current_task_object_architecture_status.md
docs/02_task_object_architecture/step_20_real_blender_smoke.md
docs/04_architecture_review_portfolio/agent_global_architecture_design.md
docs/04_architecture_review_portfolio/agent_execution_reliability_design.md
```

## 1. Executive Summary

This project is a controlled-execution AI agent architecture for modifying Blender hard-surface and mecha models. Its core design choice is to translate natural language into structured, stateful task data and then execute only registered, deterministic design operations. It is not a naive LLM-to-Blender-script system.

The central abstraction is `TaskObject`, defined in `3d_agent/task_object/schema.py`. It is the main fact source for the execution chain: user input, target, intent, planning result, runtime paths, result, diagnostics, and artifacts live in one serializable object. The lifecycle is explicit: `draft -> validated -> bound -> planned -> ready_to_execute -> executing -> completed` or `failed`.

The LLM-facing Agent Layer creates only a draft task. It does not execute Blender code, does not call `bpy`, does not call Domain operations, and does not decide the final `selected_operation`. Planning validates the task, binds the target object, selects an operation from `OperationRegistry`, completes parameters from `OperationSpec`, and checks safety policy. Runtime accepts only `ready_to_execute` tasks, derives a minimal `DomainOperationInput`, dispatches a registered domain handler, coordinates persistence, writes reports, and marks the task completed or failed.

Domain operations are fixed Python handlers in `3d_agent/blender_ops/domain_operations.py`. They represent design capabilities such as `edge_soften`, `panel_line_bevel_prepare`, and `thruster_nozzle_prepare`. These handlers call the Core API. The Core API is the only layer that imports or uses Blender `bpy`, through modules such as `core_api/scene_object_api.py` and `core_api/persistence_api.py`.

The current Atomic Operation Library v1 contains ten modifier-only, non-destructive operations. The persistence strategy saves output `.blend` copies and refuses to overwrite the source file. This makes the system safer, easier to audit, and easier to test than arbitrary LLM-generated Blender scripts.

## 2. Problem This System Solves

LLM-generated Blender scripts are powerful but unsafe. They can call arbitrary APIs, overwrite files, delete objects, apply destructive mesh edits, or fail in ways that are hard to inspect. Even when a script works once, it rarely becomes a reusable modeling capability.

Natural language design intent is also not the same thing as Blender API intent. A designer may say, "add mechanical panel detail to the chest armor". That should not directly map to random Python. It should map to a constrained design operation with known safety policy, known parameters, known target binding, known report output, and known failure behavior.

The architecture addresses several common agent failure modes:

```text
Planning mixed with execution
LLM output treated as executable code
Tool calls hidden inside natural-language reasoning
Multiple competing fact sources
No stable recovery point after failure
No clear audit trail of what changed
No reusable operation vocabulary
```

3D modeling workflows need controlled modification, rollback, explainability, repeatability, and domain-specific abstractions. This system turns open-ended user requests into structured state transitions and registered operations before touching Blender.

## 3. Core Design Philosophy

### State-based agent architecture

The system is built around explicit task state, not implicit conversation state. A task is only allowed to progress through known states, and each layer can only write the fields it owns.

### TaskObject as main fact source

`TaskObject` prevents the system from drifting into multiple execution sources. Legacy plans, blueprint objects, preview scripts, and operation dicts may still exist for compatibility or old preview flows, but real modification is centered on TaskObject.

### Controlled execution over free-form code generation

The LLM does not generate arbitrary Blender Python for execution. Real model modification flows through `OperationSpec`, Runtime dispatch, Domain handler, and Core API.

### Separation of responsibilities

The chain separates intent understanding, planning, runtime dispatch, domain operation logic, low-level Blender access, and reporting. This makes failures easier to locate and easier to test.

### Operation as design capability

An operation is a semantic modeling capability, not a direct Blender API wrapper. For example, `panel_line_bevel_prepare` is a design operation. It happens to use a Bevel modifier, but its name and contract are expressed in domain language.

### Non-destructive copy-only output

The current safety model does not rely on Blender undo. It preserves the source `.blend` and writes an output copy.

### Atomic operations first

The system intentionally starts with atomic operations before composite operation sequences. This avoids designing a sequence framework before the project has enough real modeling cases to justify it.

### Delayed abstraction

Composite operations, generalized sequence planning, object creation, boolean workflows, material workflows, and mesh edits are postponed until evaluation shows where they are needed.

## 4. High-Level Architecture

```text
User Input
  |
  v
Agent Layer
  |
  v
TaskObject(state=draft)
  |
  v
Planning Engine
  |-- validate
  |-- bind target
  |-- select operation
  |-- complete parameters
  |-- check safety policy
  v
TaskObject(state=ready_to_execute)
  |
  v
Runtime Engine
  |
  v
DomainOperationInput
  |
  v
Domain Operation Handler
  |
  v
Core API
  |
  v
Blender bpy
  |
  v
output .blend copy + Runtime report + TaskObject result
```

### Agent Layer

Input: user text and prompt-sized context summaries.

Output: `TaskObject(state=draft)`.

Allowed: classify command type, parse intent, fill Agent-owned fields.

Not allowed: bind Blender objects, select final operation, call Runtime, call Domain/Core, call `bpy`.

### TaskObject

Input: structured task fields from Agent, Planning, Runtime, and Reporting.

Output: serializable task state and execution facts.

Allowed: serve as data model and lifecycle state carrier.

Not allowed: execute side effects by itself.

### Planning Engine

Input: draft TaskObject plus scene manifest or binding context.

Output: TaskObject moved through `validated`, `bound`, `planned`, and `ready_to_execute`.

Allowed: validate, bind, select operation, complete parameters, approve safety.

Not allowed: execute Domain handlers, write reports, save files, call `bpy`.

### Runtime Engine

Input: `TaskObject(state=ready_to_execute)`.

Output: completed or failed TaskObject, report file, output blend copy on success.

Allowed: create `DomainOperationInput`, dispatch handler, coordinate persistence and reporting.

Not allowed: understand natural language, choose operation, complete parameters, modify geometry directly.

### Domain Operation

Input: `DomainOperationInput`.

Output: `OperationOutcome`.

Allowed: validate operation name, extract operation parameters, call Core API.

Not allowed: save files, write reports, mutate TaskObject, import `bpy` directly.

### Core API

Input: Blender object names and low-level modifier parameters.

Output: object lookup, modifier changes, saved output copy, low-level report state.

Allowed: use Blender `bpy`.

Not allowed: decide agent intent, plan operations, or own task state.

## 5. TaskObject-Centered State Model

`TaskObject` is defined in `3d_agent/task_object/schema.py`. It contains:

```text
task_id
task_version
state
source
task_type
target
intent
constraints
execution_policy
planning
runtime
result
diagnostics
artifact_refs
```

Important nested structures include:

```text
TaskSource: user_input, channel, metadata
TaskTarget: semantic_part, bound_object, binding_candidates
TaskIntent: desired_effect, action, detail_type, style, density, scale, symmetry, placement_zones, parameters
TaskConstraints: preserve_source_file, non_destructive, mesh_edit_allowed, notes
ExecutionPolicy: mode, preserve_source_file, output_blend_copy, report_file
TaskPlanning: selected_operation, parameters, reasoning
TaskRuntime: source_blend_file, output_blend_copy, report_file, started_at, finished_at
TaskResult: success, summary, report_file, artifacts
```

The lifecycle in `3d_agent/task_object/lifecycle.py` allows:

```text
draft -> validated
validated -> bound | failed
bound -> planned | failed
planned -> ready_to_execute | failed
ready_to_execute -> executing | failed
executing -> completed | failed
completed -> terminal
failed -> terminal
```

Field ownership in `3d_agent/task_object/ownership.py` is explicit:

| Layer | Owned fields |
| --- | --- |
| Agent | `source`, `task_type`, `target.semantic_part`, `intent`, `constraints` |
| Planning | `target.bound_object`, `target.binding_candidates`, `planning`, `execution_policy` |
| Runtime | `runtime`, `result` |
| Reporting | `artifact_refs` |
| Domain | none |

State ownership is also constrained. For example, Planning can move a task to `validated`, `bound`, `planned`, `ready_to_execute`, or `failed`, while Runtime can move it to `executing`, `completed`, or `failed`.

This model prevents multiple fact sources because the selected operation, bound object, parameters, runtime paths, and result are all part of the same serializable object. It also improves testability and recovery: unit tests can construct a TaskObject at a specific state, run one stage, and assert exact field changes. A serialized task file can enter the CLI through `--task-file` and resume from a known state.

## 6. Agent Layer

The Agent Layer is implemented in `3d_agent/agent_layer/agent_service.py` and `3d_agent/agent_layer/legacy_intent_adapter.py`.

`create_draft_task()` receives natural language input, creates or uses a `ContextManager`, calls `classify_command()`, and then calls `parse_intent()`. If the command type is not `model_edit`, it rejects the request. For model edits, it adapts legacy parser output into a draft TaskObject.

The Agent Layer consumes:

```text
ContextManager.summary_for_classifier()
ContextManager.summary_for_planner()
command_classifier
intent_parser
design taxonomy
model context
session summaries
```

It writes only Agent-owned fields:

```text
source
task_type
target.semantic_part
intent
constraints
```

It does not decide final `planning.selected_operation`. The parser may produce an action or legacy operation-like label, but actual operation selection happens in Planning through `OperationRegistry` and `OperationSpec` metadata.

## 7. Context Management System

The context system is layered, not a single prompt blob.

### Static design context

Files:

```text
3d_agent/context/design_taxonomy.json
3d_agent/context/capabilities.json
3d_agent/context/mecha_design_rules.json
```

`design_taxonomy.json` defines detail types such as panel lines, parting lines, armor layers, vents, thrusters, pipes, sensors, weapon mounts, damage, and weathering. It also defines operation phrases, actions, styles, symmetries, scales, and densities.

### Model context

Files:

```text
3d_agent/model_contexts/00_base_gundam.json
3d_agent/model/model_context.py
```

The model context is abstract metadata, not mesh data. It lists targetable parts such as head, body, chest armor, skirt armor, backpack, thruster, shield, beam rifle, camera sensor, and cockpit hatch, including aliases and categories.

### Session context

Files:

```text
3d_agent/session/design_brief.json
3d_agent/session/working_plan.json
3d_agent/session/interaction_summary.json
```

These hold current project/session facts and recent interactions. Current implementation uses them mainly in `ContextManager` summaries.

### ContextManager

`3d_agent/model/context_manager.py` loads static, model, and session context. It builds indexes by name, alias, category, and detail level. It provides:

```text
summary_for_classifier()
summary_for_planner()
summary_for_user()
answer_context_query()
find_part()
record_interaction()
```

### TaskObject context

TaskObject is execution context. After draft creation, the main chain relies on TaskObject fields rather than hidden LLM memory.

### Scene / binding context

`scene_manifest.py` validates read-only scene manifests exported from Blender. `model_binding.py` scores scene objects against semantic targets and produces binding contexts with binding status and confidence. Planning currently consumes confirmed `bound` entries and stores `bound_object` plus `binding_candidates`.

### Operation capability context

`OperationRegistry` and `OperationSpec` describe executable capabilities. This is distinct from prompt context: prompt context helps language understanding; registry context controls what can actually execute.

### Runtime context

`ExecutionContext` injects domain handlers, persistence API, report writer, and clock. It is the dependency boundary for Runtime.

### Report / feedback context

Runtime reports and `OperationOutcome` describe what happened. Current reports are useful for auditability. A full report-to-planning feedback loop is not yet implemented.

### Implementation/document difference

Confirmed difference: `capabilities.json` and some session constraints still describe an earlier abstract-planning-only agent. Current code and README now support controlled real Blender modification through TaskObject, Runtime, Domain, and Core API. The context files should be updated in a future cleanup so prompt context does not understate current capabilities.

## 8. Planning Layer

Planning is implemented in `3d_agent/planning`.

`plan_task()` composes five stages:

```text
validate_draft_task()
resolve_task_binding()
select_operation()
complete_parameters()
check_safety_policy()
```

### Validation

`validator.py` requires:

```text
state == draft
source.user_input
task_type == surface_detail_enhancement
target.semantic_part
intent.desired_effect
intent.style
intent.density
intent.scale
```

It advances the task to `validated`.

### Target binding

`binding_resolver.py` requires a validated task and either a scene manifest or an existing binding context. It uses `model_binding.create_model_binding_context()` when given a scene manifest. It accepts only confirmed `bound` bindings for execution and stores the first bound object as `target.bound_object`.

Current limitation: binding confidence exists in model binding output, but the TaskObject target only stores `bound_object` and `binding_candidates`; it does not store a confidence score or user confirmation status.

### Operation selection

`operation_selector.py` filters specs by:

```text
task_type
required_target_state
execution_policy.mode / safety_level
```

It supports explicit operation selection through `task.intent.parameters["operation"]`. If not explicit, it scores compatible specs:

```text
intent.action match: +40
intent.detail_type match: +30
intent.desired_effect match: +20
```

It uses priority and name as deterministic tie-breakers, but fails if multiple best specs share the same score and priority. If no compatible spec receives an intent match, it fails as ambiguous.

### Parameter completion

`parameter_completer.py` merges `OperationSpec.default_parameters` with explicit `TaskIntent.parameters`. It strips the planning-only `operation` parameter before Domain execution.

Supported schema types are currently:

```text
number
string
string enum
exclusive_minimum for numbers
```

Current limitations: boolean, integer, full min/max, style profiles, density profiles, scale profiles, and degree-word mapping are not yet fully modeled. For example, user phrases such as "slightly", "dense", "heavy armor", or scale-specific values are not yet systematically converted into parameter profiles.

### Safety policy

`safety_policy_checker.py` requires:

```text
safe_non_destructive mode
preserve_source_file == true
non_destructive == true
mesh_edit_allowed == false
output_blend_copy present
report_file present
output copy does not equal source file
```

It advances the task to `ready_to_execute`.

## 9. Operation Registry and OperationSpec

`OperationSpec` is defined in `3d_agent/domain/operation_contracts.py`. It represents a controlled operation contract, not a Blender API call.

Fields include:

```text
name
supported_task_types
required_target_state
default_parameters
parameter_schema
safety_level
handler_name
report_schema
intent_actions
intent_detail_types
intent_effects
priority
```

`OperationRegistry` in `3d_agent/domain/operation_registry.py` stores static specs and exposes `register()`, `get()`, `has()`, `all_specs()`, and `supported_for_task_type()`.

Implemented operations confirmed from code:

| Operation | Design purpose | Core mechanism | Non-destructive | Design principle |
| --- | --- | --- | --- | --- |
| `edge_soften` | Soften mechanical edges and basic surface detail | `add_bevel_modifier` | yes, modifier-only | Controlled edge refinement |
| `weighted_normal_finish` | Improve hard-surface highlight/shading flow | `add_weighted_normal_modifier` | yes, modifier-only | Finish pass without mesh edit |
| `solidify_thickness_preview` | Preview armor thickness | `add_solidify_modifier` | yes, modifier-only | Copy-safe mass/thickness preview |
| `panel_line_bevel_prepare` | Prepare panel or parting line base | `add_bevel_modifier` | yes, modifier-only | Surface/panel vocabulary |
| `armor_layer_plate_prepare` | Preview layered armor plate depth | `add_solidify_modifier` | yes, modifier-only | Armor layering capability |
| `vent_slot_prepare` | Prepare vent or grille detail | `add_bevel_modifier` | yes, modifier-only | Functional mechanical detail |
| `thruster_nozzle_prepare` | Prepare thruster/nozzle detail | `add_bevel_modifier` | yes, modifier-only | Propulsion design detail |
| `hardpoint_socket_prepare` | Prepare weapon/equipment mount socket | `add_bevel_modifier` | yes, modifier-only | Functional interface detail |
| `surface_inset_prepare` | Prepare recessed/inset surface | `add_solidify_modifier` | yes, modifier-only | Recessed surface detail |
| `armor_edge_lip_prepare` | Prepare armor edge lip/trim | `add_bevel_modifier` | yes, modifier-only | Mechanical edge trim |

## 10. Atomic Operation Library v1

The system starts with atomic operations because each operation has to be safe, testable, explainable, and reusable before composing larger procedures. A composite system would multiply failure cases before the base vocabulary is validated.

A useful classification of the current operation set is:

| Category | Operations |
| --- | --- |
| Surface / Panel | `edge_soften`, `panel_line_bevel_prepare`, `surface_inset_prepare`, `armor_edge_lip_prepare` |
| Form / Mass | `solidify_thickness_preview`, `armor_layer_plate_prepare` |
| Functional Detail | `vent_slot_prepare`, `thruster_nozzle_prepare`, `hardpoint_socket_prepare` |
| Finish | `weighted_normal_finish` |

This forms a small domain-specific operation language for mecha and hard-surface modeling. It covers panelization, layered armor, vents, thrusters, mount sockets, insets, armor trims, thickness preview, and hard-surface shading finish.

The common properties are:

```text
modifier-only
non-destructive
reusable
composable later
controlled by OperationSpec
executed by Runtime + Domain + Core pipeline
reported through structured Runtime reports
```

## 11. Runtime Layer

Runtime is implemented in `3d_agent/runtime/runtime_engine.py` and `runtime/execution_context.py`.

`execute_ready_task()` accepts only `TaskObject(state=ready_to_execute)`. It rejects other states before side effects. It then:

```text
builds DomainOperationInput.from_task_object(task)
resolves source_blend_file
validates output_blend_copy path
marks task executing
looks up domain handler from ExecutionContext.domain_handlers
calls handler
saves output blend copy through persistence API
writes success report
marks task completed
```

Failure handling is stage-based. Runtime wraps failures in `RuntimeExecutionError(stage, original_error)`, marks the task failed if it is still in an executable state, and attempts to write a failure report. Known stages include `state`, `domain_input`, `persistence_policy`, `domain_operation`, `persistence`, `report_writer`, and generic `execution`.

Runtime does not understand natural language, does not select operation, does not complete parameters, and does not call Core geometry helpers directly. If a handler is missing, it fails instead of falling back to another operation.

`default_execution_context()` statically maps the ten operation names to their domain handlers and injects `core_api` as persistence API plus `report_writer`.

## 12. Domain Operation Layer

Domain contracts are defined in `3d_agent/domain/operation_contracts.py`.

`DomainOperationInput` is minimal:

```text
task_id
operation
target_object
parameters
execution_policy
```

`DomainOperationInput.from_task_object()` requires a `ready_to_execute` task and rejects artifact paths in the domain execution policy. This prevents Domain from receiving report/output paths.

Domain handlers are in `3d_agent/blender_ops/domain_operations.py`. Each handler:

```text
checks operation_input.operation
extracts and validates operation-specific parameters
calls core_geometry_api.require_object()
calls a Core API modifier helper
returns OperationOutcome
```

Representative sharing:

```text
Bevel helper: edge_soften, panel_line_bevel_prepare, vent_slot_prepare, thruster_nozzle_prepare, hardpoint_socket_prepare, armor_edge_lip_prepare
Solidify helper: solidify_thickness_preview, armor_layer_plate_prepare, surface_inset_prepare
Weighted normal helper: weighted_normal_finish
```

Tests confirm Domain handlers do not save copies, do not write reports, and do not include output/report artifacts in outcomes. Domain imports `core_api as core_geometry_api`, but it does not directly import `bpy`; actual `bpy` access is behind Core API.

## 13. Core API Layer

Core API is implemented under `3d_agent/core_api`.

Key helpers:

```text
require_object()
object_snapshot()
modifier_snapshot()
add_bevel_modifier()
add_solidify_modifier()
add_weighted_normal_modifier()
remove_or_replace_named_modifier()
record_modified_object()
record_removed_modifier()
reset_modification_report_state()
save_as_copy_only()
build_modification_report()
write_modification_report()
```

`scene_object_api.py` imports Blender `bpy` to resolve objects. `persistence_api.py` imports `bpy` to save a copy and to build low-level reports. `geometry_api.py` works on object/modifier collections and records low-level modification facts.

Safety properties:

```text
same-named modifier is removed/replaced before adding a new one
source overwrite is rejected
current opened file overwrite is rejected
mesh_data_applied is recorded as false for current operations
output directories are created as needed
```

This boundary matters because Blender API access is isolated. Planning, Runtime, Domain contracts, and tests can be reasoned about without importing `bpy`. It also makes fake Core APIs easy to inject in tests.

## 14. Reporting and Diagnostics

Reporting lives under `3d_agent/reporting`.

`build_operation_report()` produces:

```text
report_version
execution_status
task_id
operation
target_object
parameters
changed_objects
operation_outcome
source_blend_file
output_blend_copy
saved_original_file
```

`build_failure_report()` adds:

```text
error_stage
error_type
error_message
```

`OperationOutcome` includes:

```text
operation
target_object
success
changed_objects
modifier_info
mesh_data_applied
diagnostics
```

Strengths:

```text
reports are structured JSON
success and failure are stage-aware
changed objects and modifier info are captured
TaskObject.result points to artifacts
source file preservation is explicit
```

Current gaps:

```text
post-check facts are not yet systematically modeled
reports do not yet feed back into future Planning
failure reports do not yet generate retry guidance
user preference profiles are future work
```

## 15. Testing and Validation

Tests are under `tests/`. The full suite currently reports 366 tests passing with:

```text
python -m unittest discover -s tests
```

Coverage areas confirmed from test files:

| Area | Representative tests |
| --- | --- |
| Agent Layer | `test_agent_layer_task_creation.py` |
| TaskObject schema/lifecycle/ownership | `test_task_object_schema.py`, `test_task_object_lifecycle.py`, `test_task_object_ownership.py` |
| Legacy fact-source cleanup | `test_task_object_legacy_fact_sources.py` |
| Planning validation/binding/selection/parameters/safety | `test_planning_*.py`, `test_planning_engine_flow.py` |
| Operation registry/contracts | `test_operation_registry.py`, `test_domain_operation_contracts.py` |
| Runtime | `test_runtime_execution_flow.py` |
| Domain operations | `test_phase_2_domain_operations.py` |
| Core API | `test_phase_2_core_geometry_api.py` |
| CLI and fake E2E | `test_phase_2_cli_execution_flow.py`, `test_end_to_end_task_object_flow.py` |
| Reporting | `test_reporting.py` |
| Legacy preview/authoring modules | `test_v0_*` files |

The fake E2E test creates a draft task from natural language, plans it with a fake scene manifest, executes it with fake persistence/reporting, and verifies TaskObject completion without real Blender.

A manual real Blender smoke test exists in `scripts/run_step20_blender_smoke.py`. It enters through `3d_agent/cli.py --task-file`, uses `examples/BlendFile/Gundam/GF-Gundam.blend`, applies `edge_soften` to `Body_Armor01`, verifies an output `.blend` copy, verifies a Runtime report, and checks that the source file hash is unchanged.

Current validation limitations:

```text
real Blender smoke covers edge_soften only
full natural-language-to-real-Blender smoke is not confirmed from code
multi-operation real smoke matrix is not yet implemented
TaskPlanning supports one selected_operation, not a sequence
```

## 16. Architectural Strengths

For interview purposes, the strongest architectural points are:

```text
clear separation of concerns
explicit state-based execution model
TaskObject as single source of truth
field ownership guard by architecture layer
controlled OperationRegistry instead of arbitrary tool calls
LLM-safe execution boundary
Core API isolation for Blender bpy
non-destructive copy-only persistence
reusable atomic operation library
structured Runtime reports
stage-aware failure handling
testability through fake handlers and fake persistence
extension through OperationSpec + Domain handler without changing the main chain
avoidance of premature composite/sequence abstraction
```

This is production-minded agent design because the architecture treats execution as a governed lifecycle, not as a chat completion side effect.

## 17. Unique Design Highlights

Compared with a naive LLM tool-calling agent, this system has several notable design choices:

1. The LLM is not the executor.
2. Natural language is translated into structured task state.
3. Operation selection is metadata-driven and deterministic enough to test.
4. Blender APIs are hidden behind Core API.
5. Atomic operations are semantic design capabilities.
6. Domain handlers are fixed code, not generated scripts.
7. Runtime refuses missing handlers instead of improvising.
8. Output copies are created instead of overwriting source files.
9. Reports preserve execution evidence.
10. The project treats mecha modeling actions as a domain-specific operation language.

The result is not a general scripting chatbot. It is a controlled execution architecture for a real 3D modeling workflow.

## 18. Current Limitations

Confirmed or strongly supported by code/docs:

```text
Parameter accuracy still needs improvement.
style / density / scale are captured in TaskIntent but not fully connected to parameter profiles.
Parameter schema currently supports number/string patterns, not a full schema language.
Target binding confidence exists in binding context but is not stored as a first-class TaskObject field.
User confirmation for ambiguous binding is not fully modeled in the TaskObject lifecycle.
Runtime preflight/post-check could be expanded into explicit reportable stages.
Runtime reports do not yet feed back into future Planning.
Real Blender smoke coverage is incomplete and currently centered on edge_soften.
Composite operation / sequence is intentionally postponed.
Object creation, boolean workflows, mesh edit workflows, and material systems are not current Core capabilities.
Some context JSON capability text is older than the current implementation.
```

Not confirmed from code:

```text
A complete natural-language-to-real-Blender smoke covering ContextManager, Agent Layer, Planning, Runtime, Domain, and Core in one real Blender run.
A persistent TaskObject store beyond CLI stdout, task files, and generated artifacts.
An automatic user preference profile derived from feedback.
```

## 19. Next-Phase Optimization Roadmap

### 19.1 Architecture / Accuracy Improvements

1. Operation parameter accuracy analysis

   Define parameter profiles per operation. Map `style`, `density`, `scale`, and degree words to parameters. Example: panel line width and segment count should respond to scale and visual density.

2. Operation selection accuracy review

   Audit `intent_actions`, `intent_detail_types`, `intent_effects`, priority, and overlap between specs. Add more test cases for Chinese natural language expressions and ambiguous requests.

3. Target binding accuracy review

   Elevate binding confidence, binding evidence, and user confirmation into the main TaskObject flow where needed.

4. Runtime preflight and post-check

   Add explicit checks for source path existence, expected modifier existence, modifier parameters, output existence, report existence, and source hash unchanged.

5. Report-to-planning feedback loop

   Use prior failures and user feedback as Planning context without turning reports into a second fact source.

6. Real Blender smoke matrix

   Extend manual smoke coverage from `edge_soften` to the full Atomic Operation Library v1.

7. Maintenance/refactor review

   Consider splitting OperationSpec definitions by category after the operation set stabilizes. Consider handler grouping only if current files become hard to maintain.

### 19.2 Functional Improvements

```text
Composite operation planning after enough real use cases
Object creation boundary design
Boolean / mesh edit safety strategy
Material system strategy
More real modeling operations after evaluation
```

The recommended order is architecture and accuracy first, then broader functionality.

## 20. Interview Presentation Version

### 20.1 30-second version

I built a controlled Blender modification agent for hard-surface mecha modeling. Instead of letting an LLM generate arbitrary Blender scripts, the system turns natural language into a stateful `TaskObject`, plans against a registry of safe design operations, dispatches deterministic Runtime handlers, and isolates Blender `bpy` behind a Core API. It writes output `.blend` copies and structured reports, so the source file stays protected and the execution is auditable.

### 20.2 2-minute version

The architecture is built around a TaskObject-centered lifecycle. The Agent Layer only understands the user request and creates a draft task. Planning then validates the task, binds the semantic target to a Blender object from a scene manifest, selects an operation from `OperationRegistry`, completes parameters from `OperationSpec`, and checks safety policy. Runtime accepts only `ready_to_execute` tasks. It derives a minimal `DomainOperationInput`, dispatches a registered Domain handler, saves an output copy, writes a report, and marks the task completed or failed.

The important design decision is that the LLM never directly calls Blender or writes executable scripts for real modification. Domain operations are fixed code such as `edge_soften`, `panel_line_bevel_prepare`, and `weighted_normal_finish`. They call Core API helpers like `add_bevel_modifier`, `add_solidify_modifier`, and `add_weighted_normal_modifier`. Core API is the only layer that touches `bpy`.

This gives the project clear safety boundaries, testable state transitions, structured reports, and a reusable atomic operation library for mecha modeling.

### 20.3 Deep-dive version

Start with TaskObject. It is the single source of truth, with fields for source input, target, intent, constraints, execution policy, planning, runtime, result, diagnostics, and artifacts. A lifecycle module controls valid state transitions. An ownership module controls which layer may modify which fields.

Then explain Planning. Planning does not execute. It turns a draft into a ready task through validation, binding, operation selection, parameter completion, and safety policy.

Then explain Runtime. Runtime does not plan. It only executes ready tasks, dispatches the selected operation, coordinates persistence/reporting, and marks success or failure.

Then explain Domain and Core. Domain handlers are design operations. Core helpers are Blender API boundaries. This split prevents free-form LLM behavior from leaking into execution.

Finally explain evaluation. The system has unit tests across TaskObject, Planning, Runtime, Domain, Core, reporting, and fake E2E, plus a manual real Blender smoke test.

### 20.4 What to emphasize to an interviewer

```text
Production-minded agent design
Safety and control over model execution
State modeling and field ownership
Separation of natural language, planning, execution, and low-level API access
Evaluation-driven growth
Domain-specific operation library design
Trade-off: atomic operations first, composite operations later
```

## 21. Teaching Version

A naive agent might take this request:

```text
Add mechanical details to the chest armor.
```

and ask an LLM to generate Blender Python. That creates several risks: unknown APIs, file overwrite, destructive edits, poor repeatability, and no reusable capability.

This architecture fixes the problem by splitting the process:

```text
Language understanding -> structured TaskObject
Planning -> controlled operation choice
Runtime -> deterministic dispatch
Domain -> fixed operation handler
Core -> bounded Blender API call
Report -> audit trail
```

How to think about agent state:

```text
State is not chat history.
State is the structured contract between layers.
A task should be inspectable before and after every stage.
```

How to design controlled tools:

```text
Expose domain operations, not raw API access.
Make operations small enough to test.
Make parameters explicit.
Make unsafe behavior impossible by construction.
```

How to separate semantic intent from execution:

```text
"Make this look more mechanical" is intent.
"Select panel_line_bevel_prepare" is planning.
"Call add_bevel_modifier" is implementation.
```

How to grow without overengineering:

```text
Start with atomic operations.
Collect real usage patterns.
Only then introduce composite operations or sequence planning.
```

## 22. Appendix

### Repository structure summary

```text
3d_agent/
  agent/                 legacy classifier/parser and older preview/blueprint helpers
  agent_layer/           TaskObject draft creation boundary
  blender_ops/           Domain operation handlers and compatibility wrappers
  context/               static design/capability JSON
  core_api/              Blender object, geometry, persistence helpers
  domain/                OperationSpec, OperationRegistry, DomainOperationInput, OperationOutcome
  integration/           older Blender script execution bridge
  model/                 model context, scene manifest, model binding, ContextManager
  model_contexts/        abstract Gundam model context JSON
  planning/              validator, binding, selector, parameter completer, safety policy, planning engine
  reporting/             Runtime report builders/writer
  runtime/               Runtime engine and execution context
  session/               design brief, working plan, interaction summary

docs/                    architecture and development documents
scripts/                 manual Blender smoke runner
tests/                   unittest suite
examples/                sample Blender/manifest assets
outputs/                 generated artifacts
```

### Key modules and files

| Area | Files |
| --- | --- |
| Task model | `3d_agent/task_object/schema.py`, `lifecycle.py`, `ownership.py` |
| Agent Layer | `3d_agent/agent_layer/agent_service.py`, `legacy_intent_adapter.py` |
| Context | `3d_agent/model/context_manager.py`, context/session/model JSON files |
| Planning | `3d_agent/planning/*.py` |
| Operation contracts | `3d_agent/domain/operation_contracts.py`, `operation_registry.py` |
| Runtime | `3d_agent/runtime/runtime_engine.py`, `execution_context.py` |
| Domain operations | `3d_agent/blender_ops/domain_operations.py` |
| Core API | `3d_agent/core_api/*.py` |
| Reporting | `3d_agent/reporting/*.py` |
| Entry points | `3d_agent/cli.py`, `3d_agent/main.py`, `start-agent-copilot.bat` |
| Smoke | `scripts/run_step20_blender_smoke.py` |

### Main data structures

```text
TaskObject
TaskSource
TaskTarget
TaskIntent
TaskConstraints
ExecutionPolicy
TaskPlanning
TaskRuntime
TaskResult
OperationSpec
OperationRegistry
DomainOperationInput
OperationOutcome
ExecutionContext
PersistenceResult
```

### Main execution flow

```text
create_draft_task()
-> plan_task()
   -> validate_draft_task()
   -> resolve_task_binding()
   -> select_operation()
   -> complete_parameters()
   -> check_safety_policy()
-> execute_ready_task()
   -> DomainOperationInput.from_task_object()
   -> domain handler
   -> core_api helper
   -> save_as_copy_only()
   -> build_operation_report()
   -> write_report()
```

### Implemented operations table

| Operation | Category | Core helper |
| --- | --- | --- |
| `edge_soften` | Surface / Panel | `add_bevel_modifier` |
| `weighted_normal_finish` | Finish | `add_weighted_normal_modifier` |
| `solidify_thickness_preview` | Form / Mass | `add_solidify_modifier` |
| `panel_line_bevel_prepare` | Surface / Panel | `add_bevel_modifier` |
| `armor_layer_plate_prepare` | Form / Mass | `add_solidify_modifier` |
| `vent_slot_prepare` | Functional Detail | `add_bevel_modifier` |
| `thruster_nozzle_prepare` | Functional Detail | `add_bevel_modifier` |
| `hardpoint_socket_prepare` | Functional Detail | `add_bevel_modifier` |
| `surface_inset_prepare` | Surface / Panel | `add_solidify_modifier` |
| `armor_edge_lip_prepare` | Surface / Panel | `add_bevel_modifier` |

### Test coverage summary

```text
Full unittest suite: 366 tests passing
TaskObject lifecycle and ownership: covered
Agent draft creation: covered
Planning stages: covered
OperationRegistry and OperationSpec: covered
DomainOperationInput and OperationOutcome: covered
Runtime success/failure flow: covered
Domain handlers: covered with fake Core API
Core API helpers: covered with fake bpy-style objects
Fake E2E TaskObject flow: covered
Manual real Blender smoke: edge_soften only
```

### Suggested diagrams

1. Layered execution diagram: Agent -> TaskObject -> Planning -> Runtime -> Domain -> Core -> Blender.
2. TaskObject lifecycle diagram: draft through completed/failed.
3. Field ownership matrix: Agent, Planning, Runtime, Reporting, Domain.
4. Operation capability diagram: OperationSpec -> selector -> handler -> Core helper.
5. Safety boundary diagram: LLM outside execution, `bpy` inside Core only.

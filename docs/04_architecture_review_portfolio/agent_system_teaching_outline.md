# 3D Model Modification Agent System - Teaching Outline

This outline teaches the system as a controlled agent execution architecture for a real domain-specific workflow: Blender hard-surface / mecha model modification.

## 1. Teaching Goal

By the end of the lesson, learners should understand:

```text
why naive LLM-to-Blender scripting is risky
how TaskObject-centered state controls execution
how Planning, Runtime, Domain, and Core API stay separated
how operation registries turn design intent into controlled capability
how to grow agent systems from atomic operations toward composite workflows
```

## 2. Start With The Naive Agent Mistake

Naive design:

```text
User: Add panel lines to the chest armor.
-> LLM writes Blender Python
-> Python is executed directly
-> Unknown bpy calls modify the scene
-> maybe source file is overwritten
-> no stable task state
-> no reusable operation
-> weak audit trail
```

Problems to discuss:

```text
LLM output is treated as executable code
planning and execution are mixed
target object may be ambiguous
parameters are not validated
source file safety is unclear
failure stage is hard to locate
script does not become reusable domain capability
```

## 3. Present The Core Idea

This project replaces free-form execution with a controlled lifecycle:

```text
Natural language
-> structured TaskObject
-> planning against operation contracts
-> runtime dispatch
-> domain handler
-> core Blender API boundary
-> output copy and report
```

Key sentence:

```text
The LLM helps understand intent, but the system executes only registered, deterministic design operations.
```

## 4. Architecture Diagram

```text
+-------------+
| User Input  |
+-------------+
       |
       v
+-------------+        prompt summaries
| Agent Layer | <---------------------+
+-------------+                       |
       |                              |
       v                              |
+-------------------------+           |
| TaskObject(state=draft) |           |
+-------------------------+           |
       |                              |
       v                              |
+------------------+                  |
| Planning Engine  |                  |
| - validate       |                  |
| - bind target    |                  |
| - select op      |                  |
| - complete params|                  |
| - safety policy  |                  |
+------------------+                  |
       |                              |
       v                              |
+--------------------------------+     |
| TaskObject(ready_to_execute)   |     |
+--------------------------------+     |
       |                              |
       v                              |
+----------------+                    |
| Runtime Engine |                    |
+----------------+                    |
       |                              |
       v                              |
+----------------------+              |
| DomainOperationInput |              |
+----------------------+              |
       |                              |
       v                              |
+------------------+                  |
| Domain Operation |                  |
+------------------+                  |
       |                              |
       v                              |
+----------+                          |
| Core API | ---- only layer using bpy|
+----------+                          |
       |                              |
       v                              |
+-----------------------------------+ |
| output .blend copy + Runtime report| |
+-----------------------------------+ |
```

## 5. TaskObject Lesson

Teach `TaskObject` as the main fact source.

Important fields:

```text
source.user_input
target.semantic_part
target.bound_object
intent.action / detail_type / desired_effect / style / density / scale
constraints
execution_policy
planning.selected_operation
planning.parameters
runtime paths
result
artifact_refs
state
```

State model:

```text
draft
-> validated
-> bound
-> planned
-> ready_to_execute
-> executing
-> completed / failed
```

Ownership model:

| Layer | Owns |
| --- | --- |
| Agent | source, task_type, semantic target, intent, constraints |
| Planning | bound object, candidates, planning result, execution policy |
| Runtime | runtime fields and result |
| Reporting | artifact references |
| Domain | no TaskObject fields |

Teaching point:

```text
State is not chat history. State is the inspectable contract between architecture layers.
```

## 6. Context Management Lesson

Explain why context is split instead of placed into one large prompt.

```text
Static design context: design vocabulary and taxonomy
Model context: abstract Gundam parts and aliases
Session context: current project/session facts
TaskObject context: execution facts
Scene/binding context: maps semantic target to Blender object
Operation capability context: what the system can actually execute
Runtime context: injected dependencies and handlers
Report/feedback context: what happened after execution
```

Important implementation note:

```text
ContextManager currently helps Agent classification and intent parsing.
Execution still depends on TaskObject, scene/binding context, OperationRegistry, and Runtime context.
```

Discuss current limitation:

```text
Session context and reports are not yet fully connected to parameter planning or future task optimization.
```

## 7. Planning Lesson

Planning is the decision layer, not the execution layer.

Pipeline:

```text
validate_draft_task()
-> resolve_task_binding()
-> select_operation()
-> complete_parameters()
-> check_safety_policy()
```

Explain each stage:

| Stage | Question answered |
| --- | --- |
| Validation | Is this task complete enough to plan? |
| Binding | Which Blender object should be modified? |
| Operation selection | Which registered design operation matches intent? |
| Parameter completion | Which parameters should the operation receive? |
| Safety policy | Is this safe to execute as copy-only/non-destructive? |

Operation selection scoring:

```text
intent.action match       +40
intent.detail_type match  +30
intent.desired_effect     +20
priority tie-break
ambiguous match -> fail fast
```

Teaching point:

```text
Planning turns semantic intent into a bounded executable contract, but does not touch Blender.
```

## 8. Operation Registry Lesson

Explain `OperationSpec` as the capability contract.

Fields:

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

Teaching contrast:

```text
Naive tool: expose bpy.ops to the LLM.
This system: expose semantic operations like panel_line_bevel_prepare.
```

Implemented operation vocabulary:

| Category | Operations |
| --- | --- |
| Surface / Panel | edge_soften, panel_line_bevel_prepare, surface_inset_prepare, armor_edge_lip_prepare |
| Form / Mass | solidify_thickness_preview, armor_layer_plate_prepare |
| Functional Detail | vent_slot_prepare, thruster_nozzle_prepare, hardpoint_socket_prepare |
| Finish | weighted_normal_finish |

## 9. Runtime Lesson

Runtime executes but does not plan.

Runtime responsibilities:

```text
accept only ready_to_execute TaskObject
create DomainOperationInput
lookup selected handler
call domain handler
save output .blend copy
write Runtime report
mark completed or failed
```

Runtime prohibitions:

```text
does not parse language
does not select operation
does not complete parameters
does not call Core geometry helpers directly
does not fallback to another operation if handler is missing
```

Failure model:

```text
RuntimeExecutionError(stage, original_error)
TaskObject.state = failed
TaskResult.success = false
failure report with error_stage and error_message
```

## 10. Domain And Core API Lesson

Domain Operation:

```text
receives DomainOperationInput
checks operation name
extracts parameters
calls Core API
returns OperationOutcome
```

Core API:

```text
requires Blender object
adds/replaces modifiers
records low-level modification facts
saves output copy
contains the only bpy access
```

Boundary diagram:

```text
Domain: edge_soften()
  -> Core: require_object()
  -> Core: add_bevel_modifier()
  -> Blender: object.modifiers.new(type="BEVEL")
```

Teaching point:

```text
The LLM never sees bpy as an execution surface. It sees domain language; Core owns Blender implementation details.
```

## 11. Reporting And Auditability Lesson

Runtime report records:

```text
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
error_stage / error_message on failure
```

Explain why this matters:

```text
The user can inspect what changed.
Failures can be assigned to a layer.
The source file is protected.
Future planning can eventually learn from reports.
```

## 12. Testing Lesson

Teach the validation stack:

```text
unit tests for TaskObject schema/lifecycle/ownership
unit tests for Agent draft creation
unit tests for Planning stages
unit tests for OperationRegistry and OperationSpec
unit tests for DomainOperationInput and OperationOutcome
unit tests for Runtime success/failure
unit tests for Domain handlers with fake Core API
unit tests for Core helpers with fake bpy-style objects
fake end-to-end TaskObject flow
manual real Blender smoke for edge_soften
```

Current known validation result:

```text
python -m unittest discover -s tests
Ran 366 tests: OK
```

## 13. Trade-Off Discussion

Good trade-offs:

```text
Atomic operations before composite sequences
Static handler map before auto-registration
Copy-only persistence before complex undo
Modifier-only operations before mesh/boolean editing
Metadata-driven selection before unconstrained tool choice
```

Why these are good:

```text
They keep the first production slice understandable, testable, and safe.
They allow evaluation before adding abstraction.
They make extension possible without changing the main chain.
```

## 14. Next Phase Teaching Discussion

Ask learners what should improve first.

Preferred order:

```text
1. Operation parameter accuracy
2. Operation selection accuracy
3. Target binding confidence and user confirmation
4. Runtime preflight/post-check
5. Report-to-planning feedback loop
6. Real Blender smoke matrix
7. Composite operation design after real patterns emerge
```

Explain the evaluation mindset:

```text
Do not add more power until the current power is accurate, inspectable, and safe.
```

## 15. Suggested Whiteboard Flow

1. Draw naive LLM scripting and list failure modes.
2. Draw the TaskObject lifecycle.
3. Add ownership by layer.
4. Draw Planning as a decision pipeline.
5. Draw OperationSpec as the capability contract.
6. Draw Runtime dispatch and failure staging.
7. Draw Domain/Core boundary and mark Core as the only `bpy` layer.
8. End with testing and next-phase evaluation roadmap.

## 16. Interview Teaching Takeaway

The system demonstrates how to design an AI agent that is useful in a real creative tooling domain without surrendering execution control to the LLM. It uses state, contracts, deterministic dispatch, clear safety boundaries, copy-only persistence, and tests to turn language understanding into governed software behavior.

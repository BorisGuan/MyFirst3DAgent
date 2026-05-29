# Gundam Model Details Design Agent

Local AI-assisted Blender modification agent for mecha model detailing. The current implementation uses a state-based `TaskObject` main chain, has completed the first full lifecycle milestone through a real Blender smoke test, and now supports ten modifier-only real operations through intent-aware operation selection. The next development track focuses on building a designer-oriented operation library for common mecha modeling actions.

## Current Milestone

Completed architecture steps: Step 0 through Step 22 in [docs/state_based_task_object_agent_development_plan.md](docs/state_based_task_object_agent_development_plan.md).

Current real modification chain:

```text
Agent Layer
-> TaskObject
-> Planning Engine
-> Runtime Engine
-> DomainOperationInput
-> Domain Operation
-> Core API
-> Blender bpy
```

`TaskObject` is the only main-chain source of truth. Legacy `OperationPlan`, Execution Blueprint, Execution Package, preview scripts, and operation dicts are no longer real modification inputs.

## What Works Now

- Natural-language input can create a draft `TaskObject`.
- Planning can validate, bind, select `edge_soften`, `weighted_normal_finish`, `solidify_thickness_preview`, `panel_line_bevel_prepare`, `armor_layer_plate_prepare`, `vent_slot_prepare`, `thruster_nozzle_prepare`, `hardpoint_socket_prepare`, `surface_inset_prepare`, or `armor_edge_lip_prepare`, complete parameters, and mark the task `ready_to_execute`.
- Planning ranks compatible `OperationSpec` candidates by explicit operation request and intent metadata.
- Runtime can execute a ready `TaskObject`, call Domain, save a `.blend` copy, write a Runtime report, and mark the task completed or failed.
- CLI supports `--input`, `--task-file`, and legacy `--modify-copy` conversion into TaskObject.
- Real Blender smoke has passed with `edge_soften` on `examples/BlendFile/Gundam/GF-Gundam.blend`.

## Common Commands

Run all unit tests:

```powershell
python -m unittest discover -s tests
```

Run the fake end-to-end TaskObject flow:

```powershell
python -m unittest tests.test_end_to_end_task_object_flow
```

Run the real Blender smoke test manually:

```powershell
python scripts\run_step20_blender_smoke.py
```

The smoke runner uses `D:\tools\blender-5.1\blender.exe` by default and writes generated artifacts under `outputs/step20_smoke/`.

## Current Limits

- Real operations currently supported in the default Runtime context: `edge_soften`, `weighted_normal_finish`, `solidify_thickness_preview`, `panel_line_bevel_prepare`, `armor_layer_plate_prepare`, `vent_slot_prepare`, `thruster_nozzle_prepare`, `hardpoint_socket_prepare`, `surface_inset_prepare`, `armor_edge_lip_prepare`.
- Dedicated multi-operation fake E2E coverage is deferred while the core designer operation library is expanded.
- The real Blender smoke currently uses a ready task file, not a full natural-language-to-Blender smoke.
- `TaskPlanning.selected_operation` is a single operation, not a sequence.
- Preview and authoring remain legacy side paths.
- Completed TaskObject persistence is not yet formalized beyond CLI stdout and smoke summary artifacts.

## Key Documents

- Current architecture status: [docs/current_task_object_architecture_status.md](docs/current_task_object_architecture_status.md)
- Legacy fact source cleanup: [docs/step_18_legacy_fact_source_cleanup.md](docs/step_18_legacy_fact_source_cleanup.md)
- Real Blender smoke result: [docs/step_20_real_blender_smoke.md](docs/step_20_real_blender_smoke.md)
- Multi-operation expansion plan: [docs/multi_operation_expansion_plan.md](docs/multi_operation_expansion_plan.md)
- Designer operation library plan: [docs/designer_operation_library_development_plan.md](docs/designer_operation_library_development_plan.md)
- Atomic operation extension analysis: [docs/atomic_operation_extension_analysis.md](docs/atomic_operation_extension_analysis.md)
- Atomic operation development plan: [docs/atomic_operation_development_plan.md](docs/atomic_operation_development_plan.md)
- Agent global architecture design: [docs/agent_global_architecture_design.md](docs/agent_global_architecture_design.md)
- Agent execution reliability design: [docs/agent_execution_reliability_design.md](docs/agent_execution_reliability_design.md)

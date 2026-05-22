# Gundam Model Details Design Agent

Local AI-assisted Blender modification agent for mecha model detailing. The current implementation uses a state-based `TaskObject` main chain and has completed the first full lifecycle milestone through a real Blender smoke test.

## Current Milestone

Completed architecture steps: Step 0 through Step 20 in [docs/state_based_task_object_agent_development_plan.md](docs/state_based_task_object_agent_development_plan.md).

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
- Planning can validate, bind, select `edge_soften`, complete parameters, and mark the task `ready_to_execute`.
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

- Only one real operation is supported: `edge_soften`.
- The real Blender smoke currently uses a ready task file, not a full natural-language-to-Blender smoke.
- `TaskPlanning.selected_operation` is a single operation, not a sequence.
- Preview and authoring remain legacy side paths.
- Completed TaskObject persistence is not yet formalized beyond CLI stdout and smoke summary artifacts.

## Key Documents

- Current architecture status: [docs/current_task_object_architecture_status.md](docs/current_task_object_architecture_status.md)
- Legacy fact source cleanup: [docs/step_18_legacy_fact_source_cleanup.md](docs/step_18_legacy_fact_source_cleanup.md)
- Real Blender smoke result: [docs/step_20_real_blender_smoke.md](docs/step_20_real_blender_smoke.md)
- Multi-operation expansion plan: [docs/multi_operation_expansion_plan.md](docs/multi_operation_expansion_plan.md)

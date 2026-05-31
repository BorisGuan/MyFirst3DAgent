# Step 20 Real Blender Smoke Test

Step 20 validates that the TaskObject main chain can run inside real Blender and save a non-destructive `.blend` copy.

## Smoke Runner

Manual runner:

```text
python scripts\run_step20_blender_smoke.py
```

The runner is not a unittest module and is not included in default unit test discovery. It generates a ready-to-execute TaskObject task file, invokes Blender through `3d_agent/cli.py --task-file`, and verifies the output artifacts.

## Environment

```text
Blender: D:\tools\blender-5.1\blender.exe
Source: examples\BlendFile\Gundam\GF-Gundam.blend
Target object: Body_Armor01
Operation: edge_soften
```

The source `.blend` is opened in background mode. The smoke output path is separate from the source file.

## Command

```text
D:\tools\blender-5.1\blender.exe -b D:\Code\GundamModelDetailsDesign\examples\BlendFile\Gundam\GF-Gundam.blend --python D:\Code\GundamModelDetailsDesign\3d_agent\cli.py -- --task-file D:\Code\GundamModelDetailsDesign\outputs\step20_smoke\GF-Gundam.step20.edge_soften.task.json
```

## Generated Artifacts

```text
outputs\step20_smoke\GF-Gundam.step20.edge_soften.task.json
outputs\step20_smoke\GF-Gundam.step20.edge_soften.blend
outputs\step20_smoke\GF-Gundam.step20.edge_soften.report.json
outputs\step20_smoke\GF-Gundam.step20.edge_soften.summary.json
outputs\step20_smoke\blender_stdout.log
outputs\step20_smoke\blender_stderr.log
```

## Result

All smoke checks passed:

```text
blender_exit_success: true
output_blend_copy_exists: true
report_json_exists: true
source_blend_unchanged: true
task_completed: true
task_result_artifact_points_to_output: true
runtime_report_success: true
```

TaskObject result:

```text
state: completed
success: true
summary: Operation edge_soften completed for Body_Armor01.
artifact: outputs\step20_smoke\GF-Gundam.step20.edge_soften.blend
```

Runtime report:

```text
execution_status: success
operation: edge_soften
target_object: Body_Armor01
parameters: {strength: 0.01, style: mechanical}
changed_objects: [Body_Armor01]
modifier: AI_PanelLine_Bevel, BEVEL, width 0.01, segments 1
saved_original_file: false
```

## Notes

`3d_agent/cli.py` now inserts its own directory into `sys.path` before importing project modules. Blender's `--python` execution does not reliably provide the script directory as an import root, and the smoke initially exposed that issue with `ModuleNotFoundError: No module named 'agent_layer'`.

The smoke preserves the architecture boundary: it enters through a serialized TaskObject, Runtime derives DomainOperationInput, Domain calls Core API, and Core API is the only layer that touches Blender's `bpy` module.
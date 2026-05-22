# V0.8B Visual Preview Guides Plan

## 1. Stage position

V0.8B upgrades the preview layer from engineering Empty markers into more legible Blender visual guides. It still does not edit bound mesh data, apply modifiers, run booleans, delete user objects, or save over the source `.blend` file.

```text
Design Rule Review
-> Geometry Preview Plan with visual_guide metadata
-> Blender visual guide script
-> preview report with generated_visual_guides
```

## 2. What changed

- `Geometry Preview Plan` preview elements now include `visual_guide` metadata.
- The Blender preview script creates generated guide objects instead of only Empty markers.
- Preview reports now include `generated_visual_guides`.

## 3. Guide types

```text
panel_line_hint     -> curve_line_overlay
surface_detail_hint -> annotation_disc
placeholder_volume  -> transparent_blockout
mounting_point_hint -> anchor_sphere
risk_marker         -> risk_sphere
manual_review_note  -> text_note
symmetry_reference  -> mirror_axis
```

The generated objects are still preview-only artifacts. They are tagged with:

```text
v0_6_preview_session_id
v0_8b_visual_guide
source_task_id
target_object
element_type
target_zone
intent
requires_user_confirmation
```

## 4. Safety boundary

V0.8B only creates new generated objects in the preview collection. It does not modify existing mesh datablocks or save the opened file.

The preview script still avoids:

```text
bpy.ops
mesh edit operations on bound objects
modifier apply
save_as_mainfile
object deletion
```

## 5. Example command

```powershell
python .\3d_agent\main.py "给胸甲加一些锐利的分件线，适合 1/144 打印。" --scene-manifest .\examples\blender_scene_manifest.json --blend-file .\examples\BlendFile\Gundam\GF-Gundam.blend --blender-executable D:\tools\blender-5.1\blender.exe --run-blender-preview
```

## 6. Validation

- V0.8B focused tests: `4 passed`.
- V0.6/V0.7/V0.8/V0.8B focused regression: `27 passed`.
- Full suite: `92 passed`.
- Real Blender smoke with `GF-Gundam.blend`: generated `2` visual guide objects and wrote `outputs/v0_7_preview_report.json`.

## 7. Next step

V0.8C should optionally save the preview result to a new `.blend` copy, never the source file. That will let users open a preserved preview scene directly without rerunning the CLI.
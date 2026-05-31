# V0.9A Blender Authoring API Plan

## 1. Stage position

V0.9A starts the transition from preview guides to controlled Blender authoring. It introduces a Blender-side helper API and the first non-destructive authoring operation: `panel_line_curve_guide`.

This is not direct mesh cutting. It creates editable curve objects in a saved copy so later stages can convert, refine, or apply them with user confirmation.

```text
Design Rule Review
-> Geometry Preview Plan
-> Blender Authoring Script
-> blender_authoring_api.py helper module
-> generated authoring curve objects
-> optional saved .blend copy
```

## 2. New CLI flags

```text
--authoring-curve-guide
--run-authoring
```

`--authoring-curve-guide` generates the authoring script and request. `--run-authoring` actually calls Blender.

## 3. Blender-side helper API

The generated `outputs/blender_authoring_api.py` module currently provides:

```text
find_object
ensure_collection
ensure_authoring_material
object_dimensions
preview_location
tag_generated_object
create_panel_line_curve_guide
save_as_copy_only
```

The authoring script imports these helpers instead of embedding all Blender logic inline.

## 4. Safety boundary

V0.9A still does not:

```text
edit existing mesh data
apply modifiers
run booleans
delete user objects
overwrite the source .blend file
```

The only save operation is copy-only, guarded by `save_as_copy_only`.

## 5. Example command

```powershell
python .\3d_agent\main.py "给胸甲加一些锐利的分件线，适合 1/144 打印。" --scene-manifest .\examples\blender_scene_manifest.json --blend-file .\examples\BlendFile\Gundam\GF-Gundam.blend --blender-executable D:\tools\blender-5.1\blender.exe --authoring-curve-guide --run-authoring --save-preview-copy --output-blend-copy .\outputs\GF-Gundam.authoring.blend
```

## 6. Validation

- V0.9A focused tests: `6 passed`.
- V0.7/V0.8B/V0.8C/V0.9A focused regression: `22 passed`.
- Full suite: `104 passed`.
- Real Blender smoke: generated `2` `panel_line_curve_guide` objects and saved `outputs/GF-Gundam.authoring.blend` without saving the original file.

## 7. Next step

V0.9B should add a geometry diff report for generated authoring objects and bound targets:

```text
before: target object mesh data name, vertex count, object transform, dimensions
after: same target mesh data unchanged, generated authoring object count, curve properties
```

That diff report will be the safety gate before any future modifier or mesh operation.
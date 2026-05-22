# V0.8C Preview Blend Copy Plan

## 1. Stage position

V0.8C lets the preview execution save a separate `.blend` copy after generating visual guide objects. It does not overwrite the source `.blend` file.

```text
V0.8B visual guide execution
-> optional save preview copy
-> execution report records saved_preview_copy and output_blend_copy
```

## 2. CLI flags

```text
--save-preview-copy
--output-blend-copy <path>
```

`--output-blend-copy` implies `--save-preview-copy`. If no output path is provided, the default request path is:

```text
outputs/<source-name>.preview.blend
```

## 3. Safety boundary

V0.8C allows `bpy.ops.wm.save_as_mainfile` only in explicit save-copy mode. The generated script refuses to save when the output path resolves to the source `.blend` path.

The execution report keeps:

```json
{
  "saved_original_file": false,
  "saved_preview_copy": true,
  "output_blend_copy": "outputs/GF-Gundam.preview.blend"
}
```

## 4. Example command

```powershell
python .\3d_agent\main.py "给胸甲加一些锐利的分件线，适合 1/144 打印。" --scene-manifest .\examples\blender_scene_manifest.json --blend-file .\examples\BlendFile\Gundam\GF-Gundam.blend --blender-executable D:\tools\blender-5.1\blender.exe --run-blender-preview --save-preview-copy --output-blend-copy .\outputs\GF-Gundam.preview.blend
```

## 5. Validation

- V0.8C focused tests: `6 passed`.
- V0.7/V0.8/V0.8B/V0.8C focused regression: `24 passed`.
- Full suite: `98 passed`.
- Real Blender smoke: `outputs/GF-Gundam.preview.blend` was created, `saved_preview_copy=true`, `saved_original_file=false`, `generated_visual_guides=2`.

## 6. Next step

V0.9 can begin non-destructive geometry authoring on copied files only. The first geometry authoring target should be a low-risk curve-based panel line guide or bevel-ready helper curve, not direct mesh cutting.
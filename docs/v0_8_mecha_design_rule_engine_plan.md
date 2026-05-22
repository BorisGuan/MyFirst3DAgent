# V0.8A Mecha Design Rule Engine Plan

## 1. Stage position

V0.8A adds a machine-readable mecha design rule layer before any direct geometry authoring. It reviews a planned edit after `Execution Package` creation and before geometry preview, Blender execution, or future mesh/modifier changes.

The goal is not to make final artistic decisions automatically. The goal is to make design constraints visible, testable, and reusable before the agent edits a `.blend` file.

```text
Natural language instruction
-> OperationPlan V2
-> Execution Blueprint
-> Execution Package
-> Mecha Design Rule Review
-> Geometry Preview / Blender Execution
```

## 2. What V0.8A does

- Loads `context/mecha_design_rules.json`.
- Reviews target part, requested operation, requested detail type, scale, density, symmetry, and unsafe user intent.
- Emits `design_rule_review` as structured JSON.
- Adds an explicit CLI flag: `--design-rule-review`.
- Automatically includes design review when geometry preview or Blender preview execution is requested.

## 3. What V0.8A does not do

- Does not edit mesh geometry.
- Does not save or overwrite `.blend` files.
- Does not generate final curves, bevels, booleans, or modifiers.
- Does not block existing V0.7 preview execution by default; it exposes review data for the next execution layer.

## 4. Rule categories

The first rule pack covers:

- Part rules: what details fit chest armor, backpack, leg armor, shield, and head.
- Scale rules: warnings and constraints for `1/144` detail density.
- Symmetry rules: left-right review for legs and backpack details.
- Geometry safety rules: preview before mesh edit, no source overwrite, prefer non-destructive helpers, record geometry diff before apply.
- Blocked user intents: overwrite source `.blend`, direct mesh edit without preview.

## 5. Review output shape

```json
{
  "review_version": "v0_8",
  "source_package_ref": "execution_package",
  "rule_pack_version": "v0_8",
  "status": "passed_with_warnings",
  "target_part": "chest_armor",
  "canonical_part": "chest_armor",
  "operation": "add_parting_lines",
  "requested_detail_type": "parting_lines",
  "recommended_detail_types": ["panel_lines", "parting_lines", "armor_layers", "vents"],
  "blocked_detail_types": ["thrusters", "weapon_mounts"],
  "matched_rules": ["part_rules.chest_armor", "operation_detail_types.add_parting_lines"],
  "warnings": [],
  "blockers": [],
  "geometry_constraints": ["preview_before_mesh_edit", "do_not_overwrite_source_blend"],
  "requires_user_confirmation": [],
  "review_summary": "parting_lines on chest_armor can proceed with design warnings."
}
```

## 6. Validation

- V0.8 focused tests: `8 passed`.
- V0.4/V0.6/V0.7/V0.8 focused regression: `31 passed`.
- Full test suite: `88 passed`.

## 7. Next step

V0.8B should use `design_rule_review.geometry_constraints`, `recommended_detail_types`, `blockers`, and `requires_user_confirmation` to upgrade preview elements from engineering Empty markers into more legible visual guides:

- panel line curve overlays
- transparent armor blockout helpers
- risk markers on unsafe zones
- mirrored preview references for symmetric parts

V0.8B should still save only preview artifacts or copies, not overwrite source `.blend` files.
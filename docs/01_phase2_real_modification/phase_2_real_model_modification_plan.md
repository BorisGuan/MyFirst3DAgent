# Phase 2 Real Model Modification Development Plan

## 1. Phase 2 Positioning

Phase 2 changes the project direction from preview/guide generation to real `.blend` model modification.

The product goal is:

```text
Natural language instruction
-> Rule Engine
-> Operation Planner
-> Interface Layer
-> Blender Execution
-> Modification Report
```

Phase 2 should not continue expanding preview-only features. Preview, visual guides, and authoring helper objects can remain as optional support tools, but they are not the main product path.

The core product goal is an Agent that understands mecha design rules and modifies a copied `.blend` file through controlled domain operations.

## 2. Core vs. Enhancement Boundary

### 2.1 Core Capabilities

These are required for the final Agent product:

1. Mecha design rules
2. Scene/object binding
3. Operation planning in domain language
4. Two-level Blender interface layer
5. Real modification request generation
6. Safe execution on a copied `.blend` file
7. Modification report for user-facing transparency

### 2.2 Enhancement Capabilities

These are useful but should not drive the next milestones:

1. Empty preview markers
2. Visual preview guides
3. Saved preview-only copies
4. Extra helper/guide objects that do not map to actual model changes
5. Diff reports before real modification exists

Enhancement capabilities can be used for debugging or user confirmation later, but Phase 2 development should prioritize actual model modification.

## 3. Phase 2 Architecture

Phase 2 must use four explicit layers:

```text
Natural Language
-> Rule Engine
-> Operation Planner
-> Interface Layer
-> Blender Execution
```

### 3.1 Rule Layer

The Rule Layer evaluates mecha design intent. It decides what the design should express, not how Blender should implement it.

The Rule Layer must not reference Blender concepts such as `modifier`, `mesh`, `bpy`, `curve`, or `object.modifiers`.

### 3.2 Operation Planning Layer

The Operation Planner converts rule outputs into domain-level operations such as:

```text
edge_soften
add_panel_line
add_armor_plate
reinforce_joint
```

It may attach implementation hints, but the operation itself must remain domain-level.

### 3.3 Interface Layer

The Interface Layer translates domain operations into controlled geometry actions. It has two levels:

1. Domain Operation Layer
2. Core Geometry API

AI and rule logic interact only with the Domain Operation Layer.

### 3.4 Blender Execution Layer

The Blender Execution Layer runs generated scripts in Blender background mode, saves copied `.blend` files, and writes modification reports.

It executes selected operations. It does not decide design intent.

## 4. Rule Engine Design

The Rule Engine is an implementation-independent design reasoning layer between natural language and operation planning.

```text
Natural Language
-> Rule Engine
-> Operation Planner
-> Interface Layer
-> Blender Execution
```

The Rule Engine expresses design intent only. It must be reusable across different implementation backends and must not contain Blender-specific terms.

### 4.1 Rule Layer Responsibilities

The Rule Layer should:

1. interpret target design intent;
2. evaluate part type, surface role, symmetry, hierarchy, density, and scale;
3. decide whether a design response is appropriate;
4. output domain design decisions and parameter intent;
5. provide rationale for the Operation Planner.

The Rule Layer should not:

1. choose a Blender modifier;
2. reference `bpy`;
3. choose mesh editing APIs;
4. emit low-level geometry commands;
5. save or modify files.

### 4.2 Rule Output Schema

```json
{
  "rule_id": "string",
  "target_object": "string",
  "conditions": {
    "surface_size": "large | medium | small",
    "position": "edge | center",
    "symmetry": true,
    "hierarchy_depth": 1
  },
  "decision": "string",
  "intent": "string",
  "parameters": {
    "intensity": "low | medium | high",
    "style": "clean | heavy | mechanical"
  }
}
```

### 4.3 Rule Output Example

```json
{
  "rule_id": "large_surface_requires_structure",
  "target_object": "ChestArmor_Upper_01",
  "conditions": {
    "surface_size": "large",
    "position": "center",
    "symmetry": true,
    "hierarchy_depth": 1
  },
  "decision": "add_structural_surface_breakup",
  "intent": "break up a large armor surface while preserving the central chest silhouette",
  "parameters": {
    "intensity": "medium",
    "style": "mechanical"
  }
}
```

This output does not mention Blender. The Operation Planner maps it to a domain operation.

## 5. Mecha Design Rule System (Structured)

The mecha design rules must be systematic enough to support real model modification. Each rule includes condition description, expected effect, and design rationale.

### 5.1 Surface Detailing Rules

#### Rule: large_surface_requires_structure

- Condition description: A large, visually exposed armor surface has too little segmentation or hierarchy.
- Expected effect: Add structural breakup such as panel lines, parting lines, or subtle edge emphasis.
- Design rationale: Large uninterrupted surfaces make a mecha part look toy-like or unfinished; controlled segmentation communicates manufactured armor panels.

#### Rule: edge_emphasis_for_readability

- Condition description: An armor part has important silhouette edges that are visually flat or hard to read.
- Expected effect: Add edge emphasis with restrained intensity.
- Design rationale: Mecha forms rely on readable hard-surface planes; edge emphasis improves mechanical clarity without requiring destructive cuts.

#### Rule: panel_line_follows_surface_logic

- Condition description: A panel line is requested on a surface with visible armor direction or part boundaries.
- Expected effect: Place panel lines along plausible manufacturing or armor separation logic.
- Design rationale: Random lines create visual noise; panel lines should imply real assembly, maintenance, or armor separation.

#### Rule: avoid_detail_on_unstable_flat_surface

- Condition description: A very small or ambiguous flat surface is requested for dense detailing.
- Expected effect: Reduce intensity or redirect details to a larger adjacent surface.
- Design rationale: Small flat areas cannot support readable detail at model scale and may become cluttered.

### 5.2 Structural Rules (Hierarchy-Driven)

#### Rule: main_body_preserves_primary_hierarchy

- Condition description: The target is a main body object such as chest armor or central torso armor.
- Expected effect: Keep detail intensity controlled and preserve the primary silhouette.
- Design rationale: Main body parts define the mecha identity; excessive detail can obscure the intended hierarchy.

#### Rule: child_objects_allow_higher_detail_density

- Condition description: The target is a child or secondary object such as vents, backpack blocks, sensor housings, or small armor inserts.
- Expected effect: Allow higher detail density than main body surfaces.
- Design rationale: Secondary objects can carry fine mechanical detail without overwhelming the full silhouette.

#### Rule: joint_regions_require_mechanical_enhancement

- Condition description: The target region is near a joint, hinge, knee, elbow, shoulder, ankle, or waist connector.
- Expected effect: Add mechanical connection logic such as reinforced edges, visible pivots, hydraulic hints, or protective clearances.
- Design rationale: Joints must visually explain movement and load transfer; purely decorative surface detail is less convincing there.

### 5.3 Symmetry Rules

#### Rule: bilateral_parts_sync_detail_language

- Condition description: The target has a left/right counterpart or belongs to a mirrored pair.
- Expected effect: Keep operation type, intensity, and style synchronized unless asymmetry is explicitly requested.
- Design rationale: Most mecha limb and backpack structures rely on bilateral consistency for visual balance.

#### Rule: mirrored_components_keep_parameter_consistency

- Condition description: A mirrored component pair receives detail or modification.
- Expected effect: Use matching design parameters across both sides.
- Design rationale: Small differences in mirrored mechanical components often look like errors rather than intentional design.

#### Rule: asymmetry_requires_functional_reason

- Condition description: The requested change breaks symmetry.
- Expected effect: Allow asymmetry only when tied to functional parts such as weapons, shields, sensors, equipment racks, or damage.
- Design rationale: Functional asymmetry can add character; arbitrary asymmetry weakens mechanical believability.

### 5.4 Mechanical Logic Rules

#### Rule: joints_show_connection_mechanics

- Condition description: The target area is part of a moving or load-bearing structure.
- Expected effect: Add or preserve visible connection mechanics.
- Design rationale: Mechanical plausibility improves when moving parts show how force and rotation are transferred.

#### Rule: armor_appears_layered_not_monolithic

- Condition description: A large armor object reads as a single uninterrupted block.
- Expected effect: Introduce layered armor logic through edge treatment, surface breakup, or added armor hierarchy.
- Design rationale: Mecha armor should suggest separately manufactured and serviceable plates, not one solid monolith.

#### Rule: exposed_inner_structure_improves_realism

- Condition description: The design style allows mechanical exposure or high-detail realism.
- Expected effect: Add restrained hints of inner frame, cable routing, piston logic, or nested mechanical parts.
- Design rationale: Selective exposure of internal structure creates depth and technical realism.

### 5.5 Density and Visual Noise Control

#### Rule: detail_per_area_has_upper_limit

- Condition description: A surface already contains dense details or the requested intensity is high.
- Expected effect: Reduce added detail density or focus it on fewer high-value zones.
- Design rationale: Over-detailing reduces readability and makes small-scale models visually muddy.

#### Rule: avoid_over_segmentation

- Condition description: A surface would be divided into too many small panels.
- Expected effect: Prefer fewer, stronger structural divisions.
- Design rationale: Too many panel breaks make armor look fragile and visually noisy.

#### Rule: preserve_visual_readability

- Condition description: A proposed change competes with key silhouette, face, chest center, sensor, or weapon read.
- Expected effect: Lower intensity or move the operation to a less critical zone.
- Design rationale: The viewer must still understand the mecha form at a glance.

### 5.6 Manufacturing / Scale Constraints

#### Rule: one_144_minimum_detail_size

- Condition description: Scale is `1/144` or equivalent small model scale.
- Expected effect: Use low-to-medium intensity and avoid extremely thin or shallow details.
- Design rationale: Details that are too small may disappear visually, break during printing, or be impossible to paint cleanly.

#### Rule: avoid_ultra_thin_floating_parts

- Condition description: A requested feature would create thin unsupported elements.
- Expected effect: Reject or thicken the feature, or change it into an attached surface treatment.
- Design rationale: Floating thin parts are fragile and often fail in printing, handling, or assembly.

#### Rule: maintain_physical_plausibility

- Condition description: A requested change ignores load paths, attachment surfaces, or object scale.
- Expected effect: Require a more plausible placement, reduce intensity, or request confirmation.
- Design rationale: Mecha detail should look mechanically buildable even when stylized.

## 6. Rule to Operation Mapping

Rules do not choose Blender operations directly. The Rule Engine outputs design decisions. The Operation Planner maps those decisions to domain operations.

```text
Rule Engine Output
-> Operation Planner Decision
-> Domain Operation
-> Interface Layer implementation hint
```

Example:

```text
Rule: large_surface_requires_structure
Decision: add_structural_surface_breakup
Operation Planner: add_panel_line
Domain Operation: add_panel_line
Implementation Hint: modifier-based bevel preparation or curve-based detail, depending on milestone
```

The rule does not say “add bevel modifier.” It says the surface needs structural breakup. The Operation Planner chooses the domain operation, and the Interface Layer chooses the implementation.

## 7. Operation Planning Layer

The Operation Planner converts rule decisions into domain-level operations. Operations must express mecha design intent, not Blender implementation details.

### 7.1 Domain-Level Operation Request

Preferred shape:

```json
{
  "request_version": "v1_0",
  "execution_mode": "modify_copy",
  "target_object": "ChestArmor_Upper_01",
  "operation": "edge_soften",
  "parameters": {
    "strength": 0.01,
    "style": "mechanical"
  },
  "implementation_hint": {
    "method": "modifier",
    "type": "bevel",
    "modifier_name": "AI_PanelLine_Bevel"
  },
  "source_blend_file": "examples/BlendFile/Gundam/GF-Gundam.blend",
  "output_blend_file": "outputs/GF-Gundam.modified.blend"
}
```

The operation is `edge_soften`, not `add_modifier`. Blender specifics live under `implementation_hint`.

### 7.2 Operation Naming Rules

Operation names must reflect mecha design intent:

```text
edge_soften
add_panel_line
add_armor_plate
reinforce_joint
route_mechanical_pipe
add_thruster_detail
add_sensor_housing
```

Operation names must not expose Blender API details:

```text
add_modifier
create_mesh
run_bpy_op
boolean_cut
```

## 8. Interface Layer Design Principles

The interface layer is a core moat of the Agent. It turns natural language intent into controlled, testable Blender operations.

### 8.1 Why Raw `bpy` Is Not Exposed

Raw `bpy` should not be exposed to AI planning or rule logic because:

1. it is too low-level for design intent;
2. it makes generated operations hard to audit;
3. it encourages backend-specific decisions too early;
4. it makes debugging difficult;
5. it increases risk of unsafe file or mesh operations.

### 8.2 Why Domain API Is Required

The Domain Operation Layer provides stable mecha operations such as `edge_soften`, `add_panel_line`, and `reinforce_joint`.

This enables:

1. controllability: only approved operations can run;
2. debugging: each operation maps to a known implementation path;
3. AI integration: the planner chooses domain verbs, not Blender calls;
4. future expansion: the backend can change while the domain contract stays stable;
5. testability: each domain operation can be tested independently.

### 8.3 Layer Dependency Rule

```text
Rule Engine -> Operation Planner -> Domain Operation Layer -> Core Geometry API -> Blender Execution
```

Rules must not call Domain Operations directly. Domain Operations must not leak `bpy` details to the planner. Core Geometry API may wrap `bpy`, but should have no mecha-domain meaning.

## 9. Interface Layer Design

The interface layer has two explicit levels.

### 9.1 Core Geometry API (Low Level)

Purpose: safe wrapper around `bpy`.

Characteristics:

1. no domain meaning;
2. only geometry, object, modifier, transform, material, and file operations;
3. reusable by multiple domain operations;
4. isolated from natural language and rule logic.

Examples:

```text
add_bevel_modifier
apply_modifier
get_surface_area
get_bbox
get_object_transform
require_object
object_snapshot
save_as_copy_only
```

Core API examples are allowed to mention Blender-level concepts because this is the backend wrapper layer.

### 9.2 Domain Operation Layer (High Level)

Purpose: translate mecha operations into geometry actions.

Characteristics:

1. exposes mecha-domain operations;
2. does not expose `bpy` details;
3. calls Core Geometry API internally;
4. is the only layer used by future AI and rule-driven planning.

Examples:

```text
edge_soften
create_panel_line
add_armor_plate
reinforce_joint
route_mechanical_pipe
```

Example mapping:

```text
Domain Operation: edge_soften
-> Core Geometry API: add_bevel_modifier
-> Blender Execution: create non-applied bevel modifier on copied file
```

## 10. Core vs. Future Interface Categories

The first implementation milestone should focus on modifier-based real modification. Other categories remain planned but should not distract from V1.0A.

### 10.1 Object and Scene Binding Interfaces

Core methods:

```text
find_object
require_object
object_snapshot
object_type_check
mesh_data_snapshot
```

Business role:

```text
Make sure the Agent modifies the intended model part, not an unrelated object.
```

### 10.2 Modifier Operation Interfaces

Core methods:

```text
add_bevel_modifier
add_weighted_normal_modifier
add_solidify_modifier
remove_or_replace_named_modifier
configure_modifier_visibility
```

Business role:

```text
Support armor edge sharpening, panel-line preparation, thickness preview, and surface finish control.
```

### 10.3 Mesh Operation Interfaces

Core methods, later only:

```text
create_mesh_from_profile
extrude_region_controlled
boolean_cut_controlled
apply_modifier_with_report
```

Business role:

```text
Support real grooves, vents, armor panels, sockets, and mechanical cuts.
```

This category should not be first.

### 10.4 Curve Operation Interfaces

Core methods:

```text
create_panel_line_curve
create_pipe_route_curve
create_hydraulic_axis_curve
convert_curve_to_mesh_copy
```

Business role:

```text
Support panel lines, pipes, cables, hydraulic rods, and route-based mechanical details.
```

### 10.5 Component Placement Interfaces

Core methods:

```text
create_armor_plate_component
create_thruster_placeholder_component
create_vent_component
create_mount_socket_component
mirror_component_pair
```

Business role:

```text
Support layered armor, backpack details, vents, hardpoints, and symmetry-driven mecha structures.
```

### 10.6 Material and Naming Interfaces

Core methods:

```text
ensure_material
assign_material
generate_operation_name
tag_modified_object
tag_generated_object
```

Business role:

```text
Make Agent-created changes traceable inside Blender.
```

### 10.7 File Policy Interfaces

Core methods:

```text
save_as_copy_only
assert_not_source_file
resolve_output_blend_path
```

Business role:

```text
Protect the source file while still producing a modified .blend output.
```

### 10.8 Modification Report Interfaces

Core methods:

```text
build_modification_report
write_modification_report
record_modified_object
record_added_modifier
record_generated_object
```

Business role:

```text
Tell the user exactly what changed after a real operation.
```

Reports become core when real modification starts. Pure “nothing changed” diff reports are not a priority.

## 11. Mecha Business Logic Categories

The operation interface should map to these mecha design domains:

1. Armor surface detailing
   - panel lines
   - parting lines
   - edge sharpening
   - surface cleanup

2. Armor composition
   - layered armor
   - added armor plates
   - shield surface structure

3. Mechanical routing
   - pipes
   - cables
   - hydraulic rods
   - exposed inner frame lines

4. Propulsion detailing
   - thrusters
   - verniers
   - exhaust vents
   - backpack mechanical blocks

5. Sensor and head details
   - cameras
   - lenses
   - sensor housings

6. Weapon and mounting interfaces
   - hardpoints
   - sockets
   - weapon mounts

7. Manufacturing and scale constraints
   - 1/144 minimum readable detail
   - avoid fragile thin features
   - avoid unsupported floating details

## 12. Phase 2 Task List and Order

### Task 1: Freeze Preview Expansion

Status: policy decision.

Stop adding new preview-only features unless they directly support a real modification operation.

### Task 2: Define Rule Output Contract

Formalize the Rule Output Schema from Section 4 so downstream planning consumes design intent instead of implementation details.

### Task 3: Define Domain-Level Real Modification Request V1

Output:

```json
{
  "request_version": "v1_0",
  "execution_mode": "modify_copy",
  "target_object": "ChestArmor_Upper_01",
  "operation": "edge_soften",
  "parameters": {
    "strength": 0.01,
    "style": "mechanical"
  },
  "implementation_hint": {
    "method": "modifier",
    "type": "bevel",
    "modifier_name": "AI_PanelLine_Bevel"
  },
  "source_blend_file": "examples/BlendFile/Gundam/GF-Gundam.blend",
  "output_blend_file": "outputs/GF-Gundam.modified.blend"
}
```

### Task 4: Build Core Geometry API for Modifier Operations

Implement Blender-side helper methods:

```text
require_object
object_snapshot
add_bevel_modifier
remove_or_replace_named_modifier
save_as_copy_only
build_modification_report
write_modification_report
```

This is the first core interface milestone.

### Task 5: Build Domain Operation Layer for `edge_soften`

Implement the domain operation:

```text
edge_soften
```

It should call Core Geometry API internally and use `implementation_hint` to select the bevel modifier implementation.

### Task 6: Add CLI for Real Modification

Suggested first CLI:

```powershell
--modify-copy
--operation edge_soften
--output-blend-copy <path>
```

The first implementation may use fixed conservative bevel parameters, then later derive them from scale and design rules.

### Task 7: Execute First Real Modification

Use Blender background mode to:

1. open source `.blend`;
2. find bound target object;
3. execute `edge_soften` through the Domain Operation Layer;
4. call Core Geometry API to add a named bevel modifier;
5. save output copy;
6. write modification report.

### Task 8: Add User-Facing Modification Report

Report only actual changes:

```json
{
  "modification_status": "success",
  "modified_objects": [
    {
      "object_name": "ChestArmor_Upper_01",
      "operation": "edge_soften",
      "implementation": {
        "method": "modifier",
        "modifier_name": "AI_PanelLine_Bevel",
        "modifier_type": "BEVEL"
      },
      "parameters": {
        "strength": 0.01,
        "segments": 1,
        "affect": "ANGLE"
      },
      "mesh_data_applied": false
    }
  ],
  "saved_original_file": false,
  "output_blend_copy": "outputs/GF-Gundam.modified.blend"
}
```

### Task 9: Connect Rule Outputs to Operation Parameters

Use rule review and scale to control domain parameters:

```text
1/144 -> lower strength, fewer segments
heavy armor -> slightly stronger edge treatment
clean anime -> restrained edge treatment
sharp mechanical -> crisp edge treatment
```

### Task 10: Expand Real Modification Operations

After the bevel modifier path is stable, add operations in this order:

1. weighted normal support for surface finish
2. solidify support for armor thickness experiments
3. curve-based panel line object attached to target object
4. armor plate component creation
5. pipe route curve
6. controlled boolean or mesh edit only after reports and rollback are reliable

## 13. Milestone Plan

### Phase 2.1: V1.0A Modifier-Based Real Modification

Goal:

```text
Execute edge_soften by adding a named bevel modifier to a bound target object in a copied .blend file.
```

Validation:

```text
output .blend exists
target object has AI_PanelLine_Bevel modifier
source file is not overwritten
modification_report.json records the domain operation and modifier implementation
tests pass
```

### Phase 2.2: V1.0B Rule-Driven Modifier Parameters

Goal:

```text
Derive edge_soften strength and implementation parameters from scale, density, style, and rule outputs.
```

### Phase 2.3: V1.1 Component/Curve Modification

Goal:

```text
Add real generated components or curves that are part of the modified model workflow, not standalone preview features.
```

### Phase 2.4: V1.2 Controlled Mesh Editing

Goal:

```text
Only after modifier/component operations are stable, introduce direct mesh/boolean operations with explicit user confirmation and reports.
```

## 14. Immediate Next Development Task

The next implementation task should be:

```text
V1.0A Modifier-Based Real Model Modification
```

Do not implement more preview or helper-guide features before V1.0A.

The first concrete change should add:

1. Rule Output consumption by the Operation Planner;
2. a domain-level `edge_soften` modification request;
3. a two-level Interface Layer path from `edge_soften` to `add_bevel_modifier`;
4. a Blender execution flow that adds `AI_PanelLine_Bevel` to `ChestArmor_Upper_01` in `outputs/GF-Gundam.modified.blend`;
5. a modification report that tells the user what changed.

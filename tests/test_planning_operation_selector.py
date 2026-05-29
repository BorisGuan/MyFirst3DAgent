import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
AGENT_ROOT = PROJECT_ROOT / "3d_agent"
if str(AGENT_ROOT) not in sys.path:
    sys.path.insert(0, str(AGENT_ROOT))

from domain import OperationRegistry, OperationSpec
from planning import OperationSelectionError, select_operation
from task_object import TaskIntent, TaskObject, TaskSource, TaskState, TaskTarget


def bound_task() -> TaskObject:
    return TaskObject(
        state=TaskState.BOUND,
        source=TaskSource(user_input="给胸甲做机械风格边缘软化", channel="agent_layer"),
        task_type="surface_detail_enhancement",
        target=TaskTarget(
            semantic_part="chest_armor",
            bound_object="ChestArmor_Upper_01",
            binding_candidates=["ChestArmor_Upper_01"],
        ),
        intent=TaskIntent(
            desired_effect="armor_layers",
            style="mechanical",
            density="low",
            scale="1/144",
        ),
    )


def selector_spec(
    name: str,
    *,
    intent_actions: tuple[str, ...] = (),
    intent_detail_types: tuple[str, ...] = (),
    intent_effects: tuple[str, ...] = (),
    priority: int = 100,
) -> OperationSpec:
    return OperationSpec(
        name=name,
        supported_task_types=("surface_detail_enhancement",),
        required_target_state="bound",
        safety_level="safe_non_destructive",
        handler_name=name,
        intent_actions=intent_actions,
        intent_detail_types=intent_detail_types,
        intent_effects=intent_effects,
        priority=priority,
    )


class PlanningOperationSelectorTests(unittest.TestCase):
    def test_selects_edge_soften_for_supported_bound_task(self) -> None:
        task = bound_task()

        returned_task = select_operation(task)

        self.assertIs(returned_task, task)
        self.assertEqual(task.state, TaskState.BOUND)
        self.assertEqual(task.planning.selected_operation, "edge_soften")
        self.assertEqual(task.planning.parameters, {})
        self.assertEqual(len(task.planning.reasoning), 1)
        self.assertIn("edge_soften", task.planning.reasoning[0])
        self.assertIn("operation registry", task.planning.reasoning[0])

    def test_default_registry_selects_panel_line_bevel_prepare_for_panel_line_intent(self) -> None:
        task = bound_task()
        task.intent.action = "add_panel_lines"
        task.intent.detail_type = "panel_lines"
        task.intent.desired_effect = "panel_lines"

        select_operation(task)

        self.assertEqual(task.planning.selected_operation, "panel_line_bevel_prepare")
        self.assertIn("intent score", task.planning.reasoning[0])

    def test_default_registry_selects_weighted_normal_finish_for_shading_intent(self) -> None:
        task = bound_task()
        task.intent.action = "improve_shading"
        task.intent.detail_type = "weighted_normal"
        task.intent.desired_effect = "hard_surface_shading_finish"

        select_operation(task)

        self.assertEqual(task.planning.selected_operation, "weighted_normal_finish")
        self.assertIn("intent score", task.planning.reasoning[0])
        self.assertIn("intent.detail_type=weighted_normal", task.planning.reasoning[0])

    def test_default_registry_selects_solidify_thickness_preview_for_thickness_intent(self) -> None:
        task = bound_task()
        task.intent.action = "add_thickness_preview"
        task.intent.detail_type = "armor_thickness"
        task.intent.desired_effect = "heavy_armor_feel"

        select_operation(task)

        self.assertEqual(task.planning.selected_operation, "solidify_thickness_preview")
        self.assertIn("intent score", task.planning.reasoning[0])
        self.assertIn("intent.detail_type=armor_thickness", task.planning.reasoning[0])

    def test_default_registry_selects_armor_layer_plate_prepare_for_layering_intent(self) -> None:
        task = bound_task()
        task.intent.action = "prepare_armor_layers"
        task.intent.detail_type = "armor_layer_plate"
        task.intent.desired_effect = "armor_layer_preparation"

        select_operation(task)

        self.assertEqual(task.planning.selected_operation, "armor_layer_plate_prepare")
        self.assertIn("intent score", task.planning.reasoning[0])
        self.assertIn("intent.detail_type=armor_layer_plate", task.planning.reasoning[0])

    def test_default_registry_selects_vent_slot_prepare_for_vent_intent(self) -> None:
        task = bound_task()
        task.intent.action = "add_vents"
        task.intent.detail_type = "vents"
        task.intent.desired_effect = "vent_slot_preparation"

        select_operation(task)

        self.assertEqual(task.planning.selected_operation, "vent_slot_prepare")
        self.assertIn("intent score", task.planning.reasoning[0])
        self.assertIn("intent.detail_type=vents", task.planning.reasoning[0])

    def test_default_registry_selects_thruster_nozzle_prepare_for_thruster_intent(self) -> None:
        task = bound_task()
        task.intent.action = "add_thrusters"
        task.intent.detail_type = "thrusters"
        task.intent.desired_effect = "thruster_nozzle_preparation"

        select_operation(task)

        self.assertEqual(task.planning.selected_operation, "thruster_nozzle_prepare")
        self.assertIn("intent score", task.planning.reasoning[0])
        self.assertIn("intent.detail_type=thrusters", task.planning.reasoning[0])

    def test_default_registry_selects_hardpoint_socket_prepare_for_weapon_mount_intent(self) -> None:
        task = bound_task()
        task.intent.action = "add_weapon_mounts"
        task.intent.detail_type = "hardpoint_socket"
        task.intent.desired_effect = "hardpoint_socket_preparation"

        select_operation(task)

        self.assertEqual(task.planning.selected_operation, "hardpoint_socket_prepare")
        self.assertIn("intent score", task.planning.reasoning[0])
        self.assertIn("intent.detail_type=hardpoint_socket", task.planning.reasoning[0])

    def test_default_registry_selects_surface_inset_prepare_for_inset_intent(self) -> None:
        task = bound_task()
        task.intent.action = "prepare_surface_inset"
        task.intent.detail_type = "surface_inset"
        task.intent.desired_effect = "surface_inset_preparation"

        select_operation(task)

        self.assertEqual(task.planning.selected_operation, "surface_inset_prepare")
        self.assertIn("intent score", task.planning.reasoning[0])
        self.assertIn("intent.detail_type=surface_inset", task.planning.reasoning[0])

    def test_default_registry_selects_armor_edge_lip_prepare_for_edge_lip_intent(self) -> None:
        task = bound_task()
        task.intent.action = "prepare_armor_edge_lip"
        task.intent.detail_type = "armor_edge_lip"
        task.intent.desired_effect = "armor_edge_lip_preparation"

        select_operation(task)

        self.assertEqual(task.planning.selected_operation, "armor_edge_lip_prepare")
        self.assertIn("intent score", task.planning.reasoning[0])
        self.assertIn("intent.detail_type=armor_edge_lip", task.planning.reasoning[0])

    def test_rejects_non_bound_task(self) -> None:
        task = bound_task()
        task.state = TaskState.VALIDATED

        with self.assertRaises(OperationSelectionError) as error_context:
            select_operation(task)

        self.assertIn("state must be 'bound'", str(error_context.exception))

    def test_rejects_bound_state_without_bound_object(self) -> None:
        task = bound_task()
        task.target.bound_object = None

        with self.assertRaises(OperationSelectionError) as error_context:
            select_operation(task)

        self.assertIn("target.bound_object is required", str(error_context.exception))

    def test_rejects_unsupported_task_type(self) -> None:
        task = bound_task()
        task.task_type = "unsupported_task"

        with self.assertRaises(OperationSelectionError) as error_context:
            select_operation(task)

        self.assertIn("No registered operation supports task_type", str(error_context.exception))

    def test_rejects_incompatible_safety_policy(self) -> None:
        task = bound_task()
        task.execution_policy.mode = "unsafe_destructive"

        with self.assertRaises(OperationSelectionError) as error_context:
            select_operation(task)

        self.assertIn("execution_policy.mode", str(error_context.exception))

    def test_uses_registry_instead_of_hardcoded_unregistered_operations(self) -> None:
        task = bound_task()
        registry = OperationRegistry(
            (
                OperationSpec(
                    name="custom_safe_operation",
                    supported_task_types=("surface_detail_enhancement",),
                    required_target_state="bound",
                    safety_level="safe_non_destructive",
                    handler_name="custom_safe_operation",
                ),
            )
        )

        select_operation(task, registry=registry)

        self.assertEqual(task.planning.selected_operation, "custom_safe_operation")

    def test_selects_explicit_operation_parameter_when_compatible(self) -> None:
        task = bound_task()
        task.intent.action = "soften_edges"
        task.intent.parameters["operation"] = "weighted_normal_finish"
        registry = OperationRegistry(
            (
                selector_spec("edge_soften", intent_actions=("soften_edges",), priority=10),
                selector_spec("weighted_normal_finish", priority=100),
            )
        )

        select_operation(task, registry=registry)

        self.assertEqual(task.planning.selected_operation, "weighted_normal_finish")
        self.assertIn("explicitly requested", task.planning.reasoning[0])

    def test_selects_highest_intent_score_instead_of_first_compatible_operation(self) -> None:
        task = bound_task()
        task.intent.action = "improve_shading"
        task.intent.detail_type = "weighted_normal"
        task.intent.desired_effect = "hard_surface_shading_finish"
        registry = OperationRegistry(
            (
                selector_spec("edge_soften", intent_actions=("soften_edges",), priority=10),
                selector_spec(
                    "weighted_normal_finish",
                    intent_actions=("improve_shading",),
                    intent_detail_types=("weighted_normal",),
                    intent_effects=("hard_surface_shading_finish",),
                    priority=100,
                ),
            )
        )

        select_operation(task, registry=registry)

        self.assertEqual(task.planning.selected_operation, "weighted_normal_finish")
        self.assertIn("intent score", task.planning.reasoning[0])
        self.assertIn("intent.detail_type=weighted_normal", task.planning.reasoning[0])

    def test_uses_priority_as_stable_tie_break_for_same_intent_score(self) -> None:
        task = bound_task()
        task.intent.action = "prepare_surface"
        registry = OperationRegistry(
            (
                selector_spec("alpha_lower_name", intent_actions=("prepare_surface",), priority=50),
                selector_spec("zeta_higher_priority", intent_actions=("prepare_surface",), priority=10),
            )
        )

        select_operation(task, registry=registry)

        self.assertEqual(task.planning.selected_operation, "zeta_higher_priority")

    def test_rejects_ambiguous_selection_when_multiple_specs_have_no_intent_match(self) -> None:
        task = bound_task()
        task.intent.desired_effect = "unmatched_effect"
        registry = OperationRegistry(
            (
                selector_spec("edge_soften"),
                selector_spec("weighted_normal_finish"),
            )
        )

        with self.assertRaises(OperationSelectionError) as error_context:
            select_operation(task, registry=registry)

        self.assertIn("ambiguous", str(error_context.exception))

    def test_rejects_ambiguous_selection_when_score_and_priority_are_tied(self) -> None:
        task = bound_task()
        task.intent.action = "prepare_surface"
        registry = OperationRegistry(
            (
                selector_spec("edge_soften", intent_actions=("prepare_surface",), priority=100),
                selector_spec("weighted_normal_finish", intent_actions=("prepare_surface",), priority=100),
            )
        )

        with self.assertRaises(OperationSelectionError) as error_context:
            select_operation(task, registry=registry)

        self.assertIn("same intent score", str(error_context.exception))

    def test_selector_does_not_generate_modifier_or_execution_parameters(self) -> None:
        task = bound_task()

        select_operation(task)

        self.assertNotIn("modifier", " ".join(task.planning.reasoning).lower())
        self.assertEqual(task.planning.parameters, {})
        self.assertIsNone(task.runtime.source_blend_file)
        self.assertIsNone(task.result.success)

    def test_selector_has_no_domain_core_cli_or_blender_dependency(self) -> None:
        source = (AGENT_ROOT / "planning" / "operation_selector.py").read_text(encoding="utf-8")

        self.assertNotIn("import bpy", source)
        self.assertNotIn("bpy.", source)
        self.assertNotIn("from blender_ops", source)
        self.assertNotIn("domain_operations", source)
        self.assertNotIn("core_geometry_api", source)
        self.assertNotIn("operation_planner", source)
        self.assertNotIn("modification_execution", source)
        self.assertNotIn("argparse", source)
        self.assertNotIn("--operation", source)


if __name__ == "__main__":
    unittest.main()
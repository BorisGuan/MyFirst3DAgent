import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
AGENT_ROOT = PROJECT_ROOT / "3d_agent"
if str(AGENT_ROOT) not in sys.path:
    sys.path.insert(0, str(AGENT_ROOT))

from domain import OperationRegistry, OperationSpec
from planning import ParameterCompletionError, complete_parameters
from task_object import TaskIntent, TaskObject, TaskPlanning, TaskSource, TaskState, TaskTarget


def selected_bound_task(intent_parameters: dict | None = None) -> TaskObject:
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
            parameters=intent_parameters or {},
        ),
        planning=TaskPlanning(
            selected_operation="edge_soften",
            reasoning=["Selected edge_soften through registry."],
        ),
    )


def selected_weighted_normal_task(intent_parameters: dict | None = None) -> TaskObject:
    task = selected_bound_task(intent_parameters)
    task.intent.action = "improve_shading"
    task.intent.detail_type = "weighted_normal"
    task.intent.desired_effect = "hard_surface_shading_finish"
    task.planning.selected_operation = "weighted_normal_finish"
    task.planning.reasoning = ["Selected weighted_normal_finish through registry."]
    return task


def selected_solidify_task(intent_parameters: dict | None = None) -> TaskObject:
    task = selected_bound_task(intent_parameters)
    task.intent.action = "add_thickness_preview"
    task.intent.detail_type = "armor_thickness"
    task.intent.desired_effect = "heavy_armor_feel"
    task.planning.selected_operation = "solidify_thickness_preview"
    task.planning.reasoning = ["Selected solidify_thickness_preview through registry."]
    return task


def selected_panel_line_task(intent_parameters: dict | None = None) -> TaskObject:
    task = selected_bound_task(intent_parameters)
    task.intent.action = "add_panel_lines"
    task.intent.detail_type = "panel_lines"
    task.intent.desired_effect = "panel_lines"
    task.planning.selected_operation = "panel_line_bevel_prepare"
    task.planning.reasoning = ["Selected panel_line_bevel_prepare through registry."]
    return task


def selected_armor_layer_task(intent_parameters: dict | None = None) -> TaskObject:
    task = selected_bound_task(intent_parameters)
    task.intent.action = "prepare_armor_layers"
    task.intent.detail_type = "armor_layer_plate"
    task.intent.desired_effect = "armor_layer_preparation"
    task.planning.selected_operation = "armor_layer_plate_prepare"
    task.planning.reasoning = ["Selected armor_layer_plate_prepare through registry."]
    return task


def selected_vent_slot_task(intent_parameters: dict | None = None) -> TaskObject:
    task = selected_bound_task(intent_parameters)
    task.intent.action = "add_vents"
    task.intent.detail_type = "vents"
    task.intent.desired_effect = "vent_slot_preparation"
    task.planning.selected_operation = "vent_slot_prepare"
    task.planning.reasoning = ["Selected vent_slot_prepare through registry."]
    return task


def selected_thruster_nozzle_task(intent_parameters: dict | None = None) -> TaskObject:
    task = selected_bound_task(intent_parameters)
    task.intent.action = "add_thrusters"
    task.intent.detail_type = "thrusters"
    task.intent.desired_effect = "thruster_nozzle_preparation"
    task.planning.selected_operation = "thruster_nozzle_prepare"
    task.planning.reasoning = ["Selected thruster_nozzle_prepare through registry."]
    return task


def selected_hardpoint_socket_task(intent_parameters: dict | None = None) -> TaskObject:
    task = selected_bound_task(intent_parameters)
    task.intent.action = "add_weapon_mounts"
    task.intent.detail_type = "hardpoint_socket"
    task.intent.desired_effect = "hardpoint_socket_preparation"
    task.planning.selected_operation = "hardpoint_socket_prepare"
    task.planning.reasoning = ["Selected hardpoint_socket_prepare through registry."]
    return task


def selected_surface_inset_task(intent_parameters: dict | None = None) -> TaskObject:
    task = selected_bound_task(intent_parameters)
    task.intent.action = "prepare_surface_inset"
    task.intent.detail_type = "surface_inset"
    task.intent.desired_effect = "surface_inset_preparation"
    task.planning.selected_operation = "surface_inset_prepare"
    task.planning.reasoning = ["Selected surface_inset_prepare through registry."]
    return task


def selected_armor_edge_lip_task(intent_parameters: dict | None = None) -> TaskObject:
    task = selected_bound_task(intent_parameters)
    task.intent.action = "prepare_armor_edge_lip"
    task.intent.detail_type = "armor_edge_lip"
    task.intent.desired_effect = "armor_edge_lip_preparation"
    task.planning.selected_operation = "armor_edge_lip_prepare"
    task.planning.reasoning = ["Selected armor_edge_lip_prepare through registry."]
    return task


class PlanningParameterCompleterTests(unittest.TestCase):
    def test_completes_edge_soften_default_parameters_and_enters_planned(self) -> None:
        task = selected_bound_task()

        returned_task = complete_parameters(task)

        self.assertIs(returned_task, task)
        self.assertEqual(task.state, TaskState.PLANNED)
        self.assertEqual(task.planning.parameters, {"strength": 0.01, "style": "mechanical"})
        self.assertEqual(task.planning.selected_operation, "edge_soften")
        self.assertEqual(len(task.planning.reasoning), 2)
        self.assertIn("Completed parameters", task.planning.reasoning[-1])

    def test_explicit_intent_parameters_override_defaults(self) -> None:
        task = selected_bound_task({"strength": 0.02, "style": "clean"})

        complete_parameters(task)

        self.assertEqual(task.planning.parameters, {"strength": 0.02, "style": "clean"})

    def test_completes_weighted_normal_finish_default_parameters(self) -> None:
        task = selected_weighted_normal_task()

        complete_parameters(task)

        self.assertEqual(
            task.planning.parameters,
            {"weight": 50.0, "keep_sharp": "true", "modifier_name": "AI_WeightedNormal_Finish"},
        )

    def test_completes_weighted_normal_finish_explicit_parameters(self) -> None:
        task = selected_weighted_normal_task(
            {
                "operation": "weighted_normal_finish",
                "weight": 25.0,
                "keep_sharp": "false",
                "modifier_name": "AI_Custom_Normal",
            }
        )

        complete_parameters(task)

        self.assertEqual(
            task.planning.parameters,
            {"weight": 25.0, "keep_sharp": "false", "modifier_name": "AI_Custom_Normal"},
        )

    def test_completes_solidify_thickness_preview_default_parameters(self) -> None:
        task = selected_solidify_task()

        complete_parameters(task)

        self.assertEqual(
            task.planning.parameters,
            {"thickness": 0.015, "offset": 0.0, "modifier_name": "AI_Solidify_ThicknessPreview"},
        )

    def test_completes_solidify_thickness_preview_explicit_parameters(self) -> None:
        task = selected_solidify_task(
            {
                "operation": "solidify_thickness_preview",
                "thickness": 0.025,
                "offset": -1.0,
                "modifier_name": "AI_Custom_Solidify",
            }
        )

        complete_parameters(task)

        self.assertEqual(
            task.planning.parameters,
            {"thickness": 0.025, "offset": -1.0, "modifier_name": "AI_Custom_Solidify"},
        )

    def test_completes_panel_line_bevel_prepare_default_parameters(self) -> None:
        task = selected_panel_line_task()

        complete_parameters(task)

        self.assertEqual(
            task.planning.parameters,
            {"width": 0.006, "segments": 1, "modifier_name": "AI_PanelLine_Prepare"},
        )

    def test_completes_panel_line_bevel_prepare_explicit_parameters(self) -> None:
        task = selected_panel_line_task(
            {
                "operation": "panel_line_bevel_prepare",
                "width": 0.008,
                "segments": 2,
                "modifier_name": "AI_Custom_PanelLine",
            }
        )

        complete_parameters(task)

        self.assertEqual(
            task.planning.parameters,
            {"width": 0.008, "segments": 2, "modifier_name": "AI_Custom_PanelLine"},
        )

    def test_completes_armor_layer_plate_prepare_default_parameters(self) -> None:
        task = selected_armor_layer_task()

        complete_parameters(task)

        self.assertEqual(
            task.planning.parameters,
            {"layer_depth": 0.01, "offset": 1.0, "modifier_name": "AI_ArmorLayer_PlatePrepare"},
        )

    def test_completes_armor_layer_plate_prepare_explicit_parameters(self) -> None:
        task = selected_armor_layer_task(
            {
                "operation": "armor_layer_plate_prepare",
                "layer_depth": 0.02,
                "offset": 0.75,
                "modifier_name": "AI_Custom_ArmorLayer",
            }
        )

        complete_parameters(task)

        self.assertEqual(
            task.planning.parameters,
            {"layer_depth": 0.02, "offset": 0.75, "modifier_name": "AI_Custom_ArmorLayer"},
        )

    def test_completes_vent_slot_prepare_default_parameters(self) -> None:
        task = selected_vent_slot_task()

        complete_parameters(task)

        self.assertEqual(
            task.planning.parameters,
            {"width": 0.004, "segments": 1, "modifier_name": "AI_VentSlot_Prepare"},
        )

    def test_completes_vent_slot_prepare_explicit_parameters(self) -> None:
        task = selected_vent_slot_task(
            {
                "operation": "vent_slot_prepare",
                "width": 0.005,
                "segments": 2,
                "modifier_name": "AI_Custom_VentSlot",
            }
        )

        complete_parameters(task)

        self.assertEqual(
            task.planning.parameters,
            {"width": 0.005, "segments": 2, "modifier_name": "AI_Custom_VentSlot"},
        )

    def test_completes_thruster_nozzle_prepare_default_parameters(self) -> None:
        task = selected_thruster_nozzle_task()

        complete_parameters(task)

        self.assertEqual(
            task.planning.parameters,
            {"width": 0.008, "segments": 2, "modifier_name": "AI_ThrusterNozzle_Prepare"},
        )

    def test_completes_thruster_nozzle_prepare_explicit_parameters(self) -> None:
        task = selected_thruster_nozzle_task(
            {
                "operation": "thruster_nozzle_prepare",
                "width": 0.012,
                "segments": 3,
                "modifier_name": "AI_Custom_ThrusterNozzle",
            }
        )

        complete_parameters(task)

        self.assertEqual(
            task.planning.parameters,
            {"width": 0.012, "segments": 3, "modifier_name": "AI_Custom_ThrusterNozzle"},
        )

    def test_completes_hardpoint_socket_prepare_default_parameters(self) -> None:
        task = selected_hardpoint_socket_task()

        complete_parameters(task)

        self.assertEqual(
            task.planning.parameters,
            {"width": 0.006, "segments": 2, "modifier_name": "AI_HardpointSocket_Prepare"},
        )

    def test_completes_hardpoint_socket_prepare_explicit_parameters(self) -> None:
        task = selected_hardpoint_socket_task(
            {
                "operation": "hardpoint_socket_prepare",
                "width": 0.01,
                "segments": 3,
                "modifier_name": "AI_Custom_HardpointSocket",
            }
        )

        complete_parameters(task)

        self.assertEqual(
            task.planning.parameters,
            {"width": 0.01, "segments": 3, "modifier_name": "AI_Custom_HardpointSocket"},
        )

    def test_completes_surface_inset_prepare_default_parameters(self) -> None:
        task = selected_surface_inset_task()

        complete_parameters(task)

        self.assertEqual(
            task.planning.parameters,
            {"inset_depth": 0.006, "offset": -1.0, "modifier_name": "AI_SurfaceInset_Prepare"},
        )

    def test_completes_surface_inset_prepare_explicit_parameters(self) -> None:
        task = selected_surface_inset_task(
            {
                "operation": "surface_inset_prepare",
                "inset_depth": 0.01,
                "offset": -0.75,
                "modifier_name": "AI_Custom_SurfaceInset",
            }
        )

        complete_parameters(task)

        self.assertEqual(
            task.planning.parameters,
            {"inset_depth": 0.01, "offset": -0.75, "modifier_name": "AI_Custom_SurfaceInset"},
        )

    def test_completes_armor_edge_lip_prepare_default_parameters(self) -> None:
        task = selected_armor_edge_lip_task()

        complete_parameters(task)

        self.assertEqual(
            task.planning.parameters,
            {"width": 0.008, "segments": 2, "modifier_name": "AI_ArmorEdgeLip_Prepare"},
        )

    def test_completes_armor_edge_lip_prepare_explicit_parameters(self) -> None:
        task = selected_armor_edge_lip_task(
            {
                "operation": "armor_edge_lip_prepare",
                "width": 0.012,
                "segments": 3,
                "modifier_name": "AI_Custom_ArmorEdgeLip",
            }
        )

        complete_parameters(task)

        self.assertEqual(
            task.planning.parameters,
            {"width": 0.012, "segments": 3, "modifier_name": "AI_Custom_ArmorEdgeLip"},
        )

    def test_rejects_invalid_strength(self) -> None:
        for invalid_strength in (0.0, -0.1, "0.02", True):
            with self.subTest(invalid_strength=invalid_strength):
                with self.assertRaises(ParameterCompletionError):
                    complete_parameters(selected_bound_task({"strength": invalid_strength}))

    def test_rejects_invalid_style(self) -> None:
        for invalid_style in ("unknown", 10):
            with self.subTest(invalid_style=invalid_style):
                with self.assertRaises(ParameterCompletionError):
                    complete_parameters(selected_bound_task({"style": invalid_style}))

    def test_rejects_unsupported_explicit_parameter(self) -> None:
        with self.assertRaises(ParameterCompletionError) as error_context:
            complete_parameters(selected_bound_task({"segments": 3}))

        self.assertIn("Unsupported parameter", str(error_context.exception))

    def test_rejects_non_bound_task(self) -> None:
        task = selected_bound_task()
        task.state = TaskState.VALIDATED

        with self.assertRaises(ParameterCompletionError) as error_context:
            complete_parameters(task)

        self.assertIn("state must be 'bound'", str(error_context.exception))

    def test_rejects_missing_selected_operation(self) -> None:
        task = selected_bound_task()
        task.planning.selected_operation = None

        with self.assertRaises(ParameterCompletionError) as error_context:
            complete_parameters(task)

        self.assertIn("planning.selected_operation is required", str(error_context.exception))

    def test_rejects_unregistered_selected_operation(self) -> None:
        task = selected_bound_task()
        task.planning.selected_operation = "add_panel_line"

        with self.assertRaises(ParameterCompletionError) as error_context:
            complete_parameters(task)

        self.assertIn("Unsupported operation", str(error_context.exception))

    def test_uses_registry_parameter_schema(self) -> None:
        task = selected_bound_task({"width": 0.4})
        registry = OperationRegistry(
            (
                OperationSpec(
                    name="edge_soften",
                    supported_task_types=("surface_detail_enhancement",),
                    required_target_state="bound",
                    default_parameters={"width": 0.1},
                    parameter_schema={"width": {"type": "number", "exclusive_minimum": 0.0}},
                    safety_level="safe_non_destructive",
                    handler_name="edge_soften",
                ),
            )
        )

        complete_parameters(task, registry=registry)

        self.assertEqual(task.planning.parameters, {"width": 0.4})

    def test_completer_does_not_write_runtime_result_or_call_execution_layers(self) -> None:
        task = selected_bound_task()

        complete_parameters(task)

        self.assertIsNone(task.runtime.source_blend_file)
        self.assertIsNone(task.runtime.output_blend_copy)
        self.assertIsNone(task.runtime.report_file)
        self.assertIsNone(task.result.success)

    def test_completer_has_no_domain_core_runtime_or_blender_dependency(self) -> None:
        source = (AGENT_ROOT / "planning" / "parameter_completer.py").read_text(encoding="utf-8")

        self.assertNotIn("import bpy", source)
        self.assertNotIn("bpy.", source)
        self.assertNotIn("from blender_ops", source)
        self.assertNotIn("domain_operations", source)
        self.assertNotIn("core_geometry_api", source)
        self.assertNotIn("from runtime", source)
        self.assertNotIn("operation_planner", source)
        self.assertNotIn("modification_execution", source)
        self.assertNotIn("report_file", source)


if __name__ == "__main__":
    unittest.main()
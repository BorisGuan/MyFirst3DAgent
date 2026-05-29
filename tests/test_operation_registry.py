import json
import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
AGENT_ROOT = PROJECT_ROOT / "3d_agent"
if str(AGENT_ROOT) not in sys.path:
    sys.path.insert(0, str(AGENT_ROOT))

from domain import OperationRegistry, OperationRegistryError, OperationSpec, default_operation_registry


class OperationRegistryTests(unittest.TestCase):
    def test_default_registry_exposes_supported_real_operations(self) -> None:
        registry = default_operation_registry()

        self.assertTrue(registry.has("edge_soften"))
        self.assertTrue(registry.has("weighted_normal_finish"))
        self.assertTrue(registry.has("solidify_thickness_preview"))
        self.assertTrue(registry.has("panel_line_bevel_prepare"))
        self.assertTrue(registry.has("armor_layer_plate_prepare"))
        self.assertTrue(registry.has("vent_slot_prepare"))
        self.assertTrue(registry.has("thruster_nozzle_prepare"))
        self.assertTrue(registry.has("hardpoint_socket_prepare"))
        self.assertTrue(registry.has("surface_inset_prepare"))
        self.assertTrue(registry.has("armor_edge_lip_prepare"))
        self.assertEqual(
            [operation.name for operation in registry.all_specs()],
            [
                "edge_soften",
                "weighted_normal_finish",
                "solidify_thickness_preview",
                "panel_line_bevel_prepare",
                "armor_layer_plate_prepare",
                "vent_slot_prepare",
                "thruster_nozzle_prepare",
                "hardpoint_socket_prepare",
                "surface_inset_prepare",
                "armor_edge_lip_prepare",
            ],
        )

    def test_edge_soften_spec_contains_required_contract_fields(self) -> None:
        spec = default_operation_registry().get("edge_soften")

        self.assertEqual(spec.name, "edge_soften")
        self.assertEqual(spec.supported_task_types, ("surface_detail_enhancement",))
        self.assertEqual(spec.required_target_state, "bound")
        self.assertEqual(spec.default_parameters, {"strength": 0.01, "style": "mechanical"})
        self.assertEqual(spec.safety_level, "safe_non_destructive")
        self.assertEqual(spec.handler_name, "edge_soften")
        self.assertIn("soften_edges", spec.intent_actions)
        self.assertIn("bevel", spec.intent_detail_types)
        self.assertIn("armor_layers", spec.intent_effects)
        self.assertEqual(spec.priority, 100)
        self.assertIn("strength", spec.parameter_schema)
        self.assertIn("style", spec.parameter_schema)
        self.assertIn("required_fields", spec.report_schema)

    def test_weighted_normal_finish_spec_contains_required_contract_fields(self) -> None:
        spec = default_operation_registry().get("weighted_normal_finish")

        self.assertEqual(spec.name, "weighted_normal_finish")
        self.assertEqual(spec.supported_task_types, ("surface_detail_enhancement",))
        self.assertEqual(spec.required_target_state, "bound")
        self.assertEqual(
            spec.default_parameters,
            {"weight": 50.0, "keep_sharp": "true", "modifier_name": "AI_WeightedNormal_Finish"},
        )
        self.assertEqual(spec.safety_level, "safe_non_destructive")
        self.assertEqual(spec.handler_name, "weighted_normal_finish")
        self.assertIn("weight", spec.parameter_schema)
        self.assertIn("keep_sharp", spec.parameter_schema)
        self.assertIn("modifier_name", spec.parameter_schema)
        self.assertIn("improve_shading", spec.intent_actions)
        self.assertIn("weighted_normal", spec.intent_detail_types)
        self.assertIn("hard_surface_shading_finish", spec.intent_effects)
        self.assertIn("required_fields", spec.report_schema)

    def test_solidify_thickness_preview_spec_contains_required_contract_fields(self) -> None:
        spec = default_operation_registry().get("solidify_thickness_preview")

        self.assertEqual(spec.name, "solidify_thickness_preview")
        self.assertEqual(spec.supported_task_types, ("surface_detail_enhancement",))
        self.assertEqual(spec.required_target_state, "bound")
        self.assertEqual(
            spec.default_parameters,
            {"thickness": 0.015, "offset": 0.0, "modifier_name": "AI_Solidify_ThicknessPreview"},
        )
        self.assertEqual(spec.safety_level, "safe_non_destructive")
        self.assertEqual(spec.handler_name, "solidify_thickness_preview")
        self.assertIn("thickness", spec.parameter_schema)
        self.assertIn("offset", spec.parameter_schema)
        self.assertIn("modifier_name", spec.parameter_schema)
        self.assertIn("add_thickness_preview", spec.intent_actions)
        self.assertIn("armor_thickness", spec.intent_detail_types)
        self.assertIn("heavy_armor_feel", spec.intent_effects)
        self.assertIn("required_fields", spec.report_schema)

    def test_panel_line_bevel_prepare_spec_contains_required_contract_fields(self) -> None:
        spec = default_operation_registry().get("panel_line_bevel_prepare")

        self.assertEqual(spec.name, "panel_line_bevel_prepare")
        self.assertEqual(spec.supported_task_types, ("surface_detail_enhancement",))
        self.assertEqual(spec.required_target_state, "bound")
        self.assertEqual(
            spec.default_parameters,
            {"width": 0.006, "segments": 1, "modifier_name": "AI_PanelLine_Prepare"},
        )
        self.assertEqual(spec.safety_level, "safe_non_destructive")
        self.assertEqual(spec.handler_name, "panel_line_bevel_prepare")
        self.assertIn("width", spec.parameter_schema)
        self.assertIn("segments", spec.parameter_schema)
        self.assertIn("modifier_name", spec.parameter_schema)
        self.assertIn("add_panel_lines", spec.intent_actions)
        self.assertIn("parting_lines", spec.intent_detail_types)
        self.assertIn("panel_line_preparation", spec.intent_effects)
        self.assertIn("required_fields", spec.report_schema)

    def test_armor_layer_plate_prepare_spec_contains_required_contract_fields(self) -> None:
        spec = default_operation_registry().get("armor_layer_plate_prepare")

        self.assertEqual(spec.name, "armor_layer_plate_prepare")
        self.assertEqual(spec.supported_task_types, ("surface_detail_enhancement",))
        self.assertEqual(spec.required_target_state, "bound")
        self.assertEqual(
            spec.default_parameters,
            {"layer_depth": 0.01, "offset": 1.0, "modifier_name": "AI_ArmorLayer_PlatePrepare"},
        )
        self.assertEqual(spec.safety_level, "safe_non_destructive")
        self.assertEqual(spec.handler_name, "armor_layer_plate_prepare")
        self.assertIn("layer_depth", spec.parameter_schema)
        self.assertIn("offset", spec.parameter_schema)
        self.assertIn("modifier_name", spec.parameter_schema)
        self.assertIn("prepare_armor_layers", spec.intent_actions)
        self.assertIn("armor_layer_plate", spec.intent_detail_types)
        self.assertIn("armor_layer_preparation", spec.intent_effects)
        self.assertIn("required_fields", spec.report_schema)

    def test_vent_slot_prepare_spec_contains_required_contract_fields(self) -> None:
        spec = default_operation_registry().get("vent_slot_prepare")

        self.assertEqual(spec.name, "vent_slot_prepare")
        self.assertEqual(spec.supported_task_types, ("surface_detail_enhancement",))
        self.assertEqual(spec.required_target_state, "bound")
        self.assertEqual(
            spec.default_parameters,
            {"width": 0.004, "segments": 1, "modifier_name": "AI_VentSlot_Prepare"},
        )
        self.assertEqual(spec.safety_level, "safe_non_destructive")
        self.assertEqual(spec.handler_name, "vent_slot_prepare")
        self.assertIn("width", spec.parameter_schema)
        self.assertIn("segments", spec.parameter_schema)
        self.assertIn("modifier_name", spec.parameter_schema)
        self.assertIn("add_vents", spec.intent_actions)
        self.assertIn("vents", spec.intent_detail_types)
        self.assertIn("vent_slot_preparation", spec.intent_effects)
        self.assertIn("required_fields", spec.report_schema)

    def test_thruster_nozzle_prepare_spec_contains_required_contract_fields(self) -> None:
        spec = default_operation_registry().get("thruster_nozzle_prepare")

        self.assertEqual(spec.name, "thruster_nozzle_prepare")
        self.assertEqual(spec.supported_task_types, ("surface_detail_enhancement",))
        self.assertEqual(spec.required_target_state, "bound")
        self.assertEqual(
            spec.default_parameters,
            {"width": 0.008, "segments": 2, "modifier_name": "AI_ThrusterNozzle_Prepare"},
        )
        self.assertEqual(spec.safety_level, "safe_non_destructive")
        self.assertEqual(spec.handler_name, "thruster_nozzle_prepare")
        self.assertIn("width", spec.parameter_schema)
        self.assertIn("segments", spec.parameter_schema)
        self.assertIn("modifier_name", spec.parameter_schema)
        self.assertIn("add_thrusters", spec.intent_actions)
        self.assertIn("thrusters", spec.intent_detail_types)
        self.assertIn("thruster_nozzle_preparation", spec.intent_effects)
        self.assertIn("required_fields", spec.report_schema)

    def test_hardpoint_socket_prepare_spec_contains_required_contract_fields(self) -> None:
        spec = default_operation_registry().get("hardpoint_socket_prepare")

        self.assertEqual(spec.name, "hardpoint_socket_prepare")
        self.assertEqual(spec.supported_task_types, ("surface_detail_enhancement",))
        self.assertEqual(spec.required_target_state, "bound")
        self.assertEqual(
            spec.default_parameters,
            {"width": 0.006, "segments": 2, "modifier_name": "AI_HardpointSocket_Prepare"},
        )
        self.assertEqual(spec.safety_level, "safe_non_destructive")
        self.assertEqual(spec.handler_name, "hardpoint_socket_prepare")
        self.assertIn("width", spec.parameter_schema)
        self.assertIn("segments", spec.parameter_schema)
        self.assertIn("modifier_name", spec.parameter_schema)
        self.assertIn("add_weapon_mounts", spec.intent_actions)
        self.assertIn("hardpoint_socket", spec.intent_detail_types)
        self.assertIn("hardpoint_socket_preparation", spec.intent_effects)
        self.assertIn("required_fields", spec.report_schema)

    def test_surface_inset_prepare_spec_contains_required_contract_fields(self) -> None:
        spec = default_operation_registry().get("surface_inset_prepare")

        self.assertEqual(spec.name, "surface_inset_prepare")
        self.assertEqual(spec.supported_task_types, ("surface_detail_enhancement",))
        self.assertEqual(spec.required_target_state, "bound")
        self.assertEqual(
            spec.default_parameters,
            {"inset_depth": 0.006, "offset": -1.0, "modifier_name": "AI_SurfaceInset_Prepare"},
        )
        self.assertEqual(spec.safety_level, "safe_non_destructive")
        self.assertEqual(spec.handler_name, "surface_inset_prepare")
        self.assertIn("inset_depth", spec.parameter_schema)
        self.assertIn("offset", spec.parameter_schema)
        self.assertIn("modifier_name", spec.parameter_schema)
        self.assertIn("prepare_surface_inset", spec.intent_actions)
        self.assertIn("surface_inset", spec.intent_detail_types)
        self.assertIn("surface_inset_preparation", spec.intent_effects)
        self.assertIn("required_fields", spec.report_schema)

    def test_armor_edge_lip_prepare_spec_contains_required_contract_fields(self) -> None:
        spec = default_operation_registry().get("armor_edge_lip_prepare")

        self.assertEqual(spec.name, "armor_edge_lip_prepare")
        self.assertEqual(spec.supported_task_types, ("surface_detail_enhancement",))
        self.assertEqual(spec.required_target_state, "bound")
        self.assertEqual(
            spec.default_parameters,
            {"width": 0.008, "segments": 2, "modifier_name": "AI_ArmorEdgeLip_Prepare"},
        )
        self.assertEqual(spec.safety_level, "safe_non_destructive")
        self.assertEqual(spec.handler_name, "armor_edge_lip_prepare")
        self.assertIn("width", spec.parameter_schema)
        self.assertIn("segments", spec.parameter_schema)
        self.assertIn("modifier_name", spec.parameter_schema)
        self.assertIn("prepare_armor_edge_lip", spec.intent_actions)
        self.assertIn("armor_edge_lip", spec.intent_detail_types)
        self.assertIn("armor_edge_lip_preparation", spec.intent_effects)
        self.assertIn("required_fields", spec.report_schema)

    def test_unsupported_operation_raises_clear_error(self) -> None:
        registry = default_operation_registry()

        with self.assertRaises(OperationRegistryError) as error_context:
            registry.get("add_panel_line")

        self.assertIn("Unsupported operation", str(error_context.exception))

    def test_registry_filters_by_supported_task_type(self) -> None:
        registry = default_operation_registry()

        self.assertEqual(
            [operation.name for operation in registry.supported_for_task_type("surface_detail_enhancement")],
            [
                "edge_soften",
                "weighted_normal_finish",
                "solidify_thickness_preview",
                "panel_line_bevel_prepare",
                "armor_layer_plate_prepare",
                "vent_slot_prepare",
                "thruster_nozzle_prepare",
                "hardpoint_socket_prepare",
                "surface_inset_prepare",
                "armor_edge_lip_prepare",
            ],
        )
        self.assertEqual(registry.supported_for_task_type("unsupported_task"), ())

    def test_operation_spec_to_dict_is_json_serializable(self) -> None:
        spec = default_operation_registry().get("edge_soften")
        encoded = json.dumps(spec.to_dict(), ensure_ascii=False)

        self.assertIn("edge_soften", encoded)
        self.assertEqual(spec.to_dict()["supported_task_types"], ["surface_detail_enhancement"])
        self.assertEqual(spec.to_dict()["intent_actions"], list(spec.intent_actions))
        self.assertEqual(spec.to_dict()["intent_detail_types"], list(spec.intent_detail_types))
        self.assertEqual(spec.to_dict()["intent_effects"], list(spec.intent_effects))
        self.assertEqual(spec.to_dict()["priority"], spec.priority)

    def test_registry_rejects_duplicate_operations(self) -> None:
        registry = OperationRegistry()

        with self.assertRaises(OperationRegistryError):
            registry.register(registry.get("edge_soften"))

    def test_registry_rejects_invalid_operation_spec(self) -> None:
        with self.assertRaises(OperationRegistryError):
            OperationRegistry((OperationSpec(name="", supported_task_types=("task",), required_target_state="bound", handler_name="handler"),))
        with self.assertRaises(OperationRegistryError):
            OperationRegistry((OperationSpec(name="bad", supported_task_types=(), required_target_state="bound", handler_name="handler"),))
        with self.assertRaises(OperationRegistryError):
            OperationRegistry((OperationSpec(name="bad", supported_task_types=("task",), required_target_state="", handler_name="handler"),))
        with self.assertRaises(OperationRegistryError):
            OperationRegistry((OperationSpec(name="bad", supported_task_types=("task",), required_target_state="bound", handler_name=""),))

    def test_registry_has_no_blender_or_handler_dependency(self) -> None:
        registry_source = (AGENT_ROOT / "domain" / "operation_registry.py").read_text(encoding="utf-8")
        contracts_source = (AGENT_ROOT / "domain" / "operation_contracts.py").read_text(encoding="utf-8")
        combined_source = registry_source + contracts_source

        self.assertNotIn("import bpy", combined_source)
        self.assertNotIn("bpy.", combined_source)
        self.assertNotIn("from blender_ops", combined_source)
        self.assertNotIn("domain_operations", combined_source)
        self.assertNotIn("core_geometry_api", combined_source)


if __name__ == "__main__":
    unittest.main()
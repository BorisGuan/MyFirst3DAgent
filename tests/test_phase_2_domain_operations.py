import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
AGENT_ROOT = PROJECT_ROOT / "3d_agent"
if str(AGENT_ROOT) not in sys.path:
    sys.path.insert(0, str(AGENT_ROOT))

from blender_ops import domain_operations
from domain import DomainOperationInput, OperationOutcome


class FakeCoreGeometryApi:
    def __init__(self) -> None:
        self.resolved_object = object()
        self.require_object_calls: list[str] = []
        self.add_bevel_modifier_calls: list[dict[str, object]] = []
        self.add_solidify_modifier_calls: list[dict[str, object]] = []
        self.add_weighted_normal_modifier_calls: list[dict[str, object]] = []
        self.save_as_copy_only_calls: list[tuple[str, str]] = []
        self.write_modification_report_calls: list[tuple[str, dict[str, object] | None]] = []

    def require_object(self, object_name: str) -> object:
        self.require_object_calls.append(object_name)
        return self.resolved_object

    def add_bevel_modifier(self, object: object, width: float, segments: int, modifier_name: str) -> dict[str, object]:
        call = {
            "object": object,
            "width": width,
            "segments": segments,
            "modifier_name": modifier_name,
            "modifier_type": "BEVEL",
        }
        self.add_bevel_modifier_calls.append(call)
        return call

    def add_solidify_modifier(
        self,
        object: object,
        thickness: float,
        offset: float,
        modifier_name: str,
    ) -> dict[str, object]:
        call = {
            "object": object,
            "thickness": thickness,
            "offset": offset,
            "modifier_name": modifier_name,
            "modifier_type": "SOLIDIFY",
        }
        self.add_solidify_modifier_calls.append(call)
        return call

    def add_weighted_normal_modifier(
        self,
        object: object,
        weight: float,
        keep_sharp: bool,
        modifier_name: str,
    ) -> dict[str, object]:
        call = {
            "object": object,
            "weight": weight,
            "keep_sharp": keep_sharp,
            "modifier_name": modifier_name,
            "modifier_type": "WEIGHTED_NORMAL",
        }
        self.add_weighted_normal_modifier_calls.append(call)
        return call

    def save_as_copy_only(self, source_file: str, output_file: str) -> str:
        self.save_as_copy_only_calls.append((source_file, output_file))
        return output_file

    def write_modification_report(self, path: str, report: dict[str, object] | None = None) -> str:
        self.write_modification_report_calls.append((path, report))
        return path


def edge_soften_input(parameters: dict[str, object] | None = None) -> DomainOperationInput:
    return DomainOperationInput(
        task_id="task-001",
        operation="edge_soften",
        target_object="ChestArmor_Upper_01",
        parameters=parameters or {"strength": 0.02, "style": "mechanical"},
        execution_policy={"mode": "safe_non_destructive", "preserve_source_file": True},
    )


def weighted_normal_input(parameters: dict[str, object] | None = None) -> DomainOperationInput:
    return DomainOperationInput(
        task_id="task-002",
        operation="weighted_normal_finish",
        target_object="ChestArmor_Upper_01",
        parameters=parameters or {"weight": 50.0, "keep_sharp": "true", "modifier_name": "AI_WeightedNormal_Finish"},
        execution_policy={"mode": "safe_non_destructive", "preserve_source_file": True},
    )


def solidify_input(parameters: dict[str, object] | None = None) -> DomainOperationInput:
    return DomainOperationInput(
        task_id="task-003",
        operation="solidify_thickness_preview",
        target_object="ChestArmor_Upper_01",
        parameters=parameters or {"thickness": 0.015, "offset": 0.0, "modifier_name": "AI_Solidify_ThicknessPreview"},
        execution_policy={"mode": "safe_non_destructive", "preserve_source_file": True},
    )


def panel_line_input(parameters: dict[str, object] | None = None) -> DomainOperationInput:
    return DomainOperationInput(
        task_id="task-004",
        operation="panel_line_bevel_prepare",
        target_object="ChestArmor_Upper_01",
        parameters=parameters or {"width": 0.006, "segments": 1, "modifier_name": "AI_PanelLine_Prepare"},
        execution_policy={"mode": "safe_non_destructive", "preserve_source_file": True},
    )


def armor_layer_input(parameters: dict[str, object] | None = None) -> DomainOperationInput:
    return DomainOperationInput(
        task_id="task-005",
        operation="armor_layer_plate_prepare",
        target_object="ChestArmor_Upper_01",
        parameters=parameters or {"layer_depth": 0.01, "offset": 1.0, "modifier_name": "AI_ArmorLayer_PlatePrepare"},
        execution_policy={"mode": "safe_non_destructive", "preserve_source_file": True},
    )


def vent_slot_input(parameters: dict[str, object] | None = None) -> DomainOperationInput:
    return DomainOperationInput(
        task_id="task-006",
        operation="vent_slot_prepare",
        target_object="ChestArmor_Upper_01",
        parameters=parameters or {"width": 0.004, "segments": 1, "modifier_name": "AI_VentSlot_Prepare"},
        execution_policy={"mode": "safe_non_destructive", "preserve_source_file": True},
    )


def thruster_nozzle_input(parameters: dict[str, object] | None = None) -> DomainOperationInput:
    return DomainOperationInput(
        task_id="task-007",
        operation="thruster_nozzle_prepare",
        target_object="Backpack_Thruster_01",
        parameters=parameters or {"width": 0.008, "segments": 2, "modifier_name": "AI_ThrusterNozzle_Prepare"},
        execution_policy={"mode": "safe_non_destructive", "preserve_source_file": True},
    )


def hardpoint_socket_input(parameters: dict[str, object] | None = None) -> DomainOperationInput:
    return DomainOperationInput(
        task_id="task-008",
        operation="hardpoint_socket_prepare",
        target_object="Shoulder_Hardpoint_01",
        parameters=parameters or {"width": 0.006, "segments": 2, "modifier_name": "AI_HardpointSocket_Prepare"},
        execution_policy={"mode": "safe_non_destructive", "preserve_source_file": True},
    )


def surface_inset_input(parameters: dict[str, object] | None = None) -> DomainOperationInput:
    return DomainOperationInput(
        task_id="task-009",
        operation="surface_inset_prepare",
        target_object="ChestArmor_Upper_01",
        parameters=parameters or {"inset_depth": 0.006, "offset": -1.0, "modifier_name": "AI_SurfaceInset_Prepare"},
        execution_policy={"mode": "safe_non_destructive", "preserve_source_file": True},
    )


def armor_edge_lip_input(parameters: dict[str, object] | None = None) -> DomainOperationInput:
    return DomainOperationInput(
        task_id="task-010",
        operation="armor_edge_lip_prepare",
        target_object="ChestArmor_Edge_01",
        parameters=parameters or {"width": 0.008, "segments": 2, "modifier_name": "AI_ArmorEdgeLip_Prepare"},
        execution_policy={"mode": "safe_non_destructive", "preserve_source_file": True},
    )


class Phase2DomainOperationsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.original_core_api = domain_operations.core_geometry_api
        self.fake_core_api = FakeCoreGeometryApi()
        domain_operations.core_geometry_api = self.fake_core_api

    def tearDown(self) -> None:
        domain_operations.core_geometry_api = self.original_core_api

    def test_edge_soften_resolves_object_and_calls_core_api_bevel_modifier(self) -> None:
        result = domain_operations.edge_soften(edge_soften_input())

        self.assertEqual(self.fake_core_api.require_object_calls, ["ChestArmor_Upper_01"])
        self.assertIsInstance(result, OperationOutcome)
        self.assertEqual(result.operation, "edge_soften")
        self.assertEqual(result.target_object, "ChestArmor_Upper_01")
        self.assertTrue(result.success)
        self.assertEqual(result.changed_objects, ["ChestArmor_Upper_01"])
        self.assertEqual(result.modifier_info["width"], 0.02)
        self.assertEqual(result.modifier_info["segments"], 1)
        self.assertEqual(result.modifier_info["modifier_name"], "AI_PanelLine_Bevel")
        self.assertFalse(result.mesh_data_applied)

    def test_edge_soften_uses_contract_defaults_when_parameters_are_empty(self) -> None:
        result = domain_operations.edge_soften(
            DomainOperationInput(
                task_id="task-001",
                operation="edge_soften",
                target_object="Body",
                parameters={},
                execution_policy={"mode": "safe_non_destructive", "preserve_source_file": True},
            )
        )

        self.assertEqual(self.fake_core_api.require_object_calls, ["Body"])
        self.assertEqual(result.modifier_info["width"], 0.01)
        self.assertEqual(result.modifier_info["segments"], 1)
        self.assertEqual(result.modifier_info["modifier_name"], "AI_PanelLine_Bevel")

    def test_edge_soften_maps_style_to_width_without_extra_operations(self) -> None:
        clean = domain_operations.edge_soften(edge_soften_input({"strength": 0.02, "style": "clean"}))
        heavy = domain_operations.edge_soften(edge_soften_input({"strength": 0.02, "style": "heavy"}))

        self.assertEqual(clean.modifier_info["width"], 0.015)
        self.assertEqual(heavy.modifier_info["width"], 0.03)
        self.assertEqual(len(self.fake_core_api.add_bevel_modifier_calls), 2)

    def test_edge_soften_does_not_save_copy_or_write_report(self) -> None:
        result = domain_operations.edge_soften(edge_soften_input())

        self.assertEqual(self.fake_core_api.require_object_calls, ["ChestArmor_Upper_01"])
        self.assertEqual(self.fake_core_api.add_bevel_modifier_calls[0]["modifier_name"], "AI_PanelLine_Bevel")
        self.assertEqual(self.fake_core_api.save_as_copy_only_calls, [])
        self.assertEqual(self.fake_core_api.write_modification_report_calls, [])
        self.assertEqual(result.to_dict()["target_object"], "ChestArmor_Upper_01")
        self.assertNotIn("output_blend_copy", result.to_dict())
        self.assertNotIn("report_file", result.to_dict())

    def test_edge_soften_returns_domain_operation_outcome_shape(self) -> None:
        outcome = domain_operations.edge_soften(edge_soften_input({"strength": 0.01, "style": "mechanical"}))

        self.assertEqual(
            outcome.to_dict(),
            {
                "operation": "edge_soften",
                "target_object": "ChestArmor_Upper_01",
                "success": True,
                "changed_objects": ["ChestArmor_Upper_01"],
                "modifier_info": {
                    "modifier_name": "AI_PanelLine_Bevel",
                    "modifier_type": "BEVEL",
                    "width": 0.01,
                    "segments": 1,
                },
                "mesh_data_applied": False,
                "diagnostics": [],
            },
        )

    def test_edge_soften_rejects_invalid_parameters_before_core_geometry_call(self) -> None:
        with self.assertRaises(ValueError):
            domain_operations.edge_soften(edge_soften_input({"strength": 0.0, "style": "mechanical"}))
        with self.assertRaises(ValueError):
            domain_operations.edge_soften(edge_soften_input({"strength": 0.01, "style": "unknown"}))
        self.assertEqual(self.fake_core_api.require_object_calls, [])

    def test_edge_soften_rejects_wrong_operation_contract(self) -> None:
        with self.assertRaises(ValueError) as error_context:
            domain_operations.edge_soften(
                DomainOperationInput(
                    task_id="task-001",
                    operation="add_panel_line",
                    target_object="ChestArmor_Upper_01",
                    parameters={"strength": 0.01, "style": "mechanical"},
                    execution_policy={"mode": "safe_non_destructive", "preserve_source_file": True},
                )
            )

        self.assertIn("edge_soften cannot handle operation", str(error_context.exception))
        self.assertEqual(self.fake_core_api.require_object_calls, [])

    def test_weighted_normal_finish_resolves_object_and_calls_core_api_modifier(self) -> None:
        result = domain_operations.weighted_normal_finish(weighted_normal_input())

        self.assertEqual(self.fake_core_api.require_object_calls, ["ChestArmor_Upper_01"])
        self.assertIsInstance(result, OperationOutcome)
        self.assertEqual(result.operation, "weighted_normal_finish")
        self.assertEqual(result.target_object, "ChestArmor_Upper_01")
        self.assertTrue(result.success)
        self.assertEqual(result.changed_objects, ["ChestArmor_Upper_01"])
        self.assertEqual(result.modifier_info["modifier_name"], "AI_WeightedNormal_Finish")
        self.assertEqual(result.modifier_info["modifier_type"], "WEIGHTED_NORMAL")
        self.assertEqual(result.modifier_info["weight"], 50.0)
        self.assertTrue(result.modifier_info["keep_sharp"])
        self.assertFalse(result.mesh_data_applied)

    def test_weighted_normal_finish_uses_defaults_when_parameters_are_empty(self) -> None:
        result = domain_operations.weighted_normal_finish(
            DomainOperationInput(
                task_id="task-002",
                operation="weighted_normal_finish",
                target_object="Body",
                parameters={},
                execution_policy={"mode": "safe_non_destructive", "preserve_source_file": True},
            )
        )

        self.assertEqual(self.fake_core_api.require_object_calls, ["Body"])
        self.assertEqual(result.modifier_info["weight"], 50.0)
        self.assertTrue(result.modifier_info["keep_sharp"])
        self.assertEqual(result.modifier_info["modifier_name"], "AI_WeightedNormal_Finish")

    def test_weighted_normal_finish_maps_false_keep_sharp_and_custom_modifier_name(self) -> None:
        result = domain_operations.weighted_normal_finish(
            weighted_normal_input({"weight": 25.0, "keep_sharp": "false", "modifier_name": "AI_Custom_Normal"})
        )

        self.assertEqual(self.fake_core_api.add_weighted_normal_modifier_calls[0]["weight"], 25.0)
        self.assertFalse(self.fake_core_api.add_weighted_normal_modifier_calls[0]["keep_sharp"])
        self.assertEqual(self.fake_core_api.add_weighted_normal_modifier_calls[0]["modifier_name"], "AI_Custom_Normal")
        self.assertFalse(result.modifier_info["keep_sharp"])

    def test_weighted_normal_finish_does_not_save_copy_or_write_report(self) -> None:
        result = domain_operations.weighted_normal_finish(weighted_normal_input())

        self.assertEqual(self.fake_core_api.save_as_copy_only_calls, [])
        self.assertEqual(self.fake_core_api.write_modification_report_calls, [])
        self.assertEqual(result.to_dict()["target_object"], "ChestArmor_Upper_01")
        self.assertNotIn("output_blend_copy", result.to_dict())
        self.assertNotIn("report_file", result.to_dict())

    def test_weighted_normal_finish_rejects_invalid_parameters_before_core_geometry_call(self) -> None:
        for parameters in (
            {"weight": 0.0, "keep_sharp": "true", "modifier_name": "AI_WeightedNormal_Finish"},
            {"weight": 50.0, "keep_sharp": "unknown", "modifier_name": "AI_WeightedNormal_Finish"},
            {"weight": 50.0, "keep_sharp": "true", "modifier_name": ""},
        ):
            with self.subTest(parameters=parameters):
                with self.assertRaises(ValueError):
                    domain_operations.weighted_normal_finish(weighted_normal_input(parameters))
        self.assertEqual(self.fake_core_api.require_object_calls, [])

    def test_weighted_normal_finish_rejects_wrong_operation_contract(self) -> None:
        with self.assertRaises(ValueError) as error_context:
            domain_operations.weighted_normal_finish(
                DomainOperationInput(
                    task_id="task-002",
                    operation="edge_soften",
                    target_object="ChestArmor_Upper_01",
                    parameters={"weight": 50.0, "keep_sharp": "true"},
                    execution_policy={"mode": "safe_non_destructive", "preserve_source_file": True},
                )
            )

        self.assertIn("weighted_normal_finish cannot handle operation", str(error_context.exception))
        self.assertEqual(self.fake_core_api.require_object_calls, [])

    def test_solidify_thickness_preview_resolves_object_and_calls_core_api_modifier(self) -> None:
        result = domain_operations.solidify_thickness_preview(solidify_input())

        self.assertEqual(self.fake_core_api.require_object_calls, ["ChestArmor_Upper_01"])
        self.assertIsInstance(result, OperationOutcome)
        self.assertEqual(result.operation, "solidify_thickness_preview")
        self.assertEqual(result.target_object, "ChestArmor_Upper_01")
        self.assertTrue(result.success)
        self.assertEqual(result.changed_objects, ["ChestArmor_Upper_01"])
        self.assertEqual(result.modifier_info["modifier_name"], "AI_Solidify_ThicknessPreview")
        self.assertEqual(result.modifier_info["modifier_type"], "SOLIDIFY")
        self.assertEqual(result.modifier_info["thickness"], 0.015)
        self.assertEqual(result.modifier_info["offset"], 0.0)
        self.assertFalse(result.mesh_data_applied)

    def test_solidify_thickness_preview_uses_defaults_when_parameters_are_empty(self) -> None:
        result = domain_operations.solidify_thickness_preview(
            DomainOperationInput(
                task_id="task-003",
                operation="solidify_thickness_preview",
                target_object="Body",
                parameters={},
                execution_policy={"mode": "safe_non_destructive", "preserve_source_file": True},
            )
        )

        self.assertEqual(self.fake_core_api.require_object_calls, ["Body"])
        self.assertEqual(result.modifier_info["thickness"], 0.015)
        self.assertEqual(result.modifier_info["offset"], 0.0)
        self.assertEqual(result.modifier_info["modifier_name"], "AI_Solidify_ThicknessPreview")

    def test_solidify_thickness_preview_uses_explicit_parameters(self) -> None:
        result = domain_operations.solidify_thickness_preview(
            solidify_input({"thickness": 0.025, "offset": -1.0, "modifier_name": "AI_Custom_Solidify"})
        )

        self.assertEqual(self.fake_core_api.add_solidify_modifier_calls[0]["thickness"], 0.025)
        self.assertEqual(self.fake_core_api.add_solidify_modifier_calls[0]["offset"], -1.0)
        self.assertEqual(self.fake_core_api.add_solidify_modifier_calls[0]["modifier_name"], "AI_Custom_Solidify")
        self.assertEqual(result.modifier_info["offset"], -1.0)

    def test_solidify_thickness_preview_does_not_save_copy_or_write_report(self) -> None:
        result = domain_operations.solidify_thickness_preview(solidify_input())

        self.assertEqual(self.fake_core_api.save_as_copy_only_calls, [])
        self.assertEqual(self.fake_core_api.write_modification_report_calls, [])
        self.assertEqual(result.to_dict()["target_object"], "ChestArmor_Upper_01")
        self.assertNotIn("output_blend_copy", result.to_dict())
        self.assertNotIn("report_file", result.to_dict())

    def test_solidify_thickness_preview_rejects_invalid_parameters_before_core_geometry_call(self) -> None:
        for parameters in (
            {"thickness": 0.0, "offset": 0.0, "modifier_name": "AI_Solidify_ThicknessPreview"},
            {"thickness": 0.015, "offset": 0.0, "modifier_name": ""},
        ):
            with self.subTest(parameters=parameters):
                with self.assertRaises(ValueError):
                    domain_operations.solidify_thickness_preview(solidify_input(parameters))
        self.assertEqual(self.fake_core_api.require_object_calls, [])

    def test_solidify_thickness_preview_rejects_wrong_operation_contract(self) -> None:
        with self.assertRaises(ValueError) as error_context:
            domain_operations.solidify_thickness_preview(
                DomainOperationInput(
                    task_id="task-003",
                    operation="edge_soften",
                    target_object="ChestArmor_Upper_01",
                    parameters={"thickness": 0.015, "offset": 0.0},
                    execution_policy={"mode": "safe_non_destructive", "preserve_source_file": True},
                )
            )

        self.assertIn("solidify_thickness_preview cannot handle operation", str(error_context.exception))
        self.assertEqual(self.fake_core_api.require_object_calls, [])

    def test_panel_line_bevel_prepare_resolves_object_and_calls_core_api_bevel_modifier(self) -> None:
        result = domain_operations.panel_line_bevel_prepare(panel_line_input())

        self.assertEqual(self.fake_core_api.require_object_calls, ["ChestArmor_Upper_01"])
        self.assertIsInstance(result, OperationOutcome)
        self.assertEqual(result.operation, "panel_line_bevel_prepare")
        self.assertEqual(result.target_object, "ChestArmor_Upper_01")
        self.assertTrue(result.success)
        self.assertEqual(result.changed_objects, ["ChestArmor_Upper_01"])
        self.assertEqual(result.modifier_info["modifier_name"], "AI_PanelLine_Prepare")
        self.assertEqual(result.modifier_info["modifier_type"], "BEVEL")
        self.assertEqual(result.modifier_info["width"], 0.006)
        self.assertEqual(result.modifier_info["segments"], 1)
        self.assertFalse(result.mesh_data_applied)

    def test_panel_line_bevel_prepare_uses_defaults_when_parameters_are_empty(self) -> None:
        result = domain_operations.panel_line_bevel_prepare(
            DomainOperationInput(
                task_id="task-004",
                operation="panel_line_bevel_prepare",
                target_object="Body",
                parameters={},
                execution_policy={"mode": "safe_non_destructive", "preserve_source_file": True},
            )
        )

        self.assertEqual(self.fake_core_api.require_object_calls, ["Body"])
        self.assertEqual(result.modifier_info["width"], 0.006)
        self.assertEqual(result.modifier_info["segments"], 1)
        self.assertEqual(result.modifier_info["modifier_name"], "AI_PanelLine_Prepare")

    def test_panel_line_bevel_prepare_uses_explicit_parameters(self) -> None:
        result = domain_operations.panel_line_bevel_prepare(
            panel_line_input({"width": 0.008, "segments": 2, "modifier_name": "AI_Custom_PanelLine"})
        )

        self.assertEqual(self.fake_core_api.add_bevel_modifier_calls[0]["width"], 0.008)
        self.assertEqual(self.fake_core_api.add_bevel_modifier_calls[0]["segments"], 2)
        self.assertEqual(self.fake_core_api.add_bevel_modifier_calls[0]["modifier_name"], "AI_Custom_PanelLine")
        self.assertEqual(result.modifier_info["segments"], 2)

    def test_panel_line_bevel_prepare_does_not_save_copy_or_write_report(self) -> None:
        result = domain_operations.panel_line_bevel_prepare(panel_line_input())

        self.assertEqual(self.fake_core_api.save_as_copy_only_calls, [])
        self.assertEqual(self.fake_core_api.write_modification_report_calls, [])
        self.assertEqual(result.to_dict()["target_object"], "ChestArmor_Upper_01")
        self.assertNotIn("output_blend_copy", result.to_dict())
        self.assertNotIn("report_file", result.to_dict())

    def test_panel_line_bevel_prepare_rejects_invalid_parameters_before_core_geometry_call(self) -> None:
        for parameters in (
            {"width": 0.0, "segments": 1, "modifier_name": "AI_PanelLine_Prepare"},
            {"width": 0.006, "segments": 0, "modifier_name": "AI_PanelLine_Prepare"},
            {"width": 0.006, "segments": 1, "modifier_name": ""},
        ):
            with self.subTest(parameters=parameters):
                with self.assertRaises(ValueError):
                    domain_operations.panel_line_bevel_prepare(panel_line_input(parameters))
        self.assertEqual(self.fake_core_api.require_object_calls, [])

    def test_panel_line_bevel_prepare_rejects_wrong_operation_contract(self) -> None:
        with self.assertRaises(ValueError) as error_context:
            domain_operations.panel_line_bevel_prepare(
                DomainOperationInput(
                    task_id="task-004",
                    operation="edge_soften",
                    target_object="ChestArmor_Upper_01",
                    parameters={"width": 0.006, "segments": 1},
                    execution_policy={"mode": "safe_non_destructive", "preserve_source_file": True},
                )
            )

        self.assertIn("panel_line_bevel_prepare cannot handle operation", str(error_context.exception))
        self.assertEqual(self.fake_core_api.require_object_calls, [])

    def test_armor_layer_plate_prepare_resolves_object_and_calls_core_api_solidify_modifier(self) -> None:
        result = domain_operations.armor_layer_plate_prepare(armor_layer_input())

        self.assertEqual(self.fake_core_api.require_object_calls, ["ChestArmor_Upper_01"])
        self.assertIsInstance(result, OperationOutcome)
        self.assertEqual(result.operation, "armor_layer_plate_prepare")
        self.assertEqual(result.target_object, "ChestArmor_Upper_01")
        self.assertTrue(result.success)
        self.assertEqual(result.changed_objects, ["ChestArmor_Upper_01"])
        self.assertEqual(result.modifier_info["modifier_name"], "AI_ArmorLayer_PlatePrepare")
        self.assertEqual(result.modifier_info["modifier_type"], "SOLIDIFY")
        self.assertEqual(result.modifier_info["layer_depth"], 0.01)
        self.assertEqual(result.modifier_info["offset"], 1.0)
        self.assertFalse(result.mesh_data_applied)

    def test_armor_layer_plate_prepare_uses_defaults_when_parameters_are_empty(self) -> None:
        result = domain_operations.armor_layer_plate_prepare(
            DomainOperationInput(
                task_id="task-005",
                operation="armor_layer_plate_prepare",
                target_object="Body",
                parameters={},
                execution_policy={"mode": "safe_non_destructive", "preserve_source_file": True},
            )
        )

        self.assertEqual(self.fake_core_api.require_object_calls, ["Body"])
        self.assertEqual(result.modifier_info["layer_depth"], 0.01)
        self.assertEqual(result.modifier_info["offset"], 1.0)
        self.assertEqual(result.modifier_info["modifier_name"], "AI_ArmorLayer_PlatePrepare")

    def test_armor_layer_plate_prepare_uses_explicit_parameters(self) -> None:
        result = domain_operations.armor_layer_plate_prepare(
            armor_layer_input({"layer_depth": 0.02, "offset": 0.75, "modifier_name": "AI_Custom_ArmorLayer"})
        )

        self.assertEqual(self.fake_core_api.add_solidify_modifier_calls[0]["thickness"], 0.02)
        self.assertEqual(self.fake_core_api.add_solidify_modifier_calls[0]["offset"], 0.75)
        self.assertEqual(self.fake_core_api.add_solidify_modifier_calls[0]["modifier_name"], "AI_Custom_ArmorLayer")
        self.assertEqual(result.modifier_info["layer_depth"], 0.02)

    def test_armor_layer_plate_prepare_does_not_save_copy_or_write_report(self) -> None:
        result = domain_operations.armor_layer_plate_prepare(armor_layer_input())

        self.assertEqual(self.fake_core_api.save_as_copy_only_calls, [])
        self.assertEqual(self.fake_core_api.write_modification_report_calls, [])
        self.assertEqual(result.to_dict()["target_object"], "ChestArmor_Upper_01")
        self.assertNotIn("output_blend_copy", result.to_dict())
        self.assertNotIn("report_file", result.to_dict())

    def test_armor_layer_plate_prepare_rejects_invalid_parameters_before_core_geometry_call(self) -> None:
        for parameters in (
            {"layer_depth": 0.0, "offset": 1.0, "modifier_name": "AI_ArmorLayer_PlatePrepare"},
            {"layer_depth": 0.01, "offset": 1.0, "modifier_name": ""},
        ):
            with self.subTest(parameters=parameters):
                with self.assertRaises(ValueError):
                    domain_operations.armor_layer_plate_prepare(armor_layer_input(parameters))
        self.assertEqual(self.fake_core_api.require_object_calls, [])

    def test_armor_layer_plate_prepare_rejects_wrong_operation_contract(self) -> None:
        with self.assertRaises(ValueError) as error_context:
            domain_operations.armor_layer_plate_prepare(
                DomainOperationInput(
                    task_id="task-005",
                    operation="edge_soften",
                    target_object="ChestArmor_Upper_01",
                    parameters={"layer_depth": 0.01, "offset": 1.0},
                    execution_policy={"mode": "safe_non_destructive", "preserve_source_file": True},
                )
            )

        self.assertIn("armor_layer_plate_prepare cannot handle operation", str(error_context.exception))
        self.assertEqual(self.fake_core_api.require_object_calls, [])

    def test_vent_slot_prepare_resolves_object_and_calls_core_api_bevel_modifier(self) -> None:
        result = domain_operations.vent_slot_prepare(vent_slot_input())

        self.assertEqual(self.fake_core_api.require_object_calls, ["ChestArmor_Upper_01"])
        self.assertIsInstance(result, OperationOutcome)
        self.assertEqual(result.operation, "vent_slot_prepare")
        self.assertEqual(result.target_object, "ChestArmor_Upper_01")
        self.assertTrue(result.success)
        self.assertEqual(result.changed_objects, ["ChestArmor_Upper_01"])
        self.assertEqual(result.modifier_info["modifier_name"], "AI_VentSlot_Prepare")
        self.assertEqual(result.modifier_info["modifier_type"], "BEVEL")
        self.assertEqual(result.modifier_info["width"], 0.004)
        self.assertEqual(result.modifier_info["segments"], 1)
        self.assertFalse(result.mesh_data_applied)

    def test_vent_slot_prepare_uses_defaults_when_parameters_are_empty(self) -> None:
        result = domain_operations.vent_slot_prepare(
            DomainOperationInput(
                task_id="task-006",
                operation="vent_slot_prepare",
                target_object="Body",
                parameters={},
                execution_policy={"mode": "safe_non_destructive", "preserve_source_file": True},
            )
        )

        self.assertEqual(self.fake_core_api.require_object_calls, ["Body"])
        self.assertEqual(result.modifier_info["width"], 0.004)
        self.assertEqual(result.modifier_info["segments"], 1)
        self.assertEqual(result.modifier_info["modifier_name"], "AI_VentSlot_Prepare")

    def test_vent_slot_prepare_uses_explicit_parameters(self) -> None:
        result = domain_operations.vent_slot_prepare(
            vent_slot_input({"width": 0.005, "segments": 2, "modifier_name": "AI_Custom_VentSlot"})
        )

        self.assertEqual(self.fake_core_api.add_bevel_modifier_calls[0]["width"], 0.005)
        self.assertEqual(self.fake_core_api.add_bevel_modifier_calls[0]["segments"], 2)
        self.assertEqual(self.fake_core_api.add_bevel_modifier_calls[0]["modifier_name"], "AI_Custom_VentSlot")
        self.assertEqual(result.modifier_info["segments"], 2)

    def test_vent_slot_prepare_does_not_save_copy_or_write_report(self) -> None:
        result = domain_operations.vent_slot_prepare(vent_slot_input())

        self.assertEqual(self.fake_core_api.save_as_copy_only_calls, [])
        self.assertEqual(self.fake_core_api.write_modification_report_calls, [])
        self.assertEqual(result.to_dict()["target_object"], "ChestArmor_Upper_01")
        self.assertNotIn("output_blend_copy", result.to_dict())
        self.assertNotIn("report_file", result.to_dict())

    def test_vent_slot_prepare_rejects_invalid_parameters_before_core_geometry_call(self) -> None:
        for parameters in (
            {"width": 0.0, "segments": 1, "modifier_name": "AI_VentSlot_Prepare"},
            {"width": 0.004, "segments": 0, "modifier_name": "AI_VentSlot_Prepare"},
            {"width": 0.004, "segments": 1, "modifier_name": ""},
        ):
            with self.subTest(parameters=parameters):
                with self.assertRaises(ValueError):
                    domain_operations.vent_slot_prepare(vent_slot_input(parameters))
        self.assertEqual(self.fake_core_api.require_object_calls, [])

    def test_vent_slot_prepare_rejects_wrong_operation_contract(self) -> None:
        with self.assertRaises(ValueError) as error_context:
            domain_operations.vent_slot_prepare(
                DomainOperationInput(
                    task_id="task-006",
                    operation="edge_soften",
                    target_object="ChestArmor_Upper_01",
                    parameters={"width": 0.004, "segments": 1},
                    execution_policy={"mode": "safe_non_destructive", "preserve_source_file": True},
                )
            )

        self.assertIn("vent_slot_prepare cannot handle operation", str(error_context.exception))
        self.assertEqual(self.fake_core_api.require_object_calls, [])

    def test_thruster_nozzle_prepare_resolves_object_and_calls_core_api_bevel_modifier(self) -> None:
        result = domain_operations.thruster_nozzle_prepare(thruster_nozzle_input())

        self.assertEqual(self.fake_core_api.require_object_calls, ["Backpack_Thruster_01"])
        self.assertIsInstance(result, OperationOutcome)
        self.assertEqual(result.operation, "thruster_nozzle_prepare")
        self.assertEqual(result.target_object, "Backpack_Thruster_01")
        self.assertTrue(result.success)
        self.assertEqual(result.changed_objects, ["Backpack_Thruster_01"])
        self.assertEqual(result.modifier_info["modifier_name"], "AI_ThrusterNozzle_Prepare")
        self.assertEqual(result.modifier_info["modifier_type"], "BEVEL")
        self.assertEqual(result.modifier_info["width"], 0.008)
        self.assertEqual(result.modifier_info["segments"], 2)
        self.assertFalse(result.mesh_data_applied)

    def test_thruster_nozzle_prepare_uses_defaults_when_parameters_are_empty(self) -> None:
        result = domain_operations.thruster_nozzle_prepare(
            DomainOperationInput(
                task_id="task-007",
                operation="thruster_nozzle_prepare",
                target_object="Body",
                parameters={},
                execution_policy={"mode": "safe_non_destructive", "preserve_source_file": True},
            )
        )

        self.assertEqual(self.fake_core_api.require_object_calls, ["Body"])
        self.assertEqual(result.modifier_info["width"], 0.008)
        self.assertEqual(result.modifier_info["segments"], 2)
        self.assertEqual(result.modifier_info["modifier_name"], "AI_ThrusterNozzle_Prepare")

    def test_thruster_nozzle_prepare_uses_explicit_parameters(self) -> None:
        result = domain_operations.thruster_nozzle_prepare(
            thruster_nozzle_input({"width": 0.012, "segments": 3, "modifier_name": "AI_Custom_ThrusterNozzle"})
        )

        self.assertEqual(self.fake_core_api.add_bevel_modifier_calls[0]["width"], 0.012)
        self.assertEqual(self.fake_core_api.add_bevel_modifier_calls[0]["segments"], 3)
        self.assertEqual(self.fake_core_api.add_bevel_modifier_calls[0]["modifier_name"], "AI_Custom_ThrusterNozzle")
        self.assertEqual(result.modifier_info["segments"], 3)

    def test_thruster_nozzle_prepare_does_not_save_copy_or_write_report(self) -> None:
        result = domain_operations.thruster_nozzle_prepare(thruster_nozzle_input())

        self.assertEqual(self.fake_core_api.save_as_copy_only_calls, [])
        self.assertEqual(self.fake_core_api.write_modification_report_calls, [])
        self.assertEqual(result.to_dict()["target_object"], "Backpack_Thruster_01")
        self.assertNotIn("output_blend_copy", result.to_dict())
        self.assertNotIn("report_file", result.to_dict())

    def test_thruster_nozzle_prepare_rejects_invalid_parameters_before_core_geometry_call(self) -> None:
        for parameters in (
            {"width": 0.0, "segments": 2, "modifier_name": "AI_ThrusterNozzle_Prepare"},
            {"width": 0.008, "segments": 0, "modifier_name": "AI_ThrusterNozzle_Prepare"},
            {"width": 0.008, "segments": 2, "modifier_name": ""},
        ):
            with self.subTest(parameters=parameters):
                with self.assertRaises(ValueError):
                    domain_operations.thruster_nozzle_prepare(thruster_nozzle_input(parameters))
        self.assertEqual(self.fake_core_api.require_object_calls, [])

    def test_thruster_nozzle_prepare_rejects_wrong_operation_contract(self) -> None:
        with self.assertRaises(ValueError) as error_context:
            domain_operations.thruster_nozzle_prepare(
                DomainOperationInput(
                    task_id="task-007",
                    operation="edge_soften",
                    target_object="Backpack_Thruster_01",
                    parameters={"width": 0.008, "segments": 2},
                    execution_policy={"mode": "safe_non_destructive", "preserve_source_file": True},
                )
            )

        self.assertIn("thruster_nozzle_prepare cannot handle operation", str(error_context.exception))
        self.assertEqual(self.fake_core_api.require_object_calls, [])

    def test_hardpoint_socket_prepare_resolves_object_and_calls_core_api_bevel_modifier(self) -> None:
        result = domain_operations.hardpoint_socket_prepare(hardpoint_socket_input())

        self.assertEqual(self.fake_core_api.require_object_calls, ["Shoulder_Hardpoint_01"])
        self.assertIsInstance(result, OperationOutcome)
        self.assertEqual(result.operation, "hardpoint_socket_prepare")
        self.assertEqual(result.target_object, "Shoulder_Hardpoint_01")
        self.assertTrue(result.success)
        self.assertEqual(result.changed_objects, ["Shoulder_Hardpoint_01"])
        self.assertEqual(result.modifier_info["modifier_name"], "AI_HardpointSocket_Prepare")
        self.assertEqual(result.modifier_info["modifier_type"], "BEVEL")
        self.assertEqual(result.modifier_info["width"], 0.006)
        self.assertEqual(result.modifier_info["segments"], 2)
        self.assertFalse(result.mesh_data_applied)

    def test_hardpoint_socket_prepare_uses_defaults_when_parameters_are_empty(self) -> None:
        result = domain_operations.hardpoint_socket_prepare(
            DomainOperationInput(
                task_id="task-008",
                operation="hardpoint_socket_prepare",
                target_object="Body",
                parameters={},
                execution_policy={"mode": "safe_non_destructive", "preserve_source_file": True},
            )
        )

        self.assertEqual(self.fake_core_api.require_object_calls, ["Body"])
        self.assertEqual(result.modifier_info["width"], 0.006)
        self.assertEqual(result.modifier_info["segments"], 2)
        self.assertEqual(result.modifier_info["modifier_name"], "AI_HardpointSocket_Prepare")

    def test_hardpoint_socket_prepare_uses_explicit_parameters(self) -> None:
        result = domain_operations.hardpoint_socket_prepare(
            hardpoint_socket_input({"width": 0.01, "segments": 3, "modifier_name": "AI_Custom_HardpointSocket"})
        )

        self.assertEqual(self.fake_core_api.add_bevel_modifier_calls[0]["width"], 0.01)
        self.assertEqual(self.fake_core_api.add_bevel_modifier_calls[0]["segments"], 3)
        self.assertEqual(self.fake_core_api.add_bevel_modifier_calls[0]["modifier_name"], "AI_Custom_HardpointSocket")
        self.assertEqual(result.modifier_info["segments"], 3)

    def test_hardpoint_socket_prepare_does_not_save_copy_or_write_report(self) -> None:
        result = domain_operations.hardpoint_socket_prepare(hardpoint_socket_input())

        self.assertEqual(self.fake_core_api.save_as_copy_only_calls, [])
        self.assertEqual(self.fake_core_api.write_modification_report_calls, [])
        self.assertEqual(result.to_dict()["target_object"], "Shoulder_Hardpoint_01")
        self.assertNotIn("output_blend_copy", result.to_dict())
        self.assertNotIn("report_file", result.to_dict())

    def test_hardpoint_socket_prepare_rejects_invalid_parameters_before_core_geometry_call(self) -> None:
        for parameters in (
            {"width": 0.0, "segments": 2, "modifier_name": "AI_HardpointSocket_Prepare"},
            {"width": 0.006, "segments": 0, "modifier_name": "AI_HardpointSocket_Prepare"},
            {"width": 0.006, "segments": 2, "modifier_name": ""},
        ):
            with self.subTest(parameters=parameters):
                with self.assertRaises(ValueError):
                    domain_operations.hardpoint_socket_prepare(hardpoint_socket_input(parameters))
        self.assertEqual(self.fake_core_api.require_object_calls, [])

    def test_hardpoint_socket_prepare_rejects_wrong_operation_contract(self) -> None:
        with self.assertRaises(ValueError) as error_context:
            domain_operations.hardpoint_socket_prepare(
                DomainOperationInput(
                    task_id="task-008",
                    operation="edge_soften",
                    target_object="Shoulder_Hardpoint_01",
                    parameters={"width": 0.006, "segments": 2},
                    execution_policy={"mode": "safe_non_destructive", "preserve_source_file": True},
                )
            )

        self.assertIn("hardpoint_socket_prepare cannot handle operation", str(error_context.exception))
        self.assertEqual(self.fake_core_api.require_object_calls, [])

    def test_surface_inset_prepare_resolves_object_and_calls_core_api_solidify_modifier(self) -> None:
        result = domain_operations.surface_inset_prepare(surface_inset_input())

        self.assertEqual(self.fake_core_api.require_object_calls, ["ChestArmor_Upper_01"])
        self.assertIsInstance(result, OperationOutcome)
        self.assertEqual(result.operation, "surface_inset_prepare")
        self.assertEqual(result.target_object, "ChestArmor_Upper_01")
        self.assertTrue(result.success)
        self.assertEqual(result.changed_objects, ["ChestArmor_Upper_01"])
        self.assertEqual(result.modifier_info["modifier_name"], "AI_SurfaceInset_Prepare")
        self.assertEqual(result.modifier_info["modifier_type"], "SOLIDIFY")
        self.assertEqual(result.modifier_info["inset_depth"], 0.006)
        self.assertEqual(result.modifier_info["offset"], -1.0)
        self.assertFalse(result.mesh_data_applied)

    def test_surface_inset_prepare_uses_defaults_when_parameters_are_empty(self) -> None:
        result = domain_operations.surface_inset_prepare(
            DomainOperationInput(
                task_id="task-009",
                operation="surface_inset_prepare",
                target_object="Body",
                parameters={},
                execution_policy={"mode": "safe_non_destructive", "preserve_source_file": True},
            )
        )

        self.assertEqual(self.fake_core_api.require_object_calls, ["Body"])
        self.assertEqual(result.modifier_info["inset_depth"], 0.006)
        self.assertEqual(result.modifier_info["offset"], -1.0)
        self.assertEqual(result.modifier_info["modifier_name"], "AI_SurfaceInset_Prepare")

    def test_surface_inset_prepare_uses_explicit_parameters(self) -> None:
        result = domain_operations.surface_inset_prepare(
            surface_inset_input({"inset_depth": 0.01, "offset": -0.75, "modifier_name": "AI_Custom_SurfaceInset"})
        )

        self.assertEqual(self.fake_core_api.add_solidify_modifier_calls[0]["thickness"], 0.01)
        self.assertEqual(self.fake_core_api.add_solidify_modifier_calls[0]["offset"], -0.75)
        self.assertEqual(self.fake_core_api.add_solidify_modifier_calls[0]["modifier_name"], "AI_Custom_SurfaceInset")
        self.assertEqual(result.modifier_info["inset_depth"], 0.01)

    def test_surface_inset_prepare_does_not_save_copy_or_write_report(self) -> None:
        result = domain_operations.surface_inset_prepare(surface_inset_input())

        self.assertEqual(self.fake_core_api.save_as_copy_only_calls, [])
        self.assertEqual(self.fake_core_api.write_modification_report_calls, [])
        self.assertEqual(result.to_dict()["target_object"], "ChestArmor_Upper_01")
        self.assertNotIn("output_blend_copy", result.to_dict())
        self.assertNotIn("report_file", result.to_dict())

    def test_surface_inset_prepare_rejects_invalid_parameters_before_core_geometry_call(self) -> None:
        for parameters in (
            {"inset_depth": 0.0, "offset": -1.0, "modifier_name": "AI_SurfaceInset_Prepare"},
            {"inset_depth": 0.006, "offset": -1.0, "modifier_name": ""},
        ):
            with self.subTest(parameters=parameters):
                with self.assertRaises(ValueError):
                    domain_operations.surface_inset_prepare(surface_inset_input(parameters))
        self.assertEqual(self.fake_core_api.require_object_calls, [])

    def test_surface_inset_prepare_rejects_wrong_operation_contract(self) -> None:
        with self.assertRaises(ValueError) as error_context:
            domain_operations.surface_inset_prepare(
                DomainOperationInput(
                    task_id="task-009",
                    operation="edge_soften",
                    target_object="ChestArmor_Upper_01",
                    parameters={"inset_depth": 0.006, "offset": -1.0},
                    execution_policy={"mode": "safe_non_destructive", "preserve_source_file": True},
                )
            )

        self.assertIn("surface_inset_prepare cannot handle operation", str(error_context.exception))
        self.assertEqual(self.fake_core_api.require_object_calls, [])

    def test_armor_edge_lip_prepare_resolves_object_and_calls_core_api_bevel_modifier(self) -> None:
        result = domain_operations.armor_edge_lip_prepare(armor_edge_lip_input())

        self.assertEqual(self.fake_core_api.require_object_calls, ["ChestArmor_Edge_01"])
        self.assertIsInstance(result, OperationOutcome)
        self.assertEqual(result.operation, "armor_edge_lip_prepare")
        self.assertEqual(result.target_object, "ChestArmor_Edge_01")
        self.assertTrue(result.success)
        self.assertEqual(result.changed_objects, ["ChestArmor_Edge_01"])
        self.assertEqual(result.modifier_info["modifier_name"], "AI_ArmorEdgeLip_Prepare")
        self.assertEqual(result.modifier_info["modifier_type"], "BEVEL")
        self.assertEqual(result.modifier_info["width"], 0.008)
        self.assertEqual(result.modifier_info["segments"], 2)
        self.assertFalse(result.mesh_data_applied)

    def test_armor_edge_lip_prepare_uses_defaults_when_parameters_are_empty(self) -> None:
        result = domain_operations.armor_edge_lip_prepare(
            DomainOperationInput(
                task_id="task-010",
                operation="armor_edge_lip_prepare",
                target_object="Body",
                parameters={},
                execution_policy={"mode": "safe_non_destructive", "preserve_source_file": True},
            )
        )

        self.assertEqual(self.fake_core_api.require_object_calls, ["Body"])
        self.assertEqual(result.modifier_info["width"], 0.008)
        self.assertEqual(result.modifier_info["segments"], 2)
        self.assertEqual(result.modifier_info["modifier_name"], "AI_ArmorEdgeLip_Prepare")

    def test_armor_edge_lip_prepare_uses_explicit_parameters(self) -> None:
        result = domain_operations.armor_edge_lip_prepare(
            armor_edge_lip_input({"width": 0.012, "segments": 3, "modifier_name": "AI_Custom_ArmorEdgeLip"})
        )

        self.assertEqual(self.fake_core_api.add_bevel_modifier_calls[0]["width"], 0.012)
        self.assertEqual(self.fake_core_api.add_bevel_modifier_calls[0]["segments"], 3)
        self.assertEqual(self.fake_core_api.add_bevel_modifier_calls[0]["modifier_name"], "AI_Custom_ArmorEdgeLip")
        self.assertEqual(result.modifier_info["segments"], 3)

    def test_armor_edge_lip_prepare_does_not_save_copy_or_write_report(self) -> None:
        result = domain_operations.armor_edge_lip_prepare(armor_edge_lip_input())

        self.assertEqual(self.fake_core_api.save_as_copy_only_calls, [])
        self.assertEqual(self.fake_core_api.write_modification_report_calls, [])
        self.assertEqual(result.to_dict()["target_object"], "ChestArmor_Edge_01")
        self.assertNotIn("output_blend_copy", result.to_dict())
        self.assertNotIn("report_file", result.to_dict())

    def test_armor_edge_lip_prepare_rejects_invalid_parameters_before_core_geometry_call(self) -> None:
        for parameters in (
            {"width": 0.0, "segments": 2, "modifier_name": "AI_ArmorEdgeLip_Prepare"},
            {"width": 0.008, "segments": 0, "modifier_name": "AI_ArmorEdgeLip_Prepare"},
            {"width": 0.008, "segments": 2, "modifier_name": ""},
        ):
            with self.subTest(parameters=parameters):
                with self.assertRaises(ValueError):
                    domain_operations.armor_edge_lip_prepare(armor_edge_lip_input(parameters))
        self.assertEqual(self.fake_core_api.require_object_calls, [])

    def test_armor_edge_lip_prepare_rejects_wrong_operation_contract(self) -> None:
        with self.assertRaises(ValueError) as error_context:
            domain_operations.armor_edge_lip_prepare(
                DomainOperationInput(
                    task_id="task-010",
                    operation="edge_soften",
                    target_object="ChestArmor_Edge_01",
                    parameters={"width": 0.008, "segments": 2},
                    execution_policy={"mode": "safe_non_destructive", "preserve_source_file": True},
                )
            )

        self.assertIn("armor_edge_lip_prepare cannot handle operation", str(error_context.exception))
        self.assertEqual(self.fake_core_api.require_object_calls, [])

    def test_domain_operation_layer_does_not_import_bpy(self) -> None:
        source = Path(domain_operations.__file__).read_text(encoding="utf-8")

        self.assertNotIn("import bpy", source)
        self.assertNotIn("bpy.", source)
        self.assertNotIn("save_as_copy_only", source)
        self.assertNotIn("write_modification_report", source)
        self.assertNotIn("implementation_hint", source)
        self.assertNotIn("from runtime", source)
        self.assertNotIn("TaskObject", source)


if __name__ == "__main__":
    unittest.main()
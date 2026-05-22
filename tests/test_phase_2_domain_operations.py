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
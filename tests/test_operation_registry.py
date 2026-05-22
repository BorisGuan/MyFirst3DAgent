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
    def test_default_registry_exposes_only_edge_soften(self) -> None:
        registry = default_operation_registry()

        self.assertTrue(registry.has("edge_soften"))
        self.assertEqual([operation.name for operation in registry.all_specs()], ["edge_soften"])

    def test_edge_soften_spec_contains_required_contract_fields(self) -> None:
        spec = default_operation_registry().get("edge_soften")

        self.assertEqual(spec.name, "edge_soften")
        self.assertEqual(spec.supported_task_types, ("surface_detail_enhancement",))
        self.assertEqual(spec.required_target_state, "bound")
        self.assertEqual(spec.default_parameters, {"strength": 0.01, "style": "mechanical"})
        self.assertEqual(spec.safety_level, "safe_non_destructive")
        self.assertEqual(spec.handler_name, "edge_soften")
        self.assertIn("strength", spec.parameter_schema)
        self.assertIn("style", spec.parameter_schema)
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
            ["edge_soften"],
        )
        self.assertEqual(registry.supported_for_task_type("unsupported_task"), ())

    def test_operation_spec_to_dict_is_json_serializable(self) -> None:
        spec = default_operation_registry().get("edge_soften")
        encoded = json.dumps(spec.to_dict(), ensure_ascii=False)

        self.assertIn("edge_soften", encoded)
        self.assertEqual(spec.to_dict()["supported_task_types"], ["surface_detail_enhancement"])

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
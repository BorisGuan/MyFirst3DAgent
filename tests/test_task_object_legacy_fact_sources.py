import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
AGENT_ROOT = PROJECT_ROOT / "3d_agent"
DOCS_ROOT = PROJECT_ROOT / "docs"
if str(AGENT_ROOT) not in sys.path:
    sys.path.insert(0, str(AGENT_ROOT))

from modification_execution import LegacyModificationExecutionError, execute_modification_plan
from operation_planner import LegacyExecutionPathError, execute_operation_request


class TaskObjectLegacyFactSourceTests(unittest.TestCase):
    def test_cli_real_modification_path_does_not_build_operation_plan(self) -> None:
        source = (AGENT_ROOT / "cli.py").read_text(encoding="utf-8")

        self.assertNotIn("create_simplified_operation_plan", source)
        self.assertNotIn("build_operation_plan_from_cli", source)
        self.assertNotIn("execute_modification_plan", source)
        self.assertIn("run_task_object_cli", source)
        self.assertIn("execute_ready_task", source)

    def test_legacy_operation_dict_execution_apis_are_disabled(self) -> None:
        with self.assertRaises(LegacyModificationExecutionError):
            execute_modification_plan({"operation": "edge_soften"})
        with self.assertRaises(LegacyExecutionPathError):
            execute_operation_request({"operation": "edge_soften", "target_object": "Body"})

    def test_runtime_engine_does_not_accept_legacy_fact_sources(self) -> None:
        source = (AGENT_ROOT / "runtime" / "runtime_engine.py").read_text(encoding="utf-8")

        self.assertNotIn("OperationPlan", source)
        self.assertNotIn("execution_blueprint", source)
        self.assertNotIn("execution_package", source)
        self.assertNotIn("operation_plan", source)
        self.assertNotIn("execute_modification_plan", source)
        self.assertIn("TaskObject", source)

    def test_step18_documentation_records_task_object_main_chain(self) -> None:
        source = (DOCS_ROOT / "step_18_legacy_fact_source_cleanup.md").read_text(encoding="utf-8")

        self.assertIn("TaskObject", source)
        self.assertIn("Runtime", source)
        self.assertIn("OperationPlan", source)
        self.assertIn("retired", source)


if __name__ == "__main__":
    unittest.main()
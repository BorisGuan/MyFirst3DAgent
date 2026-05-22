import json
import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
AGENT_ROOT = PROJECT_ROOT / "3d_agent"
if str(AGENT_ROOT) not in sys.path:
    sys.path.insert(0, str(AGENT_ROOT))

from task_object import TaskIntent, TaskObject, TaskSource, TaskState, TaskTarget


class TaskObjectSchemaTests(unittest.TestCase):
    def test_creates_default_draft_task_object(self) -> None:
        task = TaskObject()

        self.assertEqual(task.state, TaskState.DRAFT)
        self.assertEqual(task.task_version, "task_object_v1")
        self.assertEqual(task.task_type, "model_edit")
        self.assertTrue(task.task_id)
        self.assertTrue(task.constraints.preserve_source_file)
        self.assertTrue(task.constraints.non_destructive)
        self.assertFalse(task.constraints.mesh_edit_allowed)
        self.assertEqual(task.execution_policy.mode, "safe_non_destructive")

    def test_supports_required_lifecycle_states(self) -> None:
        self.assertEqual(
            {state.value for state in TaskState},
            {
                "draft",
                "validated",
                "bound",
                "planned",
                "ready_to_execute",
                "executing",
                "completed",
                "failed",
            },
        )

    def test_to_dict_and_from_dict_round_trip_through_json(self) -> None:
        task = TaskObject(
            source=TaskSource(user_input="给胸甲做机械风格边缘软化", channel="cli"),
            target=TaskTarget(semantic_part="chest_armor"),
            intent=TaskIntent(
                action="enhance_detail",
                detail_type="edge_soften",
                style="mechanical",
                density="low",
                parameters={"strength": 0.01},
            ),
            artifact_refs={"design_brief": "outputs/design_brief.json"},
        )

        encoded = json.dumps(task.to_dict(), ensure_ascii=False)
        decoded = json.loads(encoded)
        restored = TaskObject.from_dict(decoded)

        self.assertEqual(decoded["state"], "draft")
        self.assertEqual(restored.state, TaskState.DRAFT)
        self.assertEqual(restored.source.user_input, "给胸甲做机械风格边缘软化")
        self.assertEqual(restored.target.semantic_part, "chest_armor")
        self.assertEqual(restored.intent.parameters, {"strength": 0.01})
        self.assertEqual(restored.artifact_refs, {"design_brief": "outputs/design_brief.json"})

    def test_default_nested_collections_are_not_shared(self) -> None:
        first_task = TaskObject()
        second_task = TaskObject()

        first_task.planning.parameters["strength"] = 0.01
        first_task.diagnostics.append("note")

        self.assertEqual(second_task.planning.parameters, {})
        self.assertEqual(second_task.diagnostics, [])

    def test_schema_does_not_store_full_logs_or_preview_payloads(self) -> None:
        task_data = TaskObject().to_dict()

        self.assertNotIn("logs", task_data)
        self.assertNotIn("preview_data", task_data)
        self.assertIn("artifact_refs", task_data)
        self.assertIn("diagnostics", task_data)

    def test_schema_has_no_blender_or_layer_dependencies(self) -> None:
        source = (AGENT_ROOT / "task_object" / "schema.py").read_text(encoding="utf-8")

        self.assertNotIn("import bpy", source)
        self.assertNotIn("bpy.", source)
        self.assertNotIn("from agent", source)
        self.assertNotIn("from planning", source)
        self.assertNotIn("from blender_ops", source)


if __name__ == "__main__":
    unittest.main()
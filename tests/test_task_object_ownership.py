import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
AGENT_ROOT = PROJECT_ROOT / "3d_agent"
if str(AGENT_ROOT) not in sys.path:
    sys.path.insert(0, str(AGENT_ROOT))

from task_object import (
    OwnershipLayer,
    TaskObject,
    TaskOwnershipError,
    TaskState,
    apply_owned_patch,
    owned_paths,
    validate_patch_owner,
)


class TaskObjectOwnershipTests(unittest.TestCase):
    def test_agent_layer_can_patch_agent_owned_fields(self) -> None:
        task = TaskObject()

        returned_task = apply_owned_patch(
            task,
            OwnershipLayer.AGENT,
            {
                "source": {"user_input": "给胸甲做机械风格边缘软化", "channel": "cli"},
                "task_type": "surface_detail_enhancement",
                "target": {"semantic_part": "chest_armor"},
                "intent": {"action": "enhance_detail", "style": "mechanical"},
                "constraints": {"notes": ["preserve silhouette"]},
            },
        )

        self.assertIs(returned_task, task)
        self.assertEqual(task.source.user_input, "给胸甲做机械风格边缘软化")
        self.assertEqual(task.task_type, "surface_detail_enhancement")
        self.assertEqual(task.target.semantic_part, "chest_armor")
        self.assertEqual(task.intent.action, "enhance_detail")
        self.assertEqual(task.constraints.notes, ["preserve silhouette"])

    def test_planning_layer_can_patch_planning_owned_fields(self) -> None:
        task = TaskObject(state=TaskState.VALIDATED)

        apply_owned_patch(
            task,
            "planning",
            {
                "state": "bound",
                "target": {
                    "bound_object": "ChestArmor_Upper_01",
                    "binding_candidates": ["ChestArmor_Upper_01"],
                },
                "planning": {
                    "selected_operation": "edge_soften",
                    "parameters": {"strength": 0.01},
                    "reasoning": ["safe default operation"],
                },
                "execution_policy": {"output_blend_copy": "outputs/chest.preview.blend"},
            },
        )

        self.assertEqual(task.state, TaskState.BOUND)
        self.assertEqual(task.target.bound_object, "ChestArmor_Upper_01")
        self.assertEqual(task.target.binding_candidates, ["ChestArmor_Upper_01"])
        self.assertEqual(task.planning.selected_operation, "edge_soften")
        self.assertEqual(task.planning.parameters, {"strength": 0.01})
        self.assertEqual(task.execution_policy.output_blend_copy, "outputs/chest.preview.blend")

    def test_runtime_layer_can_patch_runtime_result_and_final_state(self) -> None:
        task = TaskObject(state=TaskState.READY_TO_EXECUTE)

        apply_owned_patch(
            task,
            OwnershipLayer.RUNTIME,
            {
                "state": "executing",
                "runtime": {"source_blend_file": "source.blend"},
            },
        )
        apply_owned_patch(
            task,
            OwnershipLayer.RUNTIME,
            {
                "state": "completed",
                "result": {"success": True, "summary": "edge soften applied"},
            },
        )

        self.assertEqual(task.state, TaskState.COMPLETED)
        self.assertEqual(task.runtime.source_blend_file, "source.blend")
        self.assertTrue(task.result.success)
        self.assertEqual(task.result.summary, "edge soften applied")

    def test_reporting_layer_can_only_patch_artifact_refs(self) -> None:
        task = TaskObject()

        apply_owned_patch(task, OwnershipLayer.REPORTING, {"artifact_refs": {"report": "outputs/report.json"}})

        self.assertEqual(task.artifact_refs, {"report": "outputs/report.json"})
        with self.assertRaises(TaskOwnershipError):
            validate_patch_owner(OwnershipLayer.REPORTING, {"result": {"summary": "done"}})
        with self.assertRaises(TaskOwnershipError):
            validate_patch_owner(OwnershipLayer.REPORTING, {"state": "completed"})

    def test_rejects_non_owner_field_modifications(self) -> None:
        invalid_patches = (
            (OwnershipLayer.PLANNING, {"source": {"user_input": "changed"}}, "source.user_input"),
            (OwnershipLayer.RUNTIME, {"planning": {"selected_operation": "edge_soften"}}, "planning.selected_operation"),
            (OwnershipLayer.AGENT, {"target": {"bound_object": "Body"}}, "target.bound_object"),
            (OwnershipLayer.DOMAIN, {"result": {"summary": "changed"}}, "result.summary"),
        )

        for owner, patch, field_path in invalid_patches:
            with self.subTest(owner=owner, field_path=field_path):
                with self.assertRaises(TaskOwnershipError) as error_context:
                    validate_patch_owner(owner, patch)
                self.assertIn(owner.value, str(error_context.exception))
                self.assertIn(field_path, str(error_context.exception))

    def test_rejects_state_changes_outside_owner_stage(self) -> None:
        with self.assertRaises(TaskOwnershipError):
            validate_patch_owner(OwnershipLayer.AGENT, {"state": "validated"})
        with self.assertRaises(TaskOwnershipError):
            validate_patch_owner(OwnershipLayer.PLANNING, {"state": "executing"})
        with self.assertRaises(TaskOwnershipError):
            validate_patch_owner(OwnershipLayer.RUNTIME, {"state": "planned"})

    def test_state_patch_still_uses_lifecycle_rules(self) -> None:
        task = TaskObject(state=TaskState.DRAFT)

        with self.assertRaises(ValueError):
            apply_owned_patch(task, OwnershipLayer.PLANNING, {"state": "planned"})

        self.assertEqual(task.state, TaskState.DRAFT)

    def test_owned_paths_are_reportable(self) -> None:
        self.assertIn("target.semantic_part", owned_paths(OwnershipLayer.AGENT))
        self.assertIn("planning", owned_paths("planning"))
        self.assertEqual(owned_paths(OwnershipLayer.DOMAIN), ())

    def test_legacy_target_candidates_key_is_read_as_binding_candidates(self) -> None:
        task = TaskObject.from_dict({"target": {"semantic_part": "chest", "candidates": ["Body"]}})

        self.assertEqual(task.target.binding_candidates, ["Body"])

    def test_ownership_has_no_blender_or_runtime_dependency(self) -> None:
        source = (AGENT_ROOT / "task_object" / "ownership.py").read_text(encoding="utf-8")

        self.assertNotIn("import bpy", source)
        self.assertNotIn("bpy.", source)
        self.assertNotIn("from runtime", source)
        self.assertNotIn("from blender_ops", source)


if __name__ == "__main__":
    unittest.main()
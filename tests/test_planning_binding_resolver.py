import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
AGENT_ROOT = PROJECT_ROOT / "3d_agent"
if str(AGENT_ROOT) not in sys.path:
    sys.path.insert(0, str(AGENT_ROOT))

from planning import BindingResolutionError, resolve_task_binding
from task_object import TaskIntent, TaskObject, TaskSource, TaskState, TaskTarget


def validated_task(target_part: str = "chest_armor") -> TaskObject:
    return TaskObject(
        state=TaskState.VALIDATED,
        source=TaskSource(user_input="给胸甲做机械风格边缘软化", channel="agent_layer"),
        task_type="surface_detail_enhancement",
        target=TaskTarget(semantic_part=target_part),
        intent=TaskIntent(
            desired_effect="armor_layers",
            style="sharp_mechanical",
            density="low",
            scale="1/144",
        ),
    )


def fake_manifest() -> dict:
    return {
        "manifest_version": "v0_5",
        "source_software": "blender",
        "source_file": "fake.blend",
        "unit_system": "metric",
        "objects": [
            {
                "object_name": "ChestArmor_Upper_01",
                "object_type": "MESH",
                "collection_path": ["Gundam", "Body", "Chest"],
                "dimensions": [2.4, 0.8, 1.1],
                "location": [0.0, 0.0, 0.0],
                "rotation_euler": [0.0, 0.0, 0.0],
                "vertex_count": 1200,
                "material_names": ["armor_white"],
                "custom_properties": {"part_role": "chest_armor"},
            },
            {
                "object_name": "Panel_Unknown_03",
                "object_type": "MESH",
                "collection_path": ["Gundam", "Unsorted"],
                "material_names": ["armor_white"],
            },
        ],
    }


class PlanningBindingResolverTests(unittest.TestCase):
    def test_resolves_validated_task_to_bound_object_from_manifest(self) -> None:
        task = validated_task()

        returned_task = resolve_task_binding(task, scene_manifest=fake_manifest())

        self.assertIs(returned_task, task)
        self.assertEqual(task.state, TaskState.BOUND)
        self.assertEqual(task.target.bound_object, "ChestArmor_Upper_01")
        self.assertEqual(task.target.binding_candidates, ["ChestArmor_Upper_01"])

    def test_resolves_using_existing_binding_context(self) -> None:
        task = validated_task("leg")
        binding_context = {
            "target_part": "leg",
            "bindings": [
                {"object_name": "LeftLeg_Armor_01", "binding_status": "bound"},
                {"object_name": "RightLeg_Armor_01", "binding_status": "bound"},
            ],
        }

        resolve_task_binding(task, binding_context=binding_context)

        self.assertEqual(task.state, TaskState.BOUND)
        self.assertEqual(task.target.bound_object, "LeftLeg_Armor_01")
        self.assertEqual(task.target.binding_candidates, ["LeftLeg_Armor_01", "RightLeg_Armor_01"])

    def test_rejects_non_validated_task(self) -> None:
        task = validated_task()
        task.state = TaskState.DRAFT

        with self.assertRaises(BindingResolutionError) as error_context:
            resolve_task_binding(task, scene_manifest=fake_manifest())

        self.assertIn("state must be 'validated'", str(error_context.exception))

    def test_rejects_missing_manifest_or_binding_context(self) -> None:
        with self.assertRaises(BindingResolutionError) as error_context:
            resolve_task_binding(validated_task())

        self.assertIn("scene_manifest or binding_context is required", str(error_context.exception))

    def test_rejects_binding_context_for_different_target(self) -> None:
        with self.assertRaises(BindingResolutionError) as error_context:
            resolve_task_binding(
                validated_task("chest_armor"),
                binding_context={"target_part": "leg", "bindings": []},
            )

        self.assertIn("does not match", str(error_context.exception))

    def test_reports_candidate_objects_without_binding(self) -> None:
        task = validated_task()
        binding_context = {
            "target_part": "chest_armor",
            "bindings": [
                {"object_name": "ChestArmor_Candidate", "binding_status": "candidate"},
            ],
        }

        with self.assertRaises(BindingResolutionError) as error_context:
            resolve_task_binding(task, binding_context=binding_context)

        self.assertIn("candidate objects: ChestArmor_Candidate", str(error_context.exception))
        self.assertEqual(task.state, TaskState.VALIDATED)
        self.assertIsNone(task.target.bound_object)

    def test_reports_no_binding_candidates(self) -> None:
        with self.assertRaises(BindingResolutionError) as error_context:
            resolve_task_binding(
                validated_task("shield"),
                binding_context={"target_part": "shield", "bindings": []},
            )

        self.assertIn("No binding candidates found", str(error_context.exception))

    def test_resolver_does_not_select_operation_or_fill_parameters(self) -> None:
        task = validated_task()

        resolve_task_binding(task, scene_manifest=fake_manifest())

        self.assertIsNone(task.planning.selected_operation)
        self.assertEqual(task.planning.parameters, {})
        self.assertIsNone(task.runtime.source_blend_file)
        self.assertIsNone(task.result.success)

    def test_resolver_has_no_blender_domain_or_runtime_dependency(self) -> None:
        source = (AGENT_ROOT / "planning" / "binding_resolver.py").read_text(encoding="utf-8")

        self.assertNotIn("import bpy", source)
        self.assertNotIn("bpy.", source)
        self.assertNotIn("from blender_ops", source)
        self.assertNotIn("from runtime", source)
        self.assertNotIn("operation_planner", source)
        self.assertNotIn("modification_execution", source)


if __name__ == "__main__":
    unittest.main()
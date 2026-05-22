import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
AGENT_ROOT = PROJECT_ROOT / "3d_agent"
if str(AGENT_ROOT) not in sys.path:
    sys.path.insert(0, str(AGENT_ROOT))

from model.model_binding import create_model_binding_context, review_execution_package_with_binding
from model.scene_manifest import load_scene_manifest, normalize_scene_manifest


CHEST_EXECUTION_PACKAGE = {
    "target_part": "chest_armor",
    "required_inputs": ["real_mesh_file", "target_part_object", "surface_boundary_reference"],
    "blocked_by": ["no_real_mesh", "no_surface_boundaries"],
}
SENSOR_EXECUTION_PACKAGE = {
    "target_part": "camera_sensor",
    "required_inputs": ["real_mesh_file", "target_part_object", "orientation_reference"],
    "blocked_by": ["no_real_mesh"],
}


class V05ModelBindingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.manifest = load_scene_manifest(PROJECT_ROOT / "examples" / "blender_scene_manifest.json")

    def test_chest_armor_binds_to_mesh_object(self) -> None:
        context = create_model_binding_context(
            self.manifest,
            "chest_armor",
            CHEST_EXECUTION_PACKAGE,
            source_manifest_ref="examples/blender_scene_manifest.json",
        )

        self.assertEqual(
            set(context),
            {
                "binding_version",
                "source_manifest_ref",
                "target_part",
                "bindings",
                "unbound_parts",
                "unmatched_objects",
                "binding_summary",
            },
        )
        self.assertEqual(context["binding_version"], "v0_5")
        self.assertEqual(context["source_manifest_ref"], "examples/blender_scene_manifest.json")
        self.assertEqual(context["target_part"], "chest_armor")
        self.assertEqual(context["unbound_parts"], [])

        binding = context["bindings"][0]
        self.assertEqual(binding["object_name"], "ChestArmor_Upper_01")
        self.assertEqual(binding["binding_status"], "bound")
        self.assertGreaterEqual(binding["confidence"], 0.90)
        self.assertIn("custom_property:part_role", binding["evidence"])
        self.assertIn("real_mesh_file", binding["resolved_inputs"])
        self.assertIn("target_part_object", binding["resolved_inputs"])
        self.assertNotIn("no_real_mesh", binding["remaining_blockers"])
        self.assertIn("no_surface_boundaries", binding["remaining_blockers"])

    def test_backpack_does_not_bind_thruster_children_as_backpack(self) -> None:
        context = create_model_binding_context(self.manifest, "backpack")

        bound_names = [binding["object_name"] for binding in context["bindings"]]
        self.assertEqual(bound_names, ["Backpack_Block_01"])
        self.assertIn("Backpack_Thruster_L", context["unmatched_objects"])
        self.assertIn("Backpack_Thruster_R", context["unmatched_objects"])

    def test_leg_binds_left_and_right_leg_objects(self) -> None:
        context = create_model_binding_context(self.manifest, "leg")

        bound_names = {binding["object_name"] for binding in context["bindings"]}
        self.assertEqual(bound_names, {"LeftLeg_Armor_01", "RightLeg_Armor_01"})
        self.assertEqual(context["unbound_parts"], [])
        self.assertIn("LeftLeg_Armor_01", context["binding_summary"])
        self.assertIn("RightLeg_Armor_01", context["binding_summary"])

    def test_camera_sensor_binds_with_orientation_related_evidence(self) -> None:
        context = create_model_binding_context(self.manifest, "camera_sensor")
        binding = context["bindings"][0]

        self.assertEqual(binding["object_name"], "Head_CameraSensor_01")
        self.assertEqual(binding["binding_status"], "bound")
        self.assertEqual(binding["object_summary"]["object_type"], "MESH")

    def test_name_and_collection_match_without_part_role_stays_candidate(self) -> None:
        manifest = normalize_scene_manifest(
            {
                "manifest_version": "v0_5",
                "source_software": "blender",
                "source_file": "candidate.blend",
                "objects": [
                    {
                        "object_name": "ChestArmor_Candidate",
                        "object_type": "MESH",
                        "collection_path": ["Gundam", "Body", "Chest"],
                        "material_names": ["armor_white"],
                    }
                ],
            }
        )
        context = create_model_binding_context(manifest, "chest_armor", CHEST_EXECUTION_PACKAGE)
        binding = context["bindings"][0]

        self.assertEqual(binding["binding_status"], "candidate")
        self.assertIn("chest_armor", context["unbound_parts"])
        self.assertEqual(binding["resolved_inputs"], [])
        self.assertEqual(binding["remaining_blockers"], ["no_real_mesh", "no_surface_boundaries"])

    def test_non_mesh_auxiliary_object_is_not_bound(self) -> None:
        context = create_model_binding_context(self.manifest, "chest_armor")

        bound_names = {binding["object_name"] for binding in context["bindings"]}
        self.assertNotIn("Chest_SurfaceGuide_Curve", bound_names)
        self.assertIn("Chest_SurfaceGuide_Curve", context["unmatched_objects"])

    def test_unknown_target_part_returns_unbound_context(self) -> None:
        manifest = normalize_scene_manifest(
            {
                "manifest_version": "v0_5",
                "source_software": "blender",
                "source_file": "unknown.blend",
                "objects": [
                    {
                        "object_name": "Panel_Unknown_03",
                        "object_type": "MESH",
                        "collection_path": ["Gundam", "Unsorted"],
                        "material_names": ["armor_white"],
                    }
                ],
            }
        )
        context = create_model_binding_context(manifest, "shield")

        self.assertEqual(context["bindings"], [])
        self.assertEqual(context["unbound_parts"], ["shield"])
        self.assertIn("Panel_Unknown_03", context["unmatched_objects"])

    def test_execution_package_review_resolves_object_level_inputs_only(self) -> None:
        binding_context = create_model_binding_context(
            self.manifest,
            "chest_armor",
            CHEST_EXECUTION_PACKAGE,
        )
        review = review_execution_package_with_binding(CHEST_EXECUTION_PACKAGE, binding_context)

        self.assertEqual(
            set(review),
            {
                "review_version",
                "source_package_ref",
                "source_binding_ref",
                "target_part",
                "binding_status",
                "bound_objects",
                "resolved_inputs",
                "unresolved_inputs",
                "resolved_blockers",
                "remaining_blockers",
                "review_status",
                "review_notes",
                "review_summary",
            },
        )
        self.assertEqual(review["review_version"], "v0_5")
        self.assertEqual(review["binding_status"], "bound")
        self.assertEqual(review["bound_objects"], ["ChestArmor_Upper_01"])
        self.assertIn("real_mesh_file", review["resolved_inputs"])
        self.assertIn("target_part_object", review["resolved_inputs"])
        self.assertIn("surface_boundary_reference", review["unresolved_inputs"])
        self.assertEqual(review["resolved_blockers"], ["no_real_mesh"])
        self.assertEqual(review["remaining_blockers"], ["no_surface_boundaries"])
        self.assertEqual(review["review_status"], "partially_resolved")

    def test_execution_package_review_tracks_non_blocker_required_inputs(self) -> None:
        binding_context = create_model_binding_context(
            self.manifest,
            "camera_sensor",
            SENSOR_EXECUTION_PACKAGE,
        )
        review = review_execution_package_with_binding(SENSOR_EXECUTION_PACKAGE, binding_context)

        self.assertEqual(review["resolved_blockers"], ["no_real_mesh"])
        self.assertEqual(review["remaining_blockers"], [])
        self.assertIn("orientation_reference", review["unresolved_inputs"])
        self.assertEqual(review["review_status"], "partially_resolved")

    def test_execution_package_review_requires_confirmation_for_candidate_binding(self) -> None:
        manifest = normalize_scene_manifest(
            {
                "manifest_version": "v0_5",
                "source_software": "blender",
                "source_file": "candidate.blend",
                "objects": [
                    {
                        "object_name": "ChestArmor_Candidate",
                        "object_type": "MESH",
                        "collection_path": ["Gundam", "Body", "Chest"],
                        "material_names": ["armor_white"],
                    }
                ],
            }
        )
        binding_context = create_model_binding_context(manifest, "chest_armor", CHEST_EXECUTION_PACKAGE)
        review = review_execution_package_with_binding(CHEST_EXECUTION_PACKAGE, binding_context)

        self.assertEqual(review["binding_status"], "candidate")
        self.assertEqual(review["bound_objects"], [])
        self.assertEqual(review["resolved_inputs"], [])
        self.assertEqual(review["resolved_blockers"], [])
        self.assertEqual(review["remaining_blockers"], ["no_real_mesh", "no_surface_boundaries"])
        self.assertEqual(review["review_status"], "needs_user_confirmation")

    def test_execution_package_review_blocks_when_no_binding_exists(self) -> None:
        binding_context = create_model_binding_context(self.manifest, "unknown_part", CHEST_EXECUTION_PACKAGE)
        review = review_execution_package_with_binding(CHEST_EXECUTION_PACKAGE, binding_context)

        self.assertEqual(review["binding_status"], "unbound")
        self.assertEqual(review["bound_objects"], [])
        self.assertEqual(review["review_status"], "blocked")
        self.assertIn("未找到可信绑定对象", review["review_summary"])


if __name__ == "__main__":
    unittest.main()
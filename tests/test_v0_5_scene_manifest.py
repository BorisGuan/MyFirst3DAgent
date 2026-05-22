import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
AGENT_ROOT = PROJECT_ROOT / "3d_agent"
if str(AGENT_ROOT) not in sys.path:
    sys.path.insert(0, str(AGENT_ROOT))

from model.scene_manifest import load_scene_manifest, normalize_scene_manifest


class V05SceneManifestTests(unittest.TestCase):
    def test_load_sample_scene_manifest_outputs_contract_fields(self) -> None:
        manifest = load_scene_manifest(PROJECT_ROOT / "examples" / "blender_scene_manifest.json")

        self.assertEqual(
            set(manifest),
            {"manifest_version", "source_software", "source_file", "unit_system", "objects"},
        )
        self.assertEqual(manifest["manifest_version"], "v0_5")
        self.assertEqual(manifest["source_software"], "blender")
        self.assertEqual(manifest["unit_system"], "metric")
        self.assertEqual(len(manifest["objects"]), 10)

    def test_sample_manifest_covers_required_target_parts(self) -> None:
        manifest = load_scene_manifest(PROJECT_ROOT / "examples" / "blender_scene_manifest.json")
        part_roles = {
            scene_object["custom_properties"].get("part_role")
            for scene_object in manifest["objects"]
            if scene_object["custom_properties"].get("part_role")
        }

        self.assertTrue(
            {"chest_armor", "backpack", "leg", "shield", "camera_sensor", "thruster"}.issubset(part_roles)
        )

    def test_loader_normalizes_optional_object_defaults(self) -> None:
        manifest = normalize_scene_manifest(
            {
                "manifest_version": "v0_5",
                "source_software": "blender",
                "source_file": "minimal.blend",
                "objects": [{"object_name": "MinimalObject"}],
            }
        )
        scene_object = manifest["objects"][0]

        self.assertEqual(manifest["unit_system"], "unknown")
        self.assertEqual(scene_object["object_type"], "UNKNOWN")
        self.assertEqual(scene_object["collection_path"], [])
        self.assertEqual(scene_object["dimensions"], [])
        self.assertEqual(scene_object["location"], [])
        self.assertEqual(scene_object["rotation_euler"], [])
        self.assertEqual(scene_object["vertex_count"], 0)
        self.assertEqual(scene_object["material_names"], [])
        self.assertEqual(scene_object["custom_properties"], {})

    def test_loader_keeps_curve_as_auxiliary_non_mesh_object(self) -> None:
        manifest = load_scene_manifest(PROJECT_ROOT / "examples" / "blender_scene_manifest.json")
        curve_objects = [scene_object for scene_object in manifest["objects"] if scene_object["object_type"] == "CURVE"]

        self.assertEqual(len(curve_objects), 1)
        self.assertEqual(curve_objects[0]["object_name"], "Chest_SurfaceGuide_Curve")
        self.assertEqual(
            curve_objects[0]["custom_properties"]["guide_role"],
            "surface_boundary_candidate",
        )

    def test_loader_rejects_unsupported_source_software(self) -> None:
        with self.assertRaisesRegex(ValueError, "source_software must be 'blender'"):
            normalize_scene_manifest(
                {
                    "manifest_version": "v0_5",
                    "source_software": "maya",
                    "source_file": "demo.mb",
                    "objects": [],
                }
            )

    def test_loader_rejects_invalid_vector_field(self) -> None:
        with self.assertRaisesRegex(ValueError, "dimensions must be an empty list or a 3-number list"):
            normalize_scene_manifest(
                {
                    "manifest_version": "v0_5",
                    "source_software": "blender",
                    "source_file": "demo.blend",
                    "objects": [
                        {
                            "object_name": "BadDimensions",
                            "object_type": "MESH",
                            "dimensions": [1.0, 2.0],
                        }
                    ],
                }
            )

    def test_loader_rejects_invalid_object_type(self) -> None:
        with self.assertRaisesRegex(ValueError, "object_type must be a supported object type"):
            normalize_scene_manifest(
                {
                    "manifest_version": "v0_5",
                    "source_software": "blender",
                    "source_file": "demo.blend",
                    "objects": [
                        {
                            "object_name": "BadType",
                            "object_type": "METABALL",
                        }
                    ],
                }
            )


if __name__ == "__main__":
    unittest.main()
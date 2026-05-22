import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
AGENT_ROOT = PROJECT_ROOT / "3d_agent"
if str(AGENT_ROOT) not in sys.path:
    sys.path.insert(0, str(AGENT_ROOT))

from main import build_cli_result, parse_cli_args


class V05CliSceneManifestTests(unittest.TestCase):
    def setUp(self) -> None:
        self.scene_manifest_path = str(PROJECT_ROOT / "examples" / "blender_scene_manifest.json")

    def test_parse_cli_args_removes_scene_manifest_pair(self) -> None:
        (
            user_input,
            include_package,
            include_script,
            scene_manifest_path,
            include_geometry_preview,
            include_preview_script_draft,
        ) = parse_cli_args(
            [
                "给胸甲加分件线",
                "--execution-package",
                "--scene-manifest",
                self.scene_manifest_path,
            ]
        )

        self.assertEqual(user_input, "给胸甲加分件线")
        self.assertTrue(include_package)
        self.assertFalse(include_script)
        self.assertEqual(scene_manifest_path, self.scene_manifest_path)
        self.assertFalse(include_geometry_preview)
        self.assertFalse(include_preview_script_draft)

    def test_parse_cli_args_rejects_missing_scene_manifest_path(self) -> None:
        with self.assertRaisesRegex(ValueError, "requires a path argument"):
            parse_cli_args(["给胸甲加分件线", "--scene-manifest"])

    def test_cli_result_can_include_model_binding_and_review(self) -> None:
        result = build_cli_result(
            "给胸甲加一些锐利的分件线，适合 1/144 打印。",
            include_execution_package=True,
            scene_manifest_path=self.scene_manifest_path,
        )

        self.assertEqual(result["command_type"], "model_edit")
        self.assertIn("execution_package", result)
        self.assertIn("model_binding_context", result)
        self.assertIn("execution_package_review", result)
        self.assertEqual(result["model_binding_context"]["target_part"], "chest_armor")
        self.assertEqual(result["model_binding_context"]["bindings"][0]["object_name"], "ChestArmor_Upper_01")
        self.assertEqual(result["execution_package_review"]["binding_status"], "bound")
        self.assertIn("no_real_mesh", result["execution_package_review"]["resolved_blockers"])
        self.assertIn("no_surface_boundaries", result["execution_package_review"]["remaining_blockers"])

    def test_scene_manifest_implies_execution_package(self) -> None:
        result = build_cli_result(
            "给胸甲加一些锐利的分件线，适合 1/144 打印。",
            scene_manifest_path=self.scene_manifest_path,
        )

        self.assertIn("execution_package", result)
        self.assertIn("model_binding_context", result)
        self.assertIn("execution_package_review", result)

    def test_cli_scene_manifest_does_not_affect_context_queries(self) -> None:
        result = build_cli_result(
            "现在有哪些部件？",
            include_execution_package=True,
            include_script_draft=True,
            scene_manifest_path=self.scene_manifest_path,
        )

        self.assertEqual(result["command_type"], "inspect_context")
        self.assertNotIn("execution_package", result)
        self.assertNotIn("model_binding_context", result)
        self.assertNotIn("execution_package_review", result)


if __name__ == "__main__":
    unittest.main()
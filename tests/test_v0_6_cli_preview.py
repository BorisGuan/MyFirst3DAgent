import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
AGENT_ROOT = PROJECT_ROOT / "3d_agent"
if str(AGENT_ROOT) not in sys.path:
    sys.path.insert(0, str(AGENT_ROOT))

from main import build_cli_result, parse_cli_args


class V06CliPreviewTests(unittest.TestCase):
    def setUp(self) -> None:
        self.scene_manifest_path = str(PROJECT_ROOT / "examples" / "blender_scene_manifest.json")

    def test_parse_cli_args_removes_v0_6_flags(self) -> None:
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
                "--scene-manifest",
                self.scene_manifest_path,
                "--geometry-preview",
                "--preview-script-draft",
            ]
        )

        self.assertEqual(user_input, "给胸甲加分件线")
        self.assertFalse(include_package)
        self.assertFalse(include_script)
        self.assertEqual(scene_manifest_path, self.scene_manifest_path)
        self.assertTrue(include_geometry_preview)
        self.assertTrue(include_preview_script_draft)

    def test_preview_script_draft_implies_geometry_preview(self) -> None:
        (
            user_input,
            include_package,
            include_script,
            scene_manifest_path,
            include_geometry_preview,
            include_preview_script_draft,
        ) = parse_cli_args(
            ["给胸甲加分件线", "--scene-manifest", self.scene_manifest_path, "--preview-script-draft"]
        )

        self.assertEqual(user_input, "给胸甲加分件线")
        self.assertFalse(include_package)
        self.assertFalse(include_script)
        self.assertEqual(scene_manifest_path, self.scene_manifest_path)
        self.assertTrue(include_geometry_preview)
        self.assertTrue(include_preview_script_draft)

    def test_geometry_preview_requires_scene_manifest(self) -> None:
        with self.assertRaisesRegex(ValueError, "requires --scene-manifest"):
            build_cli_result(
                "给胸甲加一些锐利的分件线，适合 1/144 打印。",
                include_geometry_preview=True,
            )

    def test_cli_can_include_geometry_preview_plan_and_safe_session(self) -> None:
        result = build_cli_result(
            "给胸甲加一些锐利的分件线，适合 1/144 打印。",
            scene_manifest_path=self.scene_manifest_path,
            include_geometry_preview=True,
        )

        self.assertEqual(result["command_type"], "model_edit")
        self.assertIn("execution_package", result)
        self.assertIn("model_binding_context", result)
        self.assertIn("execution_package_review", result)
        self.assertIn("geometry_preview_plan", result)
        self.assertIn("safe_preview_session", result)
        self.assertNotIn("blender_preview_script_draft", result)
        self.assertEqual(result["geometry_preview_plan"]["preview_version"], "v0_6")
        self.assertEqual(result["safe_preview_session"]["execution_mode"], "preview_only")

    def test_cli_preview_script_draft_includes_all_v0_6_outputs(self) -> None:
        result = build_cli_result(
            "给胸甲加一些锐利的分件线，适合 1/144 打印。",
            scene_manifest_path=self.scene_manifest_path,
            include_preview_script_draft=True,
        )

        self.assertIn("geometry_preview_plan", result)
        self.assertIn("safe_preview_session", result)
        self.assertIn("blender_preview_script_draft", result)
        self.assertIn("V0.6 Blender Preview Script Draft", result["blender_preview_script_draft"])

    def test_cli_v0_6_flags_do_not_affect_context_queries(self) -> None:
        result = build_cli_result(
            "现在有哪些部件？",
            scene_manifest_path=self.scene_manifest_path,
            include_geometry_preview=True,
            include_preview_script_draft=True,
        )

        self.assertEqual(result["command_type"], "inspect_context")
        self.assertNotIn("execution_package", result)
        self.assertNotIn("model_binding_context", result)
        self.assertNotIn("execution_package_review", result)
        self.assertNotIn("geometry_preview_plan", result)
        self.assertNotIn("safe_preview_session", result)
        self.assertNotIn("blender_preview_script_draft", result)


if __name__ == "__main__":
    unittest.main()
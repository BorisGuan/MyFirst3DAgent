import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
AGENT_ROOT = PROJECT_ROOT / "3d_agent"
if str(AGENT_ROOT) not in sys.path:
    sys.path.insert(0, str(AGENT_ROOT))

from agent.blender_preview_script_draft import create_blender_preview_script_draft
from agent.geometry_preview import create_geometry_preview_plan
from agent.safe_preview_session import create_safe_preview_session
from main import build_cli_result


SCENE_MANIFEST_PATH = PROJECT_ROOT / "examples" / "blender_scene_manifest.json"


class V08BVisualPreviewGuideTests(unittest.TestCase):
    def _preview_plan_and_script(self, user_input: str) -> tuple[dict, str]:
        result = build_cli_result(user_input, scene_manifest_path=str(SCENE_MANIFEST_PATH))
        plan = create_geometry_preview_plan(
            result["execution_package"],
            result["model_binding_context"],
            result["execution_package_review"],
        )
        session = create_safe_preview_session(plan)
        script = create_blender_preview_script_draft(plan, session)
        return plan, script

    def test_preview_elements_include_visual_guide_metadata(self) -> None:
        plan, _ = self._preview_plan_and_script("给胸甲加一些锐利的分件线，适合 1/144 打印。")

        self.assertTrue(plan["preview_elements"])
        visual_guide = plan["preview_elements"][0]["visual_guide"]
        self.assertEqual(visual_guide["guide_version"], "v0_8b")
        self.assertTrue(visual_guide["preview_only"])
        self.assertTrue(visual_guide["non_destructive"])
        self.assertIn(visual_guide["guide_type"], {"curve_line_overlay", "annotation_disc", "text_note"})

    def test_panel_line_preview_script_creates_curve_visual_guides(self) -> None:
        _, script = self._preview_plan_and_script("给胸甲加一些锐利的分件线，适合 1/144 打印。")

        self.assertIn('bpy.data.curves.new(preview_name, "CURVE")', script)
        self.assertIn("curve.bevel_depth", script)
        self.assertIn("create_curve_line_guide", script)
        self.assertIn('preview_object["v0_8b_visual_guide"] = True', script)
        self.assertIn("generated_visual_guides", script)

    def test_thruster_preview_script_creates_transparent_blockout_guides(self) -> None:
        _, script = self._preview_plan_and_script("把背包的推进器做得更高机动一点，加喷口和机械细节。")

        self.assertIn("create_blockout_guide", script)
        self.assertIn("mesh.from_pydata", script)
        self.assertIn("AI_Preview_Orange", script)
        self.assertNotIn("bpy.ops", script)
        self.assertNotIn("save_as_mainfile", script)

    def test_cli_preview_script_draft_contains_visual_guide_fields(self) -> None:
        result = build_cli_result(
            "给胸甲加一些锐利的分件线，适合 1/144 打印。",
            scene_manifest_path=str(SCENE_MANIFEST_PATH),
            include_preview_script_draft=True,
        )

        preview_elements = result["geometry_preview_plan"]["preview_elements"]
        self.assertTrue(all("visual_guide" in element for element in preview_elements))
        self.assertIn("generated_visual_guides", result["blender_preview_script_draft"])


if __name__ == "__main__":
    unittest.main()
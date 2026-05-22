import json
import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
AGENT_ROOT = PROJECT_ROOT / "3d_agent"
if str(AGENT_ROOT) not in sys.path:
    sys.path.insert(0, str(AGENT_ROOT))

from agent.blender_authoring_script import create_blender_authoring_script
from blender_ops.authoring_api import blender_authoring_api_source
from integration.blender_runner import run_blender_execution_request, write_blender_authoring_execution_script
from main import build_cli_result, parse_cli_args


SCENE_MANIFEST_PATH = PROJECT_ROOT / "examples" / "blender_scene_manifest.json"
BLEND_FILE_PATH = PROJECT_ROOT / "examples" / "BlendFile" / "Gundam" / "GF-Gundam.blend"


class V09ABlenderAuthoringApiTests(unittest.TestCase):
    def test_authoring_api_source_contains_safe_helper_methods(self) -> None:
        source = blender_authoring_api_source()

        self.assertIn("def ensure_collection", source)
        self.assertIn("def create_panel_line_curve_guide", source)
        self.assertIn("def save_as_copy_only", source)
        self.assertNotIn("bpy.ops.mesh", source)
        self.assertNotIn("modifier_apply", source)

    def test_authoring_script_uses_api_instead_of_inline_curve_logic(self) -> None:
        result = build_cli_result(
            "给胸甲加一些锐利的分件线，适合 1/144 打印。",
            scene_manifest_path=str(SCENE_MANIFEST_PATH),
            include_geometry_preview=True,
        )
        script = create_blender_authoring_script(result["geometry_preview_plan"], result["safe_preview_session"])

        self.assertIn("V0.9A Blender Authoring Script", script)
        self.assertIn("from blender_authoring_api import create_panel_line_curve_guide", script)
        self.assertIn("generated_authoring_objects", script)
        self.assertIn('"surface_detail_hint"', script)
        self.assertIn("v0_9a_only_authors_panel_line_curve_guides", script)
        self.assertNotIn("bpy.data.curves.new", script)

    def test_write_authoring_execution_script_writes_api_module(self) -> None:
        script = 'from pathlib import Path\nauthoring_report = {}\nreport_path = Path(f"{session_id}_authoring_report.json")\nprint(f"Wrote V0.9A authoring report to {report_path}")'
        with tempfile.TemporaryDirectory() as temp_dir:
            script_path = Path(
                write_blender_authoring_execution_script(
                    script,
                    str(Path(temp_dir) / "authoring_report.json"),
                    output_dir=temp_dir,
                )
            )
            api_path = Path(temp_dir) / "blender_authoring_api.py"

            self.assertTrue(script_path.exists())
            self.assertTrue(api_path.exists())
            self.assertIn("create_panel_line_curve_guide", api_path.read_text(encoding="utf-8"))
            self.assertIn("authoring_report.json", script_path.read_text(encoding="utf-8"))

    def test_parse_cli_args_accepts_authoring_curve_guide_flag(self) -> None:
        parsed = parse_cli_args(
            [
                "给胸甲加分件线",
                "--scene-manifest",
                str(SCENE_MANIFEST_PATH),
                "--blend-file",
                str(BLEND_FILE_PATH),
                "--authoring-curve-guide",
                "--run-authoring",
            ]
        )

        self.assertTrue(parsed.include_authoring_curve_guide)
        self.assertTrue(parsed.run_authoring)
        self.assertTrue(parsed.include_geometry_preview)
        self.assertTrue(parsed.include_design_rule_review)

    def test_build_cli_result_creates_authoring_request_without_running_preview(self) -> None:
        result = build_cli_result(
            "给胸甲加一些锐利的分件线，适合 1/144 打印。",
            scene_manifest_path=str(SCENE_MANIFEST_PATH),
            blend_file_path=str(BLEND_FILE_PATH),
            include_authoring_curve_guide=True,
        )

        self.assertIn("blender_authoring_script", result)
        self.assertIn("blender_authoring_request", result)
        self.assertEqual(result["blender_authoring_request"]["output_report_file"], "outputs/v0_9a_authoring_report.json")
        self.assertEqual(result["blender_authoring_script_safety_scan"]["safety_status"], "passed")

    def test_runner_reports_generated_authoring_objects(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            fake_blender = temp_path / "fake_blender.py"
            script_file = temp_path / "script.py"
            report_file = temp_path / "authoring_report.json"
            script_file.write_text("print('unused')", encoding="utf-8")
            report_file.write_text(
                json.dumps(
                    {
                        "session_id": "authoring_001",
                        "target_part": "chest_armor",
                        "generated_authoring_objects": [{"object_name": "curve_001"}],
                    }
                ),
                encoding="utf-8",
            )
            fake_blender.write_text("import sys\nprint('Blender 5.1.1')\nsys.exit(0)\n", encoding="utf-8")
            request = {
                "execution_mode": "preview_only",
                "blender_executable": str(fake_blender),
                "source_blend_file": str(script_file),
                "script_file": str(fake_blender),
                "output_report_file": str(report_file),
            }

            report = run_blender_execution_request(request)

        self.assertEqual(report["execution_status"], "success")
        self.assertEqual(report["generated_authoring_objects"], [{"object_name": "curve_001"}])
        self.assertFalse(report["modified_bound_mesh"])


if __name__ == "__main__":
    unittest.main()
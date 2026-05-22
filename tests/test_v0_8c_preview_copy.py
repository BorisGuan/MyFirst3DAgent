import json
import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
AGENT_ROOT = PROJECT_ROOT / "3d_agent"
if str(AGENT_ROOT) not in sys.path:
    sys.path.insert(0, str(AGENT_ROOT))

from integration.blender_runner import run_blender_execution_request, write_blender_execution_script
from integration.blender_script_safety import scan_blender_preview_script
from main import build_cli_result, parse_cli_args


SCENE_MANIFEST_PATH = PROJECT_ROOT / "examples" / "blender_scene_manifest.json"
BLEND_FILE_PATH = PROJECT_ROOT / "examples" / "BlendFile" / "Gundam" / "GF-Gundam.blend"


class V08CPreviewCopyTests(unittest.TestCase):
    def test_parse_cli_args_accepts_save_preview_copy_flags(self) -> None:
        parsed = parse_cli_args(
            [
                "给胸甲加分件线",
                "--scene-manifest",
                str(SCENE_MANIFEST_PATH),
                "--blend-file",
                str(BLEND_FILE_PATH),
                "--save-preview-copy",
                "--output-blend-copy",
                "outputs/custom.preview.blend",
            ]
        )

        self.assertTrue(parsed.save_preview_copy)
        self.assertEqual(parsed.output_blend_copy, "outputs/custom.preview.blend")

    def test_build_cli_result_save_copy_request_uses_separate_output_path(self) -> None:
        result = build_cli_result(
            "给胸甲加一些锐利的分件线，适合 1/144 打印。",
            scene_manifest_path=str(SCENE_MANIFEST_PATH),
            blend_file_path=str(BLEND_FILE_PATH),
            save_preview_copy=True,
            output_blend_copy="outputs/custom.preview.blend",
        )

        request = result["blender_execution_request"]
        self.assertTrue(request["save_copy"])
        self.assertEqual(request["output_blend_copy"], "outputs/custom.preview.blend")
        self.assertEqual(result["blender_preview_script_safety_scan"]["safety_status"], "passed")
        self.assertIn("bpy.ops.wm.save_as_mainfile", result["blender_preview_script_safety_scan"]["allowed_save_copy_tokens"])

    def test_save_copy_cannot_overwrite_source_blend(self) -> None:
        with self.assertRaisesRegex(ValueError, "must not overwrite"):
            build_cli_result(
                "给胸甲加一些锐利的分件线，适合 1/144 打印。",
                scene_manifest_path=str(SCENE_MANIFEST_PATH),
                blend_file_path=str(BLEND_FILE_PATH),
                save_preview_copy=True,
                output_blend_copy=str(BLEND_FILE_PATH),
            )

    def test_safety_scan_blocks_save_as_mainfile_unless_save_copy_allowed(self) -> None:
        script = "import bpy\nbpy.ops.wm.save_as_mainfile(filepath='x.blend')"

        self.assertEqual(scan_blender_preview_script(script)["safety_status"], "blocked")
        self.assertEqual(scan_blender_preview_script(script, allow_save_copy=True)["safety_status"], "passed")

    def test_write_execution_script_injects_save_copy_block(self) -> None:
        script = 'from pathlib import Path\nimport json\nimport bpy\npreview_report = {}\nreport_path = Path(f"{session_id}_preview_report.json")\nprint(f"Wrote V0.6 preview report to {report_path}")'
        with tempfile.TemporaryDirectory() as temp_dir:
            script_path = Path(
                write_blender_execution_script(
                    script,
                    str(Path(temp_dir) / "report.json"),
                    save_copy=True,
                    output_blend_copy=str(Path(temp_dir) / "copy.blend"),
                    output_dir=temp_dir,
                )
            )
            written = script_path.read_text(encoding="utf-8")

        self.assertIn("output_blend_copy", written)
        self.assertIn("Refusing to overwrite the source .blend file", written)
        self.assertIn("bpy.ops.wm.save_as_mainfile", written)

    def test_runner_reports_saved_preview_copy_from_script_report(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            fake_blender = temp_path / "fake_blender.py"
            script_file = temp_path / "script.py"
            report_file = temp_path / "report.json"
            output_copy = temp_path / "copy.blend"
            script_file.write_text("print('unused')", encoding="utf-8")
            report_file.write_text(
                json.dumps(
                    {
                        "session_id": "preview_001",
                        "target_part": "chest_armor",
                        "generated_objects": ["a"],
                        "saved_preview_copy": True,
                        "output_blend_copy": str(output_copy),
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
        self.assertTrue(report["saved_preview_copy"])
        self.assertEqual(report["output_blend_copy"], str(output_copy))
        self.assertFalse(report["saved_original_file"])


if __name__ == "__main__":
    unittest.main()
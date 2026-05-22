import json
import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
AGENT_ROOT = PROJECT_ROOT / "3d_agent"
if str(AGENT_ROOT) not in sys.path:
    sys.path.insert(0, str(AGENT_ROOT))

from integration.blender_execution_request import create_blender_execution_request
from integration.blender_runner import run_blender_execution_request, write_blender_preview_script
from integration.blender_script_safety import scan_blender_preview_script
from main import build_cli_result, parse_cli_args


SCENE_MANIFEST_PATH = PROJECT_ROOT / "examples" / "blender_scene_manifest.json"


class V07BlenderExecutionBridgeTests(unittest.TestCase):
    def test_parse_cli_args_accepts_v0_7_flags_without_breaking_legacy_unpacking(self) -> None:
        parsed = parse_cli_args(
            [
                "给胸甲加分件线",
                "--scene-manifest",
                str(SCENE_MANIFEST_PATH),
                "--blend-file",
                "examples/BlendFile/Gundam/GF-Gundam.blend",
                "--blender-executable",
                "D:/tools/blender-5.1/blender.exe",
                "--run-blender-preview",
            ]
        )
        legacy_values = tuple(parsed)

        self.assertEqual(len(legacy_values), 6)
        self.assertEqual(parsed.blend_file_path, "examples/BlendFile/Gundam/GF-Gundam.blend")
        self.assertEqual(parsed.blender_executable, "D:/tools/blender-5.1/blender.exe")
        self.assertTrue(parsed.run_blender_preview)
        self.assertTrue(parsed.include_preview_script_draft)

    def test_build_cli_result_can_create_execution_request_without_running_blender(self) -> None:
        result = build_cli_result(
            "给胸甲加一些锐利的分件线，适合 1/144 打印。",
            scene_manifest_path=str(SCENE_MANIFEST_PATH),
            blend_file_path="examples/BlendFile/Gundam/GF-Gundam.blend",
        )

        self.assertIn("blender_preview_script_safety_scan", result)
        self.assertEqual(result["blender_preview_script_safety_scan"]["safety_status"], "passed")
        self.assertIn("blender_execution_request", result)
        self.assertEqual(result["blender_execution_request"]["request_version"], "v0_7")
        self.assertEqual(result["blender_execution_request"]["execution_mode"], "preview_only")
        self.assertFalse(result["blender_execution_request"]["save_copy"])

    def test_safety_scan_blocks_destructive_script_tokens(self) -> None:
        scan = scan_blender_preview_script("import bpy\nbpy.ops.mesh.extrude_region_move()")

        self.assertEqual(scan["safety_status"], "blocked")
        self.assertIn("bpy.ops.mesh", scan["detected_forbidden_tokens"])

    def test_execution_request_records_preflight_checks(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            blend_file = Path(temp_dir) / "demo.blend"
            blend_file.write_bytes(b"placeholder")
            request = create_blender_execution_request(
                source_blend_file=str(blend_file),
                script_file="outputs/v0_7_preview_script.py",
                output_report_file="outputs/v0_7_preview_report.json",
                script_safety_scan={"safety_status": "passed"},
            )

        self.assertEqual(request["target_software"], "blender")
        self.assertIn({"check_id": "script_safety_scan", "status": "passed"}, request["preflight_checks"])
        self.assertIn({"check_id": "source_blend_file_exists", "status": "passed"}, request["preflight_checks"])

    def test_write_preview_script_creates_output_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            script_path = Path(write_blender_preview_script("print('preview')", temp_dir))

            self.assertTrue(script_path.exists())
            self.assertEqual(script_path.read_text(encoding="utf-8"), "print('preview')")

    def test_runner_reports_success_when_blender_writes_report(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            fake_blender = temp_path / "fake_blender.py"
            script_file = temp_path / "script.py"
            report_file = temp_path / "report.json"
            script_file.write_text("print('unused')", encoding="utf-8")
            report_file.write_text(
                json.dumps({"session_id": "preview_001", "target_part": "chest_armor", "generated_objects": ["a", "b"]}),
                encoding="utf-8",
            )
            fake_blender.write_text(
                "import sys\nprint('Blender 5.1.1')\nsys.exit(0)\n",
                encoding="utf-8",
            )
            request = {
                "execution_mode": "preview_only",
                "blender_executable": str(fake_blender),
                "source_blend_file": str(script_file),
                "script_file": str(fake_blender),
                "output_report_file": str(report_file),
            }

            report = run_blender_execution_request(request)

        self.assertEqual(report["execution_status"], "success")
        self.assertEqual(report["blender_version"], "Blender 5.1.1")
        self.assertEqual(report["generated_objects"], ["a", "b"])
        self.assertFalse(report["saved_original_file"])
        self.assertFalse(report["modified_bound_mesh"])


if __name__ == "__main__":
    unittest.main()
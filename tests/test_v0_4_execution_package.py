import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
AGENT_ROOT = PROJECT_ROOT / "3d_agent"
if str(AGENT_ROOT) not in sys.path:
    sys.path.insert(0, str(AGENT_ROOT))

from agent.blender_script_draft import create_blender_script_draft
from agent.execution_package import create_execution_package
from main import build_cli_result, parse_cli_args


class V04ExecutionPackageTests(unittest.TestCase):
    def _execution_blueprint_from_text(self, user_input: str) -> dict:
        result = build_cli_result(user_input)
        self.assertEqual(result["command_type"], "model_edit")
        return result["execution_blueprint"]

    def test_surface_detailing_package_outputs_contract_fields(self) -> None:
        blueprint = self._execution_blueprint_from_text(
            "给胸甲加一些锐利的分件线，适合 1/144 打印。"
        )
        package = create_execution_package(blueprint)

        self.assertEqual(
            set(package),
            {
                "package_version",
                "source_blueprint_ref",
                "target_part",
                "target_software",
                "execution_mode",
                "execution_tasks",
                "required_inputs",
                "blocked_by",
                "user_checkpoints",
                "rollback_plan",
                "output_artifacts",
                "execution_summary",
            },
        )
        self.assertEqual(package["package_version"], "v0_4")
        self.assertEqual(package["source_blueprint_ref"], "execution_blueprint")
        self.assertEqual(package["target_software"], "blender")
        self.assertEqual(package["execution_mode"], "annotation_package")
        self.assertIn("no_real_mesh", package["blocked_by"])
        self.assertTrue(package["execution_tasks"])
        self.assertTrue(package["rollback_plan"])

    def test_thruster_package_uses_placeholder_tasks(self) -> None:
        blueprint = self._execution_blueprint_from_text(
            "把背包的推进器做得更高机动一点，加喷口和机械细节。"
        )
        package = create_execution_package(blueprint)

        self.assertEqual(package["execution_mode"], "placeholder_package")
        self.assertTrue(
            any(task["task_type"] == "place_placeholder" for task in package["execution_tasks"])
        )
        self.assertIn("mounting_surface_reference", package["required_inputs"])
        self.assertIn("真实几何", package["execution_summary"])

    def test_hydraulic_package_requires_joint_review(self) -> None:
        blueprint = self._execution_blueprint_from_text("给两条腿加同样的管线和液压杆，密度中等。")
        package = create_execution_package(blueprint)

        self.assertIn("no_joint_range_data", package["blocked_by"])
        self.assertIn("joint_range_reference", package["required_inputs"])
        self.assertTrue(
            any("关节" in checkpoint for checkpoint in package["user_checkpoints"])
        )
        self.assertTrue(any(task["task_type"] == "manual_review" for task in package["execution_tasks"]))

    def test_damage_package_stays_annotation_only(self) -> None:
        blueprint = self._execution_blueprint_from_text("给盾牌加少量战损和旧化，不要太脏。")
        package = create_execution_package(blueprint)

        self.assertEqual(package["execution_mode"], "annotation_package")
        self.assertTrue(
            any(task["task_type"] in {"create_annotation", "mark_risk_zone"} for task in package["execution_tasks"])
        )
        self.assertIn("真实几何", package["execution_summary"])

    def test_sensor_package_uses_placeholder_and_orientation_checkpoint(self) -> None:
        blueprint = self._execution_blueprint_from_text("给头部加一个小型传感器，朝前。")
        package = create_execution_package(blueprint)

        self.assertEqual(package["execution_mode"], "placeholder_package")
        self.assertTrue(
            any(task["task_type"] == "place_placeholder" for task in package["execution_tasks"])
        )
        self.assertTrue(any("朝向" in checkpoint for checkpoint in package["user_checkpoints"]))

    def test_blender_script_draft_is_non_destructive_marker_script(self) -> None:
        blueprint = self._execution_blueprint_from_text(
            "给胸甲加一些锐利的分件线，适合 1/144 打印。"
        )
        package = create_execution_package(blueprint)
        script = create_blender_script_draft(package)

        self.assertIn("does not edit mesh geometry", script)
        self.assertIn("bpy.data.objects.new", script)
        self.assertNotIn("bpy.ops.object.modifier_apply", script)
        self.assertNotIn("bpy.ops.wm.save_as_mainfile", script)

    def test_cli_default_keeps_v0_3_shape(self) -> None:
        result = build_cli_result("给胸甲加一些锐利的分件线，适合 1/144 打印。")

        self.assertIn("execution_blueprint", result)
        self.assertNotIn("execution_package", result)
        self.assertNotIn("blender_script_draft", result)

    def test_cli_can_include_execution_package(self) -> None:
        result = build_cli_result(
            "给胸甲加一些锐利的分件线，适合 1/144 打印。",
            include_execution_package=True,
        )

        self.assertIn("execution_package", result)
        self.assertEqual(result["execution_package"]["package_version"], "v0_4")

    def test_cli_script_draft_implies_execution_package(self) -> None:
        result = build_cli_result(
            "给胸甲加一些锐利的分件线，适合 1/144 打印。",
            include_script_draft=True,
        )

        self.assertIn("execution_package", result)
        self.assertIn("blender_script_draft", result)

    def test_cli_flags_do_not_affect_context_queries(self) -> None:
        result = build_cli_result("现在有哪些部件？", include_execution_package=True, include_script_draft=True)

        self.assertEqual(result["command_type"], "inspect_context")
        self.assertNotIn("execution_blueprint", result)
        self.assertNotIn("execution_package", result)
        self.assertNotIn("blender_script_draft", result)

    def test_parse_cli_args_removes_v0_4_flags(self) -> None:
        (
            user_input,
            include_package,
            include_script,
            scene_manifest_path,
            include_geometry_preview,
            include_preview_script_draft,
        ) = parse_cli_args(
            ["给胸甲加刻线", "--execution-package", "--script-draft"]
        )

        self.assertEqual(user_input, "给胸甲加刻线")
        self.assertTrue(include_package)
        self.assertTrue(include_script)
        self.assertIsNone(scene_manifest_path)
        self.assertFalse(include_geometry_preview)
        self.assertFalse(include_preview_script_draft)


if __name__ == "__main__":
    unittest.main()
"""Entry point for the minimal 3D modeling agent."""

import json
import sys
from dataclasses import dataclass
from pathlib import Path

from cli import is_task_object_cli_args, run_task_object_cli
from agent.blender_authoring_script import create_blender_authoring_script
from agent.blender_preview_script_draft import create_blender_preview_script_draft
from agent.blender_script_draft import create_blender_script_draft
from agent.design_rule_engine import review_mecha_design_rules
from agent.execution_package import create_execution_package
from agent.geometry_preview import create_geometry_preview_plan
from agent.loop import run_agent
from agent.safe_preview_session import create_safe_preview_session
from integration.blender_execution_request import create_blender_execution_request
from integration.blender_runner import (
    run_blender_execution_request,
    write_blender_authoring_execution_script,
    write_blender_execution_script,
)
from integration.blender_script_safety import scan_blender_preview_script
from model.model_binding import create_model_binding_context, review_execution_package_with_binding
from model.scene_manifest import load_scene_manifest

EXECUTION_PACKAGE_FLAG = "--execution-package"
SCRIPT_DRAFT_FLAG = "--script-draft"
SCENE_MANIFEST_FLAG = "--scene-manifest"
GEOMETRY_PREVIEW_FLAG = "--geometry-preview"
PREVIEW_SCRIPT_DRAFT_FLAG = "--preview-script-draft"
BLEND_FILE_FLAG = "--blend-file"
BLENDER_EXECUTABLE_FLAG = "--blender-executable"
RUN_BLENDER_PREVIEW_FLAG = "--run-blender-preview"
DESIGN_RULE_REVIEW_FLAG = "--design-rule-review"
SAVE_PREVIEW_COPY_FLAG = "--save-preview-copy"
OUTPUT_BLEND_COPY_FLAG = "--output-blend-copy"
AUTHORING_CURVE_GUIDE_FLAG = "--authoring-curve-guide"
RUN_AUTHORING_FLAG = "--run-authoring"


def build_task_object_cli_result(args: list[str], **dependencies) -> dict:
    """Run the TaskObject main-chain CLI path from main.py."""
    return run_task_object_cli(args, **dependencies)


@dataclass(frozen=True)
class CliArgs:
    user_input: str
    include_execution_package: bool
    include_script_draft: bool
    scene_manifest_path: str | None
    include_geometry_preview: bool
    include_preview_script_draft: bool
    blend_file_path: str | None = None
    blender_executable: str = "blender"
    run_blender_preview: bool = False
    include_design_rule_review: bool = False
    save_preview_copy: bool = False
    output_blend_copy: str | None = None
    include_authoring_curve_guide: bool = False
    run_authoring: bool = False

    def __iter__(self):
        yield self.user_input
        yield self.include_execution_package
        yield self.include_script_draft
        yield self.scene_manifest_path
        yield self.include_geometry_preview
        yield self.include_preview_script_draft


def build_cli_result(
    user_input: str,
    include_execution_package: bool = False,
    include_script_draft: bool = False,
    scene_manifest_path: str | None = None,
    include_geometry_preview: bool = False,
    include_preview_script_draft: bool = False,
    blend_file_path: str | None = None,
    blender_executable: str = "blender",
    run_blender_preview: bool = False,
    include_design_rule_review: bool = False,
    save_preview_copy: bool = False,
    output_blend_copy: str | None = None,
    include_authoring_curve_guide: bool = False,
    run_authoring: bool = False,
) -> dict:
    """Build the CLI JSON result without printing it."""
    result = run_agent(user_input)
    if result.get("command_type") != "model_edit" or "execution_blueprint" not in result:
        return result

    if include_geometry_preview or include_preview_script_draft or blend_file_path or run_blender_preview or include_authoring_curve_guide:
        if not scene_manifest_path:
            raise ValueError("--geometry-preview requires --scene-manifest <path>.")
    if (run_blender_preview or run_authoring) and not blend_file_path:
        raise ValueError("--run-blender-preview requires --blend-file <path>.")
    if save_preview_copy and not blend_file_path:
        raise ValueError("--save-preview-copy requires --blend-file <path>.")
    if save_preview_copy and output_blend_copy and blend_file_path:
        if Path(output_blend_copy).resolve() == Path(blend_file_path).resolve():
            raise ValueError("--output-blend-copy must not overwrite --blend-file.")

    needs_design_rule_review = (
        include_design_rule_review
        or include_geometry_preview
        or include_preview_script_draft
        or bool(blend_file_path)
        or include_authoring_curve_guide
    )

    if include_execution_package or include_script_draft or scene_manifest_path or needs_design_rule_review:
        result["execution_package"] = create_execution_package(result["execution_blueprint"])
    if needs_design_rule_review:
        result["design_rule_review"] = review_mecha_design_rules(
            result,
            result["execution_package"],
            user_input,
        )
    if include_script_draft:
        result["blender_script_draft"] = create_blender_script_draft(result["execution_package"])
    if scene_manifest_path:
        scene_manifest = load_scene_manifest(scene_manifest_path)
        result["model_binding_context"] = create_model_binding_context(
            scene_manifest,
            result["target_part"],
            result["execution_package"],
            source_manifest_ref=scene_manifest_path,
        )
        result["execution_package_review"] = review_execution_package_with_binding(
            result["execution_package"],
            result["model_binding_context"],
        )
    if include_geometry_preview or include_preview_script_draft or blend_file_path or include_authoring_curve_guide:
        result["geometry_preview_plan"] = create_geometry_preview_plan(
            result["execution_package"],
            result["model_binding_context"],
            result["execution_package_review"],
        )
        result["safe_preview_session"] = create_safe_preview_session(result["geometry_preview_plan"])
    if include_preview_script_draft:
        result["blender_preview_script_draft"] = create_blender_preview_script_draft(
            result["geometry_preview_plan"],
            result["safe_preview_session"],
        )
    if blend_file_path:
        if "blender_preview_script_draft" not in result:
            result["blender_preview_script_draft"] = create_blender_preview_script_draft(
                result["geometry_preview_plan"],
                result["safe_preview_session"],
            )
        output_report_file = "outputs/v0_7_preview_report.json"
        output_copy_path = output_blend_copy
        if save_preview_copy and not output_copy_path:
            output_copy_path = str(Path("outputs") / f"{Path(blend_file_path).stem}.preview.blend")
        script_file = write_blender_execution_script(
            result["blender_preview_script_draft"],
            output_report_file,
            save_copy=save_preview_copy,
            output_blend_copy=output_copy_path,
        )
        result["blender_preview_script_safety_scan"] = scan_blender_preview_script(
            Path(script_file).read_text(encoding="utf-8"),
            allow_save_copy=save_preview_copy,
        )
        result["blender_execution_request"] = create_blender_execution_request(
            source_blend_file=blend_file_path,
            script_file=script_file,
            output_report_file=output_report_file,
            blender_executable=blender_executable,
            save_copy=save_preview_copy,
            output_blend_copy=output_copy_path,
            safe_preview_session=result["safe_preview_session"],
            script_safety_scan=result["blender_preview_script_safety_scan"],
        )
    if include_authoring_curve_guide:
        result["blender_authoring_script"] = create_blender_authoring_script(
            result["geometry_preview_plan"],
            result["safe_preview_session"],
        )
        authoring_report_file = "outputs/v0_9a_authoring_report.json"
        authoring_copy_path = output_blend_copy
        if save_preview_copy and not authoring_copy_path:
            authoring_copy_path = str(Path("outputs") / f"{Path(blend_file_path).stem}.authoring.blend")
        authoring_script_file = write_blender_authoring_execution_script(
            result["blender_authoring_script"],
            authoring_report_file,
            save_copy=save_preview_copy,
            output_blend_copy=authoring_copy_path,
        )
        result["blender_authoring_script_safety_scan"] = scan_blender_preview_script(
            Path(authoring_script_file).read_text(encoding="utf-8"),
            allow_save_copy=save_preview_copy,
        )
        result["blender_authoring_request"] = create_blender_execution_request(
            source_blend_file=blend_file_path,
            script_file=authoring_script_file,
            output_report_file=authoring_report_file,
            blender_executable=blender_executable,
            save_copy=save_preview_copy,
            output_blend_copy=authoring_copy_path,
            safe_preview_session=result["safe_preview_session"],
            script_safety_scan=result["blender_authoring_script_safety_scan"],
        )
    if run_blender_preview:
        safety_scan = result["blender_preview_script_safety_scan"]
        if safety_scan.get("safety_status") != "passed":
            raise ValueError("Blender preview script safety scan failed.")
        result["blender_execution_report"] = run_blender_execution_request(result["blender_execution_request"])
    if run_authoring:
        safety_scan = result["blender_authoring_script_safety_scan"]
        if safety_scan.get("safety_status") != "passed":
            raise ValueError("Blender authoring script safety scan failed.")
        result["blender_authoring_report"] = run_blender_execution_request(result["blender_authoring_request"])
    return result


def parse_cli_args(args: list[str]) -> CliArgs:
    """Parse the small CLI surface without treating flags as user text."""
    include_execution_package = False
    include_script_draft = False
    include_geometry_preview = False
    include_preview_script_draft = False
    include_design_rule_review = False
    save_preview_copy = False
    include_authoring_curve_guide = False
    run_authoring = False
    scene_manifest_path = None
    blend_file_path = None
    output_blend_copy = None
    blender_executable = "blender"
    run_blender_preview = False
    user_input_parts = []
    index = 0
    while index < len(args):
        arg = args[index]
        if arg == EXECUTION_PACKAGE_FLAG:
            include_execution_package = True
        elif arg == SCRIPT_DRAFT_FLAG:
            include_script_draft = True
        elif arg == GEOMETRY_PREVIEW_FLAG:
            include_geometry_preview = True
        elif arg == PREVIEW_SCRIPT_DRAFT_FLAG:
            include_preview_script_draft = True
            include_geometry_preview = True
        elif arg == BLEND_FILE_FLAG:
            next_index = index + 1
            if next_index >= len(args) or args[next_index].startswith("--"):
                raise ValueError("--blend-file requires a path argument.")
            blend_file_path = args[next_index]
            include_preview_script_draft = True
            include_geometry_preview = True
            index = next_index
        elif arg == BLENDER_EXECUTABLE_FLAG:
            next_index = index + 1
            if next_index >= len(args) or args[next_index].startswith("--"):
                raise ValueError("--blender-executable requires a path argument.")
            blender_executable = args[next_index]
            index = next_index
        elif arg == RUN_BLENDER_PREVIEW_FLAG:
            run_blender_preview = True
            include_preview_script_draft = True
            include_geometry_preview = True
            include_design_rule_review = True
        elif arg == DESIGN_RULE_REVIEW_FLAG:
            include_design_rule_review = True
        elif arg == SAVE_PREVIEW_COPY_FLAG:
            save_preview_copy = True
        elif arg == OUTPUT_BLEND_COPY_FLAG:
            next_index = index + 1
            if next_index >= len(args) or args[next_index].startswith("--"):
                raise ValueError("--output-blend-copy requires a path argument.")
            output_blend_copy = args[next_index]
            save_preview_copy = True
            index = next_index
        elif arg == AUTHORING_CURVE_GUIDE_FLAG:
            include_authoring_curve_guide = True
            include_preview_script_draft = True
            include_geometry_preview = True
            include_design_rule_review = True
        elif arg == RUN_AUTHORING_FLAG:
            run_authoring = True
            include_authoring_curve_guide = True
            include_preview_script_draft = True
            include_geometry_preview = True
            include_design_rule_review = True
        elif arg == SCENE_MANIFEST_FLAG:
            next_index = index + 1
            if next_index >= len(args) or args[next_index].startswith("--"):
                raise ValueError("--scene-manifest requires a path argument.")
            scene_manifest_path = args[next_index]
            index = next_index
        else:
            user_input_parts.append(arg)
        index += 1
    return CliArgs(
        user_input=" ".join(user_input_parts).strip(),
        include_execution_package=include_execution_package,
        include_script_draft=include_script_draft,
        scene_manifest_path=scene_manifest_path,
        include_geometry_preview=include_geometry_preview,
        include_preview_script_draft=include_preview_script_draft,
        blend_file_path=blend_file_path,
        blender_executable=blender_executable,
        run_blender_preview=run_blender_preview,
        include_design_rule_review=include_design_rule_review,
        save_preview_copy=save_preview_copy,
        output_blend_copy=output_blend_copy,
        include_authoring_curve_guide=include_authoring_curve_guide,
        run_authoring=run_authoring,
    )


if __name__ == "__main__":
    if is_task_object_cli_args(sys.argv[1:]):
        try:
            task_object_result = build_task_object_cli_result(sys.argv[1:])
        except Exception as error:
            raise SystemExit(str(error)) from error
        print(json.dumps(task_object_result, ensure_ascii=False, indent=2))
        raise SystemExit(0)

    try:
        cli_args = parse_cli_args(sys.argv[1:])
    except ValueError as error:
        raise SystemExit(str(error)) from error
    user_input = cli_args.user_input
    if not user_input:
        user_input = input("请输入建模指令: ").strip()

    if not user_input:
        raise SystemExit("No user instruction provided.")

    try:
        result = build_cli_result(
            user_input,
            cli_args.include_execution_package,
            cli_args.include_script_draft,
            cli_args.scene_manifest_path,
            cli_args.include_geometry_preview,
            cli_args.include_preview_script_draft,
            cli_args.blend_file_path,
            cli_args.blender_executable,
            cli_args.run_blender_preview,
            cli_args.include_design_rule_review,
            cli_args.save_preview_copy,
            cli_args.output_blend_copy,
            cli_args.include_authoring_curve_guide,
            cli_args.run_authoring,
        )
    except ValueError as error:
        raise SystemExit(str(error)) from error
    user_message = result.get("user_message")
    designer_brief = result.get("designer_brief")

    if user_message:
        print(user_message, file=sys.stderr)
    if designer_brief:
        print(designer_brief, file=sys.stderr)

    print(json.dumps(result, ensure_ascii=False, indent=2))

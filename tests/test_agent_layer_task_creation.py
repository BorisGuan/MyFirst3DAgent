import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
AGENT_ROOT = PROJECT_ROOT / "3d_agent"
if str(AGENT_ROOT) not in sys.path:
    sys.path.insert(0, str(AGENT_ROOT))

from agent_layer import AgentLayerTaskCreationError, create_draft_task
from agent_layer.legacy_intent_adapter import create_task_draft_from_legacy_intent
from task_object import TaskState


class FakeContextManager:
    def __init__(self) -> None:
        self.classifier_summary_requested = False
        self.planner_summary_requested = False

    def summary_for_classifier(self) -> dict:
        self.classifier_summary_requested = True
        return {"model": {"available_targets": ["chest_armor"]}}

    def summary_for_planner(self) -> dict:
        self.planner_summary_requested = True
        return {"model": {"parts": [{"name": "chest_armor"}]}}


def fake_model_edit_classifier(user_input: str, context_summary: dict) -> dict[str, str]:
    return {
        "command_type": "model_edit",
        "confidence": "high",
        "reasoning": "test classifier",
    }


def fake_inspect_classifier(user_input: str, context_summary: dict) -> dict[str, str]:
    return {
        "command_type": "inspect_context",
        "confidence": "high",
        "reasoning": "test classifier",
    }


def fake_intent_parser(user_input: str, model_context: dict) -> dict:
    return {
        "target_part": "chest_armor",
        "operation": "add_armor_layers",
        "detail_type": "armor_layers",
        "style": "sharp_mechanical",
        "density": "low",
        "symmetry": "single_target",
        "scale": "1/144",
        "placement_zones": ["upper_chest_plate"],
        "constraints": ["preserve silhouette"],
    }


class AgentLayerTaskCreationTests(unittest.TestCase):
    def test_creates_draft_task_object_from_natural_language(self) -> None:
        context_manager = FakeContextManager()

        task = create_draft_task(
            " 给胸甲做机械风格边缘软化 ",
            context_manager=context_manager,
            classifier=fake_model_edit_classifier,
            intent_parser=fake_intent_parser,
        )

        self.assertEqual(task.state, TaskState.DRAFT)
        self.assertEqual(task.source.user_input, "给胸甲做机械风格边缘软化")
        self.assertEqual(task.source.channel, "agent_layer")
        self.assertEqual(task.source.metadata["command_type"], "model_edit")
        self.assertEqual(task.task_type, "surface_detail_enhancement")
        self.assertEqual(task.target.semantic_part, "chest_armor")
        self.assertEqual(task.intent.desired_effect, "armor_layers")
        self.assertEqual(task.intent.action, "add_armor_layers")
        self.assertEqual(task.intent.style, "sharp_mechanical")
        self.assertEqual(task.intent.density, "low")
        self.assertEqual(task.intent.scale, "1/144")
        self.assertEqual(task.constraints.notes, ["preserve silhouette"])
        self.assertTrue(context_manager.classifier_summary_requested)
        self.assertTrue(context_manager.planner_summary_requested)

    def test_draft_task_contains_no_execution_decisions_or_results(self) -> None:
        task = create_draft_task(
            "给胸甲加细节",
            context_manager=FakeContextManager(),
            classifier=fake_model_edit_classifier,
            intent_parser=fake_intent_parser,
        )

        self.assertIsNone(task.target.bound_object)
        self.assertEqual(task.target.binding_candidates, [])
        self.assertIsNone(task.planning.selected_operation)
        self.assertEqual(task.planning.parameters, {})
        self.assertIsNone(task.runtime.source_blend_file)
        self.assertIsNone(task.runtime.output_blend_copy)
        self.assertIsNone(task.runtime.report_file)
        self.assertIsNone(task.result.success)
        self.assertEqual(task.result.summary, "")

    def test_rejects_non_model_edit_command_without_parsing_intent(self) -> None:
        parser_called = False

        def parser(user_input: str, model_context: dict) -> dict:
            nonlocal parser_called
            parser_called = True
            return {}

        with self.assertRaises(AgentLayerTaskCreationError):
            create_draft_task(
                "列出当前部件",
                context_manager=FakeContextManager(),
                classifier=fake_inspect_classifier,
                intent_parser=parser,
            )

        self.assertFalse(parser_called)

    def test_rejects_empty_user_input(self) -> None:
        with self.assertRaises(AgentLayerTaskCreationError):
            create_draft_task("  ", context_manager=FakeContextManager())

    def test_legacy_adapter_only_writes_agent_owned_fields(self) -> None:
        task = create_task_draft_from_legacy_intent(
            "给胸甲加装甲层次",
            {"command_type": "model_edit", "confidence": "medium", "reasoning": "ok"},
            fake_intent_parser("给胸甲加装甲层次", {}),
        )

        self.assertEqual(task.state, TaskState.DRAFT)
        self.assertEqual(task.target.semantic_part, "chest_armor")
        self.assertIsNone(task.target.bound_object)
        self.assertIsNone(task.planning.selected_operation)
        self.assertEqual(task.runtime.output_blend_copy, None)

    def test_agent_layer_has_no_execution_or_blender_dependency(self) -> None:
        agent_service_source = (AGENT_ROOT / "agent_layer" / "agent_service.py").read_text(encoding="utf-8")
        adapter_source = (AGENT_ROOT / "agent_layer" / "legacy_intent_adapter.py").read_text(encoding="utf-8")
        combined_source = agent_service_source + adapter_source

        self.assertNotIn("import bpy", combined_source)
        self.assertNotIn("bpy.", combined_source)
        self.assertNotIn("from blender_ops", combined_source)
        self.assertNotIn("from runtime", combined_source)
        self.assertNotIn("operation_planner", combined_source)
        self.assertNotIn("modification_execution", combined_source)
        self.assertNotIn("create_plan", combined_source)
        self.assertNotIn("execution_package", combined_source)


if __name__ == "__main__":
    unittest.main()
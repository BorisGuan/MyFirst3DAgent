"""Agent Layer service for creating TaskObject drafts from user input."""

from __future__ import annotations

from typing import Any, Callable

from agent.command_classifier import classify_command
from agent.intent_parser import parse_intent
from agent_layer.legacy_intent_adapter import create_task_draft_from_legacy_intent
from model.context_manager import ContextManager
from task_object import TaskObject


Classifier = Callable[[str, dict[str, Any]], dict[str, str]]
IntentParser = Callable[[str, dict[str, Any]], dict[str, Any]]


class AgentLayerTaskCreationError(ValueError):
    """Raised when Agent Layer cannot create a TaskObject draft."""


def create_draft_task(
    user_input: str,
    context_manager: ContextManager | None = None,
    classifier: Classifier = classify_command,
    intent_parser: IntentParser = parse_intent,
) -> TaskObject:
    """Create TaskObject(state=draft) from natural-language user input."""
    normalized_input = user_input.strip()
    if not normalized_input:
        raise AgentLayerTaskCreationError("user_input is required to create a draft TaskObject.")

    context = context_manager or ContextManager()
    command = classifier(normalized_input, context.summary_for_classifier())
    if command.get("command_type") != "model_edit":
        raise AgentLayerTaskCreationError(
            f"Agent Layer can only create model_edit TaskObject drafts, got {command.get('command_type')!r}."
        )

    legacy_intent = intent_parser(normalized_input, context.summary_for_planner())
    return create_task_draft_from_legacy_intent(normalized_input, command, legacy_intent)
"""Main Agent Loop.

This module wires the minimal workflow together:
1. Load abstract model context.
2. Classify the user command.
3. Route the command to the matching lightweight workflow.
"""

from typing import Any

from agent.command_classifier import classify_command
from agent.execution_blueprint import create_execution_blueprint
from agent.formatter import format_blueprint
from agent.intent_parser import parse_intent
from agent.planner import create_plan
from agent.risk_checker import evaluate_risks
from model.context_manager import ContextManager


def run_agent(user_input: str) -> dict[str, Any]:
    """Run the minimal command understanding workflow."""
    context_manager = ContextManager()
    command = classify_command(user_input, context_manager.summary_for_classifier())
    command_type = command["command_type"]

    if command_type == "model_edit":
        result = _run_model_edit(user_input, context_manager, command)
    elif command_type == "inspect_context":
        result = _run_inspect_context(user_input, context_manager, command)
    elif command_type == "explain_capability":
        result = _run_explain_capability(command)
    else:
        result = _run_unknown(command)

    context_manager.record_interaction(user_input, command, result)
    return result


def _run_model_edit(
    user_input: str,
    context_manager: ContextManager,
    command: dict[str, str],
) -> dict[str, Any]:
    planner_context = context_manager.summary_for_planner()
    intent = parse_intent(user_input, planner_context)
    plan = create_plan(intent, context_manager.raw_model_context())
    plan = evaluate_risks(plan, context_manager.raw_model_context())
    plan = format_blueprint(plan)
    plan["execution_blueprint"] = create_execution_blueprint(plan, context_manager.raw_model_context())
    return {
        "command_type": "model_edit",
        "confidence": command["confidence"],
        **plan,
    }


def _run_inspect_context(
    user_input: str,
    context_manager: ContextManager,
    command: dict[str, str],
) -> dict[str, Any]:
    query_result = context_manager.answer_context_query(user_input)
    return {
        "command_type": "inspect_context",
        "status": "ok",
        "confidence": command["confidence"],
        **query_result,
        "reasoning": command["reasoning"],
    }


def _run_explain_capability(command: dict[str, str]) -> dict[str, Any]:
    context_manager = ContextManager()
    return {
        "command_type": "explain_capability",
        "status": "ok",
        "confidence": command["confidence"],
        "capabilities": context_manager.capabilities.get("capabilities", []),
        "limitations": context_manager.capabilities.get("limitations", []),
        "reasoning": command["reasoning"],
    }


def _run_unknown(command: dict[str, str]) -> dict[str, Any]:
    return {
        "command_type": "unknown",
        "status": "unsupported",
        "confidence": command["confidence"],
        "reasoning": command["reasoning"],
        "user_message": "当前 Agent 只支持模型上下文查询和抽象建模修改计划。",
    }

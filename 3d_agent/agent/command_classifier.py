"""First-pass user command classification.

This layer decides which agent workflow should handle a request before any
model-edit plan is generated.
"""

import json
from pathlib import Path
from typing import Any

import config
from agent.intent_parser import (
    _extract_chat_completion_text,
    _post_json,
    _strip_json_markdown,
)


PROMPT_PATH = Path(__file__).resolve().parents[1] / "prompts" / "command_classifier_prompt.txt"
ALLOWED_COMMAND_TYPES = {"model_edit", "inspect_context", "explain_capability", "unknown"}
ALLOWED_CONFIDENCES = {"low", "medium", "high"}


def classify_command(user_input: str, context_summary: dict[str, Any]) -> dict[str, str]:
    """Classify a user request into a high-level command type."""
    if config.AI_PROVIDER == "copilot_api":
        command = _classify_with_copilot_api(user_input, context_summary)
    elif config.AI_PROVIDER == "openai":
        command = _classify_with_openai(user_input, context_summary)
    elif config.AI_PROVIDER == "mock":
        command = _classify_with_mock(user_input)
    else:
        raise ValueError(f"Unsupported AI_PROVIDER: {config.AI_PROVIDER}")

    return _validate_command(command)


def _classify_with_copilot_api(
    user_input: str,
    context_summary: dict[str, Any],
) -> dict[str, Any]:
    prompt = _build_prompt(user_input, context_summary)
    payload = {
        "model": config.COPILOT_API_MODEL,
        "temperature": 0,
        "response_format": {"type": "json_object"},
        "messages": [{"role": "user", "content": prompt}],
    }
    response = _post_json(
        f"{config.COPILOT_API_BASE_URL}/v1/chat/completions",
        payload,
        {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {config.COPILOT_API_AUTH_TOKEN}",
        },
    )
    content = _extract_chat_completion_text(response)
    return json.loads(_strip_json_markdown(content))


def _classify_with_openai(user_input: str, context_summary: dict[str, Any]) -> dict[str, Any]:
    if not config.OPENAI_API_KEY:
        raise RuntimeError("AI_PROVIDER=openai requires OPENAI_API_KEY to be set.")

    try:
        from openai import OpenAI
    except ImportError as exc:
        raise RuntimeError("Install the openai package to enable OpenAI mode.") from exc

    prompt = _build_prompt(user_input, context_summary)
    client = OpenAI(api_key=config.OPENAI_API_KEY)
    response = client.chat.completions.create(
        model=config.OPENAI_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        response_format={"type": "json_object"},
    )

    content = response.choices[0].message.content
    if not content:
        raise ValueError("LLM returned empty command classification content.")
    return json.loads(content)


def _build_prompt(user_input: str, context_summary: dict[str, Any]) -> str:
    template = PROMPT_PATH.read_text(encoding="utf-8")
    return template.format(
        context_summary=json.dumps(
            context_summary,
            ensure_ascii=False,
            indent=2,
        ),
        user_input=user_input,
    )


def _classify_with_mock(user_input: str) -> dict[str, str]:
    lowered_input = user_input.lower()
    if any(keyword in lowered_input for keyword in ["有哪些", "是否有", "有没有", "列出", "parts", "accessories"]):
        return {
            "command_type": "inspect_context",
            "confidence": "high",
            "reasoning": "用户在询问当前模型上下文或可用部件",
        }
    if any(keyword in lowered_input for keyword in ["你能", "能做什么", "支持", "能力", "capability"]):
        return {
            "command_type": "explain_capability",
            "confidence": "high",
            "reasoning": "用户在询问 Agent 能力边界",
        }
    if any(keyword in lowered_input for keyword in ["渲染", "blender", "导出", "mesh", "布尔", "执行"]):
        return {
            "command_type": "unknown",
            "confidence": "medium",
            "reasoning": "用户请求超出当前抽象规划能力",
        }
    return {
        "command_type": "model_edit",
        "confidence": "medium",
        "reasoning": "用户可能在请求模型细节修改计划",
    }


def _validate_command(command: dict[str, Any]) -> dict[str, str]:
    command_type = command.get("command_type")
    confidence = command.get("confidence")
    reasoning = command.get("reasoning", "")

    if command_type not in ALLOWED_COMMAND_TYPES:
        return {
            "command_type": "unknown",
            "confidence": "low",
            "reasoning": f"无法识别的 command_type: {command_type}",
        }

    if confidence not in ALLOWED_CONFIDENCES:
        confidence = "low"

    if not isinstance(reasoning, str) or not reasoning:
        reasoning = "已完成指令分类"

    return {
        "command_type": command_type,
        "confidence": confidence,
        "reasoning": reasoning,
    }

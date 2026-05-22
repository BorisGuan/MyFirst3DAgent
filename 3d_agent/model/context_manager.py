"""Layered context manager for the minimal 3D agent.

The manager keeps long-lived domain knowledge, current model context, session
state, and prompt-sized summaries separate. It does not inspect real 3D data.
"""

import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from model.model_context import PROJECT_ROOT, get_model_context


DEFAULT_CAPABILITIES_PATH = PROJECT_ROOT / "context" / "capabilities.json"
DEFAULT_TAXONOMY_PATH = PROJECT_ROOT / "context" / "design_taxonomy.json"
DEFAULT_DESIGN_BRIEF_PATH = PROJECT_ROOT / "session" / "design_brief.json"
DEFAULT_WORKING_PLAN_PATH = PROJECT_ROOT / "session" / "working_plan.json"
DEFAULT_INTERACTION_SUMMARY_PATH = PROJECT_ROOT / "session" / "interaction_summary.json"
MAX_RECORDED_INTERACTIONS = 20


class ContextManager:
    """Owns layered context loading, indexing, and query helpers."""

    def __init__(
        self,
        model_context: dict[str, Any] | None = None,
        capabilities: dict[str, Any] | None = None,
        taxonomy: dict[str, Any] | None = None,
        design_brief: dict[str, Any] | None = None,
        working_plan: dict[str, Any] | None = None,
        interaction_summary: dict[str, Any] | None = None,
    ) -> None:
        self.model_context = model_context or get_model_context()
        self.capabilities = capabilities or _load_json(DEFAULT_CAPABILITIES_PATH)
        self.taxonomy = taxonomy or _load_json(DEFAULT_TAXONOMY_PATH)
        self.design_brief = design_brief or _load_json(DEFAULT_DESIGN_BRIEF_PATH)
        self.working_plan = working_plan or _load_json(DEFAULT_WORKING_PLAN_PATH)
        self.interaction_summary = interaction_summary or _load_json(
            DEFAULT_INTERACTION_SUMMARY_PATH
        )

        self.model = self.model_context["model"]
        self.parts = self.model["parts"]
        self.by_name = {part["name"]: part for part in self.parts}
        self.by_alias = self._build_alias_index()
        self.by_category = self._build_category_index()
        self.by_detail_level = self._build_detail_level_index()

    def raw_model_context(self) -> dict[str, Any]:
        """Return the full merged model context for strict validation."""
        return self.model_context

    def valid_target_names(self) -> set[str]:
        """Return every legal target_part name."""
        return set(self.by_name)

    def summary_for_classifier(self) -> dict[str, Any]:
        """Return a compact context slice for command classification."""
        return {
            "capabilities": {
                "supported_command_types": self.capabilities.get("supported_command_types", []),
                "limitations": self.capabilities.get("limitations", []),
            },
            "model": self._model_summary(include_aliases=True),
            "session": self._session_summary(),
            "recent_interactions": self.interaction_summary.get("recent_interactions", [])[-5:],
        }

    def summary_for_planner(self) -> dict[str, Any]:
        """Return the context slice needed to produce model_edit plans."""
        return {
            "capabilities": {
                "purpose": self.capabilities.get("purpose", ""),
                "limitations": self.capabilities.get("limitations", []),
            },
            "design_taxonomy": self.taxonomy,
            "model": self.model,
            "session": {
                "design_brief": self.design_brief,
                "working_plan": self.working_plan,
                "recent_interactions": self.interaction_summary.get(
                    "recent_interactions", []
                )[-5:],
            },
        }

    def context_stats(self) -> dict[str, Any]:
        """Return deterministic statistics for the layered model context."""
        return {
            "part_count": len(self.parts),
            "category_counts": {
                category: len(parts)
                for category, parts in sorted(self.by_category.items())
            },
            "detail_level_counts": {
                detail_level: len(parts)
                for detail_level, parts in sorted(self.by_detail_level.items())
            },
            "catalog_part_count": sum(
                1 for part in self.parts if part.get("is_catalog_part")
            ),
            "scanned_part_count": sum(1 for part in self.parts if part.get("is_scanned")),
            "special_part_count": sum(1 for part in self.parts if part.get("is_special")),
            "context_files": self.model.get("context_files", []),
        }

    def summary_for_user(self) -> dict[str, Any]:
        """Return a compact user-facing summary of current context state."""
        stats = self.context_stats()
        return {
            "model_name": self.model["name"],
            "stats": stats,
            "categories": sorted(self.by_category),
            "highlights": self._build_highlights(stats),
            "session": self._session_summary(),
        }

    def answer_context_query(self, user_input: str) -> dict[str, Any]:
        """Answer simple model-context questions with deterministic lookup."""
        if self._asks_for_context_summary(user_input):
            return {
                "query_type": "context_summary",
                **self.summary_for_user(),
                "user_message": "已生成当前分层上下文摘要。",
            }

        matched_part = self.find_part(user_input)
        if matched_part:
            return {
                "query_type": "part_lookup",
                "matched_part": self._public_part(matched_part),
                "user_message": f"当前上下文中包含 {matched_part.get('display_name') or matched_part['name']}。",
            }

        lowered_input = user_input.lower()
        if any(keyword in lowered_input for keyword in ["低", "low", "细节少"]):
            parts = [self._public_part(part) for part in self.by_detail_level.get("low", [])]
            return {
                "query_type": "low_detail_parts",
                "parts": parts,
                "user_message": f"当前有 {len(parts)} 个低细节部件。",
            }

        if any(keyword in lowered_input for keyword in ["特殊", "special", "自定义"]):
            parts = [self._public_part(part) for part in self.parts if part.get("is_special")]
            return {
                "query_type": "special_parts",
                "parts": parts,
                "user_message": f"当前有 {len(parts)} 个特殊部件。",
            }

        category = self._detect_category(user_input)
        if category:
            parts = [self._public_part(part) for part in self.by_category.get(category, [])]
            return {
                "query_type": "category_parts",
                "category": category,
                "parts": parts,
                "user_message": f"当前 {category} 分类下有 {len(parts)} 个目标。",
            }

        return {
            "query_type": "list_all_parts",
            "model_name": self.model["name"],
            "context_files": self.model.get("context_files", []),
            "part_count": len(self.parts),
            "parts": [self._public_part(part) for part in self.parts],
            "user_message": f"当前模型上下文包含 {len(self.parts)} 个可用目标。",
        }

    def find_part(self, text: str) -> dict[str, Any] | None:
        """Find a model part by canonical name, display name, or alias."""
        lowered_text = text.lower()
        for alias, part in self.by_alias.items():
            if alias.lower() in lowered_text:
                return part
        return None

    def record_interaction(
        self,
        user_input: str,
        command: dict[str, str],
        result: dict[str, Any],
    ) -> None:
        """Persist a compact summary of the latest agent turn."""
        summary = _load_json(DEFAULT_INTERACTION_SUMMARY_PATH)
        interactions = summary.get("recent_interactions", [])
        interactions.append(
            {
                "user_input": user_input,
                "command_type": command.get("command_type", "unknown"),
                "confidence": command.get("confidence", "low"),
                "result_summary": self._summarize_result(result),
            }
        )

        summary["turn_count"] = int(summary.get("turn_count", 0)) + 1
        summary["recent_interactions"] = interactions[-MAX_RECORDED_INTERACTIONS:]
        _write_json(DEFAULT_INTERACTION_SUMMARY_PATH, summary)

    def _model_summary(self, include_aliases: bool) -> dict[str, Any]:
        targets = []
        for part in self.parts:
            target = {
                "name": part["name"],
                "display_name": part.get("display_name", ""),
                "category": part.get("category", "part"),
                "detail_level": part.get("detail_level", "low"),
                "is_catalog_part": part.get("is_catalog_part", False),
                "is_scanned": part.get("is_scanned", False),
                "is_special": part.get("is_special", False),
            }
            if include_aliases:
                target["aliases"] = part.get("aliases", [])
            targets.append(target)

        return {
            "name": self.model["name"],
            "context_files": self.model.get("context_files", []),
            "part_count": len(self.parts),
            "categories": sorted(self.by_category),
            "available_targets": targets,
        }

    def _session_summary(self) -> dict[str, Any]:
        return {
            "project_goal": self.design_brief.get("project_goal", ""),
            "style": self.design_brief.get("style", []),
            "constraints": self.design_brief.get("constraints", []),
            "focus_parts": self.design_brief.get("focus_parts", []),
            "current_phase": self.working_plan.get("current_phase", ""),
        }

    def _build_highlights(self, stats: dict[str, Any]) -> list[str]:
        highlights = []
        if stats["scanned_part_count"] == 0:
            highlights.append("当前上下文只有基础/扩展部件库，还没有扫描模型结果。")
        else:
            highlights.append(f"当前已包含 {stats['scanned_part_count']} 个扫描到的部件。")

        if stats["special_part_count"] == 0:
            highlights.append("当前没有特殊机型部件。")
        else:
            highlights.append(f"当前有 {stats['special_part_count']} 个特殊机型部件。")

        low_detail_count = stats["detail_level_counts"].get("low", 0)
        if low_detail_count:
            highlights.append(f"当前有 {low_detail_count} 个低细节目标，适合优先做复杂化规划。")

        project_goal = self.design_brief.get("project_goal", "")
        if project_goal:
            highlights.append(f"当前设计目标是：{project_goal}")

        return highlights

    def _asks_for_context_summary(self, user_input: str) -> bool:
        lowered_input = user_input.lower()
        return any(
            keyword in lowered_input
            for keyword in ["上下文摘要", "上下文情况", "总结", "概览", "summary", "overview"]
        )

    def _summarize_result(self, result: dict[str, Any]) -> dict[str, Any]:
        command_type = result.get("command_type", "unknown")
        if command_type == "model_edit":
            return {
                "target_part": result.get("target_part"),
                "action": result.get("action"),
                "detail_type": result.get("detail_type"),
                "density": result.get("density"),
            }
        if command_type == "inspect_context":
            summary = {
                "query_type": result.get("query_type"),
                "user_message": result.get("user_message", ""),
            }
            if "matched_part" in result:
                summary["matched_part"] = result["matched_part"].get("name")
            if "part_count" in result:
                summary["part_count"] = result["part_count"]
            return summary
        return {
            "status": result.get("status", ""),
            "user_message": result.get("user_message", ""),
        }

    def _public_part(self, part: dict[str, Any]) -> dict[str, Any]:
        return {
            "name": part["name"],
            "display_name": part.get("display_name", ""),
            "category": part.get("category", "part"),
            "detail_level": part.get("detail_level", "low"),
            "is_catalog_part": part.get("is_catalog_part", False),
            "is_scanned": part.get("is_scanned", False),
            "is_special": part.get("is_special", False),
            "sources": part.get("sources", []),
        }

    def _build_alias_index(self) -> dict[str, dict[str, Any]]:
        alias_index: dict[str, dict[str, Any]] = {}
        for part in self.parts:
            aliases = [part["name"], part.get("display_name", ""), *part.get("aliases", [])]
            for alias in aliases:
                if isinstance(alias, str) and alias:
                    alias_index[alias] = part
        return alias_index

    def _build_category_index(self) -> dict[str, list[dict[str, Any]]]:
        category_index: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for part in self.parts:
            category_index[part.get("category", "part")].append(part)
        return dict(category_index)

    def _build_detail_level_index(self) -> dict[str, list[dict[str, Any]]]:
        detail_level_index: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for part in self.parts:
            detail_level_index[part.get("detail_level", "low")].append(part)
        return dict(detail_level_index)

    def _detect_category(self, user_input: str) -> str | None:
        category_aliases = {
            "weapon": ["武器", "weapon", "枪", "军刀", "火箭筒"],
            "weapon_accessory": ["武器配件", "盾", "浮游炮", "护盾"],
            "equipment": ["装备", "配件", "背包", "推进器", "挂点"],
            "armor": ["装甲", "甲", "armor"],
            "core_body": ["身体", "主体", "躯干", "核心"],
            "limb": ["四肢", "手臂", "腿", "左", "右"],
            "limb_group": ["四肢", "手脚", "手臂", "腿部"],
            "detail_part": ["细节件", "天线", "传感器", "舱门"],
        }
        lowered_input = user_input.lower()
        for category, aliases in category_aliases.items():
            if any(alias.lower() in lowered_input for alias in aliases):
                return category
        return None


def _load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def _write_json(path: Path, data: dict[str, Any]) -> None:
    with path.open("w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)
        file.write("\n")

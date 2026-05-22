"""Load the abstract model context used by the agent.

Only compact metadata is exposed. Real 3D data such as meshes, vertices, faces,
textures, or scene objects must stay outside this context.
"""

import json
import os
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTEXT_DIR = PROJECT_ROOT / "model_contexts"
CATALOG_CONTEXT_TYPES = {"base", "base_catalog", "catalog"}
SCAN_CONTEXT_TYPES = {"scan", "scanned", "scanned_model"}


def get_model_context(context_path: str | Path | None = None) -> dict[str, Any]:
    """Return the abstract model context expected by the prompt."""
    path = Path(
        context_path
        or os.getenv("MODEL_CONTEXT_PATH")
        or os.getenv("MODEL_CONTEXT_DIR")
        or DEFAULT_CONTEXT_DIR
    )
    return load_model_context(path)


def load_model_context(context_path: str | Path) -> dict[str, Any]:
    """Load abstract model metadata from a JSON file or directory."""
    path = Path(context_path)
    if path.is_dir():
        return load_model_contexts_from_directory(path)

    with path.open("r", encoding="utf-8") as file:
        context = json.load(file)

    _validate_model_context(context)
    _annotate_single_file_context(context, path.name)
    return context


def load_model_contexts_from_directory(context_dir: str | Path) -> dict[str, Any]:
    """Load and merge every JSON model context file in a directory."""
    path = Path(context_dir)
    context_files = sorted(path.glob("*.json"))
    if not context_files:
        raise ValueError(f"No model context JSON files found in: {path}")

    contexts = [_load_context_file(context_file) for context_file in context_files]
    merged_context = _merge_model_contexts(contexts)
    _validate_model_context(merged_context)
    return merged_context


def build_model_context_from_scan(scan_source: Any) -> dict[str, Any]:
    """Future interface for converting scanner output into model context JSON.

    A scanner should inspect a model outside the LLM, identify abstract parts
    and accessories, then return the same structure used by files under
    model_contexts/.
    """
    raise NotImplementedError("Model scanning is a future extension point.")


def _load_context_file(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as file:
        context = json.load(file)
    _validate_model_context(context)
    context["_source_file"] = path.name
    return context


def _merge_model_contexts(contexts: list[dict[str, Any]]) -> dict[str, Any]:
    first_model = contexts[0]["model"]
    merged_model: dict[str, Any] = {
        "context_version": first_model.get("context_version", "1.0"),
        "name": first_model["name"],
        "description": first_model.get("description", ""),
        "context_files": [context["_source_file"] for context in contexts],
        "parts": [],
    }

    catalog_part_names: set[str] = set()
    parts_by_name: dict[str, dict[str, Any]] = {}
    part_order: list[str] = []

    for context in contexts:
        model = context["model"]
        context_type = model.get("context_type", "extension")
        source_file = context["_source_file"]

        for part in model["parts"]:
            part_name = part["name"]
            if context_type in CATALOG_CONTEXT_TYPES:
                catalog_part_names.add(part_name)

            if part_name not in parts_by_name:
                parts_by_name[part_name] = {}
                part_order.append(part_name)

            parts_by_name[part_name] = _merge_part(
                parts_by_name[part_name],
                part,
                context_type,
                source_file,
            )

    for part_name in part_order:
        part = parts_by_name[part_name]
        source_types = set(part.pop("_source_types"))
        part["sources"] = sorted(part["sources"])
        part["is_catalog_part"] = part_name in catalog_part_names
        part["is_scanned"] = bool(source_types & SCAN_CONTEXT_TYPES)
        part["is_special"] = part_name not in catalog_part_names
        merged_model["parts"].append(part)

    return {"model": merged_model}


def _merge_part(
    current: dict[str, Any],
    incoming: dict[str, Any],
    context_type: str,
    source_file: str,
) -> dict[str, Any]:
    merged = dict(current)
    current_aliases = merged.get("aliases", [])
    incoming_aliases = incoming.get("aliases", [])

    for key, value in incoming.items():
        if key != "aliases":
            merged[key] = value

    merged["aliases"] = _unique_strings([*current_aliases, *incoming_aliases])
    merged["sources"] = _unique_strings([*merged.get("sources", []), source_file])
    merged["_source_types"] = _unique_strings(
        [*merged.get("_source_types", []), context_type]
    )
    return merged


def _annotate_single_file_context(context: dict[str, Any], source_file: str) -> None:
    context_type = context["model"].get("context_type", "extension")
    is_catalog_file = context_type in CATALOG_CONTEXT_TYPES
    is_scan_file = context_type in SCAN_CONTEXT_TYPES
    for part in context["model"]["parts"]:
        part["sources"] = _unique_strings([*part.get("sources", []), source_file])
        part["is_catalog_part"] = is_catalog_file
        part["is_scanned"] = is_scan_file
        part["is_special"] = not is_catalog_file


def _unique_strings(values: list[Any]) -> list[str]:
    unique_values: list[str] = []
    seen_values: set[str] = set()
    for value in values:
        if not isinstance(value, str) or not value:
            continue
        if value not in seen_values:
            unique_values.append(value)
            seen_values.add(value)
    return unique_values


def _validate_model_context(context: dict[str, Any]) -> None:
    model = context.get("model")
    if not isinstance(model, dict):
        raise ValueError("Model context must contain a 'model' object.")

    if not isinstance(model.get("name"), str) or not model["name"]:
        raise ValueError("Model context requires model.name.")

    parts = model.get("parts")
    if not isinstance(parts, list) or not parts:
        raise ValueError("Model context requires a non-empty model.parts list.")

    seen_names: set[str] = set()
    for part in parts:
        if not isinstance(part, dict):
            raise ValueError("Each model part must be an object.")

        name = part.get("name")
        detail_level = part.get("detail_level")
        if not isinstance(name, str) or not name:
            raise ValueError("Each model part requires a non-empty name.")
        if name in seen_names:
            raise ValueError(f"Duplicate model part name: {name}")
        if detail_level not in {"low", "medium", "high"}:
            raise ValueError(f"Invalid detail_level for part {name}: {detail_level}")
        seen_names.add(name)

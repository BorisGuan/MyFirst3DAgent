"""Compatibility wrapper for the split Core API modules."""

from __future__ import annotations

from core_api import (
    add_bevel_modifier,
    add_solidify_modifier,
    add_weighted_normal_modifier,
    build_modification_report,
    object_snapshot,
    remove_or_replace_named_modifier,
    require_object,
    reset_modification_report_state,
    save_as_copy_only,
    write_modification_report,
)

__all__ = [
    "add_bevel_modifier",
    "add_solidify_modifier",
    "add_weighted_normal_modifier",
    "build_modification_report",
    "object_snapshot",
    "remove_or_replace_named_modifier",
    "require_object",
    "reset_modification_report_state",
    "save_as_copy_only",
    "write_modification_report",
]
"""Core API layer exports."""

from core_api.geometry_api import (
    add_bevel_modifier,
    add_solidify_modifier,
    add_weighted_normal_modifier,
    remove_or_replace_named_modifier,
)
from core_api.persistence_api import (
    build_modification_report,
    reset_modification_report_state,
    save_as_copy_only,
    write_modification_report,
)
from core_api.scene_object_api import object_snapshot, require_object

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
"""Safety checks for Blender Python scripts before background execution."""

from __future__ import annotations


FORBIDDEN_SCRIPT_TOKENS = (
    "bpy.ops.object.delete",
    "bpy.ops.mesh",
    "bpy.ops.wm.save_as_mainfile",
    "bpy.ops.wm.save_mainfile",
    "modifier_apply",
    ".modifiers.new",
    "bmesh",
    "subprocess",
    "shutil.rmtree",
)


SAVE_COPY_ALLOWED_TOKENS = ("bpy.ops.wm.save_as_mainfile",)


def scan_blender_preview_script(script_text: str, allow_save_copy: bool = False) -> dict:
    """Return a small machine-readable safety scan for a preview-only script."""
    allowed_tokens = set(SAVE_COPY_ALLOWED_TOKENS if allow_save_copy else ())
    hits = [token for token in FORBIDDEN_SCRIPT_TOKENS if token in script_text and token not in allowed_tokens]
    return {
        "scan_version": "v0_7",
        "safety_status": "blocked" if hits else "passed",
        "forbidden_tokens": list(FORBIDDEN_SCRIPT_TOKENS),
        "allowed_save_copy_tokens": list(allowed_tokens),
        "detected_forbidden_tokens": hits,
    }
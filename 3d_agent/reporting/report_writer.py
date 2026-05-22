"""Report file writer for the Reporting side-system."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def write_report(path: str | Path, report: dict[str, Any]) -> str:
    """Write report as JSON and return the written path."""
    report_path = Path(path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return str(report_path)
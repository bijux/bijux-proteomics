"""Compatibility structure-report entrypoints."""

from bijux_proteomics.structure_report import Metrics, Report
from bijux_proteomics.structure_report.render import (
    confidence_summary,
    format_pct,
    nl_summary,
    to_text,
)

__all__ = [
    "Metrics",
    "Report",
    "confidence_summary",
    "format_pct",
    "nl_summary",
    "to_text",
]

"""Compatibility structure-report entrypoints."""

from bijux_proteomics.review.structure_reports import Metrics, Report
from bijux_proteomics.review.structure_reports.render import (
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

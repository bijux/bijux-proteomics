"""Compatibility forwarding module for canonical core report rendering."""

from __future__ import annotations

from typing import Any

from bijux_proteomics.structure_report import render as _core_render
from bijux_proteomics.structure_report.render import (  # noqa: F401
    SummaryGenerator,
    TextGenerator,
    confidence_summary,
    format_pct,
    format_value,
    from_json,
    json_schema,
    to_json,
    to_text,
)

LANGCHAIN_AVAILABLE = _core_render.LANGCHAIN_AVAILABLE
HuggingFaceHub = _core_render.HuggingFaceHub
PromptTemplate = _core_render.PromptTemplate


def _sync_optional_dependencies() -> None:
    _core_render.LANGCHAIN_AVAILABLE = LANGCHAIN_AVAILABLE
    _core_render.HuggingFaceHub = HuggingFaceHub
    _core_render.PromptTemplate = PromptTemplate


def nl_summary(report: Any, generator: SummaryGenerator | None = None) -> str:
    """Mirror the legacy monkeypatch surface while delegating to core rendering."""
    _sync_optional_dependencies()
    return _core_render.nl_summary(report, generator=generator)


__all__ = [
    "HuggingFaceHub",
    "LANGCHAIN_AVAILABLE",
    "PromptTemplate",
    "SummaryGenerator",
    "TextGenerator",
    "confidence_summary",
    "format_pct",
    "format_value",
    "from_json",
    "json_schema",
    "nl_summary",
    "to_json",
    "to_text",
]

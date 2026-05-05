"""Canonical runtime package for bijux proteomics execution surfaces."""

from typing import Any

from bijux_proteomics_runtime.api import AppConfig, create_app
from bijux_proteomics_runtime.interfaces.cli import cli
from bijux_proteomics_runtime.runtime.control.execution import RunManager

__all__ = [
    "AppConfig",
    "Metrics",
    "Report",
    "RunManager",
    "cli",
    "create_app",
    "low_confidence_segments",
]


def __getattr__(name: str) -> Any:
    if name in {"Metrics", "Report"}:
        from bijux_proteomics_intelligence import report as _report

        return getattr(_report, name)
    if name == "low_confidence_segments":
        from bijux_proteomics_intelligence.domain import low_confidence_segments

        return low_confidence_segments
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

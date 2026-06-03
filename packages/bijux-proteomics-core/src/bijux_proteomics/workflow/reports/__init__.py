"""Workflow report owners for governed biological and scientific result outputs."""

from __future__ import annotations

from importlib import import_module
from typing import Any

_REPORT_EXPORT_MODULES = (
    "bijux_proteomics.workflow.reports.biological_reporting",
    "bijux_proteomics.workflow.reports.biological_result_graph",
)


def __getattr__(name: str) -> Any:
    for module_path in _REPORT_EXPORT_MODULES:
        module = import_module(module_path)
        if hasattr(module, name):
            value = getattr(module, name)
            globals()[name] = value
            return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

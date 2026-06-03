"""Workflow artifact export and governed result-bundle owners."""

from __future__ import annotations

from importlib import import_module
from typing import Any

_EXPORT_MODULES = (
    "bijux_proteomics.workflow.exports.artifact_layout",
    "bijux_proteomics.workflow.exports.interactive_result_bundle",
    "bijux_proteomics.workflow.exports.interactive_result_comparison",
    "bijux_proteomics.workflow.exports.output_validation",
    "bijux_proteomics.workflow.exports.result_archive",
    "bijux_proteomics.workflow.exports.result_manifest",
    "bijux_proteomics.workflow.exports.result_search_index",
)


def __getattr__(name: str) -> Any:
    for module_path in _EXPORT_MODULES:
        module = import_module(module_path)
        if hasattr(module, name):
            value = getattr(module, name)
            globals()[name] = value
            return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

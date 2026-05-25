"""Workflow demo owners over shipped review-grade example datasets."""

from __future__ import annotations

from importlib import import_module

_DEMO_EXPORT_MODULES = (
    "bijux_proteomics.workflow.demo.surprising_demo",
    "bijux_proteomics.workflow.demo.surprising_demo_interrogation",
)


def __getattr__(name: str) -> object:
    for module_path in _DEMO_EXPORT_MODULES:
        module = import_module(module_path)
        if hasattr(module, name):
            value = getattr(module, name)
            globals()[name] = value
            return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

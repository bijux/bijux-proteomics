"""Canonical runtime package for bijux proteomics execution surfaces."""

from typing import Any

from bijux_proteomics_runtime.api import AppConfig, create_app
from bijux_proteomics_runtime.interfaces.cli import cli
from bijux_proteomics_runtime.runtime.control.execution import RunManager

__all__ = [
    "AppConfig",
    "RunManager",
    "cli",
    "create_app",
]


def __getattr__(name: str) -> Any:
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

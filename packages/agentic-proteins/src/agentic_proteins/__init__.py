# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Agentic Proteins package."""

from __future__ import annotations

from importlib import metadata
from typing import Any

__all__ = [
    "Report",
    "Metrics",
    "low_confidence_segments",
]


def __getattr__(name: str) -> Any:
    if name in {"Metrics", "Report"}:
        from bijux_proteomics_intelligence import report as _report

        return getattr(_report, name)
    if name == "low_confidence_segments":
        from bijux_proteomics_knowledge.confidence import low_confidence_segments

        return low_confidence_segments
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


try:
    __version__ = metadata.version("agentic-proteins")
except metadata.PackageNotFoundError:
    __version__ = ""

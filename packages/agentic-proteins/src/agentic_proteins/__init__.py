# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Agentic Proteins package."""

from __future__ import annotations

from importlib import metadata

from agentic_proteins.domain.confidence import low_confidence_segments
from agentic_proteins.report import Metrics, Report

__all__ = [
    "Report",
    "Metrics",
    "low_confidence_segments",
]

try:
    __version__ = metadata.version("agentic-proteins")
except metadata.PackageNotFoundError:
    __version__ = ""

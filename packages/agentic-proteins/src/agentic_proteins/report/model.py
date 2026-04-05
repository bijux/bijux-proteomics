# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Report model and API."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Literal

if TYPE_CHECKING:
    from agentic_proteins.report.compute import Metrics


@dataclass(frozen=True)
class Report:
    """Dataclass for the full prediction report."""

    provider: str
    metrics: Metrics
    notes: str
    low_conf_segments: tuple[tuple[int, int], ...] = ()
    warnings: list[str] = field(default_factory=list)
    links: dict[str, str] = field(default_factory=dict)
    schema_version: Literal["1.0"] = "1.0"
    provenance: dict[str, Any] = field(default_factory=dict)

# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Contracts for biological sample-context exports."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BiologicalCohortContextExportNames:
    """Artifact names emitted for cohort-context exports."""

    summary_name: str | None
    stratum_name: str | None
    effect_name: str | None
    interaction_name: str | None


@dataclass(frozen=True)
class BiologicalTissueContextExportNames:
    """Artifact names emitted for tissue-context exports."""

    summary_name: str | None
    sample_name: str | None
    unexpected_name: str | None
    interpretation_name: str | None


__all__ = [
    "BiologicalCohortContextExportNames",
    "BiologicalTissueContextExportNames",
]

# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Stable missingness classification models."""

from __future__ import annotations

from enum import StrEnum

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel


class MissingnessLabel(StrEnum):
    """Owned entity-level missingness labels for downstream statistical handling."""

    RANDOM = "random"
    INTENSITY_CENSORED = "intensity_censored"
    CONDITION_SPECIFIC = "condition_specific"
    SAMPLE_FAILURE = "sample_failure"
    STRUCTURAL_ABSENCE = "structural_absence"


class MissingnessClassificationEntry(JsonModel):
    """One entity-level missingness classification row."""

    model_config = ConfigDict(extra="forbid")

    entity_id: str = Field(..., min_length=1)
    label: MissingnessLabel
    observed_sample_count: int = Field(..., ge=0)
    missing_sample_count: int = Field(..., ge=0)
    missing_fraction: float = Field(..., ge=0.0, le=1.0)
    mean_log2_observed_abundance: float | None = None
    note: str = Field(..., min_length=1)


class MissingnessClassificationReport(JsonModel):
    """Five-label missingness classification over one quantitative matrix."""

    model_config = ConfigDict(extra="forbid")

    entries: tuple[MissingnessClassificationEntry, ...] = Field(default_factory=tuple)
    failed_sample_ids: tuple[str, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


__all__ = [
    "MissingnessClassificationEntry",
    "MissingnessClassificationReport",
    "MissingnessLabel",
]

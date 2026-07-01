# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owned data models for differential-result robustness surfaces."""

from __future__ import annotations

from enum import StrEnum

from pydantic import ConfigDict, Field

from bijux_proteomics.quantification.contracts.differential import (
    DifferentialResultRobustnessQcStatus,
    DifferentialResultRobustnessReasonCode,
)
from bijux_proteomics_foundation import JsonModel


class DifferentialResultRobustnessAnalysisKind(StrEnum):
    """Stable analysis-family labels for robustness ledgers."""

    TWO_CONDITION = "two_condition"
    TIME_COURSE = "time_course"


class DifferentialResultRobustnessEntry(JsonModel):
    """One robustness decomposition row for one differential result."""

    model_config = ConfigDict(extra="forbid")

    analysis_kind: DifferentialResultRobustnessAnalysisKind
    entity_id: str = Field(..., min_length=1)
    primary_condition: str = Field(..., min_length=1)
    comparison_condition: str | None = None
    robustness_score: float = Field(..., ge=0.0, le=1.0)
    qc_status: DifferentialResultRobustnessQcStatus
    reason_codes: tuple[DifferentialResultRobustnessReasonCode, ...] = Field(
        default_factory=tuple
    )
    effect_size_score: float = Field(..., ge=0.0, le=1.0)
    fdr_score: float = Field(..., ge=0.0, le=1.0)
    missingness_score: float = Field(..., ge=0.0, le=1.0)
    imputation_dependence_score: float = Field(..., ge=0.0, le=1.0)
    peptide_support_score: float = Field(..., ge=0.0, le=1.0)
    replicate_consistency_score: float = Field(..., ge=0.0, le=1.0)
    qc_score: float = Field(..., ge=0.0, le=1.0)
    note: str = Field(..., min_length=1)


class DifferentialResultRobustnessReport(JsonModel):
    """Owned robustness report over one differential result collection."""

    model_config = ConfigDict(extra="forbid")

    analysis_kind: DifferentialResultRobustnessAnalysisKind
    entries: tuple[DifferentialResultRobustnessEntry, ...] = Field(
        default_factory=tuple
    )
    low_robustness_entry_count: int = Field(..., ge=0)
    caution_qc_entry_count: int = Field(..., ge=0)
    failed_qc_entry_count: int = Field(..., ge=0)
    note: str = Field(..., min_length=1)


class BootstrapEffectRobustnessTier(StrEnum):
    """Stable resampling tiers for entity-level effect robustness."""

    STABLE = "stable"
    CAUTION = "caution"
    UNSTABLE = "unstable"


class BootstrapEffectStabilityEntry(JsonModel):
    """One entity-level effect stability summary over bootstrap resamples."""

    model_config = ConfigDict(extra="forbid")

    entity_id: str = Field(..., min_length=1)
    median_log2fc: float
    sign_consistency: float = Field(..., ge=0.0, le=1.0)
    q_value_stability: float = Field(..., ge=0.0, le=1.0)
    robustness_tier: BootstrapEffectRobustnessTier


class BootstrapEffectStabilityReport(JsonModel):
    """Owned bootstrap effect-stability report over one two-condition contrast."""

    model_config = ConfigDict(extra="forbid")

    condition_a: str = Field(..., min_length=1)
    condition_b: str = Field(..., min_length=1)
    n_resamples: int = Field(..., ge=10)
    significance_threshold: float = Field(..., gt=0.0, lt=1.0)
    entries: tuple[BootstrapEffectStabilityEntry, ...] = Field(default_factory=tuple)
    stable_entry_count: int = Field(..., ge=0)
    caution_entry_count: int = Field(..., ge=0)
    unstable_entry_count: int = Field(..., ge=0)
    note: str = Field(..., min_length=1)


__all__ = [
    "BootstrapEffectRobustnessTier",
    "BootstrapEffectStabilityEntry",
    "BootstrapEffectStabilityReport",
    "DifferentialResultRobustnessAnalysisKind",
    "DifferentialResultRobustnessEntry",
    "DifferentialResultRobustnessReport",
]

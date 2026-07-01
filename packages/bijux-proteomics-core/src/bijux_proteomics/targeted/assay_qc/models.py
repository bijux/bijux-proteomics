# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Stable contracts for targeted assay-QC reporting."""

from __future__ import annotations

from pydantic import ConfigDict, Field

from bijux_proteomics.io.fragment_ratio_stability import FragmentRatioStabilityReport
from bijux_proteomics.targeted.transition_coelution import (
    TargetedTransitionCoelutionReport,
)
from bijux_proteomics_foundation import JsonModel


class TargetedTransitionConsistencyEntry(JsonModel):
    """One sample-level transition consistency record for a targeted precursor."""

    model_config = ConfigDict(extra="forbid")

    target_id: str = Field(..., min_length=1)
    sample_id: str = Field(..., min_length=1)
    detected_transition_count: int = Field(..., ge=0)
    expected_transition_count: int = Field(..., ge=0)
    consistency_fraction: float = Field(..., ge=0.0, le=1.0)


class TargetedFragmentRatioEntry(JsonModel):
    """One transition share inside a targeted precursor for one sample."""

    model_config = ConfigDict(extra="forbid")

    target_id: str = Field(..., min_length=1)
    sample_id: str = Field(..., min_length=1)
    transition_id: str = Field(..., min_length=1)
    intensity: float = Field(..., ge=0.0)
    total_target_intensity: float = Field(..., ge=0.0)
    relative_share: float = Field(..., ge=0.0, le=1.0)
    reference_relative_share: float = Field(..., ge=0.0, le=1.0)
    absolute_share_delta: float = Field(..., ge=0.0, le=1.0)
    ratio_cv: float | None = Field(default=None, ge=0.0)
    drift_flag: bool = False
    unstable_transition_flagged: bool = False
    flagged: bool = False


class TargetedTransitionQcEntry(JsonModel):
    """One sample-resolved transition QC record for a targeted precursor."""

    model_config = ConfigDict(extra="forbid")

    target_id: str = Field(..., min_length=1)
    sample_id: str = Field(..., min_length=1)
    condition: str | None = None
    transition_id: str = Field(..., min_length=1)
    detected: bool
    intensity: float | None = Field(default=None, ge=0.0)
    quality_flag: str | None = None
    relative_share: float | None = Field(default=None, ge=0.0, le=1.0)
    reference_relative_share: float | None = Field(default=None, ge=0.0, le=1.0)
    absolute_share_delta: float | None = Field(default=None, ge=0.0, le=1.0)
    ratio_cv: float | None = Field(default=None, ge=0.0)
    coeluting: bool = False
    coelution_flagged: bool = False
    reference_alignment_flagged: bool = False
    coelution_delta_minutes: float | None = Field(default=None, ge=0.0)
    reference_delta_minutes: float | None = Field(default=None, ge=0.0)
    quality_flagged: bool = False
    ratio_flagged: bool = False
    ratio_drift_flagged: bool = False
    ratio_unstable_transition_flagged: bool = False
    passed: bool
    failure_reasons: tuple[str, ...] = Field(default_factory=tuple)


class TargetedRetentionTimeConsistencyEntry(JsonModel):
    """One sample-level retention-time consistency record for a targeted precursor."""

    model_config = ConfigDict(extra="forbid")

    target_id: str = Field(..., min_length=1)
    sample_id: str = Field(..., min_length=1)
    observed_transition_count: int = Field(..., ge=0)
    mean_retention_time_minutes: float | None = Field(default=None, ge=0.0)
    reference_retention_time_minutes: float | None = Field(default=None, ge=0.0)
    absolute_delta_minutes: float | None = Field(default=None, ge=0.0)
    flagged: bool = False


class TargetedReplicateCvEntry(JsonModel):
    """One condition-level replicate-CV record for a targeted precursor."""

    model_config = ConfigDict(extra="forbid")

    target_id: str = Field(..., min_length=1)
    condition: str = Field(..., min_length=1)
    replicate_count: int = Field(..., ge=0)
    detected_replicate_count: int = Field(..., ge=0)
    mean_intensity: float | None = Field(default=None, ge=0.0)
    coefficient_of_variation: float | None = Field(default=None, ge=0.0)
    flagged: bool = False


class TargetedTargetQcEntry(JsonModel):
    """One sample-resolved target QC record with explicit reliability semantics."""

    model_config = ConfigDict(extra="forbid")

    target_id: str = Field(..., min_length=1)
    sample_id: str = Field(..., min_length=1)
    condition: str | None = None
    expected_transition_count: int = Field(..., ge=0)
    observed_transition_count: int = Field(..., ge=0)
    coeluting_transition_count: int = Field(..., ge=0)
    coeluting_transition_ids: tuple[str, ...] = Field(default_factory=tuple)
    passing_transition_count: int = Field(..., ge=0)
    passing_transition_ids: tuple[str, ...] = Field(default_factory=tuple)
    failing_transition_ids: tuple[str, ...] = Field(default_factory=tuple)
    passing_total_intensity: float | None = Field(default=None, ge=0.0)
    mean_retention_time_minutes: float | None = Field(default=None, ge=0.0)
    reference_retention_time_minutes: float | None = Field(default=None, ge=0.0)
    absolute_delta_minutes: float | None = Field(default=None, ge=0.0)
    quality_flag_count: int = Field(..., ge=0)
    condition_replicate_cv: float | None = Field(default=None, ge=0.0)
    condition_replicate_cv_flagged: bool = False
    reliability_score: float = Field(..., ge=0.0, le=1.0)
    reliable: bool
    reliability_reasons: tuple[str, ...] = Field(default_factory=tuple)


class TargetedUnreliableTargetEntry(JsonModel):
    """One explicitly flagged targeted precursor under sample or condition review."""

    model_config = ConfigDict(extra="forbid")

    target_id: str = Field(..., min_length=1)
    sample_id: str | None = None
    condition: str | None = None
    flagged_transition_ids: tuple[str, ...] = Field(default_factory=tuple)
    quality_flags: tuple[str, ...] = Field(default_factory=tuple)
    reasons: tuple[str, ...] = Field(default_factory=tuple)


class TargetedAssayQcSummary(JsonModel):
    """Compact summary over one targeted assay QC report."""

    model_config = ConfigDict(extra="forbid")

    target_count: int = Field(..., ge=0)
    sample_count: int = Field(..., ge=0)
    target_qc_entry_count: int = Field(..., ge=0)
    reliable_target_entry_count: int = Field(..., ge=0)
    transition_consistency_entry_count: int = Field(..., ge=0)
    coelution_target_entry_count: int = Field(..., ge=0)
    flagged_coelution_target_entry_count: int = Field(..., ge=0)
    transition_coelution_entry_count: int = Field(..., ge=0)
    coeluting_transition_entry_count: int = Field(..., ge=0)
    transition_qc_entry_count: int = Field(..., ge=0)
    passing_transition_qc_entry_count: int = Field(..., ge=0)
    fragment_ratio_entry_count: int = Field(..., ge=0)
    fragment_ratio_stability_fragment_entry_count: int = Field(..., ge=0)
    unstable_fragment_ratio_entry_count: int = Field(..., ge=0)
    drift_flagged_fragment_ratio_observation_count: int = Field(..., ge=0)
    retention_time_entry_count: int = Field(..., ge=0)
    flagged_retention_time_entry_count: int = Field(..., ge=0)
    replicate_cv_entry_count: int = Field(..., ge=0)
    flagged_replicate_cv_entry_count: int = Field(..., ge=0)
    unreliable_target_entry_count: int = Field(..., ge=0)
    unreliable_target_count: int = Field(..., ge=0)


class TargetedAssayQcReport(JsonModel):
    """Targeted assay QC report over transition consistency and fragment ratios."""

    model_config = ConfigDict(extra="forbid")

    source_name: str = Field(..., min_length=1)
    transition_coelution: TargetedTransitionCoelutionReport
    fragment_ratio_stability: FragmentRatioStabilityReport
    target_qc: tuple[TargetedTargetQcEntry, ...] = Field(default_factory=tuple)
    transition_consistency: tuple[TargetedTransitionConsistencyEntry, ...] = Field(
        default_factory=tuple
    )
    transition_qc: tuple[TargetedTransitionQcEntry, ...] = Field(default_factory=tuple)
    fragment_ratios: tuple[TargetedFragmentRatioEntry, ...] = Field(
        default_factory=tuple
    )
    retention_time_consistency: tuple[TargetedRetentionTimeConsistencyEntry, ...] = (
        Field(default_factory=tuple)
    )
    replicate_cv: tuple[TargetedReplicateCvEntry, ...] = Field(default_factory=tuple)
    unreliable_targets: tuple[TargetedUnreliableTargetEntry, ...] = Field(
        default_factory=tuple
    )
    summary: TargetedAssayQcSummary
    note: str = Field(..., min_length=1)


__all__ = [
    "TargetedAssayQcReport",
    "TargetedAssayQcSummary",
    "TargetedFragmentRatioEntry",
    "TargetedReplicateCvEntry",
    "TargetedRetentionTimeConsistencyEntry",
    "TargetedTargetQcEntry",
    "TargetedTransitionConsistencyEntry",
    "TargetedTransitionQcEntry",
    "TargetedUnreliableTargetEntry",
]

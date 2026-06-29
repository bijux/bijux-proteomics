# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Public contracts for targeted biomarker stability analysis."""

from __future__ import annotations

from enum import StrEnum

from pydantic import ConfigDict, Field

from bijux_proteomics.targeted.panel_design import TargetedPanelCandidateKind
from bijux_proteomics_foundation import JsonModel


class BiomarkerStabilityDimension(StrEnum):
    """Stable subgroup dimensions checked for candidate stability."""

    CONDITION = "condition"
    BATCH = "batch"
    TIMEPOINT = "timepoint"
    SAMPLE_TYPE = "sample_type"


class BiomarkerStabilityReasonCode(StrEnum):
    """Stable reasons behind one biomarker stability downgrade."""

    LOW_RELIABLE_SAMPLE_FRACTION = "low_reliable_sample_fraction"
    SINGLE_CONDITION_SIGNAL_ONLY = "single_condition_signal_only"
    BATCH_SENSITIVE_SIGNAL = "batch_sensitive_signal"
    TIMEPOINT_SENSITIVE_SIGNAL = "timepoint_sensitive_signal"
    SAMPLE_TYPE_SENSITIVE_SIGNAL = "sample_type_sensitive_signal"
    ASSAY_DISAGREEMENT = "assay_disagreement"
    SPARSE_SUBGROUP_COVERAGE = "sparse_subgroup_coverage"
    NO_MATCHING_TARGETED_SIGNAL = "no_matching_targeted_signal"


class BiomarkerSubgroupBehaviorStatus(StrEnum):
    """Stable per-subgroup behavior statuses."""

    STABLE = "stable"
    VARIABLE = "variable"
    SPARSE = "sparse"
    UNSUPPORTED = "unsupported"


class BiomarkerStabilityPolicy(JsonModel):
    """Policy controlling subgroup stability scoring and downgrade thresholds."""

    model_config = ConfigDict(extra="forbid")

    batch_field: str = Field(default="batch", min_length=1)
    timepoint_field: str = Field(default="timepoint", min_length=1)
    sample_type_field: str = Field(default="sample_type", min_length=1)
    minimum_reliable_samples_per_group: int = Field(default=2, ge=1)
    minimum_reliable_sample_fraction: float = Field(default=0.5, ge=0.0, le=1.0)
    subgroup_median_delta_threshold: float = Field(default=1.0, ge=0.0)
    batch_residual_delta_threshold: float = Field(default=0.75, ge=0.0)
    assay_disagreement_delta_threshold: float = Field(default=0.75, ge=0.0)
    downgrade_below_score: float = Field(default=0.75, ge=0.0, le=1.0)


class BiomarkerSubgroupBehaviorEntry(JsonModel):
    """One candidate-level subgroup behavior summary."""

    model_config = ConfigDict(extra="forbid")

    candidate_id: str = Field(..., min_length=1)
    dimension: BiomarkerStabilityDimension
    subgroup_value: str = Field(..., min_length=1)
    reliable_sample_count: int = Field(..., ge=0)
    total_sample_count: int = Field(..., ge=0)
    mean_log2_intensity: float | None = None
    median_log2_intensity: float | None = None
    coefficient_of_variation: float | None = Field(default=None, ge=0.0)
    residual_median_log2_intensity: float | None = None
    status: BiomarkerSubgroupBehaviorStatus
    note: str = Field(..., min_length=1)


class BiomarkerStabilityEntry(JsonModel):
    """One biomarker candidate scored for targeted subgroup stability."""

    model_config = ConfigDict(extra="forbid")

    candidate_id: str = Field(..., min_length=1)
    candidate_kind: TargetedPanelCandidateKind
    display_label: str = Field(..., min_length=1)
    target_protein_ref: str = Field(..., min_length=1)
    site_key: str | None = None
    original_priority_rank: int = Field(..., ge=1)
    adjusted_priority_rank: int = Field(..., ge=1)
    original_final_score: float = Field(..., ge=0.0, le=1.0)
    adjusted_final_score: float = Field(..., ge=0.0, le=1.0)
    original_penalty_total: float = Field(..., ge=0.0)
    adjusted_penalty_total: float = Field(..., ge=0.0)
    stability_penalty: float = Field(..., ge=0.0)
    stability_score: float = Field(..., ge=0.0, le=1.0)
    reliable_sample_fraction: float = Field(..., ge=0.0, le=1.0)
    condition_breadth_score: float = Field(..., ge=0.0, le=1.0)
    assay_agreement_score: float = Field(..., ge=0.0, le=1.0)
    batch_stability_score: float | None = Field(default=None, ge=0.0, le=1.0)
    timepoint_stability_score: float | None = Field(default=None, ge=0.0, le=1.0)
    sample_type_stability_score: float | None = Field(default=None, ge=0.0, le=1.0)
    reliable_sample_count: int = Field(..., ge=0)
    total_sample_count: int = Field(..., ge=0)
    condition_count_with_signal: int = Field(..., ge=0)
    total_condition_count: int = Field(..., ge=0)
    assay_entry_count: int = Field(..., ge=0)
    matched_target_count: int = Field(..., ge=0)
    downgraded: bool
    instability_reasons: tuple[BiomarkerStabilityReasonCode, ...] = Field(
        default_factory=tuple
    )
    subgroup_behavior_count: int = Field(..., ge=0)
    note: str = Field(..., min_length=1)


class BiomarkerStabilitySummary(JsonModel):
    """Compact summary over one biomarker stability pass."""

    model_config = ConfigDict(extra="forbid")

    candidate_count: int = Field(..., ge=0)
    downgraded_candidate_count: int = Field(..., ge=0)
    low_reliable_sample_fraction_count: int = Field(..., ge=0)
    single_condition_signal_only_count: int = Field(..., ge=0)
    batch_sensitive_candidate_count: int = Field(..., ge=0)
    timepoint_sensitive_candidate_count: int = Field(..., ge=0)
    sample_type_sensitive_candidate_count: int = Field(..., ge=0)
    assay_disagreement_candidate_count: int = Field(..., ge=0)
    sparse_subgroup_candidate_count: int = Field(..., ge=0)


class BiomarkerStabilityReport(JsonModel):
    """Owned biomarker stability analysis over targeted subgroup behavior."""

    model_config = ConfigDict(extra="forbid")

    source_name: str = Field(..., min_length=1)
    policy: BiomarkerStabilityPolicy
    entries: tuple[BiomarkerStabilityEntry, ...] = Field(default_factory=tuple)
    subgroup_behavior: tuple[BiomarkerSubgroupBehaviorEntry, ...] = Field(
        default_factory=tuple
    )
    summary: BiomarkerStabilitySummary
    note: str = Field(..., min_length=1)


__all__ = [
    "BiomarkerStabilityDimension",
    "BiomarkerStabilityEntry",
    "BiomarkerStabilityPolicy",
    "BiomarkerStabilityReasonCode",
    "BiomarkerStabilityReport",
    "BiomarkerStabilitySummary",
    "BiomarkerSubgroupBehaviorEntry",
    "BiomarkerSubgroupBehaviorStatus",
]

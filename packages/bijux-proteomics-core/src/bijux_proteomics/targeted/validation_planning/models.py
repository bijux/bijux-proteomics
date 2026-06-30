# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Stable models for targeted validation experiment planning."""

from __future__ import annotations

from enum import StrEnum

from pydantic import ConfigDict, Field

from bijux_proteomics.identification.peptide_evidence import PeptideEvidenceClass
from bijux_proteomics.sequences.peptide_chemical_liability import (
    PeptideChemicalLiabilityTier,
)
from bijux_proteomics.sequences.peptide_detectability import PeptideDetectabilityTier
from bijux_proteomics.sequences.peptide_uniqueness_index import (
    PeptideUniquenessClass,
)
from bijux_proteomics.targeted.assay_interference import (
    TargetedAssayInterferenceRiskTier,
)
from bijux_proteomics.targeted.panel_design import (
    TargetedPanelCandidateKind,
    TargetedPanelWarningCode,
)
from bijux_proteomics_foundation import JsonModel


class ValidationExperimentPlanningMode(StrEnum):
    """How one validation plan recommendation was derived."""

    PILOT_BACKED = "pilot_backed"
    HEURISTIC = "heuristic"


class ValidationExperimentWarningCode(StrEnum):
    """Stable warnings emitted by validation experiment planning."""

    UNDERPOWERED_DESIGN = "underpowered_design"
    HIGH_EXPECTED_MISSINGNESS = "high_expected_missingness"
    HIGH_ASSAY_RISK = "high_assay_risk"
    NON_UNIQUE_TARGET = "non_unique_target"
    REDUCED_TRANSITION_SUPPORT = "reduced_transition_support"
    CANDIDATE_PENALIZED = "candidate_penalized"
    MISSING_PILOT_VARIANCE = "missing_pilot_variance"
    VARIANCE_FALLBACK_USED = "variance_fallback_used"
    MISSING_SELECTION_CONTEXT = "missing_selection_context"
    SITE_CANDIDATE_NOT_PANELIZED = "site_candidate_not_panelized"


class ValidationExperimentWarningSeverity(StrEnum):
    """Severity of one validation planning warning."""

    NOTICE = "notice"
    CAUTION = "caution"
    HIGH = "high"


class ValidationExperimentPlanningPolicy(JsonModel):
    """Planner policy for sample recommendation and underpowered design checks."""

    model_config = ConfigDict(extra="forbid")

    proposed_samples_per_group: int = Field(default=6, ge=1)
    fdr_target: float = Field(default=0.05, gt=0.0, le=0.25)
    target_power: float = Field(default=0.8, gt=0.5, lt=0.999)
    heuristic_minimum_samples_per_group: int = Field(default=4, ge=2)


class ValidationPlanningBiomarkerCandidateInput(JsonModel):
    """Minimal biomarker-candidate context needed for targeted validation planning."""

    model_config = ConfigDict(extra="forbid")

    candidate_id: str = Field(..., min_length=1)
    candidate_kind: TargetedPanelCandidateKind
    display_label: str = Field(..., min_length=1)
    target_protein_ref: str = Field(..., min_length=1)
    site_key: str | None = None
    priority_rank: int = Field(..., ge=1)
    final_score: float = Field(..., ge=0.0, le=1.0)
    penalty_total: float = Field(..., ge=0.0)
    uncertainty: float = Field(default=0.0, ge=0.0, le=1.0)
    effect_size: float | None = None
    adjusted_p_value: float | None = Field(default=None, ge=0.0, le=1.0)
    support_count: int = Field(default=0, ge=0)
    robustness_score: float = Field(..., ge=0.0, le=1.0)
    assay_feasibility_score: float = Field(..., ge=0.0, le=1.0)
    rank_reason_codes: tuple[str, ...] = Field(default_factory=tuple)
    ranking_note: str = Field(..., min_length=1)


class ValidationPlanningSelectedPeptideInput(JsonModel):
    """Selected-peptide observability context used to estimate validation missingness."""

    model_config = ConfigDict(extra="forbid")

    target_protein_ref: str = Field(..., min_length=1)
    target_protein_group_id: str = Field(..., min_length=1)
    gene_symbol: str | None = None
    peptide_sequence: str = Field(..., min_length=1)
    canonical_peptide: str = Field(..., min_length=1)
    rank: int = Field(..., ge=1)
    observed_in_discovery: bool
    observed_psm_count: int | None = Field(default=None, ge=0)
    run_count: int | None = Field(default=None, ge=0)
    detection_frequency: float | None = Field(default=None, ge=0.0, le=1.0)
    replicate_consistency: float | None = Field(default=None, ge=0.0, le=1.0)
    primary_evidence_class: PeptideEvidenceClass | None = None
    uniqueness_class: PeptideUniquenessClass
    uniqueness_score: float = Field(..., ge=0.0, le=1.0)
    detectability_score: float = Field(..., ge=0.0, le=1.0)
    detectability_tier: PeptideDetectabilityTier
    suitability_score: float = Field(..., ge=0.0, le=1.0)
    liability_tier: PeptideChemicalLiabilityTier
    liability_codes: tuple[str, ...] = Field(default_factory=tuple)


class ValidationPlanningPanelAssayInput(JsonModel):
    """Panel assay context promoted from targeted panel design."""

    model_config = ConfigDict(extra="forbid")

    assay_entry_id: str = Field(..., min_length=1)
    biomarker_candidate_id: str = Field(..., min_length=1)
    biomarker_candidate_kind: TargetedPanelCandidateKind
    biomarker_display_label: str = Field(..., min_length=1)
    biomarker_priority_rank: int = Field(..., ge=1)
    target_protein_ref: str = Field(..., min_length=1)
    target_protein_group_id: str = Field(..., min_length=1)
    gene_symbol: str | None = None
    peptide_sequence: str = Field(..., min_length=1)
    canonical_peptide: str = Field(..., min_length=1)
    uniqueness_class: PeptideUniquenessClass
    uniqueness_score: float = Field(..., ge=0.0, le=1.0)
    selected_transition_count: int = Field(..., ge=0)
    exported_transition_count: int = Field(..., ge=0)
    assay_interference_risk_tier: TargetedAssayInterferenceRiskTier
    warning_codes: tuple[TargetedPanelWarningCode, ...] = Field(default_factory=tuple)
    warning_note: str = Field(..., min_length=1)


class ValidationPlanningPilotVarianceInput(JsonModel):
    """Pilot variance and missingness context reused for targeted validation planning."""

    model_config = ConfigDict(extra="forbid")

    entity_id: str = Field(..., min_length=1)
    protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    observed_sample_count: int = Field(..., ge=0)
    missing_fraction: float = Field(..., ge=0.0, le=1.0)
    contributing_condition_count: int = Field(..., ge=0)
    used_global_variance_fallback: bool = False
    pooled_log2_stddev: float = Field(..., ge=0.0)


class ValidationPlanningOmittedCandidateInput(JsonModel):
    """Biomarker candidate omitted from the targeted panel before planning."""

    model_config = ConfigDict(extra="forbid")

    candidate_id: str = Field(..., min_length=1)
    candidate_kind: TargetedPanelCandidateKind
    display_label: str = Field(..., min_length=1)
    target_protein_ref: str = Field(..., min_length=1)
    site_key: str | None = None
    priority_rank: int = Field(..., ge=1)
    omission_reason: str = Field(..., min_length=1)


class ValidationExperimentPlanEntry(JsonModel):
    """One assay-backed validation plan row."""

    model_config = ConfigDict(extra="forbid")

    assay_entry_id: str = Field(..., min_length=1)
    biomarker_candidate_id: str = Field(..., min_length=1)
    biomarker_candidate_kind: TargetedPanelCandidateKind
    biomarker_display_label: str = Field(..., min_length=1)
    biomarker_priority_rank: int = Field(..., ge=1)
    target_protein_ref: str = Field(..., min_length=1)
    target_protein_group_id: str = Field(..., min_length=1)
    gene_symbol: str | None = None
    peptide_sequence: str = Field(..., min_length=1)
    canonical_peptide: str = Field(..., min_length=1)
    uniqueness_class: PeptideUniquenessClass
    uniqueness_score: float = Field(..., ge=0.0, le=1.0)
    selected_transition_count: int = Field(..., ge=0)
    exported_transition_count: int = Field(..., ge=0)
    assay_interference_risk_tier: TargetedAssayInterferenceRiskTier
    assay_risk_score: float = Field(..., ge=0.0, le=1.0)
    expected_missingness_fraction: float = Field(..., ge=0.0, le=1.0)
    effect_size: float | None = None
    robustness_score: float = Field(..., ge=0.0, le=1.0)
    pilot_pooled_log2_stddev: float | None = Field(default=None, ge=0.0)
    pilot_observed_sample_count: int | None = Field(default=None, ge=0)
    planning_mode: ValidationExperimentPlanningMode
    proposed_samples_per_group: int = Field(..., ge=1)
    recommended_minimum_samples_per_group: int = Field(..., ge=1)
    underpowered: bool
    warning_codes: tuple[ValidationExperimentWarningCode, ...] = Field(
        default_factory=tuple
    )
    planning_note: str = Field(..., min_length=1)


class ValidationExperimentWarningEntry(JsonModel):
    """One explicit planning warning or omitted-candidate reminder."""

    model_config = ConfigDict(extra="forbid")

    warning_id: str = Field(..., min_length=1)
    severity: ValidationExperimentWarningSeverity
    warning_code: ValidationExperimentWarningCode
    biomarker_candidate_id: str = Field(..., min_length=1)
    assay_entry_id: str | None = None
    target_protein_ref: str = Field(..., min_length=1)
    peptide_sequence: str | None = None
    message: str = Field(..., min_length=1)


class ValidationExperimentPlanningSummary(JsonModel):
    """Compact summary over one validation planning pass."""

    model_config = ConfigDict(extra="forbid")

    biomarker_candidate_count: int = Field(..., ge=0)
    planned_target_count: int = Field(..., ge=0)
    planned_assay_count: int = Field(..., ge=0)
    omitted_candidate_count: int = Field(..., ge=0)
    proposed_samples_per_group: int = Field(..., ge=1)
    recommended_panel_samples_per_group: int = Field(..., ge=1)
    underpowered_assay_count: int = Field(..., ge=0)
    high_expected_missingness_assay_count: int = Field(..., ge=0)
    high_assay_risk_assay_count: int = Field(..., ge=0)
    pilot_backed_assay_count: int = Field(..., ge=0)
    heuristic_assay_count: int = Field(..., ge=0)
    warning_count: int = Field(..., ge=0)


class ValidationExperimentPlanningReport(JsonModel):
    """Owned targeted validation experiment planning report."""

    model_config = ConfigDict(extra="forbid")

    policy: ValidationExperimentPlanningPolicy
    summary: ValidationExperimentPlanningSummary
    plan_entries: tuple[ValidationExperimentPlanEntry, ...] = Field(
        default_factory=tuple
    )
    warnings: tuple[ValidationExperimentWarningEntry, ...] = Field(
        default_factory=tuple
    )
    note: str = Field(..., min_length=1)


__all__ = [
    "ValidationExperimentPlanEntry",
    "ValidationExperimentPlanningMode",
    "ValidationExperimentPlanningPolicy",
    "ValidationExperimentPlanningReport",
    "ValidationExperimentPlanningSummary",
    "ValidationExperimentWarningCode",
    "ValidationExperimentWarningEntry",
    "ValidationExperimentWarningSeverity",
    "ValidationPlanningBiomarkerCandidateInput",
    "ValidationPlanningOmittedCandidateInput",
    "ValidationPlanningPanelAssayInput",
    "ValidationPlanningPilotVarianceInput",
    "ValidationPlanningSelectedPeptideInput",
]

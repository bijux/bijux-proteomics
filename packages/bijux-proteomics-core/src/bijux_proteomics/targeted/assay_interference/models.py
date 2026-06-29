# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Public contracts for targeted assay interference scoring."""

from __future__ import annotations

from enum import StrEnum

from pydantic import ConfigDict, Field

from bijux_proteomics.chemistry import FragmentIonSeries
from bijux_proteomics_foundation import JsonModel


class TargetedAssayInterferenceRiskTier(StrEnum):
    """Assay interference severity tiers used before panel handoff."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class TargetedAssayInterferenceReason(StrEnum):
    """Stable reasons behind assay or transition interference downgrades."""

    SHARED_PEPTIDE = "shared_peptide"
    PANEL_FRAGMENT_OVERLAP = "panel_fragment_overlap"
    BACKGROUND_PEPTIDE_OVERLAP = "background_peptide_overlap"
    LIBRARY_FRAGMENT_OVERLAP = "library_fragment_overlap"
    LIBRARY_COELUTION_COMPETITOR = "library_coelution_competitor"
    INTRINSIC_TRANSITION_RISK = "intrinsic_transition_risk"
    INSUFFICIENT_EXPORTED_TRANSITIONS = "insufficient_exported_transitions"


class TargetedAssayInterferenceTransitionEntry(JsonModel):
    """One transition-level interference score beside the selected assay panel."""

    model_config = ConfigDict(extra="forbid")

    assay_entry_id: str = Field(..., min_length=1)
    target_protein_ref: str = Field(..., min_length=1)
    target_protein_group_id: str = Field(..., min_length=1)
    gene_symbol: str | None = None
    peptide_sequence: str = Field(..., min_length=1)
    canonical_peptide: str = Field(..., min_length=1)
    precursor_charge: int = Field(..., ge=1)
    precursor_mz: float = Field(..., gt=0.0)
    fragment_label: str = Field(..., min_length=1)
    ion_type: FragmentIonSeries
    fragment_ordinal: int = Field(..., ge=1)
    fragment_charge: int = Field(..., ge=1)
    fragment_sequence: str = Field(..., min_length=1)
    fragment_mz: float = Field(..., gt=0.0)
    expected_relative_intensity: float | None = Field(default=None, ge=0.0, le=1.0)
    selected_transition_rank: int = Field(..., ge=1)
    intrinsic_interference_risk_score: float = Field(..., ge=0.0, le=1.0)
    panel_overlap_transition_count: int = Field(..., ge=0)
    background_overlap_peptide_count: int = Field(..., ge=0)
    library_overlap_peptide_count: int = Field(..., ge=0)
    coeluting_library_overlap_peptide_count: int = Field(..., ge=0)
    interference_risk_score: float = Field(..., ge=0.0, le=1.0)
    interference_risk_tier: TargetedAssayInterferenceRiskTier
    downgrade_reasons: tuple[TargetedAssayInterferenceReason, ...] = Field(
        default_factory=tuple
    )
    export_allowed: bool
    export_caveat: str = Field(..., min_length=1)


class TargetedAssayInterferenceAssayEntry(JsonModel):
    """One assay-level interference score for targeted panel promotion."""

    model_config = ConfigDict(extra="forbid")

    assay_entry_id: str = Field(..., min_length=1)
    target_protein_ref: str = Field(..., min_length=1)
    target_protein_group_id: str = Field(..., min_length=1)
    gene_symbol: str | None = None
    peptide_sequence: str = Field(..., min_length=1)
    canonical_peptide: str = Field(..., min_length=1)
    peptide_rank: int = Field(..., ge=1)
    precursor_charge: int = Field(..., ge=1)
    precursor_mz: float = Field(..., gt=0.0)
    selected_transition_count: int = Field(..., ge=0)
    exported_transition_count: int = Field(..., ge=0)
    shared_peptide_penalty: float = Field(..., ge=0.0, le=1.0)
    panel_overlap_transition_count: int = Field(..., ge=0)
    background_overlap_peptide_count: int = Field(..., ge=0)
    library_overlap_peptide_count: int = Field(..., ge=0)
    coeluting_library_overlap_peptide_count: int = Field(..., ge=0)
    intrinsic_transition_risk_score: float = Field(..., ge=0.0, le=1.0)
    interference_risk_score: float = Field(..., ge=0.0, le=1.0)
    interference_risk_tier: TargetedAssayInterferenceRiskTier
    downgrade_reasons: tuple[TargetedAssayInterferenceReason, ...] = Field(
        default_factory=tuple
    )
    panel_export_allowed: bool
    panel_export_caveat: str = Field(..., min_length=1)
    source_library_entry_id: str | None = None


class TargetedAssayInterferencePanelEntry(JsonModel):
    """One retained transition row for pre-run targeted panel export."""

    model_config = ConfigDict(extra="forbid")

    assay_entry_id: str = Field(..., min_length=1)
    target_protein_ref: str = Field(..., min_length=1)
    target_protein_group_id: str = Field(..., min_length=1)
    gene_symbol: str | None = None
    peptide_sequence: str = Field(..., min_length=1)
    canonical_peptide: str = Field(..., min_length=1)
    precursor_charge: int = Field(..., ge=1)
    precursor_mz: float = Field(..., gt=0.0)
    fragment_label: str = Field(..., min_length=1)
    fragment_mz: float = Field(..., gt=0.0)
    expected_relative_intensity: float | None = Field(default=None, ge=0.0, le=1.0)
    assay_interference_risk_tier: TargetedAssayInterferenceRiskTier
    transition_interference_risk_tier: TargetedAssayInterferenceRiskTier
    export_caveat: str = Field(..., min_length=1)


class TargetedAssayInterferenceSummary(JsonModel):
    """Compact accounting over one targeted assay interference scoring pass."""

    model_config = ConfigDict(extra="forbid")

    assay_entry_count: int = Field(..., ge=0)
    low_risk_assay_count: int = Field(..., ge=0)
    medium_risk_assay_count: int = Field(..., ge=0)
    high_risk_assay_count: int = Field(..., ge=0)
    downgraded_assay_count: int = Field(..., ge=0)
    panel_export_assay_count: int = Field(..., ge=0)
    transition_entry_count: int = Field(..., ge=0)
    panel_export_transition_count: int = Field(..., ge=0)


class TargetedAssayInterferenceReport(JsonModel):
    """Targeted assay interference report before laboratory panel export."""

    model_config = ConfigDict(extra="forbid")

    protease: str = Field(..., min_length=1)
    missed_cleavages: int = Field(..., ge=0)
    precursor_tolerance_da: float = Field(..., gt=0.0)
    fragment_tolerance_da: float = Field(..., gt=0.0)
    coelution_rt_window_minutes: float = Field(..., gt=0.0)
    minimum_export_transitions: int = Field(..., ge=1)
    summary: TargetedAssayInterferenceSummary
    assay_entries: tuple[TargetedAssayInterferenceAssayEntry, ...] = Field(
        default_factory=tuple
    )
    transition_entries: tuple[TargetedAssayInterferenceTransitionEntry, ...] = Field(
        default_factory=tuple
    )
    panel_entries: tuple[TargetedAssayInterferencePanelEntry, ...] = Field(
        default_factory=tuple
    )
    note: str = Field(..., min_length=1)


__all__ = [
    "TargetedAssayInterferenceAssayEntry",
    "TargetedAssayInterferencePanelEntry",
    "TargetedAssayInterferenceReason",
    "TargetedAssayInterferenceReport",
    "TargetedAssayInterferenceRiskTier",
    "TargetedAssayInterferenceSummary",
    "TargetedAssayInterferenceTransitionEntry",
]

# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Summary contracts for biological result report bundles."""

from __future__ import annotations

from pydantic import ConfigDict, Field

from bijux_proteomics.domain.confidence import ConfidenceTier
from bijux_proteomics_foundation import JsonModel


class BiologicalResultReportSummary(JsonModel):
    """Compact summary over one biological result bundle."""

    model_config = ConfigDict(extra="forbid")

    protein_count: int = Field(..., ge=0)
    significant_protein_count: int = Field(..., ge=0)
    sample_count: int = Field(..., ge=0)
    annotation_entry_count: int = Field(..., ge=0)
    annotation_unmapped_count: int = Field(..., ge=0)
    protein_card_count: int = Field(..., ge=0)
    warning_card_count: int = Field(..., ge=0)
    tissue_mismatch_warning_count: int = Field(..., ge=0)
    cohort_blocked_stratum_count: int = Field(..., ge=0)
    cohort_subgroup_effect_count: int = Field(..., ge=0)
    cohort_interaction_candidate_count: int = Field(..., ge=0)
    experiment_confidence_score: float = Field(..., ge=0.0, le=1.0)
    experiment_confidence_tier: ConfidenceTier
    low_confidence_component_count: int = Field(..., ge=0)
    high_confidence_section_count: int = Field(..., ge=0)
    moderate_confidence_section_count: int = Field(..., ge=0)
    weak_confidence_section_count: int = Field(..., ge=0)
    exploratory_section_count: int = Field(..., ge=0)
    invalid_section_count: int = Field(..., ge=0)
    context_entry_count: int = Field(..., ge=0)
    context_unmapped_count: int = Field(..., ge=0)
    context_term_count: int = Field(..., ge=0)
    go_enriched_term_count: int = Field(..., ge=0)
    pathway_enriched_entry_count: int = Field(..., ge=0)
    complex_enriched_entry_count: int = Field(..., ge=0)
    heatmap_entity_count: int = Field(..., ge=0)
    pca_outlier_sample_count: int = Field(..., ge=0)


__all__ = ["BiologicalResultReportSummary"]

# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi
"""Stable identifiers, labels, and titles for biological report sections."""

from __future__ import annotations

from enum import StrEnum

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel


class BiologicalReportSectionKey(StrEnum):
    """Stable identifiers for biological report sections with scientific confidence."""

    EXPERIMENT_CONFIDENCE = "experiment_confidence"
    EVIDENCE_AWARE_RANKING = "evidence_aware_ranking"
    VALIDATED_BIOLOGICAL_CLAIMS = "validated_biological_claims"
    BIOLOGICAL_HYPOTHESES = "biological_hypotheses"
    ENRICHMENT_FOREGROUND_BACKGROUND = "enrichment_foreground_background"
    REGULATOR_INFERENCE = "regulator_inference"
    DRUG_TARGET_INTERPRETATION = "drug_target_interpretation"
    DISEASE_PHENOTYPE_INTERPRETATION = "disease_phenotype_interpretation"
    COHORT_STRATIFICATION = "cohort_stratification"
    TISSUE_CELL_TYPE_CONTEXT = "tissue_cell_type_context"
    COMPARTMENT_BIOLOGY = "compartment_biology"
    PATHWAY_ACTIVITY = "pathway_activity"
    COMPLEX_ACTIVITY = "complex_activity"
    PROTEIN_MECHANISM_CARDS = "protein_mechanism_cards"


class BiologicalReportSectionConfidenceLabel(StrEnum):
    """Derived confidence labels for scientific report sections."""

    HIGH = "high"
    MODERATE = "moderate"
    WEAK = "weak"
    EXPLORATORY = "exploratory"
    INVALID = "invalid"


class BiologicalReportSectionConfidenceEntry(JsonModel):
    """One deterministic confidence assignment for a biological report section."""

    model_config = ConfigDict(extra="forbid")

    section_key: BiologicalReportSectionKey
    section_title: str = Field(..., min_length=1)
    confidence_label: BiologicalReportSectionConfidenceLabel
    rationale: str = Field(..., min_length=1)


_BIOLOGICAL_REPORT_SECTION_TITLES = {
    BiologicalReportSectionKey.EXPERIMENT_CONFIDENCE: "Experiment confidence",
    BiologicalReportSectionKey.EVIDENCE_AWARE_RANKING: "Evidence-aware ranking",
    BiologicalReportSectionKey.VALIDATED_BIOLOGICAL_CLAIMS: "Validated biological claims",
    BiologicalReportSectionKey.BIOLOGICAL_HYPOTHESES: "Biological hypotheses",
    BiologicalReportSectionKey.ENRICHMENT_FOREGROUND_BACKGROUND: (
        "Enrichment foreground/background model"
    ),
    BiologicalReportSectionKey.REGULATOR_INFERENCE: "Regulator inference",
    BiologicalReportSectionKey.DRUG_TARGET_INTERPRETATION: "Drug-target interpretation",
    BiologicalReportSectionKey.DISEASE_PHENOTYPE_INTERPRETATION: (
        "Disease and phenotype interpretation"
    ),
    BiologicalReportSectionKey.COHORT_STRATIFICATION: "Cohort stratification",
    BiologicalReportSectionKey.TISSUE_CELL_TYPE_CONTEXT: "Tissue and cell-type context",
    BiologicalReportSectionKey.COMPARTMENT_BIOLOGY: "Compartment biology",
    BiologicalReportSectionKey.PATHWAY_ACTIVITY: "Pathway activity",
    BiologicalReportSectionKey.COMPLEX_ACTIVITY: "Complex activity",
    BiologicalReportSectionKey.PROTEIN_MECHANISM_CARDS: "Protein mechanism cards",
}

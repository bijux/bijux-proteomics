# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi
"""Section-block HTML for biological result reports."""

from __future__ import annotations

from ..biological_report_bundle_contracts import (
    BiologicalResultReportBundle,
)
from ..biological_report_section_metadata import (
    BiologicalReportSectionKey,
)
from .contextual_tables import (
    _render_cohort_stratification_table_html,
    _render_compartment_biology_table_html,
    _render_complex_activity_table_html,
    _render_disease_phenotype_table_html,
    _render_drug_target_table_html,
    _render_pathway_activity_table_html,
    _render_regulator_inference_table_html,
    _render_tissue_cell_type_context_table_html,
)
from .scientific_tables import (
    _render_biological_claim_validation_table_html,
    _render_biological_hypothesis_table_html,
    _render_evidence_aware_ranking_table_html,
    _render_experiment_confidence_table_html,
    _render_foreground_background_model_table_html,
    _render_protein_mechanism_card_table_html,
)
from .support import (
    _render_biological_report_section_confidence_table_html,
    _render_section_heading_html,
)


def _render_biological_report_section_blocks_html(
    report: BiologicalResultReportBundle,
) -> str:
    section_confidence_html = _render_biological_report_section_confidence_table_html(
        report
    )
    confidence_table_html = _render_experiment_confidence_table_html(report)
    ranking_table_html = _render_evidence_aware_ranking_table_html(report)
    claim_validation_html = _render_biological_claim_validation_table_html(report)
    hypothesis_html = _render_biological_hypothesis_table_html(report)
    foreground_background_html = _render_foreground_background_model_table_html(report)
    regulator_inference_html = _render_regulator_inference_table_html(report)
    drug_target_html = _render_drug_target_table_html(report)
    disease_phenotype_html = _render_disease_phenotype_table_html(report)
    cohort_stratification_html = _render_cohort_stratification_table_html(report)
    tissue_context_html = _render_tissue_cell_type_context_table_html(report)
    compartment_biology_html = _render_compartment_biology_table_html(report)
    pathway_activity_html = _render_pathway_activity_table_html(report)
    complex_activity_html = _render_complex_activity_table_html(report)
    card_table_html = _render_protein_mechanism_card_table_html(report)

    return (
        "<h2>Section confidence</h2>"
        f"{section_confidence_html}"
        f"{_render_section_heading_html(report, BiologicalReportSectionKey.EXPERIMENT_CONFIDENCE)}"
        f"{confidence_table_html}"
        f"{_render_section_heading_html(report, BiologicalReportSectionKey.EVIDENCE_AWARE_RANKING)}"
        f"{ranking_table_html}"
        f"{_render_section_heading_html(report, BiologicalReportSectionKey.VALIDATED_BIOLOGICAL_CLAIMS)}"
        f"{claim_validation_html}"
        f"{_render_section_heading_html(report, BiologicalReportSectionKey.BIOLOGICAL_HYPOTHESES)}"
        f"{hypothesis_html}"
        f"{_render_section_heading_html(report, BiologicalReportSectionKey.ENRICHMENT_FOREGROUND_BACKGROUND)}"
        f"{foreground_background_html}"
        f"{_render_section_heading_html(report, BiologicalReportSectionKey.REGULATOR_INFERENCE)}"
        f"{regulator_inference_html}"
        f"{_render_section_heading_html(report, BiologicalReportSectionKey.DRUG_TARGET_INTERPRETATION)}"
        f"{drug_target_html}"
        f"{_render_section_heading_html(report, BiologicalReportSectionKey.DISEASE_PHENOTYPE_INTERPRETATION)}"
        f"{disease_phenotype_html}"
        f"{_render_section_heading_html(report, BiologicalReportSectionKey.COHORT_STRATIFICATION)}"
        f"{cohort_stratification_html}"
        f"{_render_section_heading_html(report, BiologicalReportSectionKey.TISSUE_CELL_TYPE_CONTEXT)}"
        f"{tissue_context_html}"
        f"{_render_section_heading_html(report, BiologicalReportSectionKey.COMPARTMENT_BIOLOGY)}"
        f"{compartment_biology_html}"
        f"{_render_section_heading_html(report, BiologicalReportSectionKey.PATHWAY_ACTIVITY)}"
        f"{pathway_activity_html}"
        f"{_render_section_heading_html(report, BiologicalReportSectionKey.COMPLEX_ACTIVITY)}"
        f"{complex_activity_html}"
        f"{_render_section_heading_html(report, BiologicalReportSectionKey.PROTEIN_MECHANISM_CARDS)}"
        f"{card_table_html}"
    )


__all__ = ["_render_biological_report_section_blocks_html"]

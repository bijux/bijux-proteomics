# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi
"""Review and claim report assembly for biological quant-table workflows."""

from __future__ import annotations

from pathlib import Path
from typing import NamedTuple

from bijux_proteomics.review.explanations.volcano_plots import VolcanoReviewPolicy
from bijux_proteomics.study import (
    LcmsRunQcReport,
    QcRunAssessmentReport,
)
from bijux_proteomics.workflow.reports.biological_report_experiment_review import (
    _build_biological_experiment_review_reports,
)
from bijux_proteomics.workflow.reports.quant_table.interpretation_reports import (
    _build_biological_quant_table_interpretation_reports,
)


class BiologicalQuantTableReviewReports(NamedTuple):
    """Review and interpretation reports derived from supporting analyses."""

    volcano_review: object
    heatmap_report: object
    sample_exploration_report: object
    cohort_stratification_report: object | None
    experiment_confidence_report: object
    evidence_aware_ranking_report: object | None
    claim_validation_report: object
    biological_hypothesis_report: object


def _build_biological_quant_table_review_reports(
    *,
    normalized_table: object,
    differential_report: object,
    experiment_design: object,
    design_entries: tuple[object, ...],
    active_selection_policy: object,
    protein_cards: object,
    protein_mechanism_cards: object,
    pathway_activity_report: object | None,
    pathway_enrichment_report: object | None,
    regulator_inference_report: object | None,
    resolved_condition_a: str,
    resolved_condition_b: str,
    protocol_context_tsv_path: Path | None,
    run_qc_reports: tuple[LcmsRunQcReport, ...],
    run_qc_assessments: tuple[QcRunAssessmentReport, ...],
    volcano_policy: VolcanoReviewPolicy | None,
) -> BiologicalQuantTableReviewReports:
    experiment_review_reports = _build_biological_experiment_review_reports(
        normalized_table=normalized_table,
        differential_report=differential_report,
        experiment_design=experiment_design,
        design_entries=design_entries,
        selection_policy=active_selection_policy,
        protein_cards=protein_cards,
        resolved_condition_a=resolved_condition_a,
        resolved_condition_b=resolved_condition_b,
        protocol_context_tsv_path=protocol_context_tsv_path,
        run_qc_reports=run_qc_reports,
        run_qc_assessments=run_qc_assessments,
        volcano_policy=volcano_policy,
    )
    interpretation_reports = _build_biological_quant_table_interpretation_reports(
        differential_report=differential_report,
        active_selection_policy=active_selection_policy,
        protein_cards=protein_cards,
        protein_mechanism_cards=protein_mechanism_cards,
        pathway_activity_report=pathway_activity_report,
        pathway_enrichment_report=pathway_enrichment_report,
        regulator_inference_report=regulator_inference_report,
        experiment_review_reports=experiment_review_reports,
    )
    return BiologicalQuantTableReviewReports(
        volcano_review=experiment_review_reports.volcano_review,
        heatmap_report=experiment_review_reports.heatmap_report,
        sample_exploration_report=experiment_review_reports.sample_exploration_report,
        cohort_stratification_report=(
            experiment_review_reports.cohort_stratification_report
        ),
        experiment_confidence_report=(
            experiment_review_reports.experiment_confidence_report
        ),
        evidence_aware_ranking_report=(
            interpretation_reports.evidence_aware_ranking_report
        ),
        claim_validation_report=interpretation_reports.claim_validation_report,
        biological_hypothesis_report=(
            interpretation_reports.biological_hypothesis_report
        ),
    )


__all__ = [
    "BiologicalQuantTableReviewReports",
    "_build_biological_quant_table_review_reports",
]

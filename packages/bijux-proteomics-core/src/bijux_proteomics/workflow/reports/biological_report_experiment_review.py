# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owned experiment-level review outputs for biological report bundles."""

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics.quantification.contracts import (
    DifferentialAbundanceReport,
    LabelFreeQuantTable,
)
from bijux_proteomics.review.explanations.volcano_plots import (
    VolcanoReviewPolicy,
)
from bijux_proteomics.study import (
    ExperimentDesign,
    LcmsRunQcReport,
    QcRunAssessmentReport,
)
from bijux_proteomics.workflow.cards.protein_evidence_cards import (
    ProteinEvidenceCardReport,
)
from bijux_proteomics.workflow.reports.biological_report_experiment_confidence_assembly import (
    _build_biological_experiment_confidence_report,
)
from bijux_proteomics.workflow.reports.biological_report_experiment_diagnostics import (
    _build_biological_experiment_diagnostics_reports,
)
from bijux_proteomics.workflow.reports.biological_report_experiment_review_contracts import (
    BiologicalExperimentReviewReports,
)
from bijux_proteomics.workflow.reports.biological_report_selection_policy import (
    BiologicalResultSelectionPolicy,
)


def _build_biological_experiment_review_reports(
    *,
    normalized_table: LabelFreeQuantTable,
    differential_report: DifferentialAbundanceReport,
    experiment_design: ExperimentDesign,
    design_entries: tuple[ExperimentalDesignEntry, ...],
    selection_policy: BiologicalResultSelectionPolicy,
    protein_cards: ProteinEvidenceCardReport,
    resolved_condition_a: str,
    resolved_condition_b: str,
    protocol_context_tsv_path: Path | None,
    run_qc_reports: tuple[LcmsRunQcReport, ...],
    run_qc_assessments: tuple[QcRunAssessmentReport, ...],
    volcano_policy: VolcanoReviewPolicy | None,
) -> BiologicalExperimentReviewReports:
    diagnostics_reports = _build_biological_experiment_diagnostics_reports(
        normalized_table=normalized_table,
        differential_report=differential_report,
        experiment_design=experiment_design,
        design_entries=design_entries,
        selection_policy=selection_policy,
        resolved_condition_a=resolved_condition_a,
        resolved_condition_b=resolved_condition_b,
        volcano_policy=volcano_policy,
    )
    experiment_confidence_report = _build_biological_experiment_confidence_report(
        normalized_table=normalized_table,
        experiment_design=experiment_design,
        design_entries=design_entries,
        protein_cards=protein_cards,
        resolved_condition_a=resolved_condition_a,
        resolved_condition_b=resolved_condition_b,
        protocol_context_tsv_path=protocol_context_tsv_path,
        run_qc_reports=run_qc_reports,
        run_qc_assessments=run_qc_assessments,
    )
    return BiologicalExperimentReviewReports(
        volcano_review=diagnostics_reports.volcano_review,
        heatmap_report=diagnostics_reports.heatmap_report,
        sample_exploration_report=diagnostics_reports.sample_exploration_report,
        cohort_stratification_report=(diagnostics_reports.cohort_stratification_report),
        experiment_confidence_report=experiment_confidence_report,
    )


__all__ = ["_build_biological_experiment_review_reports"]

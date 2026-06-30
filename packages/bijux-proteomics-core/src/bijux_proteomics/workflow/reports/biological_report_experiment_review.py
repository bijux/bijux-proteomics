# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owned experiment-level review outputs for biological report bundles."""

from __future__ import annotations

from pathlib import Path
from typing import NamedTuple

from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics.lab.protocol_context import (
    parse_lab_protocol_context_table,
    require_single_lab_protocol_context,
)
from bijux_proteomics.quantification.contracts import (
    DifferentialAbundanceReport,
    LabelFreeQuantTable,
)
from bijux_proteomics.quantification.missingness import (
    build_missingness_condition_summary_report,
)
from bijux_proteomics.quantification.provenance import (
    HeatmapMissingValuePolicy,
    HeatmapPreparationPolicy,
    HeatmapPreparationReport,
    SampleExplorationReport,
    build_heatmap_preparation_report,
    build_sample_exploration_report,
)
from bijux_proteomics.quantification.statistics import build_power_estimation_report
from bijux_proteomics.review.explanations.volcano_plots import (
    VolcanoReviewPolicy,
    VolcanoReviewReport,
    build_quantification_volcano_review,
)
from bijux_proteomics.study import (
    ExperimentConfidenceReport,
    ExperimentDesign,
    LcmsRunQcReport,
    QcRunAssessmentReport,
    build_experiment_confidence_report,
    build_experiment_feasibility_report,
    build_protocol_consistency_report,
)
from bijux_proteomics.workflow.cards.protein_evidence_cards import (
    ProteinEvidenceCardReport,
)
from bijux_proteomics.workflow.reports.biological_report_contrast_selection import (
    _select_heatmap_entity_ids,
)
from bijux_proteomics.workflow.reports.biological_report_selection_policy import (
    BiologicalResultSelectionPolicy,
)
from bijux_proteomics.workflow.studies.cohort_stratification import (
    CohortStratificationReport,
    build_cohort_stratification_report,
)


class BiologicalExperimentReviewReports(NamedTuple):
    """Experiment-level review artifacts for one biological report bundle."""

    volcano_review: VolcanoReviewReport
    heatmap_report: HeatmapPreparationReport
    sample_exploration_report: SampleExplorationReport
    cohort_stratification_report: CohortStratificationReport | None
    experiment_confidence_report: ExperimentConfidenceReport


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
    volcano_review = build_quantification_volcano_review(
        differential_report,
        protein_refs_by_entity=normalized_table.entity_protein_refs,
        policy=volcano_policy,
    )
    selected_entity_ids = _select_heatmap_entity_ids(
        differential_report,
        policy=selection_policy,
    )
    heatmap_report = build_heatmap_preparation_report(
        normalized_table,
        design_entries=design_entries,
        policy=HeatmapPreparationPolicy(
            entity_ids=selected_entity_ids,
            min_observed_fraction=selection_policy.heatmap_min_observed_fraction,
            max_entity_count=selection_policy.heatmap_max_entity_count,
            z_score_rows=True,
            missing_value_policy=HeatmapMissingValuePolicy.FILL_ROW_MEDIAN,
        ),
    )
    sample_exploration_report = build_sample_exploration_report(
        normalized_table,
        design_entries,
    )
    cohort_stratification_report: CohortStratificationReport | None = (
        build_cohort_stratification_report(
            normalized_table,
            experiment_design,
            condition_a=resolved_condition_a,
            condition_b=resolved_condition_b,
        )
    )
    if (
        cohort_stratification_report is not None
        and cohort_stratification_report.summary.field_count == 0
    ):
        cohort_stratification_report = None
    feasibility_report = build_experiment_feasibility_report(
        experiment_design,
        condition_a=resolved_condition_a,
        condition_b=resolved_condition_b,
    )
    protocol_consistency_report = None
    if protocol_context_tsv_path is not None:
        protocol_consistency_report = build_protocol_consistency_report(
            require_single_lab_protocol_context(
                parse_lab_protocol_context_table(protocol_context_tsv_path)
            ),
            run_qc_report=run_qc_reports[0] if len(run_qc_reports) == 1 else None,
        )
    experiment_confidence_report = build_experiment_confidence_report(
        experiment_design,
        validity_report=feasibility_report.validity_report,
        feasibility_report=feasibility_report,
        missingness_condition_summary_report=build_missingness_condition_summary_report(
            normalized_table,
            design_entries=design_entries,
        ),
        power_estimation_report=build_power_estimation_report(
            normalized_table,
            design_entries,
        ),
        run_qc_reports=run_qc_reports,
        run_qc_assessments=run_qc_assessments,
        protocol_consistency_report=protocol_consistency_report,
        warning_card_count=protein_cards.summary.warning_card_count,
        protein_card_count=protein_cards.summary.protein_result_count,
    )
    return BiologicalExperimentReviewReports(
        volcano_review=volcano_review,
        heatmap_report=heatmap_report,
        sample_exploration_report=sample_exploration_report,
        cohort_stratification_report=cohort_stratification_report,
        experiment_confidence_report=experiment_confidence_report,
    )

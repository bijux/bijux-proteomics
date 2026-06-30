# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Experiment-level diagnostic review outputs for biological report bundles."""

from __future__ import annotations

from typing import NamedTuple

from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics.quantification.contracts import (
    DifferentialAbundanceReport,
    LabelFreeQuantTable,
)
from bijux_proteomics.quantification.provenance import (
    HeatmapMissingValuePolicy,
    HeatmapPreparationPolicy,
    HeatmapPreparationReport,
    SampleExplorationReport,
    build_heatmap_preparation_report,
    build_sample_exploration_report,
)
from bijux_proteomics.review.explanations.volcano_plots import (
    VolcanoReviewPolicy,
    VolcanoReviewReport,
    build_quantification_volcano_review,
)
from bijux_proteomics.study import ExperimentDesign
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


class BiologicalExperimentDiagnosticsReports(NamedTuple):
    """Experiment-level diagnostic artifacts for one biological report bundle."""

    volcano_review: VolcanoReviewReport
    heatmap_report: HeatmapPreparationReport
    sample_exploration_report: SampleExplorationReport
    cohort_stratification_report: CohortStratificationReport | None


def _build_biological_experiment_diagnostics_reports(
    *,
    normalized_table: LabelFreeQuantTable,
    differential_report: DifferentialAbundanceReport,
    experiment_design: ExperimentDesign,
    design_entries: tuple[ExperimentalDesignEntry, ...],
    selection_policy: BiologicalResultSelectionPolicy,
    resolved_condition_a: str,
    resolved_condition_b: str,
    volcano_policy: VolcanoReviewPolicy | None,
) -> BiologicalExperimentDiagnosticsReports:
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
    return BiologicalExperimentDiagnosticsReports(
        volcano_review=volcano_review,
        heatmap_report=heatmap_report,
        sample_exploration_report=sample_exploration_report,
        cohort_stratification_report=cohort_stratification_report,
    )


__all__ = [
    "BiologicalExperimentDiagnosticsReports",
    "_build_biological_experiment_diagnostics_reports",
]

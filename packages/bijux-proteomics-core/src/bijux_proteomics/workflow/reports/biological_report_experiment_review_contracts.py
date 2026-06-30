# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Experiment-review contracts for biological report bundles."""

from __future__ import annotations

from typing import NamedTuple

from bijux_proteomics.quantification.provenance import (
    HeatmapPreparationReport,
    SampleExplorationReport,
)
from bijux_proteomics.review.explanations.volcano_plots import VolcanoReviewReport
from bijux_proteomics.study import ExperimentConfidenceReport
from bijux_proteomics.workflow.studies.cohort_stratification import (
    CohortStratificationReport,
)


class BiologicalExperimentReviewReports(NamedTuple):
    """Experiment-level review artifacts for one biological report bundle."""

    volcano_review: VolcanoReviewReport
    heatmap_report: HeatmapPreparationReport
    sample_exploration_report: SampleExplorationReport
    cohort_stratification_report: CohortStratificationReport | None
    experiment_confidence_report: ExperimentConfidenceReport


__all__ = ["BiologicalExperimentReviewReports"]

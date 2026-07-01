# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Study-result package surfaces grouped by durable ownership boundaries."""

from __future__ import annotations

from bijux_proteomics.workflow.studies.study_results.advanced import (
    build_proteomics_study_result_from_advanced_diann_workflow_report,
    build_proteomics_study_result_from_advanced_fragpipe_workflow_report,
    build_proteomics_study_result_from_advanced_maxquant_workflow_report,
    build_proteomics_study_result_from_advanced_ptm_workflow_report,
    build_proteomics_study_result_from_advanced_tmt_workflow_report,
)
from bijux_proteomics.workflow.studies.study_results.dispatch import (
    build_proteomics_study_result,
    build_proteomics_study_result_from_run_bundle,
)
from bijux_proteomics.workflow.studies.study_results.label_free import (
    build_proteomics_study_result_from_biological_report_bundle,
    build_proteomics_study_result_from_dda_workflow_bundle,
    build_proteomics_study_result_from_diann_workflow_bundle,
    build_proteomics_study_result_from_maxquant_workflow_bundle,
)
from bijux_proteomics.workflow.studies.study_results.models import (
    ProteomicsStudyCardKind,
    ProteomicsStudyCardSurface,
    ProteomicsStudyConclusionEntry,
    ProteomicsStudyConclusionKind,
    ProteomicsStudyDesignEntry,
    ProteomicsStudyDesignSnapshot,
    ProteomicsStudyKind,
    ProteomicsStudyMatrixKind,
    ProteomicsStudyMatrixSurface,
    ProteomicsStudyQcKind,
    ProteomicsStudyQcSurface,
    ProteomicsStudyResult,
    ProteomicsStudyResultSummary,
    ProteomicsStudyStatisticKind,
    ProteomicsStudyStatisticSurface,
)
from bijux_proteomics.workflow.studies.study_results.modification import (
    build_proteomics_study_result_from_ptm_workflow_bundle,
)
from bijux_proteomics.workflow.studies.study_results.multiplex import (
    build_proteomics_study_result_from_tmt_workflow_bundle,
)
from bijux_proteomics.workflow.studies.study_results.validation import (
    build_proteomics_study_result_from_targeted_validation_workflow_report,
)

__all__ = [
    "ProteomicsStudyCardKind",
    "ProteomicsStudyCardSurface",
    "ProteomicsStudyConclusionEntry",
    "ProteomicsStudyConclusionKind",
    "ProteomicsStudyDesignEntry",
    "ProteomicsStudyDesignSnapshot",
    "ProteomicsStudyKind",
    "ProteomicsStudyMatrixKind",
    "ProteomicsStudyMatrixSurface",
    "ProteomicsStudyQcKind",
    "ProteomicsStudyQcSurface",
    "ProteomicsStudyResult",
    "ProteomicsStudyResultSummary",
    "ProteomicsStudyStatisticKind",
    "ProteomicsStudyStatisticSurface",
    "build_proteomics_study_result",
    "build_proteomics_study_result_from_advanced_diann_workflow_report",
    "build_proteomics_study_result_from_advanced_fragpipe_workflow_report",
    "build_proteomics_study_result_from_advanced_maxquant_workflow_report",
    "build_proteomics_study_result_from_advanced_ptm_workflow_report",
    "build_proteomics_study_result_from_advanced_tmt_workflow_report",
    "build_proteomics_study_result_from_biological_report_bundle",
    "build_proteomics_study_result_from_dda_workflow_bundle",
    "build_proteomics_study_result_from_diann_workflow_bundle",
    "build_proteomics_study_result_from_maxquant_workflow_bundle",
    "build_proteomics_study_result_from_ptm_workflow_bundle",
    "build_proteomics_study_result_from_run_bundle",
    "build_proteomics_study_result_from_targeted_validation_workflow_report",
    "build_proteomics_study_result_from_tmt_workflow_bundle",
]

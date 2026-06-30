# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Multiplexed study-result builders."""

from __future__ import annotations

from bijux_proteomics.workflow.pipelines.tmt_experiment_workflow import (
    TmtExperimentWorkflowBundle,
)
from bijux_proteomics.workflow.studies.study_results.assembly import (
    _build_study_result,
)
from bijux_proteomics.workflow.studies.study_results.design import (
    _design_from_tmt_workflow,
)
from bijux_proteomics.workflow.studies.study_results.models import (
    ProteomicsStudyCardSurface,
    ProteomicsStudyKind,
    ProteomicsStudyMatrixKind,
    ProteomicsStudyMatrixSurface,
    ProteomicsStudyQcKind,
    ProteomicsStudyQcSurface,
    ProteomicsStudyResult,
    ProteomicsStudyStatisticKind,
    ProteomicsStudyStatisticSurface,
)


def build_proteomics_study_result_from_tmt_workflow_bundle(
    bundle: TmtExperimentWorkflowBundle,
) -> ProteomicsStudyResult:
    """Normalize one TMT workflow bundle into a study result."""

    report = bundle.report
    matrix_surfaces = []
    if report.tmt_matrix_report is not None:
        matrix_surfaces.append(
            ProteomicsStudyMatrixSurface(
                surface_name="tmt_matrix_report",
                kind=ProteomicsStudyMatrixKind.REPORTER_CHANNEL,
                entity_count=report.tmt_matrix_report.summary.protein_row_count,
                sample_count=report.summary.sample_count,
                note=report.tmt_matrix_report.note,
            )
        )
    if report.tmt_ratio_report is not None:
        matrix_surfaces.append(
            ProteomicsStudyMatrixSurface(
                surface_name="tmt_ratio_report",
                kind=ProteomicsStudyMatrixKind.PROTEIN_RATIO,
                entity_count=report.summary.protein_ratio_count,
                sample_count=report.summary.sample_count,
                note=report.tmt_ratio_report.note,
            )
        )
    return _build_study_result(
        study_kind=ProteomicsStudyKind.TMT,
        source_surface="TmtExperimentWorkflowBundle",
        design=_design_from_tmt_workflow(bundle),
        matrix_surfaces=tuple(matrix_surfaces),
        statistic_surfaces=(
            ProteomicsStudyStatisticSurface(
                surface_name="differential_analysis_report",
                kind=ProteomicsStudyStatisticKind.DIFFERENTIAL_LABEL_BASED,
                entity_count=(
                    0
                    if report.differential_analysis_report.differential_abundance_report
                    is None
                    else len(
                        report.differential_analysis_report.differential_abundance_report.entries
                    )
                ),
                significant_entity_count=(
                    0
                    if report.differential_analysis_report.differential_abundance_report
                    is None
                    else sum(
                        1
                        for entry in report.differential_analysis_report.differential_abundance_report.entries
                        if entry.adjusted_p_value is not None
                        and entry.adjusted_p_value <= 0.1
                    )
                ),
                note=report.differential_analysis_report.note,
            ),
        ),
        qc_surfaces=(
            ProteomicsStudyQcSurface(
                surface_name="metadata_validation_report",
                kind=ProteomicsStudyQcKind.TMT_METADATA_VALIDATION,
                issue_count=bundle.summary.missing_source_channel_count,
                note=bundle.metadata_validation_report.note,
            ),
            ProteomicsStudyQcSurface(
                surface_name="sample_qc_entries",
                kind=ProteomicsStudyQcKind.LABEL_BASED_SAMPLE_QC,
                issue_count=bundle.summary.sample_qc_entry_count,
                note="tmt workflow preserves sample-level multiplex qc entries",
            ),
        ),
        card_surfaces=(),
        biological_conclusions=(),
        label_based_report=report,
        note=(
            "study result keeps tmt design, reporter matrix, ratio, differential, "
            "and multiplex qc surfaces on one comparable object"
        ),
    )


__all__ = ["build_proteomics_study_result_from_tmt_workflow_bundle"]

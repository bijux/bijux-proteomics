# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Label-free and direct-biology study-result builders."""

from __future__ import annotations

from bijux_proteomics.workflow.pipelines.dda_biological_workflow import (
    DdaBiologicalWorkflowBundle,
)
from bijux_proteomics.workflow.pipelines.diann_biological_workflow import (
    DiannBiologicalWorkflowBundle,
)
from bijux_proteomics.workflow.pipelines.maxquant_biological_workflow import (
    MaxquantBiologicalWorkflowBundle,
)
from bijux_proteomics.workflow.reports.biological_reporting import (
    BiologicalResultReportBundle,
)
from bijux_proteomics.workflow.studies.study_results.assembly import (
    _biological_card_surfaces,
    _biological_conclusions_from_biological_report,
    _build_study_result,
)
from bijux_proteomics.workflow.studies.study_results.design import (
    _design_from_biological_report,
)
from bijux_proteomics.workflow.studies.study_results.models import (
    ProteomicsStudyCardKind,
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


def build_proteomics_study_result_from_biological_report_bundle(
    report: BiologicalResultReportBundle,
) -> ProteomicsStudyResult:
    """Normalize one direct biological-report bundle into a study result."""

    return _build_study_result(
        study_kind=ProteomicsStudyKind.LABEL_FREE,
        source_surface="BiologicalResultReportBundle",
        design=_design_from_biological_report(report),
        matrix_surfaces=(
            ProteomicsStudyMatrixSurface(
                surface_name="heatmap_report",
                kind=ProteomicsStudyMatrixKind.HEATMAP_REVIEW,
                entity_count=report.heatmap_report.summary.output_entity_count,
                sample_count=report.heatmap_report.summary.sample_count,
                note=report.heatmap_report.note,
            ),
        ),
        statistic_surfaces=(
            ProteomicsStudyStatisticSurface(
                surface_name="differential_report",
                kind=ProteomicsStudyStatisticKind.DIFFERENTIAL_PROTEIN,
                entity_count=len(report.differential_report.entries),
                significant_entity_count=report.summary.significant_protein_count,
                note="biological report preserves differential protein statistics",
            ),
        ),
        qc_surfaces=(
            ProteomicsStudyQcSurface(
                surface_name="sample_exploration_report",
                kind=ProteomicsStudyQcKind.SAMPLE_EXPLORATION,
                issue_count=report.summary.pca_outlier_sample_count,
                note=report.sample_exploration_report.note,
            ),
            ProteomicsStudyQcSurface(
                surface_name="experiment_confidence_report",
                kind=ProteomicsStudyQcKind.EXPERIMENT_CONFIDENCE,
                issue_count=report.summary.low_confidence_component_count,
                note=report.experiment_confidence_report.note,
            ),
        ),
        card_surfaces=(
            ProteomicsStudyCardSurface(
                surface_name="protein_cards",
                kind=ProteomicsStudyCardKind.PROTEIN_EVIDENCE,
                card_count=report.summary.protein_card_count,
                warning_count=report.summary.warning_card_count,
                note=report.protein_cards.note,
            ),
            ProteomicsStudyCardSurface(
                surface_name="protein_mechanism_cards",
                kind=ProteomicsStudyCardKind.PROTEIN_MECHANISM,
                card_count=report.protein_mechanism_cards.summary.card_count,
                warning_count=report.protein_mechanism_cards.summary.warning_card_count,
                note=report.protein_mechanism_cards.note,
            ),
        ),
        biological_conclusions=_biological_conclusions_from_biological_report(report),
        biological_report=report,
        note=(
            "study result preserves direct biological reporting surfaces so label-free "
            "studies can be compared without relying on export directories alone"
        ),
    )


def build_proteomics_study_result_from_dda_workflow_bundle(
    bundle: DdaBiologicalWorkflowBundle,
) -> ProteomicsStudyResult:
    """Normalize one DDA workflow bundle into a study result."""

    return _build_study_result(
        study_kind=ProteomicsStudyKind.DDA,
        source_surface="DdaBiologicalWorkflowBundle",
        design=_design_from_biological_report(bundle.biological_report),
        matrix_surfaces=(
            ProteomicsStudyMatrixSurface(
                surface_name="protein_lfq_report",
                kind=ProteomicsStudyMatrixKind.LABEL_FREE_PROTEIN,
                entity_count=bundle.protein_lfq_report.summary.protein_row_count,
                sample_count=bundle.protein_lfq_report.summary.sample_count,
                note=bundle.protein_lfq_report.note,
            ),
            ProteomicsStudyMatrixSurface(
                surface_name="heatmap_report",
                kind=ProteomicsStudyMatrixKind.HEATMAP_REVIEW,
                entity_count=bundle.biological_report.heatmap_report.summary.output_entity_count,
                sample_count=bundle.biological_report.heatmap_report.summary.sample_count,
                note=bundle.biological_report.heatmap_report.note,
            ),
        ),
        statistic_surfaces=(
            ProteomicsStudyStatisticSurface(
                surface_name="differential_report",
                kind=ProteomicsStudyStatisticKind.DIFFERENTIAL_PROTEIN,
                entity_count=len(bundle.biological_report.differential_report.entries),
                significant_entity_count=bundle.summary.significant_protein_count,
                note="dda workflow preserves downstream differential protein results",
            ),
        ),
        qc_surfaces=(
            ProteomicsStudyQcSurface(
                surface_name="psm_acceptance",
                kind=ProteomicsStudyQcKind.DDA_ACCEPTANCE,
                issue_count=bundle.summary.filtered_psm_count
                + bundle.summary.parse_rejected_row_count,
                note="dda workflow preserves accepted, filtered, and parse-rejected psm evidence",
            ),
            ProteomicsStudyQcSurface(
                surface_name="parsimony_review",
                kind=ProteomicsStudyQcKind.DDA_PARSIMONY,
                issue_count=bundle.parsimony_review.summary.unresolved_ambiguity_count,
                note=(
                    "dda workflow preserves parsimony-selected proteins and unresolved "
                    "protein ambiguities for study-level review"
                ),
            ),
            ProteomicsStudyQcSurface(
                surface_name="sample_exploration_report",
                kind=ProteomicsStudyQcKind.SAMPLE_EXPLORATION,
                issue_count=bundle.biological_report.summary.pca_outlier_sample_count,
                note=bundle.biological_report.sample_exploration_report.note,
            ),
            ProteomicsStudyQcSurface(
                surface_name="experiment_confidence_report",
                kind=ProteomicsStudyQcKind.EXPERIMENT_CONFIDENCE,
                issue_count=bundle.biological_report.summary.low_confidence_component_count,
                note=bundle.biological_report.experiment_confidence_report.note,
            ),
        ),
        card_surfaces=_biological_card_surfaces(bundle.biological_report),
        biological_conclusions=_biological_conclusions_from_biological_report(
            bundle.biological_report
        ),
        biological_report=bundle.biological_report,
        note=(
            "study result keeps dda acceptance, parsimony, protein quantification, "
            "and downstream biological interpretation on one comparable object"
        ),
    )


def build_proteomics_study_result_from_diann_workflow_bundle(
    bundle: DiannBiologicalWorkflowBundle,
) -> ProteomicsStudyResult:
    """Normalize one DIA-NN workflow bundle into a study result."""

    return _build_study_result(
        study_kind=ProteomicsStudyKind.DIA,
        source_surface="DiannBiologicalWorkflowBundle",
        design=_design_from_biological_report(bundle.biological_report),
        matrix_surfaces=(
            ProteomicsStudyMatrixSurface(
                surface_name="precursor_matrix_report",
                kind=ProteomicsStudyMatrixKind.DIA_PRECURSOR,
                entity_count=bundle.precursor_matrix_report.summary.precursor_row_count,
                sample_count=bundle.precursor_matrix_report.summary.sample_count,
                note=bundle.precursor_matrix_report.note,
            ),
            ProteomicsStudyMatrixSurface(
                surface_name="peptide_matrix_report",
                kind=ProteomicsStudyMatrixKind.DIA_PEPTIDE,
                entity_count=bundle.peptide_matrix_report.summary.peptide_row_count,
                sample_count=bundle.peptide_matrix_report.summary.sample_count,
                note=bundle.peptide_matrix_report.note,
            ),
            ProteomicsStudyMatrixSurface(
                surface_name="protein_matrix_report",
                kind=ProteomicsStudyMatrixKind.DIA_PROTEIN,
                entity_count=bundle.protein_matrix_report.summary.protein_row_count,
                sample_count=bundle.protein_matrix_report.summary.sample_count,
                note=bundle.protein_matrix_report.note,
            ),
        ),
        statistic_surfaces=(
            ProteomicsStudyStatisticSurface(
                surface_name="differential_analysis_report",
                kind=ProteomicsStudyStatisticKind.DIFFERENTIAL_PROTEIN,
                entity_count=(
                    0
                    if bundle.differential_analysis_report.differential_abundance_report
                    is None
                    else len(
                        bundle.differential_analysis_report.differential_abundance_report.entries
                    )
                ),
                significant_entity_count=bundle.summary.significant_protein_count,
                note=bundle.differential_analysis_report.note,
            ),
        ),
        qc_surfaces=(
            ProteomicsStudyQcSurface(
                surface_name="run_qc_report",
                kind=ProteomicsStudyQcKind.DIA_RUN_QC,
                issue_count=bundle.summary.flagged_run_count,
                note=bundle.run_qc_report.note,
            ),
            ProteomicsStudyQcSurface(
                surface_name="sample_exploration_report",
                kind=ProteomicsStudyQcKind.SAMPLE_EXPLORATION,
                issue_count=bundle.biological_report.summary.pca_outlier_sample_count,
                note=bundle.biological_report.sample_exploration_report.note,
            ),
            ProteomicsStudyQcSurface(
                surface_name="experiment_confidence_report",
                kind=ProteomicsStudyQcKind.EXPERIMENT_CONFIDENCE,
                issue_count=bundle.biological_report.summary.low_confidence_component_count,
                note=bundle.biological_report.experiment_confidence_report.note,
            ),
        ),
        card_surfaces=_biological_card_surfaces(bundle.biological_report),
        biological_conclusions=_biological_conclusions_from_biological_report(
            bundle.biological_report
        ),
        biological_report=bundle.biological_report,
        note=(
            "study result keeps dia precursor, peptide, protein, qc, and biology "
            "surfaces on one object for programmatic comparison"
        ),
    )


def build_proteomics_study_result_from_maxquant_workflow_bundle(
    bundle: MaxquantBiologicalWorkflowBundle,
) -> ProteomicsStudyResult:
    """Normalize one MaxQuant workflow bundle into a study result."""

    return _build_study_result(
        study_kind=ProteomicsStudyKind.MAXQUANT,
        source_surface="MaxquantBiologicalWorkflowBundle",
        design=_design_from_biological_report(bundle.biological_report),
        matrix_surfaces=(
            ProteomicsStudyMatrixSurface(
                surface_name="lfq_table",
                kind=ProteomicsStudyMatrixKind.LABEL_FREE_PROTEIN,
                entity_count=len(bundle.lfq_table.entity_ids),
                sample_count=len(bundle.lfq_table.sample_ids),
                note="maxquant workflow preserves accepted protein-group LFQ values",
            ),
            ProteomicsStudyMatrixSurface(
                surface_name="heatmap_report",
                kind=ProteomicsStudyMatrixKind.HEATMAP_REVIEW,
                entity_count=bundle.biological_report.heatmap_report.summary.output_entity_count,
                sample_count=bundle.biological_report.heatmap_report.summary.sample_count,
                note=bundle.biological_report.heatmap_report.note,
            ),
        ),
        statistic_surfaces=(
            ProteomicsStudyStatisticSurface(
                surface_name="differential_report",
                kind=ProteomicsStudyStatisticKind.DIFFERENTIAL_PROTEIN,
                entity_count=len(bundle.biological_report.differential_report.entries),
                significant_entity_count=bundle.summary.significant_protein_count,
                note="maxquant workflow preserves downstream differential protein results",
            ),
        ),
        qc_surfaces=(
            ProteomicsStudyQcSurface(
                surface_name="import_report",
                kind=ProteomicsStudyQcKind.MAXQUANT_IMPORT,
                issue_count=bundle.summary.filtered_protein_group_count,
                note=(
                    "maxquant workflow preserves evidence, peptide, protein-group, "
                    "and rejected-evidence import surfaces for study-level review"
                ),
            ),
            ProteomicsStudyQcSurface(
                surface_name="acceptance_policy",
                kind=ProteomicsStudyQcKind.MAXQUANT_ACCEPTANCE,
                issue_count=bundle.summary.filtered_protein_group_count,
                note="maxquant workflow preserves filtered protein groups before biology",
            ),
            ProteomicsStudyQcSurface(
                surface_name="sample_exploration_report",
                kind=ProteomicsStudyQcKind.SAMPLE_EXPLORATION,
                issue_count=bundle.biological_report.summary.pca_outlier_sample_count,
                note=bundle.biological_report.sample_exploration_report.note,
            ),
            ProteomicsStudyQcSurface(
                surface_name="experiment_confidence_report",
                kind=ProteomicsStudyQcKind.EXPERIMENT_CONFIDENCE,
                issue_count=bundle.biological_report.summary.low_confidence_component_count,
                note=bundle.biological_report.experiment_confidence_report.note,
            ),
        ),
        card_surfaces=_biological_card_surfaces(bundle.biological_report),
        biological_conclusions=_biological_conclusions_from_biological_report(
            bundle.biological_report
        ),
        biological_report=bundle.biological_report,
        note=(
            "study result keeps maxquant acceptance, lfq, and downstream biology "
            "surfaces on one programmatic object"
        ),
    )


__all__ = [
    "build_proteomics_study_result_from_biological_report_bundle",
    "build_proteomics_study_result_from_dda_workflow_bundle",
    "build_proteomics_study_result_from_diann_workflow_bundle",
    "build_proteomics_study_result_from_maxquant_workflow_bundle",
]

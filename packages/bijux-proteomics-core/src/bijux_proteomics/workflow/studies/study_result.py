# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Programmatic study-level result surfaces over owned proteomics workflows."""

from __future__ import annotations

from bijux_proteomics.ptm import PtmReportBundle
from bijux_proteomics.workflow.pipelines.advanced_diann import (
    AdvancedDiannWorkflowReport,
)
from bijux_proteomics.workflow.pipelines.advanced_fragpipe import (
    AdvancedFragpipeWorkflowReport,
)
from bijux_proteomics.workflow.pipelines.advanced_maxquant import (
    AdvancedMaxquantWorkflowReport,
)
from bijux_proteomics.workflow.pipelines.advanced_ptm import AdvancedPtmWorkflowReport
from bijux_proteomics.workflow.pipelines.advanced_targeted import (
    TargetedValidationWorkflowReport,
)
from bijux_proteomics.workflow.pipelines.advanced_tmt import AdvancedTmtWorkflowReport
from bijux_proteomics.workflow.pipelines.dda_biological_workflow import (
    DdaBiologicalWorkflowBundle,
)
from bijux_proteomics.workflow.pipelines.diann_biological_workflow import (
    DiannBiologicalWorkflowBundle,
)
from bijux_proteomics.workflow.pipelines.flagship_run import ProteomicsRunBundle
from bijux_proteomics.workflow.pipelines.label_based_reporting import (
    LabelBasedReportBundle,
)
from bijux_proteomics.workflow.pipelines.maxquant_biological_workflow import (
    MaxquantBiologicalWorkflowBundle,
)
from bijux_proteomics.workflow.pipelines.ptm_site_workflow import PtmSiteWorkflowBundle
from bijux_proteomics.workflow.pipelines.tmt_experiment_workflow import (
    TmtExperimentWorkflowBundle,
)
from bijux_proteomics.workflow.reports.biological_reporting import (
    BiologicalResultReportBundle,
)
from bijux_proteomics.workflow.studies.study_results.design import (
    _design_from_biological_report,
    _design_from_experimental_entries,
    _design_from_sample_metadata,
    _design_from_tmt_workflow,
)
from bijux_proteomics.workflow.studies.study_results import (
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


def build_proteomics_study_result(
    source: (
        AdvancedDiannWorkflowReport
        | AdvancedFragpipeWorkflowReport
        | AdvancedMaxquantWorkflowReport
        | AdvancedPtmWorkflowReport
        | AdvancedTmtWorkflowReport
        | BiologicalResultReportBundle
        | DdaBiologicalWorkflowBundle
        | DiannBiologicalWorkflowBundle
        | MaxquantBiologicalWorkflowBundle
        | ProteomicsRunBundle
        | PtmSiteWorkflowBundle
        | TargetedValidationWorkflowReport
        | TmtExperimentWorkflowBundle
    ),
) -> ProteomicsStudyResult:
    """Normalize one owned workflow output into a comparable study result."""

    if isinstance(source, ProteomicsRunBundle):
        return build_proteomics_study_result_from_run_bundle(source)
    if isinstance(source, AdvancedDiannWorkflowReport):
        return build_proteomics_study_result_from_advanced_diann_workflow_report(source)
    if isinstance(source, AdvancedFragpipeWorkflowReport):
        return build_proteomics_study_result_from_advanced_fragpipe_workflow_report(
            source
        )
    if isinstance(source, AdvancedMaxquantWorkflowReport):
        return build_proteomics_study_result_from_advanced_maxquant_workflow_report(
            source
        )
    if isinstance(source, AdvancedPtmWorkflowReport):
        return build_proteomics_study_result_from_advanced_ptm_workflow_report(source)
    if isinstance(source, AdvancedTmtWorkflowReport):
        return build_proteomics_study_result_from_advanced_tmt_workflow_report(source)
    if isinstance(source, DdaBiologicalWorkflowBundle):
        return build_proteomics_study_result_from_dda_workflow_bundle(source)
    if isinstance(source, DiannBiologicalWorkflowBundle):
        return build_proteomics_study_result_from_diann_workflow_bundle(source)
    if isinstance(source, MaxquantBiologicalWorkflowBundle):
        return build_proteomics_study_result_from_maxquant_workflow_bundle(source)
    if isinstance(source, TargetedValidationWorkflowReport):
        return build_proteomics_study_result_from_targeted_validation_workflow_report(
            source
        )
    if isinstance(source, TmtExperimentWorkflowBundle):
        return build_proteomics_study_result_from_tmt_workflow_bundle(source)
    if isinstance(source, PtmSiteWorkflowBundle):
        return build_proteomics_study_result_from_ptm_workflow_bundle(source)
    if isinstance(source, BiologicalResultReportBundle):
        return build_proteomics_study_result_from_biological_report_bundle(source)
    raise TypeError(f"unsupported proteomics study result source: {type(source)!r}")


def build_proteomics_study_result_from_run_bundle(
    bundle: ProteomicsRunBundle,
) -> ProteomicsStudyResult:
    """Normalize one flagship run bundle into a study-level comparison object."""

    if bundle.diann_workflow is not None:
        return build_proteomics_study_result_from_diann_workflow_bundle(
            bundle.diann_workflow
        )
    if bundle.maxquant_workflow is not None:
        return build_proteomics_study_result_from_maxquant_workflow_bundle(
            bundle.maxquant_workflow
        )
    if bundle.fragpipe_workflow is not None:
        return build_proteomics_study_result_from_dda_workflow_bundle(
            bundle.fragpipe_workflow
        )
    raise InvalidWorkflowError(
        "proteomics run bundle does not include a study workflow payload"
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


def build_proteomics_study_result_from_advanced_diann_workflow_report(
    report: AdvancedDiannWorkflowReport,
) -> ProteomicsStudyResult:
    """Normalize one advanced DIA-NN workflow report into a study result."""

    study_result = build_proteomics_study_result_from_diann_workflow_bundle(
        report.diann_workflow
    )
    return _copy_study_result(
        study_result,
        source_surface="AdvancedDiannWorkflowReport",
        qc_surfaces=study_result.qc_surfaces
        + (
            ProteomicsStudyQcSurface(
                surface_name="belief_audit",
                kind=ProteomicsStudyQcKind.BELIEF_AUDIT,
                issue_count=report.summary.downgraded_protein_count,
                note="advanced dia-nn preserves belief-audit downgrade rows beside the base dia workflow result",
            ),
            ProteomicsStudyQcSurface(
                surface_name="fragment_coelution_report",
                kind=ProteomicsStudyQcKind.FRAGMENT_COHERENCE,
                issue_count=0
                if report.fragment_coelution_report is None
                else report.summary.fragment_coelution_fragment_count,
                note=(
                    "advanced dia-nn preserves fragment-level coelution review when fragment evidence is supplied"
                ),
            ),
        ),
        note=(
            "study result preserves the advanced dia-nn review surface through the "
            "canonical dia study object without dropping base matrices, qc, claims, "
            "belief audit, or fragment coherence review"
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


def build_proteomics_study_result_from_advanced_maxquant_workflow_report(
    report: AdvancedMaxquantWorkflowReport,
) -> ProteomicsStudyResult:
    """Normalize one advanced MaxQuant workflow report into a study result."""

    study_result = build_proteomics_study_result_from_maxquant_workflow_bundle(
        report.maxquant_workflow
    )
    return _copy_study_result(
        study_result,
        source_surface="AdvancedMaxquantWorkflowReport",
        qc_surfaces=study_result.qc_surfaces
        + (
            ProteomicsStudyQcSurface(
                surface_name="excluded_protein_groups",
                kind=ProteomicsStudyQcKind.PROTEIN_GROUP_DISCREPANCY,
                issue_count=report.summary.excluded_reverse_or_contaminant_count
                + report.summary.additional_filtered_protein_group_count,
                note="advanced maxquant preserves excluded and filtered protein-group review beside the base maxquant study object",
            ),
        ),
        note=(
            "study result preserves the advanced maxquant review surface through the "
            "canonical maxquant study object without dropping excluded-group review "
            "or downstream biological interpretation"
        ),
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


def build_proteomics_study_result_from_advanced_tmt_workflow_report(
    report: AdvancedTmtWorkflowReport,
) -> ProteomicsStudyResult:
    """Normalize one advanced TMT workflow report into a study result."""

    study_result = build_proteomics_study_result_from_tmt_workflow_bundle(
        report.tmt_workflow
    )
    return _copy_study_result(
        study_result,
        source_surface="AdvancedTmtWorkflowReport",
        qc_surfaces=study_result.qc_surfaces
        + (
            ProteomicsStudyQcSurface(
                surface_name="compression_review",
                kind=ProteomicsStudyQcKind.LABEL_BASED_SIGNAL_REVIEW,
                issue_count=report.summary.excluded_protein_count
                + report.summary.high_interference_peptide_count,
                note="advanced tmt preserves interference-aware peptide and protein compression review beside the base label-based study object",
            ),
        ),
        card_surfaces=study_result.card_surfaces
        + (
            ProteomicsStudyCardSurface(
                surface_name="advanced_tmt_evidence_cards",
                kind=ProteomicsStudyCardKind.PROTEIN_EVIDENCE,
                card_count=report.summary.evidence_card_count,
                warning_count=report.summary.excluded_protein_count,
                note="advanced tmt preserves interference-aware evidence cards for each reviewed protein outcome",
            ),
        ),
        note=(
            "study result preserves the advanced tmt review surface through the "
            "canonical label-based study object without dropping interference-aware "
            "signal review or evidence-card summaries"
        ),
    )


def build_proteomics_study_result_from_ptm_workflow_bundle(
    bundle: PtmSiteWorkflowBundle,
) -> ProteomicsStudyResult:
    """Normalize one PTM-site workflow bundle into a study result."""

    report = bundle.report
    matrix_surfaces = []
    statistic_surfaces = []
    card_surfaces = []
    conclusions: list[ProteomicsStudyConclusionEntry] = []
    if report.site_quantification is not None:
        matrix_surfaces.append(
            ProteomicsStudyMatrixSurface(
                surface_name="site_quantification",
                kind=ProteomicsStudyMatrixKind.PTM_SITE,
                entity_count=report.summary.quantified_site_row_count,
                sample_count=len(report.site_quantification.sample_ids),
                note=report.site_quantification.note,
            )
        )
    if report.differential_analysis is not None:
        statistic_surfaces.append(
            ProteomicsStudyStatisticSurface(
                surface_name="differential_analysis",
                kind=ProteomicsStudyStatisticKind.DIFFERENTIAL_PTM_SITE,
                entity_count=len(
                    report.differential_analysis.differential_report.entries
                ),
                significant_entity_count=report.summary.differential_site_count,
                note=report.differential_analysis.note,
            )
        )
    if report.evidence_cards is not None:
        card_surfaces.append(
            ProteomicsStudyCardSurface(
                surface_name="ptm_evidence_cards",
                kind=ProteomicsStudyCardKind.PTM_EVIDENCE,
                card_count=report.evidence_cards.summary.card_count,
                warning_count=report.evidence_cards.summary.warning_card_count,
                note=report.evidence_cards.note,
            )
        )
        conclusions.extend(
            ProteomicsStudyConclusionEntry(
                conclusion_id=claim.claim_id,
                kind=ProteomicsStudyConclusionKind.PTM_NARRATIVE_CLAIM,
                subject_id=claim.site_key,
                subject_label=claim.site_key,
                status=claim.claim_kind.value,
                score=None,
                evidence_surface="ptm_evidence_cards",
                summary_text=claim.text,
            )
            for claim in report.evidence_cards.narrative_claims
        )
    return _build_study_result(
        study_kind=ProteomicsStudyKind.PTM,
        source_surface="PtmSiteWorkflowBundle",
        design=_design_from_experimental_entries(bundle.experiment_design.entries),
        matrix_surfaces=tuple(matrix_surfaces),
        statistic_surfaces=tuple(statistic_surfaces),
        qc_surfaces=(
            ProteomicsStudyQcSurface(
                surface_name="evidence_parse_report",
                kind=ProteomicsStudyQcKind.PTM_EVIDENCE_PARSING,
                issue_count=bundle.summary.rejected_evidence_count,
                note="ptm workflow preserves accepted and rejected localized evidence rows before site quantification",
            ),
        ),
        card_surfaces=tuple(card_surfaces),
        biological_conclusions=tuple(conclusions),
        ptm_report=report,
        note=(
            "study result keeps ptm evidence parsing, site quantification, "
            "differential analysis, and site-level narrative claims on one object"
        ),
    )


def build_proteomics_study_result_from_advanced_ptm_workflow_report(
    report: AdvancedPtmWorkflowReport,
) -> ProteomicsStudyResult:
    """Normalize one advanced PTM workflow report into a study result."""

    study_result = build_proteomics_study_result_from_ptm_workflow_bundle(
        report.ptm_workflow
    )
    return _copy_study_result(
        study_result,
        source_surface="AdvancedPtmWorkflowReport",
        qc_surfaces=study_result.qc_surfaces
        + (
            ProteomicsStudyQcSurface(
                surface_name="exact_site_exclusion_audit",
                kind=ProteomicsStudyQcKind.PTM_AMBIGUITY_REVIEW,
                issue_count=report.summary.excluded_ambiguous_row_count,
                note="advanced ptm preserves exact-site ambiguity exclusions beside the base ptm study object",
            ),
        ),
        note=(
            "study result preserves the advanced ptm review surface through the "
            "canonical ptm study object without dropping exact-site ambiguity review "
            "or occupancy counterpart context"
        ),
    )


def build_proteomics_study_result_from_advanced_fragpipe_workflow_report(
    report: AdvancedFragpipeWorkflowReport,
) -> ProteomicsStudyResult:
    """Normalize one advanced FragPipe workflow report into a study result."""

    study_result = build_proteomics_study_result_from_dda_workflow_bundle(
        report.fragpipe_workflow
    )
    return _copy_study_result(
        study_result,
        source_surface="AdvancedFragpipeWorkflowReport",
        qc_surfaces=study_result.qc_surfaces
        + (
            ProteomicsStudyQcSurface(
                surface_name="protein_group_discrepancies",
                kind=ProteomicsStudyQcKind.PROTEIN_GROUP_DISCREPANCY,
                issue_count=report.summary.protein_group_discrepancy_count,
                note="advanced fragpipe preserves explicit source-versus-workflow protein-group discrepancy review beside the base dda study object",
            ),
        ),
        note=(
            "study result preserves the advanced fragpipe review surface through the "
            "canonical dda study object without dropping peptide-evidence or "
            "protein-group discrepancy review"
        ),
    )


def build_proteomics_study_result_from_targeted_validation_workflow_report(
    report: TargetedValidationWorkflowReport,
) -> ProteomicsStudyResult:
    """Normalize one advanced targeted-validation workflow report into a study result."""

    sample_ids = tuple(
        sorted({item.sample_id for item in report.import_report.observations})
    )
    design = _design_from_sample_metadata(
        (ProteomicsStudyDesignEntry(sample_id=sample_id) for sample_id in sample_ids),
        note=(
            "targeted validation preserves sample identifiers directly from the "
            "imported targeted observations even when the design-condition mapping "
            "is not carried forward on the review report object"
        ),
    )
    conclusions = tuple(
        ProteomicsStudyConclusionEntry(
            conclusion_id=entry.candidate_id,
            kind=_conclusion_kind_from_targeted_verdict(entry.verdict.value),
            subject_id=entry.candidate_id,
            subject_label=entry.display_label,
            status=entry.verdict.value,
            score=None,
            evidence_surface="advanced_targeted_evidence_cards",
            summary_text=entry.note,
        )
        for entry in report.validation_report.entries
    )
    return _build_study_result(
        study_kind=ProteomicsStudyKind.TARGETED,
        source_surface="TargetedValidationWorkflowReport",
        design=design,
        matrix_surfaces=(
            ProteomicsStudyMatrixSurface(
                surface_name="targeted_target_matrix",
                kind=ProteomicsStudyMatrixKind.TARGETED_TARGET,
                entity_count=report.summary.matrix_target_count,
                sample_count=len(sample_ids),
                note="targeted validation preserves one precursor-target matrix over the imported assay observations",
            ),
        ),
        statistic_surfaces=(
            ProteomicsStudyStatisticSurface(
                surface_name="targeted_validation_report",
                kind=ProteomicsStudyStatisticKind.TARGETED_VALIDATION,
                entity_count=report.summary.discovery_claim_count,
                significant_entity_count=report.summary.confirmed_count
                + report.summary.contradicted_count,
                note="targeted validation preserves decisive confirmed and contradicted claim outcomes beside inconclusive follow-up results",
            ),
        ),
        qc_surfaces=(
            ProteomicsStudyQcSurface(
                surface_name="targeted_assay_qc",
                kind=ProteomicsStudyQcKind.TARGETED_ASSAY_QC,
                issue_count=report.summary.unreliable_target_entry_count
                + report.summary.flagged_coelution_target_entry_count
                + report.summary.drift_flagged_fragment_ratio_observation_count,
                note="targeted validation preserves assay reliability, coelution, and fragment-ratio drift review before candidate verdicts",
            ),
        ),
        card_surfaces=(
            ProteomicsStudyCardSurface(
                surface_name="advanced_targeted_evidence_cards",
                kind=ProteomicsStudyCardKind.TARGETED_VALIDATION,
                card_count=report.summary.evidence_card_count,
                warning_count=report.summary.inconclusive_count,
                note="targeted validation preserves one candidate-level evidence card per reviewed biomarker candidate",
            ),
        ),
        biological_conclusions=conclusions,
        note=(
            "study result preserves advanced targeted validation as one canonical "
            "targeted study object with target-matrix, assay-qc, verdict, evidence-card, "
            "and candidate-conclusion surfaces"
        ),
    )


def _build_study_result(
    *,
    study_kind: ProteomicsStudyKind,
    source_surface: str,
    design: ProteomicsStudyDesignSnapshot,
    matrix_surfaces: tuple[ProteomicsStudyMatrixSurface, ...],
    statistic_surfaces: tuple[ProteomicsStudyStatisticSurface, ...],
    qc_surfaces: tuple[ProteomicsStudyQcSurface, ...],
    card_surfaces: tuple[ProteomicsStudyCardSurface, ...],
    biological_conclusions: tuple[ProteomicsStudyConclusionEntry, ...],
    biological_report: BiologicalResultReportBundle | None = None,
    label_based_report: LabelBasedReportBundle | None = None,
    ptm_report: PtmReportBundle | None = None,
    note: str,
) -> ProteomicsStudyResult:
    return ProteomicsStudyResult(
        study_kind=study_kind,
        source_surface=source_surface,
        design=design,
        matrix_surfaces=matrix_surfaces,
        statistic_surfaces=statistic_surfaces,
        qc_surfaces=qc_surfaces,
        card_surfaces=card_surfaces,
        biological_conclusions=biological_conclusions,
        biological_report=biological_report,
        label_based_report=label_based_report,
        ptm_report=ptm_report,
        summary=ProteomicsStudyResultSummary(
            design_entry_count=len(design.entries),
            matrix_surface_count=len(matrix_surfaces),
            statistic_surface_count=len(statistic_surfaces),
            qc_surface_count=len(qc_surfaces),
            card_surface_count=len(card_surfaces),
            conclusion_count=len(biological_conclusions),
        ),
        note=note,
    )


def _copy_study_result(
    study_result: ProteomicsStudyResult,
    *,
    source_surface: str,
    note: str,
    qc_surfaces: tuple[ProteomicsStudyQcSurface, ...] | None = None,
    card_surfaces: tuple[ProteomicsStudyCardSurface, ...] | None = None,
) -> ProteomicsStudyResult:
    stable_qc_surfaces = (
        study_result.qc_surfaces if qc_surfaces is None else qc_surfaces
    )
    stable_card_surfaces = (
        study_result.card_surfaces if card_surfaces is None else card_surfaces
    )
    return study_result.model_copy(
        update={
            "source_surface": source_surface,
            "qc_surfaces": stable_qc_surfaces,
            "card_surfaces": stable_card_surfaces,
            "summary": ProteomicsStudyResultSummary(
                design_entry_count=study_result.summary.design_entry_count,
                matrix_surface_count=study_result.summary.matrix_surface_count,
                statistic_surface_count=study_result.summary.statistic_surface_count,
                qc_surface_count=len(stable_qc_surfaces),
                card_surface_count=len(stable_card_surfaces),
                conclusion_count=study_result.summary.conclusion_count,
            ),
            "note": note,
        }
    )


def _biological_card_surfaces(
    report: BiologicalResultReportBundle,
) -> tuple[ProteomicsStudyCardSurface, ...]:
    return (
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
    )


def _biological_conclusions_from_biological_report(
    report: BiologicalResultReportBundle,
) -> tuple[ProteomicsStudyConclusionEntry, ...]:
    conclusions: list[ProteomicsStudyConclusionEntry] = []
    if report.claim_validation_report is not None:
        conclusions.extend(
            ProteomicsStudyConclusionEntry(
                conclusion_id=claim.claim_id,
                kind=ProteomicsStudyConclusionKind.SUPPORTED_CLAIM,
                subject_id=claim.subject_id,
                subject_label=claim.subject_label,
                status=claim.status.value,
                score=claim.robustness_score,
                evidence_surface="claim_validation_report",
                summary_text=claim.claim_text,
            )
            for claim in report.claim_validation_report.supported_claims
        )
        conclusions.extend(
            ProteomicsStudyConclusionEntry(
                conclusion_id=claim.claim_id,
                kind=ProteomicsStudyConclusionKind.REJECTED_CLAIM,
                subject_id=claim.subject_id,
                subject_label=claim.subject_label,
                status=claim.status.value,
                score=claim.robustness_score,
                evidence_surface="claim_validation_report",
                summary_text=claim.claim_text,
            )
            for claim in report.claim_validation_report.rejected_claims
        )
    if report.biological_hypothesis_report is not None:
        conclusions.extend(
            ProteomicsStudyConclusionEntry(
                conclusion_id=hypothesis.hypothesis_id,
                kind=ProteomicsStudyConclusionKind.BIOLOGICAL_HYPOTHESIS,
                subject_id=hypothesis.subject_id,
                subject_label=hypothesis.subject_label,
                status=hypothesis.confidence_tier.value,
                score=hypothesis.confidence_score,
                evidence_surface="biological_hypothesis_report",
                summary_text=hypothesis.claim,
            )
            for hypothesis in report.biological_hypothesis_report.hypotheses
        )
    if report.regulator_inference_report is not None:
        conclusions.extend(
            ProteomicsStudyConclusionEntry(
                conclusion_id=entry.regulator,
                kind=ProteomicsStudyConclusionKind.REGULATOR_INFERENCE,
                subject_id=entry.regulator,
                subject_label=entry.regulator,
                status=entry.direction.value,
                score=entry.score,
                evidence_surface="regulator_inference_report",
                summary_text=entry.note,
            )
            for entry in report.regulator_inference_report.entries
        )
    return tuple(
        sorted(
            conclusions,
            key=lambda entry: (entry.kind.value, entry.subject_id, entry.conclusion_id),
        )
    )
def _conclusion_kind_from_targeted_verdict(
    verdict: str,
) -> ProteomicsStudyConclusionKind:
    if verdict == "confirmed":
        return ProteomicsStudyConclusionKind.SUPPORTED_CLAIM
    if verdict == "contradicted":
        return ProteomicsStudyConclusionKind.REJECTED_CLAIM
    return ProteomicsStudyConclusionKind.REFUSED_CLAIM


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

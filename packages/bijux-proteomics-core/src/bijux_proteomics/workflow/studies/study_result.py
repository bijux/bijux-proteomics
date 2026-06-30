# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Programmatic study-level result surfaces over owned proteomics workflows."""

from __future__ import annotations

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
from bijux_proteomics.workflow.studies.study_results.modification import (
    build_proteomics_study_result_from_ptm_workflow_bundle,
)
from bijux_proteomics.workflow.studies.study_results.multiplex import (
    build_proteomics_study_result_from_tmt_workflow_bundle,
)
from bijux_proteomics.workflow.studies.study_results.label_free import (
    build_proteomics_study_result_from_biological_report_bundle,
    build_proteomics_study_result_from_dda_workflow_bundle,
    build_proteomics_study_result_from_diann_workflow_bundle,
    build_proteomics_study_result_from_maxquant_workflow_bundle,
)
from bijux_proteomics.workflow.studies.study_results.validation import (
    build_proteomics_study_result_from_targeted_validation_workflow_report,
)
from bijux_proteomics.workflow.studies.study_results.assembly import (
    _biological_card_surfaces,
    _biological_conclusions_from_biological_report,
    _build_study_result,
    _copy_study_result,
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

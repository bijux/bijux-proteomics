# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Advanced overlay builders for study-result surfaces."""

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
from bijux_proteomics.workflow.pipelines.advanced_tmt import AdvancedTmtWorkflowReport
from bijux_proteomics.workflow.studies.study_results.assembly import (
    _copy_study_result,
)
from bijux_proteomics.workflow.studies.study_results.label_free import (
    build_proteomics_study_result_from_dda_workflow_bundle,
    build_proteomics_study_result_from_diann_workflow_bundle,
    build_proteomics_study_result_from_maxquant_workflow_bundle,
)
from bijux_proteomics.workflow.studies.study_results.models import (
    ProteomicsStudyCardKind,
    ProteomicsStudyCardSurface,
    ProteomicsStudyQcKind,
    ProteomicsStudyQcSurface,
    ProteomicsStudyResult,
)
from bijux_proteomics.workflow.studies.study_results.modification import (
    build_proteomics_study_result_from_ptm_workflow_bundle,
)
from bijux_proteomics.workflow.studies.study_results.multiplex import (
    build_proteomics_study_result_from_tmt_workflow_bundle,
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
    "build_proteomics_study_result_from_advanced_diann_workflow_report",
    "build_proteomics_study_result_from_advanced_fragpipe_workflow_report",
    "build_proteomics_study_result_from_advanced_maxquant_workflow_report",
    "build_proteomics_study_result_from_advanced_ptm_workflow_report",
    "build_proteomics_study_result_from_advanced_tmt_workflow_report",
]

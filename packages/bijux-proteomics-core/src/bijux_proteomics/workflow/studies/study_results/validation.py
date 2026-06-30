# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Targeted-validation study-result builders."""

from __future__ import annotations

from bijux_proteomics.workflow.pipelines.advanced_targeted import (
    TargetedValidationWorkflowReport,
)
from bijux_proteomics.workflow.studies.study_results.assembly import (
    _build_study_result,
)
from bijux_proteomics.workflow.studies.study_results.design import (
    _design_from_sample_metadata,
)
from bijux_proteomics.workflow.studies.study_results.models import (
    ProteomicsStudyCardKind,
    ProteomicsStudyCardSurface,
    ProteomicsStudyConclusionEntry,
    ProteomicsStudyConclusionKind,
    ProteomicsStudyDesignEntry,
    ProteomicsStudyKind,
    ProteomicsStudyMatrixKind,
    ProteomicsStudyMatrixSurface,
    ProteomicsStudyQcKind,
    ProteomicsStudyQcSurface,
    ProteomicsStudyResult,
    ProteomicsStudyStatisticKind,
    ProteomicsStudyStatisticSurface,
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


def _conclusion_kind_from_targeted_verdict(
    verdict: str,
) -> ProteomicsStudyConclusionKind:
    if verdict == "confirmed":
        return ProteomicsStudyConclusionKind.SUPPORTED_CLAIM
    if verdict == "contradicted":
        return ProteomicsStudyConclusionKind.REJECTED_CLAIM
    return ProteomicsStudyConclusionKind.REFUSED_CLAIM


__all__ = ["build_proteomics_study_result_from_targeted_validation_workflow_report"]

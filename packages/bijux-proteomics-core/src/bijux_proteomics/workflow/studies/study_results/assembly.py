# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Shared assembly helpers for study-result builders."""

from __future__ import annotations

from bijux_proteomics.ptm import PtmReportBundle
from bijux_proteomics.workflow.pipelines.label_based_reporting import (
    LabelBasedReportBundle,
)
from bijux_proteomics.workflow.reports.biological_reporting import (
    BiologicalResultReportBundle,
)
from bijux_proteomics.workflow.studies.study_results.models import (
    ProteomicsStudyCardKind,
    ProteomicsStudyCardSurface,
    ProteomicsStudyConclusionEntry,
    ProteomicsStudyConclusionKind,
    ProteomicsStudyDesignSnapshot,
    ProteomicsStudyKind,
    ProteomicsStudyMatrixSurface,
    ProteomicsStudyQcSurface,
    ProteomicsStudyResult,
    ProteomicsStudyResultSummary,
    ProteomicsStudyStatisticSurface,
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


__all__ = [
    "_biological_card_surfaces",
    "_biological_conclusions_from_biological_report",
    "_build_study_result",
    "_copy_study_result",
]

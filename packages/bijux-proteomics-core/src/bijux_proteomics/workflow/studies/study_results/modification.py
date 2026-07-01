# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""PTM-oriented study-result builders."""

from __future__ import annotations

from bijux_proteomics.workflow.pipelines.ptm_site_workflow import PtmSiteWorkflowBundle
from bijux_proteomics.workflow.studies.study_results.assembly import (
    _build_study_result,
)
from bijux_proteomics.workflow.studies.study_results.design import (
    _design_from_experimental_entries,
)
from bijux_proteomics.workflow.studies.study_results.models import (
    ProteomicsStudyCardKind,
    ProteomicsStudyCardSurface,
    ProteomicsStudyConclusionEntry,
    ProteomicsStudyConclusionKind,
    ProteomicsStudyKind,
    ProteomicsStudyMatrixKind,
    ProteomicsStudyMatrixSurface,
    ProteomicsStudyQcKind,
    ProteomicsStudyQcSurface,
    ProteomicsStudyResult,
    ProteomicsStudyStatisticKind,
    ProteomicsStudyStatisticSurface,
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


__all__ = ["build_proteomics_study_result_from_ptm_workflow_bundle"]

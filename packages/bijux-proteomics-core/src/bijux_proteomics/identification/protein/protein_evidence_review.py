# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Compatibility review wrapper over the owned protein evidence engine."""

from __future__ import annotations

from bijux_proteomics.identification.contracts import PsmRecord
from bijux_proteomics.identification.peptide.cross_run_reproducibility import (
    RunDetectionContext,
)
from bijux_proteomics.identification.protein.protein_evidence import (
    ProteinEvidenceDowngradeReason,
    ProteinEvidenceEntry,
    ProteinEvidenceReport,
    ProteinEvidenceSummary,
    ProteinEvidenceTier,
    build_protein_evidence_report,
    render_protein_evidence_entries_tsv,
    render_protein_evidence_summary_tsv,
)

ProteinEvidenceReviewEntry = ProteinEvidenceEntry
ProteinEvidenceReviewReport = ProteinEvidenceReport
ProteinEvidenceReviewSummary = ProteinEvidenceSummary


def build_protein_evidence_review_report(
    records: tuple[PsmRecord, ...],
    *,
    high_q_value: float = 0.01,
    moderate_q_value: float = 0.05,
    score_orientation: str = "higher_better",
    run_contexts: tuple[RunDetectionContext, ...] = (),
    exploratory_protein_refs: tuple[str, ...] = (),
) -> ProteinEvidenceReviewReport:
    """Build the reviewer-facing protein evidence packet from the owned engine."""
    return build_protein_evidence_report(
        records,
        high_q_value=high_q_value,
        moderate_q_value=moderate_q_value,
        score_orientation=score_orientation,
        run_contexts=run_contexts,
        exploratory_protein_refs=exploratory_protein_refs,
    )


__all__ = [
    "ProteinEvidenceDowngradeReason",
    "ProteinEvidenceReviewEntry",
    "ProteinEvidenceReviewReport",
    "ProteinEvidenceReviewSummary",
    "ProteinEvidenceTier",
    "build_protein_evidence_review_report",
    "render_protein_evidence_entries_tsv",
    "render_protein_evidence_summary_tsv",
]

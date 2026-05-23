# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Compatibility review wrapper over the owned peptide evidence engine."""

from __future__ import annotations

from bijux_proteomics.identification.contracts import PsmRecord
from bijux_proteomics.identification.peptide_evidence import (
    PeptideEvidenceClass,
    PeptideEvidenceEntry,
    PeptideEvidenceReport,
    PeptideEvidenceSummary,
    PeptideEvidenceTag,
    build_peptide_evidence_report,
    render_peptide_evidence_entries_tsv,
    render_peptide_evidence_summary_tsv,
)

PeptideEvidencePrimaryClass = PeptideEvidenceClass
PeptideEvidenceReviewEntry = PeptideEvidenceEntry
PeptideEvidenceReviewReport = PeptideEvidenceReport
PeptideEvidenceReviewSummary = PeptideEvidenceSummary


def build_peptide_evidence_review_report(
    records: tuple[PsmRecord, ...],
    *,
    threshold: float | None = 0.05,
    score_orientation: str = "higher_better",
    strong_q_value: float = 0.01,
    reproducible_spectrum_count: int = 2,
) -> PeptideEvidenceReviewReport:
    """Build the reviewer-facing peptide evidence packet from the owned engine."""
    return build_peptide_evidence_report(
        records,
        threshold=threshold,
        score_orientation=score_orientation,
        strong_q_value=strong_q_value,
        reproducible_spectrum_count=reproducible_spectrum_count,
    )


__all__ = [
    "PeptideEvidencePrimaryClass",
    "PeptideEvidenceReviewEntry",
    "PeptideEvidenceReviewReport",
    "PeptideEvidenceReviewSummary",
    "PeptideEvidenceTag",
    "build_peptide_evidence_review_report",
    "render_peptide_evidence_entries_tsv",
    "render_peptide_evidence_summary_tsv",
]

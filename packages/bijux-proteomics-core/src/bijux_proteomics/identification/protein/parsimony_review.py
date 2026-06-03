# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Compatibility review surface over the owned protein parsimony engine."""

from __future__ import annotations

from bijux_proteomics.identification.contracts import ParsimonyVariant, PsmRecord
from bijux_proteomics.identification.protein.protein_parsimony import (
    ProteinParsimonyAmbiguityEntry,
    ProteinParsimonyProteinEntry,
    ProteinParsimonyReport,
    ProteinParsimonySummary,
    build_protein_parsimony_report,
    render_protein_parsimony_ambiguities_tsv,
    render_protein_parsimony_proteins_tsv,
    render_protein_parsimony_summary_tsv,
)

ParsimonyReviewSummary = ProteinParsimonySummary
ParsimonyReviewProteinEntry = ProteinParsimonyProteinEntry
ParsimonyAmbiguityEntry = ProteinParsimonyAmbiguityEntry
ParsimonyReviewReport = ProteinParsimonyReport


def build_parsimony_review_report(
    records: tuple[PsmRecord, ...],
    *,
    variant: ParsimonyVariant = ParsimonyVariant.GREEDY_COVERAGE,
    review_variants: tuple[ParsimonyVariant, ...] = (
        ParsimonyVariant.GREEDY_COVERAGE,
        ParsimonyVariant.UNIQUE_EVIDENCE_PRIORITY,
        ParsimonyVariant.BEST_SCORE_PRIORITY,
    ),
) -> ParsimonyReviewReport:
    """Build the reviewer-facing protein parsimony packet from the owner surface."""
    return build_protein_parsimony_report(
        records,
        variant=variant,
        review_variants=review_variants,
    )


def render_parsimony_review_summary_tsv(report: ParsimonyReviewReport) -> str:
    """Render the parsimony review summary ledger as TSV."""
    return render_protein_parsimony_summary_tsv(report)


def render_parsimony_review_proteins_tsv(report: ParsimonyReviewReport) -> str:
    """Render the selected parsimony protein set as TSV."""
    return render_protein_parsimony_proteins_tsv(report)


def render_parsimony_review_ambiguities_tsv(report: ParsimonyReviewReport) -> str:
    """Render unresolved protein parsimony ambiguities as TSV."""
    return render_protein_parsimony_ambiguities_tsv(report)

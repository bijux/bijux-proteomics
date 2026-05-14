# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.identification import (
    ParsimonyVariant,
    build_parsimony_review_report,
    filter_psms_by_fdr,
    parse_psm_tsv,
    render_parsimony_review_ambiguities_tsv,
    render_parsimony_review_proteins_tsv,
    render_parsimony_review_summary_tsv,
)

from .test_identification_surface import _default_mapping, _psm_fixture


def test_parsimony_review_reports_selected_proteins_and_unresolved_ambiguity() -> None:
    report = parse_psm_tsv(
        _psm_fixture("protein_parsimony_variants.tsv"), mapping=_default_mapping()
    )
    accepted = filter_psms_by_fdr(report.accepted_records, threshold=0.05)

    review = build_parsimony_review_report(
        accepted,
        variant=ParsimonyVariant.GREEDY_COVERAGE,
        review_variants=(
            ParsimonyVariant.GREEDY_COVERAGE,
            ParsimonyVariant.UNIQUE_EVIDENCE_PRIORITY,
        ),
    )

    assert review.summary.variant is ParsimonyVariant.GREEDY_COVERAGE
    assert review.summary.total_observed_peptides == 6
    assert review.summary.explained_peptide_count == 6
    assert review.summary.unexplained_peptide_count == 0
    assert review.summary.selected_protein_count == 2
    assert review.summary.shared_selected_peptide_count == 1
    assert review.summary.variant_difference_count == 1
    assert review.summary.unresolved_ambiguity_count == 2

    first = review.selected_proteins[0]
    second = review.selected_proteins[1]
    assert first.protein_ref == "P10001"
    assert first.newly_explained_peptides == ("ALPHAK", "BRAVOK", "CHARLIEK", "DELTAK")
    assert first.unresolved_shared_peptides == ("BRAVOK",)
    assert second.protein_ref == "P20002"
    assert second.newly_explained_peptides == ("ECHOK", "FOXTROTK")
    assert second.unresolved_shared_peptides == ("BRAVOK",)

    peptide_ambiguity = next(
        entry for entry in review.unresolved_ambiguities if entry.subject_id == "BRAVOK"
    )
    assert peptide_ambiguity.candidate_proteins == ("P10001", "P20002")
    assert peptide_ambiguity.strategy_assignments["greedy_coverage"] == (
        "P10001",
        "P20002",
    )

    variant_ambiguity = next(
        entry
        for entry in review.unresolved_ambiguities
        if entry.kind.value == "protein_set"
    )
    assert variant_ambiguity.first_difference_rank == 1
    assert variant_ambiguity.strategy_assignments["greedy_coverage"] == (
        "P10001",
        "P20002",
    )
    assert variant_ambiguity.strategy_assignments["unique_evidence_priority"] == (
        "P20002",
        "P10001",
    )

    summary_tsv = render_parsimony_review_summary_tsv(review)
    proteins_tsv = render_parsimony_review_proteins_tsv(review)
    ambiguities_tsv = render_parsimony_review_ambiguities_tsv(review)

    assert "selected_protein_count\t2" in summary_tsv
    assert (
        "greedy_coverage\t1\tP10001\tpg-001\tP10001\tALPHAK;BRAVOK;CHARLIEK;DELTAK"
        in proteins_tsv
    )
    assert "BRAVOK\tpeptide_assignment\tP10001;P20002" in ambiguities_tsv

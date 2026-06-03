# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.identification import ParsimonyVariant, parse_psm_tsv
from bijux_proteomics.identification.protein_parsimony import (
    build_protein_parsimony_report,
    render_protein_parsimony_ambiguities_tsv,
    render_protein_parsimony_proteins_tsv,
    render_protein_parsimony_summary_tsv,
)

from .test_identification_surface import _default_mapping


def _psm_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "psm" / name


def test_protein_parsimony_report_preserves_selected_proteins_and_unresolved_shared_peptides() -> (
    None
):
    parse_report = parse_psm_tsv(
        _psm_fixture("protein_parsimony_variants.tsv"),
        mapping=_default_mapping(),
    )
    report = build_protein_parsimony_report(
        parse_report.accepted_records,
        variant=ParsimonyVariant.GREEDY_COVERAGE,
        review_variants=(
            ParsimonyVariant.GREEDY_COVERAGE,
            ParsimonyVariant.UNIQUE_EVIDENCE_PRIORITY,
        ),
    )

    assert report.summary.selected_protein_count == 2
    assert report.explained_peptides == (
        "ALPHAK",
        "BRAVOK",
        "CHARLIEK",
        "DELTAK",
        "ECHOK",
        "FOXTROTK",
    )
    assert report.unexplained_peptides == ()
    assert report.selected_proteins[0].protein_ref == "P10001"
    assert report.selected_proteins[0].unresolved_shared_peptides == ("BRAVOK",)
    assert report.selected_proteins[1].protein_ref == "P20002"
    assert report.selected_proteins[1].unresolved_shared_peptides == ("BRAVOK",)


def test_protein_parsimony_report_keeps_shared_peptide_only_cases_ambiguous() -> None:
    parse_report = parse_psm_tsv(
        _psm_fixture("protein_parsimony_variants.tsv"),
        mapping=_default_mapping(),
    )
    report = build_protein_parsimony_report(
        parse_report.accepted_records,
        variant=ParsimonyVariant.GREEDY_COVERAGE,
        review_variants=(
            ParsimonyVariant.GREEDY_COVERAGE,
            ParsimonyVariant.UNIQUE_EVIDENCE_PRIORITY,
        ),
    )

    shared_peptide = next(
        entry for entry in report.unresolved_ambiguities if entry.subject_id == "BRAVOK"
    )
    assert shared_peptide.candidate_proteins == ("P10001", "P20002")
    assert shared_peptide.strategy_assignments["greedy_coverage"] == (
        "P10001",
        "P20002",
    )

    variant_difference = next(
        entry
        for entry in report.unresolved_ambiguities
        if entry.kind.value == "protein_set"
    )
    assert variant_difference.first_difference_rank == 1


def test_protein_parsimony_renderers_emit_stable_ledgers() -> None:
    parse_report = parse_psm_tsv(
        _psm_fixture("protein_parsimony_variants.tsv"),
        mapping=_default_mapping(),
    )
    report = build_protein_parsimony_report(
        parse_report.accepted_records,
        variant=ParsimonyVariant.GREEDY_COVERAGE,
        review_variants=(
            ParsimonyVariant.GREEDY_COVERAGE,
            ParsimonyVariant.UNIQUE_EVIDENCE_PRIORITY,
        ),
    )

    summary_tsv = render_protein_parsimony_summary_tsv(report)
    proteins_tsv = render_protein_parsimony_proteins_tsv(report)
    ambiguities_tsv = render_protein_parsimony_ambiguities_tsv(report)

    assert "selected_protein_count\t2" in summary_tsv
    assert "reproducibility_hash\t" in summary_tsv
    assert (
        "greedy_coverage\t1\tP10001\tpg-001\tP10001\tALPHAK;BRAVOK;CHARLIEK;DELTAK"
        in proteins_tsv
    )
    assert "BRAVOK\tpeptide_assignment\tP10001;P20002" in ambiguities_tsv

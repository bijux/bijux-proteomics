from __future__ import annotations

import json
from pathlib import Path

from bijux_proteomics import (
    PeptideDigestionMode,
    build_digest_duplicate_accounting,
    digest_sequence,
    filter_digested_peptides,
)


def _digestion_fixture(name: str) -> Path:
    return Path(__file__).parent / "fixtures" / "digestion" / name


def test_digest_sequence_performs_full_tryptic_cleavage() -> None:
    peptides = digest_sequence(
        "MKWVTFISLLFLFSSAYSRGVFRRDTHKSEIAHRFKDLGE",
        source_accession="ALBU_HUMAN",
    )

    assert [peptide.sequence for peptide in peptides] == [
        "MK",
        "WVTFISLLFLFSSAYSR",
        "GVFR",
        "R",
        "DTHK",
        "SEIAHR",
        "FK",
        "DLGE",
    ]
    assert peptides[0].start == 1
    assert peptides[1].start == 3
    assert all(peptide.protease == "trypsin" for peptide in peptides)


def test_digest_sequence_honors_trypsin_proline_block() -> None:
    peptides = digest_sequence("AKRPQKAAAR", source_accession="block-test")

    assert [peptide.sequence for peptide in peptides] == ["AK", "RPQK", "AAAR"]


def test_digest_sequence_supports_missed_cleavages() -> None:
    peptides = digest_sequence(
        "AKAAKAAK",
        source_accession="missed-cleavage-test",
        missed_cleavages=1,
    )

    assert [peptide.sequence for peptide in peptides] == [
        "AK",
        "AKAAK",
        "AAK",
        "AAKAAK",
        "AAK",
    ]
    assert [peptide.missed_cleavages for peptide in peptides] == [0, 1, 0, 1, 0]


def test_digest_sequence_supports_semi_specific_mode() -> None:
    peptides = digest_sequence(
        "AKAAK",
        source_accession="semi-specific-test",
        mode=PeptideDigestionMode.SEMI_SPECIFIC,
    )

    sequences = {peptide.sequence for peptide in peptides}
    assert {"AK", "AKAAK", "K", "KAAK", "AAK"} <= sequences
    assert any(peptide.cleavage_type == "semi_specific" for peptide in peptides)


def test_digest_sequence_supports_bounded_non_specific_mode() -> None:
    peptides = digest_sequence(
        "PEPTIDE",
        source_accession="non-specific-test",
        mode=PeptideDigestionMode.NON_SPECIFIC,
        min_length=3,
        max_length=4,
    )

    assert [peptide.sequence for peptide in peptides[:5]] == [
        "PEP",
        "PEPT",
        "EPT",
        "EPTI",
        "PTI",
    ]
    assert all(3 <= len(peptide.sequence) <= 4 for peptide in peptides)
    assert all(peptide.cleavage_type == "non_specific" for peptide in peptides)


def test_digest_sequence_matches_curated_protease_reference_cases() -> None:
    fixture = json.loads(_digestion_fixture("protease_reference_cases.json").read_text())

    for case in fixture:
        peptides = digest_sequence(
            case["sequence"],
            protease=case["protease"],
            mode=PeptideDigestionMode(case["digestion_mode"]),
            min_length=case.get("min_length", 1),
            max_length=case.get("max_length"),
        )
        assert [peptide.sequence for peptide in peptides] == case["expected_peptides"]


def test_filter_digested_peptides_supports_length_bounds() -> None:
    peptides = digest_sequence(
        "MKWVTFISLLFLFSSAYSRGVFR", source_accession="filter-test"
    )
    filtered, report = filter_digested_peptides(peptides, min_length=3, max_length=10)

    assert [peptide.sequence for peptide in filtered] == ["GVFR"]
    assert report.input_peptides == len(peptides)
    assert report.output_peptides == 1
    assert report.excluded_by_length == len(peptides) - 1


def test_filter_digested_peptides_supports_mass_bounds() -> None:
    peptides = digest_sequence(
        "AKAAKAAK",
        source_accession="mass-filter-test",
        missed_cleavages=1,
    )
    filtered, report = filter_digested_peptides(
        peptides,
        min_mass=350.0,
        max_mass=700.0,
    )

    assert [peptide.sequence for peptide in filtered] == ["AKAAK", "AAKAAK"]
    assert report.excluded_by_mass == len(peptides) - len(filtered)


def test_digest_duplicate_accounting_distinguishes_occurrences_from_unique_sequences() -> (
    None
):
    peptides = digest_sequence(
        "AKAAKAAK",
        source_accession="duplicate-accounting-test",
        missed_cleavages=1,
    )

    accounting = build_digest_duplicate_accounting(peptides)

    assert accounting.total_peptide_occurrences == 5
    assert accounting.unique_sequence_count == 4
    assert accounting.duplicate_sequence_count == 1
    assert accounting.duplicate_occurrence_count == 1
    assert [entry.model_dump() for entry in accounting.repeated_sequences] == [
        {
            "sequence": "AAK",
            "occurrence_count": 2,
            "protein_accessions": ("duplicate-accounting-test",),
        }
    ]

from __future__ import annotations

from bijux_proteomics import (
    PeptideUniqueness,
    classify_peptide_uniqueness,
    digest_sequence,
)


def test_classify_peptide_uniqueness_distinguishes_unique_and_shared_peptides() -> None:
    peptides = (
        *digest_sequence("AKAAK", source_accession="P11111"),
        *digest_sequence("AKBBK".replace("B", "A"), source_accession="P22222"),
        *digest_sequence("QQQK", source_accession="P33333"),
    )

    entries = classify_peptide_uniqueness(tuple(peptides))
    by_sequence = {entry.sequence: entry for entry in entries}

    assert by_sequence["AK"].uniqueness is PeptideUniqueness.SHARED
    assert by_sequence["AK"].protein_accessions == ("P11111", "P22222")
    assert by_sequence["QQQK"].uniqueness is PeptideUniqueness.UNIQUE
    assert by_sequence["QQQK"].protein_accessions == ("P33333",)

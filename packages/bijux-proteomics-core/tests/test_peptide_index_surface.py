from __future__ import annotations

from bijux_proteomics import (
    PeptideUniqueness,
    build_peptide_protein_index,
    classify_peptide_uniqueness,
    digest_protein_records,
    digest_sequence,
    parse_fasta_document,
    FastaParseMode,
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


def test_build_peptide_protein_index_tracks_parent_coordinates() -> None:
    peptides = (
        *digest_sequence(
            "AKAAK", source_accession="P11111", source_identifier="protein-1"
        ),
        *digest_sequence(
            "KAAK", source_accession="P22222", source_identifier="protein-2"
        ),
    )

    entries = build_peptide_protein_index(tuple(peptides))
    by_sequence = {entry.sequence: entry for entry in entries}

    assert by_sequence["AAK"].protein_accessions == ("P11111", "P22222")
    assert [coordinate.model_dump() for coordinate in by_sequence["AAK"].coordinates] == [
        {
            "protein_accession": "P11111",
            "protein_family": "P11111",
            "source_identifier": "protein-1",
            "start": 3,
            "end": 5,
            "isoform": None,
        },
        {
            "protein_accession": "P22222",
            "protein_family": "P22222",
            "source_identifier": "protein-2",
            "start": 2,
            "end": 4,
            "isoform": None,
        },
    ]
    assert by_sequence["AK"].uniqueness is PeptideUniqueness.UNIQUE


def test_digest_protein_records_preserves_isoform_specific_origin_coordinates() -> None:
    report = parse_fasta_document(
        (
            ">sp|P12345|TP53_HUMAN canonical\nAKAK\n"
            ">sp|P12345-2|TP53_HUMAN isoform 2\nAKAK\n"
        ),
        mode=FastaParseMode.STRICT,
    )

    entries = build_peptide_protein_index(digest_protein_records(report.accepted_records))
    by_sequence = {entry.sequence: entry for entry in entries}

    assert by_sequence["AK"].protein_accessions == ("P12345", "P12345-2")
    assert [coordinate.model_dump() for coordinate in by_sequence["AK"].coordinates] == [
        {
            "protein_accession": "P12345",
            "protein_family": "P12345",
            "source_identifier": "sp|P12345|TP53_HUMAN",
            "start": 1,
            "end": 2,
            "isoform": None,
        },
        {
            "protein_accession": "P12345",
            "protein_family": "P12345",
            "source_identifier": "sp|P12345|TP53_HUMAN",
            "start": 3,
            "end": 4,
            "isoform": None,
        },
        {
            "protein_accession": "P12345-2",
            "protein_family": "P12345",
            "source_identifier": "sp|P12345-2|TP53_HUMAN",
            "start": 1,
            "end": 2,
            "isoform": 2,
        },
        {
            "protein_accession": "P12345-2",
            "protein_family": "P12345",
            "source_identifier": "sp|P12345-2|TP53_HUMAN",
            "start": 3,
            "end": 4,
            "isoform": 2,
        },
    ]

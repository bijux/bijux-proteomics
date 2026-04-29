from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from bijux_proteomics import (
    DecoyGenerationMode,
    FastaParseMode,
    build_fasta_provenance_manifest,
    build_fasta_stats,
    deduplicate_fasta_records,
    filter_fasta_records,
    generate_decoy_records,
    parse_fasta_document,
    parse_fasta_records,
    parse_uniprot_accession,
    sequence_checksum,
    validate_protein_sequence,
    validate_target_decoy_database,
)


def test_parse_fasta_records_preserves_header_identity() -> None:
    records = parse_fasta_records(
        ">sp|P12345|TP53_HUMAN Cellular tumor antigen p53\nMEEPQSDPSV\n"
    )

    assert len(records) == 1
    assert records[0].identifier == "sp|P12345|TP53_HUMAN"
    assert records[0].description == "Cellular tumor antigen p53"
    assert records[0].residues == "MEEPQSDPSV"


def test_parse_fasta_records_requires_header_first() -> None:
    with pytest.raises(ValueError, match="begin with a header"):
        parse_fasta_records("MEEPQSDPSV")


def test_parse_fasta_document_strict_rejects_duplicates_and_ambiguous_sequences(
    fasta_fixture_dir: Path,
) -> None:
    report = parse_fasta_document(
        (fasta_fixture_dir / "mixed_quality.fasta").read_text(),
        mode=FastaParseMode.STRICT,
    )

    assert report.total_records == 4
    assert len(report.accepted_records) == 2
    assert len(report.rejected_records) == 2
    assert report.duplicate_identifiers == ("sp|P12345|DEMO_HUMAN",)
    rejected_identifiers = {item.source_identifier for item in report.rejected_records}
    assert rejected_identifiers == {
        "sp|P12345|DEMO_HUMAN",
        "custom_ambig",
    }


def test_parse_fasta_document_permissive_accepts_ambiguous_terminal_stop_with_warnings(
    fasta_fixture_dir: Path,
) -> None:
    report = parse_fasta_document(
        (fasta_fixture_dir / "mixed_quality.fasta").read_text(),
        mode=FastaParseMode.PERMISSIVE,
    )

    ambiguous = next(
        record
        for record in report.accepted_records
        if record.source_identifier == "custom_ambig"
    )
    issue_codes = {issue.code for issue in ambiguous.validation_issues}
    assert ambiguous.residues == "ACDXZ"
    assert {
        "lowercase_residues",
        "terminal_stop_codon_removed",
        "ambiguous_residue",
    } <= issue_codes


def test_validate_protein_sequence_flags_invalid_character_and_stop_codon() -> None:
    result = validate_protein_sequence("ACD*?Z", mode=FastaParseMode.STRICT)

    issue_codes = {issue.code for issue in result.issues}
    assert "stop_codon" in issue_codes
    assert "invalid_character" in issue_codes
    assert result.is_valid is False


def test_parse_uniprot_accession_preserves_isoform_suffix() -> None:
    accession = parse_uniprot_accession("P12345-2")

    assert accession.accession == "P12345"
    assert accession.isoform == 2


def test_parse_uniprot_accession_rejects_invalid_tokens() -> None:
    with pytest.raises(ValueError, match="valid UniProt accession"):
        parse_uniprot_accession("TP53_HUMAN")


def test_sequence_checksum_normalizes_case_and_whitespace() -> None:
    assert sequence_checksum(" acd ef \n") == sequence_checksum("ACDEF")


def test_normalized_records_capture_accession_gene_and_organism(
    fasta_fixture_dir: Path,
) -> None:
    report = parse_fasta_document(
        (fasta_fixture_dir / "valid_records.fasta").read_text(),
        mode=FastaParseMode.STRICT,
    )
    record = report.accepted_records[0]

    assert record.accession_namespace == "uniprot"
    assert record.canonical_accession == "P04637"
    assert record.gene == "TP53"
    assert record.organism == "Homo sapiens"
    assert record.display_name == "TP53"


def test_build_fasta_stats_reports_lengths_duplicates_and_contaminants(
    fasta_fixture_dir: Path,
) -> None:
    report = parse_fasta_document(
        (fasta_fixture_dir / "dedup_input.fasta").read_text(),
        mode=FastaParseMode.PERMISSIVE,
    )
    stats = build_fasta_stats(report.accepted_records)

    assert stats.total_records == 4
    assert stats.unique_accessions == 3
    assert stats.total_residues == sum(
        record.residue_count for record in report.accepted_records
    )
    assert stats.duplicate_identifier_count == 1
    assert stats.duplicate_sequence_count == 2
    assert stats.contaminant_count == 1


def test_deduplicate_fasta_records_prefers_first_accession_then_sequence(
    fasta_fixture_dir: Path,
) -> None:
    report = parse_fasta_document(
        (fasta_fixture_dir / "dedup_input.fasta").read_text(),
        mode=FastaParseMode.PERMISSIVE,
    )
    records, dedup_report = deduplicate_fasta_records(report.accepted_records)

    assert len(records) == 2
    assert dedup_report.output_records == 2
    assert dedup_report.duplicate_accessions == ("sp|P11111|AAA_HUMAN",)
    assert dedup_report.duplicate_sequences == ("sp|P22222|BBB_MOUSE",)


def test_filter_fasta_records_supports_length_organism_and_contaminant_filters(
    fasta_fixture_dir: Path,
) -> None:
    report = parse_fasta_document(
        (fasta_fixture_dir / "dedup_input.fasta").read_text(),
        mode=FastaParseMode.PERMISSIVE,
    )
    filtered, filter_report = filter_fasta_records(
        report.accepted_records,
        min_length=9,
        organism="Homo sapiens",
        exclude_contaminants=True,
    )

    assert [record.canonical_accession for record in filtered] == ["P11111", "P11111"]
    assert filter_report.excluded_by_length == 0
    assert filter_report.excluded_by_organism == 1
    assert filter_report.excluded_as_contaminant == 1


def test_build_fasta_provenance_manifest_records_source_hash_and_counts(
    fasta_fixture_dir: Path,
) -> None:
    input_fasta = fasta_fixture_dir / "valid_records.fasta"
    report = parse_fasta_document(input_fasta.read_text(), mode=FastaParseMode.STRICT)
    manifest = build_fasta_provenance_manifest(
        operation="fasta-parse",
        source_path=input_fasta,
        parse_mode=FastaParseMode.STRICT,
        input_record_count=report.total_records,
        accepted_record_count=len(report.accepted_records),
        rejected_record_count=len(report.rejected_records),
        output_record_count=len(report.accepted_records),
        parameters={"mode": "strict"},
    )

    assert manifest.source_path == str(input_fasta)
    assert (
        manifest.source_sha256 == hashlib.sha256(input_fasta.read_bytes()).hexdigest()
    )
    assert manifest.accepted_record_count == 3
    assert manifest.document_schema.document_kind == "fasta_provenance_manifest"
    assert manifest.document_schema.content_hash is not None


def test_generate_decoy_records_supports_reverse_and_shuffle_modes(
    fasta_fixture_dir: Path,
) -> None:
    report = parse_fasta_document(
        (fasta_fixture_dir / "valid_records.fasta").read_text(),
        mode=FastaParseMode.STRICT,
    )
    reverse_decoys = generate_decoy_records(
        report.accepted_records,
        mode=DecoyGenerationMode.REVERSE,
    )
    shuffled_decoys = generate_decoy_records(
        report.accepted_records,
        mode=DecoyGenerationMode.SHUFFLE,
        seed=11,
    )

    assert reverse_decoys[0].canonical_accession.startswith("DECOY_")
    assert reverse_decoys[0].residues == report.accepted_records[0].residues[::-1]
    assert shuffled_decoys[0].residues != report.accepted_records[0].residues


def test_validate_target_decoy_database_detects_complete_pairs(
    fasta_fixture_dir: Path,
) -> None:
    report = parse_fasta_document(
        (fasta_fixture_dir / "target_decoy_valid.fasta").read_text(),
        mode=FastaParseMode.STRICT,
    )
    validation = validate_target_decoy_database(report.accepted_records)

    assert validation.valid is True
    assert validation.target_count == 2
    assert validation.decoy_count == 2
    assert not validation.missing_decoys


def test_validate_target_decoy_database_reports_missing_decoys(
    fasta_fixture_dir: Path,
) -> None:
    report = parse_fasta_document(
        (fasta_fixture_dir / "valid_records.fasta").read_text(),
        mode=FastaParseMode.STRICT,
    )
    validation = validate_target_decoy_database(report.accepted_records)

    assert validation.valid is False
    assert set(validation.missing_decoys) == {
        "P04637",
        "NP_000537.3",
        "ENSP00000354587",
    }

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from bijux_proteomics.sequences import (
    DecoyGenerationMode,
    DuplicateAccessionPolicy,
    FastaParseMode,
    ResiduePolicyState,
    append_contaminant_database,
    build_builtin_contaminant_records,
    build_decoy_generation_manifest,
    build_decoy_generation_report,
    build_fasta_database_profile,
    build_fasta_provenance_manifest,
    build_fasta_stats,
    build_sequence_residue_policy,
    canonicalize_protein_reference,
    compute_decoy_generation_reproducibility_hash,
    deduplicate_fasta_records,
    filter_fasta_records,
    generate_decoy_records,
    load_builtin_contaminant_records,
    parse_fasta_document,
    parse_fasta_records,
    parse_uniprot_accession,
    relabel_contaminant_records,
    render_fasta_profile_invalid_sequence_tsv,
    render_fasta_profile_length_distribution_tsv,
    render_fasta_profile_organism_distribution_tsv,
    render_fasta_profile_summary_tsv,
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


def test_parse_fasta_document_reports_empty_sequence_duplicate_accession_and_database_composition(
    fasta_fixture_dir: Path,
) -> None:
    report = parse_fasta_document(
        (fasta_fixture_dir / "production_grade_database.fasta").read_text(),
        mode=FastaParseMode.STRICT,
    )

    assert report.total_records == 9
    assert len(report.accepted_records) == 6
    assert len(report.rejected_records) == 3
    assert report.duplicate_identifiers == ()
    assert report.duplicate_accessions == ("uniprot:P04637",)
    rejected_by_identifier = {
        item.source_identifier: {issue.code for issue in item.issues}
        for item in report.rejected_records
    }
    assert rejected_by_identifier["P04637"] == {"duplicate_accession"}
    assert rejected_by_identifier["custom_empty"] == {"empty_sequence"}
    assert rejected_by_identifier["custom_invalid"] == {
        "unsupported_residue",
        "invalid_character",
    }
    assert report.database_composition.accepted_record_count == 6
    assert report.database_composition.target_count == 5
    assert report.database_composition.decoy_count == 1
    assert report.database_composition.contaminant_count == 1
    assert report.database_composition.accession_namespace_counts == {
        "custom": 2,
        "ensembl": 1,
        "refseq": 1,
        "uniprot": 2,
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


def test_parse_fasta_document_requires_explicit_duplicate_accession_policy() -> None:
    report = parse_fasta_document(
        (
            ">sp|P12345|PROT_HUMAN canonical\nMPEPTIDEK\n"
            ">sp|P12345|PROT_HUMAN_DUP duplicate\nMPEPTIDER\n"
        ),
        mode=FastaParseMode.PERMISSIVE,
    )

    assert len(report.accepted_records) == 1
    assert len(report.rejected_records) == 1
    assert report.duplicate_accessions == ("uniprot:P12345",)
    assert report.rejected_records[0].source_identifier == "sp|P12345|PROT_HUMAN_DUP"
    assert {issue.code for issue in report.rejected_records[0].issues} == {
        "duplicate_accession"
    }


def test_parse_fasta_document_can_accept_duplicate_accessions_with_warning_policy() -> (
    None
):
    report = parse_fasta_document(
        (
            ">sp|P12345|PROT_HUMAN canonical GN=TP53 OS=Homo sapiens\nMPEPTIDEK\n"
            ">sp|P12345|PROT_HUMAN_DUP duplicate GN=TP53 OS=Homo sapiens\nMPEPTIDER\n"
        ),
        mode=FastaParseMode.PERMISSIVE,
        duplicate_accession_policy=DuplicateAccessionPolicy.ACCEPT_WITH_WARNING,
    )

    assert len(report.accepted_records) == 2
    duplicate_record = report.accepted_records[1]
    assert duplicate_record.canonical_accession == "P12345"
    assert duplicate_record.gene == "TP53"
    assert duplicate_record.organism == "Homo sapiens"
    assert {issue.code for issue in duplicate_record.validation_issues} == {
        "duplicate_accession"
    }


def test_validate_protein_sequence_flags_invalid_character_and_stop_codon() -> None:
    result = validate_protein_sequence("ACD*?Z", mode=FastaParseMode.STRICT)

    issue_codes = {issue.code for issue in result.issues}
    assert "stop_codon" in issue_codes
    assert "invalid_character" in issue_codes
    assert result.is_valid is False


def test_sequence_residue_policy_explicitly_distinguishes_warnings_from_refusals() -> (
    None
):
    strict_policy = build_sequence_residue_policy(FastaParseMode.STRICT)
    permissive_policy = build_sequence_residue_policy(FastaParseMode.PERMISSIVE)

    strict_states = {entry.residue: entry.state for entry in strict_policy.entries}
    permissive_states = {
        entry.residue: entry.state for entry in permissive_policy.entries
    }

    assert strict_states["B"] is ResiduePolicyState.REFUSED
    assert permissive_states["B"] is ResiduePolicyState.ACCEPTED_WITH_WARNING
    assert permissive_states["U"] is ResiduePolicyState.REFUSED
    assert permissive_states["O"] is ResiduePolicyState.REFUSED


def test_validate_protein_sequence_permissive_mode_still_refuses_unsupported_residues() -> (
    None
):
    result = validate_protein_sequence("ACDUO", mode=FastaParseMode.PERMISSIVE)

    issue_codes = {issue.code for issue in result.issues}
    assert "unsupported_residue" in issue_codes
    assert result.is_valid is False


def test_parse_uniprot_accession_preserves_isoform_suffix() -> None:
    accession = parse_uniprot_accession("P12345-2")

    assert accession.accession == "P12345"
    assert accession.isoform == 2


def test_parse_uniprot_accession_rejects_invalid_tokens() -> None:
    with pytest.raises(ValueError, match="valid UniProt accession"):
        parse_uniprot_accession("TP53_HUMAN")


def test_canonicalize_protein_reference_normalizes_supported_accession_families() -> (
    None
):
    assert canonicalize_protein_reference("sp|P04637|P53_HUMAN") == "P04637"
    assert (
        canonicalize_protein_reference("ref|NP_000537.3|CALM1_HUMAN") == "NP_000537.3"
    )
    assert canonicalize_protein_reference("ENSP00000354587.5") == "ENSP00000354587"
    assert canonicalize_protein_reference("lab_bait_001") == "lab_bait_001"


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


def test_parse_fasta_document_extracts_biological_headers_across_supported_families() -> (
    None
):
    report = parse_fasta_document(
        (
            ">sp|P04637|P53_HUMAN Cellular tumor antigen p53 OS=Homo sapiens GN=TP53\n"
            "MEEPQSDPSV\n"
            ">ref|NP_000537.3|TP53 isoform alpha [Homo sapiens]\n"
            "MEEPQSDPSV\n"
            ">ENSP00000354587.5 pep chromosome:GRCh38 gene_symbol:CALM1 description:Calmodulin-1\n"
            "MADQLTEEQI\n"
            ">custom_bait_001 Synthetic bait protein\n"
            "PEPTIDER\n"
            ">DECOY_sp|P11111|AAA_HUMAN Alpha decoy OS=Homo sapiens GN=AAA\n"
            "PEPTIDEK\n"
            ">CON__trypsin_lab Trypsin contaminant OS=Bos taurus GN=PRSS1\n"
            "MKWVTFISL\n"
        ),
        mode=FastaParseMode.STRICT,
    )

    by_identifier = {
        record.source_identifier: record for record in report.accepted_records
    }

    assert by_identifier["sp|P04637|P53_HUMAN"].accession_namespace == "uniprot"
    assert by_identifier["sp|P04637|P53_HUMAN"].canonical_accession == "P04637"
    assert by_identifier["sp|P04637|P53_HUMAN"].gene == "TP53"
    assert by_identifier["sp|P04637|P53_HUMAN"].organism == "Homo sapiens"
    assert by_identifier["sp|P04637|P53_HUMAN"].description == (
        "Cellular tumor antigen p53"
    )

    assert by_identifier["ref|NP_000537.3|TP53"].accession_namespace == "refseq"
    assert by_identifier["ref|NP_000537.3|TP53"].canonical_accession == "NP_000537.3"

    assert by_identifier["ENSP00000354587.5"].accession_namespace == "ensembl"
    assert by_identifier["ENSP00000354587.5"].canonical_accession == "ENSP00000354587"
    assert by_identifier["ENSP00000354587.5"].gene == "CALM1"
    assert by_identifier["ENSP00000354587.5"].description == "Calmodulin-1"

    assert by_identifier["custom_bait_001"].accession_namespace == "custom"
    assert by_identifier["custom_bait_001"].canonical_accession == "custom_bait_001"

    assert by_identifier["DECOY_sp|P11111|AAA_HUMAN"].decoy is True
    assert by_identifier["DECOY_sp|P11111|AAA_HUMAN"].canonical_accession == (
        "DECOY_P11111"
    )
    assert by_identifier["CON__trypsin_lab"].contaminant is True


def test_build_fasta_stats_reports_lengths_duplicates_and_contaminants(
    fasta_fixture_dir: Path,
) -> None:
    report = parse_fasta_document(
        (fasta_fixture_dir / "dedup_input.fasta").read_text(),
        mode=FastaParseMode.PERMISSIVE,
        duplicate_accession_policy=DuplicateAccessionPolicy.ACCEPT_WITH_WARNING,
    )
    stats = build_fasta_stats(report.accepted_records)

    assert stats.total_records == 4
    assert stats.unique_accessions == 3
    assert stats.total_residues == sum(
        record.residue_count for record in report.accepted_records
    )
    assert stats.duplicate_identifier_count == 1
    assert stats.duplicate_accession_count == 1
    assert stats.duplicate_sequence_count == 2
    assert stats.contaminant_count == 1


def test_build_fasta_stats_reports_target_and_decoy_counts(
    fasta_fixture_dir: Path,
) -> None:
    report = parse_fasta_document(
        (fasta_fixture_dir / "target_decoy_valid.fasta").read_text(),
        mode=FastaParseMode.STRICT,
    )
    stats = build_fasta_stats(report.accepted_records)

    assert stats.total_records == 4
    assert stats.target_count == 2
    assert stats.decoy_count == 2
    assert stats.accession_namespace_counts == {"uniprot": 4}


def test_load_builtin_contaminant_records_returns_labeled_builtin_panel() -> None:
    records = build_builtin_contaminant_records()
    with pytest.warns(DeprecationWarning, match="build_builtin_contaminant_records"):
        legacy_records = load_builtin_contaminant_records()

    assert len(records) == 4
    assert legacy_records == records
    assert all(record.contaminant for record in records)
    assert all(record.canonical_accession.startswith("CON__") for record in records)
    assert any(record.gene == "ALB" for record in records)
    assert any(record.gene == "PRSS1" for record in records)


def test_append_contaminant_database_supports_builtin_and_external_fastas(
    fasta_fixture_dir: Path,
) -> None:
    target_report = parse_fasta_document(
        (fasta_fixture_dir / "valid_records.fasta").read_text(),
        mode=FastaParseMode.STRICT,
    )
    external_report = parse_fasta_document(
        (fasta_fixture_dir / "external_contaminants.fasta").read_text(),
        mode=FastaParseMode.STRICT,
    )

    appended, build_report = append_contaminant_database(
        target_report.accepted_records,
        include_builtin=True,
        external_contaminant_records=external_report.accepted_records,
    )

    assert build_report.input_target_record_count == 3
    assert build_report.appended_builtin_record_count == 4
    assert build_report.appended_external_record_count == 2
    assert build_report.output_record_count == 9
    assert all(record.contaminant for record in appended[3:])
    assert all(record.source_header.startswith("CON__") for record in appended[3:])
    assert "CON__trypsin_lab" in build_report.contaminant_accessions
    assert build_report.contaminant_namespace_counts == {"custom": 2, "uniprot": 4}


def test_relabel_contaminant_records_preserves_existing_prefixes(
    fasta_fixture_dir: Path,
) -> None:
    report = parse_fasta_document(
        (fasta_fixture_dir / "dedup_input.fasta").read_text(),
        mode=FastaParseMode.PERMISSIVE,
        duplicate_accession_policy=DuplicateAccessionPolicy.ACCEPT_WITH_WARNING,
    )
    relabeled = relabel_contaminant_records(report.accepted_records[-1:])

    assert len(relabeled) == 1
    assert relabeled[0].source_identifier == "CON__CRAP"
    assert relabeled[0].canonical_accession == "CON__CRAP"
    assert relabeled[0].contaminant is True


def test_build_fasta_database_profile_reports_length_and_organism_distribution(
    fasta_fixture_dir: Path,
) -> None:
    report = parse_fasta_document(
        (fasta_fixture_dir / "production_grade_database.fasta").read_text(),
        mode=FastaParseMode.STRICT,
    )

    profile = build_fasta_database_profile(
        report.accepted_records,
        rejected_records=report.rejected_records,
    )

    assert profile.summary.input_record_count == 9
    assert profile.summary.protein_count == 6
    assert profile.summary.rejected_record_count == 3
    assert profile.summary.target_count == 5
    assert profile.summary.decoy_count == 1
    assert profile.summary.contaminant_count == 1
    assert profile.summary.organism_annotated_count == 5
    assert profile.summary.organism_missing_count == 1
    assert profile.summary.accession_namespace_counts == {
        "custom": 2,
        "ensembl": 1,
        "refseq": 1,
        "uniprot": 2,
    }
    assert [row.bin_label for row in profile.length_distribution] == [
        "1-99",
        "100-249",
        "250-499",
        "500-999",
        "1000+",
    ]
    assert profile.length_distribution[0].protein_count == 6
    assert profile.length_distribution[1].protein_count == 0
    assert [row.organism for row in profile.organism_distribution] == [
        "Homo sapiens",
        "Mus musculus",
    ]
    assert profile.organism_distribution[0].protein_count == 4
    assert profile.organism_distribution[0].decoy_count == 1
    assert profile.organism_distribution[0].contaminant_count == 1
    assert profile.organism_distribution[1].protein_count == 1
    assert [row.source_identifier for row in profile.invalid_sequence_report] == [
        "custom_empty",
        "custom_invalid",
    ]
    assert profile.invalid_sequence_report[0].primary_issue_code == "empty_sequence"
    assert profile.invalid_sequence_report[1].primary_issue_code == "invalid_character"


def test_render_fasta_profile_ledgers_emit_tsv_headers_and_rows(
    fasta_fixture_dir: Path,
) -> None:
    report = parse_fasta_document(
        (fasta_fixture_dir / "production_grade_database.fasta").read_text(),
        mode=FastaParseMode.STRICT,
    )
    profile = build_fasta_database_profile(
        report.accepted_records,
        rejected_records=report.rejected_records,
    )

    summary_tsv = render_fasta_profile_summary_tsv(profile)
    length_tsv = render_fasta_profile_length_distribution_tsv(profile)
    organism_tsv = render_fasta_profile_organism_distribution_tsv(profile)
    invalid_sequence_tsv = render_fasta_profile_invalid_sequence_tsv(profile)

    assert summary_tsv.splitlines()[0].startswith("input_record_count\tprotein_count")
    assert "\t6\t3\t6\t5\t1\t1\t" in summary_tsv
    assert length_tsv.splitlines()[0] == (
        "bin_label\tmin_length\tmax_length\tprotein_count\tresidue_count"
    )
    assert "1-99\t1\t99\t6\t116" in length_tsv
    assert organism_tsv.splitlines()[0] == (
        "organism\tprotein_count\ttarget_count\tdecoy_count\tcontaminant_count"
    )
    assert "Homo sapiens\t4\t3\t1\t1" in organism_tsv
    assert invalid_sequence_tsv.splitlines()[0] == (
        "source_identifier\tsource_header\tprimary_issue_code\tprimary_issue_message\tissue_codes\tissue_messages"
    )
    assert (
        "custom_empty\tcustom_empty Example empty\tempty_sequence\tsequence must contain at least one amino-acid residue"
        in invalid_sequence_tsv
    )
    assert (
        "custom_invalid\tcustom_invalid Example invalid\tinvalid_character\tsequence contains invalid non-residue characters"
        in invalid_sequence_tsv
    )


def test_deduplicate_fasta_records_prefers_first_accession_then_sequence(
    fasta_fixture_dir: Path,
) -> None:
    report = parse_fasta_document(
        (fasta_fixture_dir / "dedup_input.fasta").read_text(),
        mode=FastaParseMode.PERMISSIVE,
        duplicate_accession_policy=DuplicateAccessionPolicy.ACCEPT_WITH_WARNING,
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
        duplicate_accession_policy=DuplicateAccessionPolicy.ACCEPT_WITH_WARNING,
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


def test_build_decoy_generation_report_flags_unchanged_shuffle_sequences() -> None:
    report = parse_fasta_document(
        ">sp|P00001|HOMO_HUMAN Homopolymer OS=Homo sapiens GN=HOMO\nAAAAAA\n",
        mode=FastaParseMode.STRICT,
    )
    decoys = generate_decoy_records(
        report.accepted_records,
        mode=DecoyGenerationMode.SHUFFLE,
        seed=11,
    )

    generation_report = build_decoy_generation_report(
        report.accepted_records,
        decoys,
        mode=DecoyGenerationMode.SHUFFLE,
        prefix="DECOY_",
        seed=11,
    )

    assert generation_report.generated_decoy_count == 1
    assert generation_report.unchanged_sequence_count == 1
    assert generation_report.unchanged_sequence_accessions == ("DECOY_P00001",)
    assert generation_report.target_sequence_collision_count == 1


def test_generate_decoy_records_rejects_prefix_collisions_with_existing_targets() -> (
    None
):
    report = parse_fasta_document(
        (
            ">target_one Alpha target [Homo sapiens]\nMPEPTIDE\n"
            ">LAB_target_one Existing prefixed target [Homo sapiens]\nMSEQENCE\n"
        ),
        mode=FastaParseMode.STRICT,
    )

    with pytest.raises(
        ValueError,
        match="prefix would collide with existing target accessions",
    ):
        generate_decoy_records(
            report.accepted_records,
            mode=DecoyGenerationMode.REVERSE,
            prefix="LAB_",
        )


def test_decoy_generation_manifest_captures_reproducibility_hash(
    fasta_fixture_dir: Path,
) -> None:
    input_fasta = fasta_fixture_dir / "valid_records.fasta"
    report = parse_fasta_document(input_fasta.read_text(), mode=FastaParseMode.STRICT)
    decoys = generate_decoy_records(
        report.accepted_records,
        mode=DecoyGenerationMode.SHUFFLE,
        seed=11,
    )
    output_records = (*report.accepted_records, *decoys)

    manifest = build_decoy_generation_manifest(
        input_records=report.accepted_records,
        output_records=output_records,
        mode=DecoyGenerationMode.SHUFFLE,
        prefix="DECOY_",
        seed=11,
        source_path=input_fasta,
    )

    assert manifest.output_record_count == len(output_records)
    assert (
        manifest.reproducibility_hash
        == compute_decoy_generation_reproducibility_hash(
            report.accepted_records,
            mode=DecoyGenerationMode.SHUFFLE,
            prefix="DECOY_",
            seed=11,
        )
    )
    assert manifest.document_schema.document_kind == "decoy_generation_manifest"


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


def test_generate_decoy_records_rejects_target_plus_decoy_input() -> None:
    report = parse_fasta_document(
        (
            ">sp|P00001|ALPHA_HUMAN Alpha OS=Homo sapiens GN=ALPHA\nMPEPTIDE\n"
            ">DECOY_sp|P00001|ALPHA_HUMAN Alpha decoy OS=Homo sapiens GN=ALPHA\n"
            "EDITPEPM\n"
        ),
        mode=FastaParseMode.STRICT,
    )

    with pytest.raises(ValueError, match="requires target-only inputs"):
        generate_decoy_records(
            report.accepted_records, mode=DecoyGenerationMode.REVERSE
        )

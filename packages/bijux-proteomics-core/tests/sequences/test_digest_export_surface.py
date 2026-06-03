from __future__ import annotations

from collections.abc import Mapping
import json
from pathlib import Path

import pytest

from bijux_proteomics.sequences import FastaParseMode, parse_fasta_document
from bijux_proteomics.sequences.digestion import (
    PeptideDigestionMode,
    build_digest_benchmark_report,
    build_digest_manifest,
    build_digest_policy,
    compute_digest_policy_hash,
    digest_protein_records,
    export_peptide_protein_table_tsv,
    export_peptides_fasta,
    export_peptides_jsonl,
    export_peptides_parquet,
    export_peptides_tsv,
    peptide_export_fingerprint,
)
from bijux_proteomics_foundation.outcomes.exceptions import (
    MissingOptionalDependencyError,
)


def test_digest_protein_records_and_manifest_are_stable(
    fasta_fixture_dir: Path,
) -> None:
    input_fasta = fasta_fixture_dir / "valid_records.fasta"
    report = parse_fasta_document(input_fasta.read_text(), mode=FastaParseMode.STRICT)
    peptides = digest_protein_records(
        report.accepted_records,
        protease="trypsin",
        missed_cleavages=1,
        mode=PeptideDigestionMode.FULL,
        min_length=3,
        max_length=25,
    )

    manifest = build_digest_manifest(
        peptides=peptides,
        protease="trypsin",
        digestion_mode=PeptideDigestionMode.FULL,
        missed_cleavages=1,
        min_length=3,
        max_length=25,
        min_mass=None,
        max_mass=None,
        source_path=input_fasta,
        input_record_count=report.total_records,
    )

    assert manifest.protease == "trypsin"
    assert manifest.input_record_count == 3
    assert manifest.output_peptide_count == len(peptides)
    assert manifest.digest_policy.protease == "trypsin"
    assert manifest.policy_hash == compute_digest_policy_hash(manifest.digest_policy)
    assert manifest.output_sha256 == peptide_export_fingerprint(peptides)
    assert manifest.document_schema.document_kind == "peptide_digest_manifest"


def test_digest_policy_hash_captures_exact_cleavage_and_filter_assumptions() -> None:
    policy = build_digest_policy(
        protease="trypsin",
        digestion_mode=PeptideDigestionMode.FULL,
        missed_cleavages=1,
        min_length=7,
        max_length=30,
        min_mass=500.0,
        max_mass=3000.0,
    )

    assert policy.cleavage_residues == "KR"
    assert policy.blocked_by_next == "P"
    assert compute_digest_policy_hash(policy) == compute_digest_policy_hash(policy)


def test_digest_exports_write_stable_tsv_jsonl_fasta_and_peptide_protein_table(
    fasta_fixture_dir: Path,
    tmp_path: Path,
) -> None:
    report = parse_fasta_document(
        (fasta_fixture_dir / "valid_records.fasta").read_text(),
        mode=FastaParseMode.STRICT,
    )
    peptides = digest_protein_records(
        report.accepted_records,
        protease="trypsin",
        min_length=3,
    )
    tsv_path = tmp_path / "peptides.tsv"
    jsonl_path = tmp_path / "peptides.jsonl"
    fasta_path = tmp_path / "peptides.fasta"
    protein_table_path = tmp_path / "peptide_protein_table.tsv"

    export_peptides_tsv(peptides, tsv_path)
    export_peptides_jsonl(peptides, jsonl_path)
    export_peptides_fasta(peptides, fasta_path)
    export_peptide_protein_table_tsv(peptides, protein_table_path)

    tsv_lines = tsv_path.read_text().splitlines()
    assert tsv_lines[0].startswith("source_accession\tsource_identifier\tsequence")
    assert "\tlength\t" in tsv_lines[0]
    assert len(tsv_lines) == len(peptides) + 1

    jsonl_rows = [json.loads(line) for line in jsonl_path.read_text().splitlines()]
    assert len(jsonl_rows) == len(peptides)
    assert {"sequence", "length", "neutral_mass", "protease"} <= set(jsonl_rows[0])
    assert jsonl_rows[0]["length"] == len(jsonl_rows[0]["sequence"])

    fasta_lines = fasta_path.read_text().splitlines()
    assert fasta_lines[0].startswith(">")
    assert "|mc=" in fasta_lines[0]
    assert "|len=" in fasta_lines[0]
    assert fasta_lines[1] == peptides[0].sequence

    protein_table_lines = protein_table_path.read_text().splitlines()
    assert protein_table_lines[0].startswith("sequence\tlength\tneutral_mass")
    first_table_row = protein_table_lines[1].split("\t")
    assert first_table_row[0] == peptides[0].sequence
    assert int(first_table_row[1]) == len(peptides[0].sequence)
    assert int(first_table_row[9]) == peptides[0].missed_cleavages


def test_digest_export_fingerprint_is_reproducible(fasta_fixture_dir: Path) -> None:
    report = parse_fasta_document(
        (fasta_fixture_dir / "valid_records.fasta").read_text(),
        mode=FastaParseMode.STRICT,
    )
    left = digest_protein_records(
        report.accepted_records, protease="trypsin", min_length=3
    )
    right = digest_protein_records(
        report.accepted_records, protease="trypsin", min_length=3
    )

    assert peptide_export_fingerprint(left) == peptide_export_fingerprint(right)


def test_digest_repeatability_fixture_produces_identical_peptide_and_manifest_outputs() -> (
    None
):
    input_fasta = (
        Path(__file__).resolve().parent.parent
        / "fixtures"
        / "digestion"
        / "repeatability_input.fasta"
    )
    report = parse_fasta_document(input_fasta.read_text(), mode=FastaParseMode.STRICT)

    left = digest_protein_records(
        report.accepted_records,
        protease="trypsin",
        missed_cleavages=1,
        mode=PeptideDigestionMode.FULL,
        min_length=2,
        max_length=25,
    )
    right = digest_protein_records(
        report.accepted_records,
        protease="trypsin",
        missed_cleavages=1,
        mode=PeptideDigestionMode.FULL,
        min_length=2,
        max_length=25,
    )

    left_manifest = build_digest_manifest(
        peptides=left,
        protease="trypsin",
        digestion_mode=PeptideDigestionMode.FULL,
        missed_cleavages=1,
        min_length=2,
        max_length=25,
        min_mass=None,
        max_mass=None,
        source_path=input_fasta,
        input_record_count=report.total_records,
    )
    right_manifest = build_digest_manifest(
        peptides=right,
        protease="trypsin",
        digestion_mode=PeptideDigestionMode.FULL,
        missed_cleavages=1,
        min_length=2,
        max_length=25,
        min_mass=None,
        max_mass=None,
        source_path=input_fasta,
        input_record_count=report.total_records,
    )

    assert [peptide.to_dict() for peptide in left] == [
        peptide.to_dict() for peptide in right
    ]
    assert peptide_export_fingerprint(left) == peptide_export_fingerprint(right)
    assert left_manifest.policy_hash == right_manifest.policy_hash
    assert left_manifest.output_sha256 == right_manifest.output_sha256
    assert (
        left_manifest.digest_policy.to_dict() == right_manifest.digest_policy.to_dict()
    )


def test_digest_benchmark_report_exposes_rate_metrics() -> None:
    peptides = digest_protein_records(
        (
            parse_fasta_document(
                ">sp|P12345|DEMO Demo\nMKWVTFISLLFLFSSAYSRGVFR\n",
                mode=FastaParseMode.STRICT,
            ).accepted_records[0],
        ),
        protease="trypsin",
        min_length=3,
    )
    report = build_digest_benchmark_report(
        protein_count=1,
        total_residues=23,
        peptides=peptides,
        elapsed_seconds=0.5,
        peak_memory_bytes=2048,
    )

    assert report.peptide_count == len(peptides)
    assert report.peptides_per_second == len(peptides) / 0.5
    assert report.peak_memory_bytes == 2048


def test_export_peptides_parquet_is_feature_gated(
    fasta_fixture_dir: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    report = parse_fasta_document(
        (fasta_fixture_dir / "valid_records.fasta").read_text(),
        mode=FastaParseMode.STRICT,
    )
    peptides = digest_protein_records(report.accepted_records, protease="trypsin")

    import builtins

    original_import = builtins.__import__

    def fake_import(
        name: str,
        globals: Mapping[str, object] | None = None,
        locals: Mapping[str, object] | None = None,
        fromlist: tuple[str, ...] = (),
        level: int = 0,
    ) -> object:
        if name.startswith("pyarrow"):
            raise ImportError("simulated missing pyarrow")
        return original_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    with pytest.raises(
        MissingOptionalDependencyError,
        match="bijux-proteomics-core\\[parquet\\]",
    ):
        export_peptides_parquet(peptides, tmp_path / "peptides.parquet")

from __future__ import annotations

from collections.abc import Mapping
import json
from pathlib import Path

import pytest

from bijux_proteomics import (
    FastaParseMode,
    PeptideDigestionMode,
    build_digest_benchmark_report,
    build_digest_manifest,
    digest_protein_records,
    export_peptides_jsonl,
    export_peptides_parquet,
    export_peptides_tsv,
    parse_fasta_document,
    peptide_export_fingerprint,
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
    assert manifest.output_sha256 == peptide_export_fingerprint(peptides)
    assert manifest.document_schema.document_kind == "peptide_digest_manifest"


def test_digest_exports_write_stable_tsv_and_jsonl(
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

    export_peptides_tsv(peptides, tsv_path)
    export_peptides_jsonl(peptides, jsonl_path)

    tsv_lines = tsv_path.read_text().splitlines()
    assert tsv_lines[0].startswith("source_accession\tsource_identifier\tsequence")
    assert len(tsv_lines) == len(peptides) + 1

    jsonl_rows = [json.loads(line) for line in jsonl_path.read_text().splitlines()]
    assert len(jsonl_rows) == len(peptides)
    assert {"sequence", "neutral_mass", "protease"} <= set(jsonl_rows[0])


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
    with pytest.raises(RuntimeError, match="pyarrow"):
        export_peptides_parquet(peptides, tmp_path / "peptides.parquet")

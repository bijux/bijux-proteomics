# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.sequences import FastaParseMode, parse_fasta_document
from bijux_proteomics.sequences.digestion import PeptideDigestionMode
from bijux_proteomics.sequences.theoretical_digest import (
    build_theoretical_digest_bundle,
    export_theoretical_digest_bundle,
)


def _fasta_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "fasta" / name


def test_theoretical_digest_export_writes_governed_tsv_bundle(tmp_path: Path) -> None:
    report = parse_fasta_document(
        _fasta_fixture("valid_records.fasta").read_text(),
        mode=FastaParseMode.STRICT,
    )
    bundle = build_theoretical_digest_bundle(
        report.accepted_records,
        protease="trypsin",
        missed_cleavages=1,
        digestion_mode=PeptideDigestionMode.FULL,
        min_length=3,
        max_length=25,
    )

    peptides_path, mappings_path, summary_path = export_theoretical_digest_bundle(
        bundle,
        tmp_path,
    )

    assert peptides_path.name == "digest_peptides.tsv"
    assert mappings_path.name == "peptide_to_protein.tsv"
    assert summary_path.name == "digest_summary.tsv"
    assert (
        peptides_path.read_text()
        .splitlines()[0]
        .startswith("canonical_notation\tstripped_sequence")
    )
    assert (
        mappings_path.read_text()
        .splitlines()[0]
        .startswith("canonical_notation\tstripped_sequence\tsource_accession")
    )
    assert (
        summary_path.read_text()
        .splitlines()[0]
        .startswith("input_record_count\tpeptide_occurrence_count")
    )
    assert bundle.search_space_hash in summary_path.read_text()

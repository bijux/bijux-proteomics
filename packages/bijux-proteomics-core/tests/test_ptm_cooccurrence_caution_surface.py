# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.ptm import map_ptm_evidence_to_protein_sites, parse_ptm_localization_tsv
from bijux_proteomics.ptm_advanced_workflows import build_ptm_cooccurrence_caution_report
from bijux_proteomics.sequences import FastaParseMode, parse_fasta_document


def _fixture_path(name: str) -> Path:
    return Path(__file__).parent / "fixtures" / "ptm" / name


def _protein_sequences() -> dict[str, str]:
    fasta = Path(__file__).parent / "fixtures" / "fasta" / "ptm_sites.fasta"
    report = parse_fasta_document(fasta.read_text(), mode=FastaParseMode.STRICT)
    return {record.canonical_accession: record.residues for record in report.accepted_records}


def test_ptm_cooccurrence_caution_report_separates_evidence_levels() -> None:
    parsed = parse_ptm_localization_tsv(_fixture_path("localization_results.tsv"))
    mappings = map_ptm_evidence_to_protein_sites(
        parsed.accepted_records, protein_sequences=_protein_sequences()
    )

    run_by_spectrum = {
        "scan=ptm-001": "run-a",
        "scan=ptm-002": "run-a",
        "scan=ptm-003": "run-b",
        "scan=ptm-004": "run-b",
    }
    report = build_ptm_cooccurrence_caution_report(
        mappings,
        spectrum_run_by_id=run_by_spectrum,
    )

    assert report.entries
    assert report.same_protein_pair_count >= 1
    assert report.same_sample_pair_count >= 1
    assert report.same_run_pair_count >= 1
    pair = next(entry for entry in report.entries if entry.same_protein_evidence)
    assert "protein-level" in pair.caution or "sample-level" in pair.caution or "co-localization" in pair.caution

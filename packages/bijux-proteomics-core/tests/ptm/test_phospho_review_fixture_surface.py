# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.ptm import (
    build_ptm_site_table,
    map_ptm_evidence_to_protein_sites,
    parse_ptm_localization_tsv,
)
from bijux_proteomics.ptm.review import (
    build_phospho_specific_review_fixture_report,
)
from bijux_proteomics.quantification import parse_ms1_feature_table
from bijux_proteomics.sequences import FastaParseMode, parse_fasta_document


def _ptm_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "ptm" / name


def _protein_sequences() -> dict[str, str]:
    fasta = (
        Path(__file__).resolve().parent.parent
        / "fixtures"
        / "fasta"
        / "ptm_sites.fasta"
    )
    report = parse_fasta_document(fasta.read_text(), mode=FastaParseMode.STRICT)
    return {
        record.canonical_accession: record.residues
        for record in report.accepted_records
    }


def test_phospho_review_fixture_report_tracks_motif_occupancy_and_ambiguity() -> None:
    parsed = parse_ptm_localization_tsv(_ptm_fixture("localization_results.tsv"))
    mappings = map_ptm_evidence_to_protein_sites(
        parsed.accepted_records, protein_sequences=_protein_sequences()
    )
    site_entries = build_ptm_site_table(mappings)
    features = parse_ms1_feature_table(
        _ptm_fixture("ptm_features.tsv")
    ).accepted_records

    report = build_phospho_specific_review_fixture_report(
        site_entries,
        feature_records=features,
        protein_sequences=_protein_sequences(),
    )

    assert report.phospho_site_keys
    assert report.motif_window_count == len(report.phospho_site_keys)
    assert report.occupancy_sample_count >= len(report.quantified_sample_ids)
    assert "C1" in report.quantified_sample_ids
    assert report.ambiguous_site_keys

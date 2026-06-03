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
    build_ptm_occupancy_counterpart_report,
)
from bijux_proteomics.quantification import parse_ms1_feature_table
from bijux_proteomics.sequences import FastaParseMode, parse_fasta_document


def _fixture_path(name: str) -> Path:
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


def test_ptm_occupancy_counterpart_report_marks_missing_counterparts_and_ambiguity() -> (
    None
):
    parsed = parse_ptm_localization_tsv(_fixture_path("localization_results.tsv"))
    mappings = map_ptm_evidence_to_protein_sites(
        parsed.accepted_records, protein_sequences=_protein_sequences()
    )
    site_entries = build_ptm_site_table(mappings)
    feature_records = parse_ms1_feature_table(
        _fixture_path("ptm_features.tsv")
    ).accepted_records

    feature_records = tuple(
        record
        for record in feature_records
        if not (record.sample_id == "T2" and record.canonical_peptide == "SPEPTIDEK")
    )
    report = build_ptm_occupancy_counterpart_report(
        site_entries,
        feature_records=feature_records,
    )

    assert report.entries
    assert report.high_confidence_count >= 1
    assert report.missing_counterpart_count >= 1
    assert report.missing_unmodified_evidence_count >= 1
    assert report.ambiguous_site_count >= 1

    missing_entry = next(
        entry
        for entry in report.entries
        if entry.counterpart_status.value == "missing_counterpart"
    )
    assert missing_entry.confidence_tier.value == "missing_unmodified_evidence"
    assert "cannot be treated as high-confidence" in missing_entry.caveat
    assert (
        missing_entry.modified_feature_count == 0
        or missing_entry.unmodified_feature_count == 0
    )

    complete_entry = next(
        entry
        for entry in report.entries
        if entry.counterpart_status.value == "complete"
    )
    assert complete_entry.confidence_tier.value == "high_confidence"
    assert complete_entry.modified_peptides
    assert complete_entry.unmodified_peptides

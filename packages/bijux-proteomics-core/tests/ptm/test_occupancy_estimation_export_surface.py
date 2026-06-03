# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.ptm import (
    build_ptm_occupancy_counterpart_report,
    build_ptm_site_occupancy_report,
    build_ptm_site_table,
    map_ptm_evidence_to_protein_sites,
    parse_ptm_localization_tsv,
    render_ptm_occupancy_counterpart_tsv,
    render_ptm_site_occupancy_entry_tsv,
    render_ptm_site_occupancy_summary_tsv,
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


def test_ptm_occupancy_tsv_renderers_preserve_counterpart_linkage() -> None:
    parsed = parse_ptm_localization_tsv(_fixture_path("localization_results.tsv"))
    mappings = map_ptm_evidence_to_protein_sites(
        parsed.accepted_records,
        protein_sequences=_protein_sequences(),
    )
    site_entries = build_ptm_site_table(mappings)
    feature_records = parse_ms1_feature_table(
        _fixture_path("ptm_features.tsv")
    ).accepted_records
    occupancy_report = build_ptm_site_occupancy_report(
        site_entries,
        feature_records=feature_records,
    )
    counterpart_report = build_ptm_occupancy_counterpart_report(
        site_entries,
        feature_records=feature_records,
    )

    summary_tsv = render_ptm_site_occupancy_summary_tsv(occupancy_report)
    entry_tsv = render_ptm_site_occupancy_entry_tsv(occupancy_report)
    counterpart_tsv = render_ptm_occupancy_counterpart_tsv(counterpart_report)

    assert summary_tsv.splitlines()[0] == (
        "entry_count\tcomplete_count\thigh_confidence_count\tmissing_counterpart_count\tmissing_unmodified_evidence_count\tmissing_modified_evidence_count\tambiguous_site_count"
    )
    assert "confidence_tier" in entry_tsv.splitlines()[0]
    assert "S[Phospho]PEPTIDEK" in entry_tsv
    assert "SPEPTIDEK" in entry_tsv
    assert "counterpart_status" in counterpart_tsv
    assert "high_confidence" in counterpart_tsv
    assert "complete" in counterpart_tsv

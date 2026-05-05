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
    build_ptm_cooccurrence_caution_report,
    build_ptm_occupancy_counterpart_report,
)
from bijux_proteomics.quantification import parse_ms1_feature_table
from bijux_proteomics.sequences import FastaParseMode, parse_fasta_document
from bijux_proteomics_lab.handoffs.ptm import build_ptm_lab_validation_packet


def _fixture_path(name: str) -> Path:
    return (
        Path(__file__).resolve().parents[2]
        / "bijux-proteomics-core"
        / "tests"
        / "fixtures"
        / "ptm"
        / name
    )


def _protein_sequences() -> dict[str, str]:
    fasta = (
        Path(__file__).resolve().parents[2]
        / "bijux-proteomics-core"
        / "tests"
        / "fixtures"
        / "fasta"
        / "ptm_sites.fasta"
    )
    report = parse_fasta_document(fasta.read_text(), mode=FastaParseMode.STRICT)
    return {
        record.canonical_accession: record.residues
        for record in report.accepted_records
    }


def test_ptm_lab_validation_packet_includes_assay_risk_controls_and_evidence_needs() -> (
    None
):
    parsed = parse_ptm_localization_tsv(_fixture_path("localization_results.tsv"))
    mappings = map_ptm_evidence_to_protein_sites(
        parsed.accepted_records, protein_sequences=_protein_sequences()
    )
    sites = build_ptm_site_table(mappings)
    features = parse_ms1_feature_table(
        _fixture_path("ptm_features.tsv")
    ).accepted_records
    features = tuple(
        row
        for row in features
        if not (row.sample_id == "T2" and row.canonical_peptide == "SPEPTIDEK")
    )
    occupancy = build_ptm_occupancy_counterpart_report(sites, feature_records=features)
    cooccurrence = build_ptm_cooccurrence_caution_report(
        mappings,
        spectrum_run_by_id={"scan=ptm-001": "run-a", "scan=ptm-002": "run-a"},
    )
    packet = build_ptm_lab_validation_packet(
        sites,
        occupancy_report=occupancy,
        cooccurrence_report=cooccurrence,
    )

    assert packet.entries
    assert packet.unresolved_risk_count >= 1
    high_risk = next(
        entry for entry in packet.entries if entry.assay_risk.value == "high"
    )
    assert high_risk.ambiguous_site is True
    missing_counterpart = next(
        entry
        for entry in packet.entries
        if "complete_modified_unmodified_counterpart_quant" in entry.evidence_needs
    )
    assert missing_counterpart.assay_risk.value in {"medium", "high"}

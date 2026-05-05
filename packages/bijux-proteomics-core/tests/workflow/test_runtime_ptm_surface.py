# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.quantification import parse_ms1_feature_table
from bijux_proteomics_runtime.workflows.runs import run_ptm_workflow_end_to_end
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


def test_run_ptm_workflow_end_to_end_tracks_localization_to_packet() -> None:
    features = parse_ms1_feature_table(
        _ptm_fixture("ptm_features.tsv")
    ).accepted_records
    report = run_ptm_workflow_end_to_end(
        _ptm_fixture("localization_results.tsv"),
        protein_sequences=_protein_sequences(),
        feature_records=features,
    )

    assert report.status.value == "completed"
    assert report.accepted_identification_count >= 1
    assert report.mapped_site_count >= 1
    assert report.motif_window_count >= 1
    assert report.occupancy_entry_count >= 1
    assert report.lab_packet_target_count >= 1
    assert report.steps[-1].step_id == "build-review-packet"

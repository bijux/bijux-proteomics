# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import json
from pathlib import Path

from bijux_proteomics.identification import PsmRecord, TargetDecoyLabel
from bijux_proteomics.identification.confidence import (
    build_psm_peptide_protein_trace_bundle,
    export_psm_peptide_protein_trace_bundle,
    write_psm_peptide_protein_trace_bundle,
)


def _records() -> tuple[PsmRecord, ...]:
    return (
        PsmRecord(
            spectrum_id="trace-001",
            peptide="PEPTIDE",
            canonical_peptide="PEPTIDE",
            charge=2,
            score=100.0,
            q_value=0.001,
            protein_refs=("P11111", "P22222"),
            target_decoy_label=TargetDecoyLabel.TARGET,
        ),
        PsmRecord(
            spectrum_id="trace-002",
            peptide="PEPTIDER",
            canonical_peptide="PEPTIDER",
            charge=2,
            score=90.0,
            q_value=0.01,
            protein_refs=("P11111",),
            target_decoy_label=TargetDecoyLabel.TARGET,
        ),
    )


def test_psm_peptide_protein_trace_bundle_keeps_hash_and_counts() -> None:
    bundle = build_psm_peptide_protein_trace_bundle(_records())

    assert bundle.trace_entry_count == 2
    assert bundle.distinct_psm_count == 2
    assert bundle.distinct_peptide_count == 2
    assert bundle.distinct_protein_count == 2
    assert len(bundle.trace_hash) == 64


def test_export_psm_peptide_protein_trace_bundle_writes_json_payload(
    tmp_path: Path,
) -> None:
    bundle = build_psm_peptide_protein_trace_bundle(_records())
    destination = tmp_path / "trace_bundle.json"
    compatibility_destination = tmp_path / "trace_bundle_compatibility.json"

    write_psm_peptide_protein_trace_bundle(bundle, destination)
    export_psm_peptide_protein_trace_bundle(bundle, compatibility_destination)

    payload = json.loads(destination.read_text())
    assert payload["trace_entry_count"] == 2
    assert payload["trace_hash"] == bundle.trace_hash
    assert compatibility_destination.read_text() == destination.read_text()

# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.identification import PsmRecord, TargetDecoyLabel
from bijux_proteomics.identification_iteration04 import (
    build_confidence_threshold_sensitivity_bundle,
)


def _records() -> tuple[PsmRecord, ...]:
    return (
        PsmRecord(
            spectrum_id="thr-001",
            peptide="PEPTIDE",
            canonical_peptide="PEPTIDE",
            charge=2,
            score=200.0,
            q_value=0.0005,
            protein_refs=("P11111",),
            target_decoy_label=TargetDecoyLabel.TARGET,
        ),
        PsmRecord(
            spectrum_id="thr-002",
            peptide="PEPTIDER",
            canonical_peptide="PEPTIDER",
            charge=2,
            score=160.0,
            q_value=0.005,
            protein_refs=("P11111",),
            target_decoy_label=TargetDecoyLabel.TARGET,
        ),
        PsmRecord(
            spectrum_id="thr-003",
            peptide="PEPTIDEX",
            canonical_peptide="PEPTIDEX",
            charge=3,
            score=140.0,
            q_value=0.03,
            protein_refs=("P22222",),
            target_decoy_label=TargetDecoyLabel.TARGET,
        ),
        PsmRecord(
            spectrum_id="thr-004",
            peptide="DECOYPEP",
            canonical_peptide="DECOYPEP",
            charge=2,
            score=50.0,
            q_value=0.2,
            protein_refs=("DECOY_P99999",),
            target_decoy_label=TargetDecoyLabel.DECOY,
        ),
    )


def test_confidence_threshold_sensitivity_bundle_covers_expected_thresholds() -> None:
    bundle = build_confidence_threshold_sensitivity_bundle(_records())

    assert bundle.thresholds == (0.001, 0.01, 0.05, 0.1)
    assert len(bundle.entries) == 4
    assert bundle.entries[0].threshold == 0.001
    assert bundle.entries[-1].threshold == 0.1
    assert bundle.entries[-1].accepted_psm_count >= bundle.entries[0].accepted_psm_count
    assert len(bundle.source_reproducibility_hash) == 64

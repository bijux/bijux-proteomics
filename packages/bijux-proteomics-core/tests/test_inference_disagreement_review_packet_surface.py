# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.identification import PsmRecord, TargetDecoyLabel
from bijux_proteomics.identification_iteration04 import (
    InferenceDisagreementSeverity,
    build_inference_disagreement_review_packet,
)


def _records() -> tuple[PsmRecord, ...]:
    return (
        PsmRecord(
            spectrum_id="inf-001",
            peptide="PEPTIDE",
            canonical_peptide="PEPTIDE",
            charge=2,
            score=120.0,
            q_value=0.001,
            protein_refs=("P11111", "P22222"),
            target_decoy_label=TargetDecoyLabel.TARGET,
        ),
        PsmRecord(
            spectrum_id="inf-002",
            peptide="PEPTIDEX",
            canonical_peptide="PEPTIDEX",
            charge=2,
            score=115.0,
            q_value=0.003,
            protein_refs=("P11111",),
            target_decoy_label=TargetDecoyLabel.TARGET,
        ),
        PsmRecord(
            spectrum_id="inf-003",
            peptide="PEPTIDEY",
            canonical_peptide="PEPTIDEY",
            charge=2,
            score=110.0,
            q_value=0.004,
            protein_refs=("P22222",),
            target_decoy_label=TargetDecoyLabel.TARGET,
        ),
    )


def test_inference_disagreement_review_packet_surfaces_review_severity() -> None:
    packet = build_inference_disagreement_review_packet(_records())

    assert packet.entry_count >= 1
    assert packet.warning_count + packet.blocking_count == packet.entry_count
    assert any(
        entry.severity
        in {
            InferenceDisagreementSeverity.WARNING,
            InferenceDisagreementSeverity.BLOCKING,
        }
        for entry in packet.entries
    )
    assert len(packet.recommendation) > 10

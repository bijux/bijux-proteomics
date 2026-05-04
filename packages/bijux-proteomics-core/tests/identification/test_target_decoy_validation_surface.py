# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.identification import (
    PsmRecord,
    TargetDecoyLabel,
    TargetDecoyLabelPolicy,
)
from bijux_proteomics.identification.confidence import validate_custom_decoy_strategy


def _records_with_collision() -> tuple[PsmRecord, ...]:
    return (
        PsmRecord(
            spectrum_id="decoy-001",
            peptide="PEPTIDE",
            canonical_peptide="PEPTIDE",
            charge=2,
            score=100.0,
            q_value=0.001,
            protein_refs=("P11111",),
            target_decoy_label=TargetDecoyLabel.TARGET,
        ),
        PsmRecord(
            spectrum_id="decoy-002",
            peptide="DECOYPEP",
            canonical_peptide="DECOYPEP",
            charge=2,
            score=50.0,
            q_value=0.2,
            protein_refs=("DECOY_P11111",),
            target_decoy_label=TargetDecoyLabel.DECOY,
        ),
    )


def test_validate_custom_decoy_strategy_surfaces_collision_risk() -> None:
    report = validate_custom_decoy_strategy(
        _records_with_collision(),
        policy=TargetDecoyLabelPolicy(protein_prefix="DECOY_"),
    )

    assert report.valid is False
    assert "shared_base_accession_pairs" in report.policy_issue_codes
    assert "collisions" in report.risk_summary

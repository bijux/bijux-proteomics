# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.identification import PsmRecord, TargetDecoyLabel
from bijux_proteomics.identification_iteration04 import (
    ProteinInferenceStrategyKind,
    compare_protein_inference_strategies,
)


def _records() -> tuple[PsmRecord, ...]:
    return (
        PsmRecord(
            spectrum_id="s001",
            peptide="PEPTIDE",
            canonical_peptide="PEPTIDE",
            charge=2,
            score=150.0,
            q_value=0.001,
            protein_refs=("P11111", "P22222"),
            target_decoy_label=TargetDecoyLabel.TARGET,
        ),
        PsmRecord(
            spectrum_id="s002",
            peptide="PEPTIDER",
            canonical_peptide="PEPTIDER",
            charge=2,
            score=120.0,
            q_value=0.01,
            protein_refs=("P11111",),
            target_decoy_label=TargetDecoyLabel.TARGET,
        ),
        PsmRecord(
            spectrum_id="s003",
            peptide="PEPTIDEX",
            canonical_peptide="PEPTIDEX",
            charge=3,
            score=100.0,
            q_value=0.02,
            protein_refs=("P33333",),
            target_decoy_label=TargetDecoyLabel.TARGET,
        ),
        PsmRecord(
            spectrum_id="s004",
            peptide="DECOYPEP",
            canonical_peptide="DECOYPEP",
            charge=2,
            score=10.0,
            q_value=0.3,
            protein_refs=("DECOY_P99999",),
            target_decoy_label=TargetDecoyLabel.DECOY,
        ),
    )


def test_compare_protein_inference_strategies_reports_pairwise_overlaps() -> None:
    report = compare_protein_inference_strategies(_records(), picked_threshold=0.05)

    assert len(report.selections) == 5
    assert {selection.strategy_kind for selection in report.selections} == {
        ProteinInferenceStrategyKind.PARSIMONY,
        ProteinInferenceStrategyKind.RAZOR,
        ProteinInferenceStrategyKind.PICKED,
        ProteinInferenceStrategyKind.GROUPED,
        ProteinInferenceStrategyKind.CONSERVATIVE,
    }
    assert len(report.comparisons) == 10
    assert any(comparison.jaccard_similarity < 1.0 for comparison in report.comparisons)

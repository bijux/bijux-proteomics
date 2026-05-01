# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.quantification import MissingValueKind, Ms1FeatureRecord
from bijux_proteomics.quantification_iteration05 import (
    ProteinRollupStrategyKind,
    build_protein_rollup_strategy_comparison_report,
)


def _records() -> tuple[Ms1FeatureRecord, ...]:
    return (
        Ms1FeatureRecord(
            feature_id="r-001",
            sample_id="s1",
            peptide="PEPA",
            canonical_peptide="PEPA",
            intensity=1000.0,
            protein_refs=("P1",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="r-002",
            sample_id="s1",
            peptide="PEPB",
            canonical_peptide="PEPB",
            intensity=600.0,
            protein_refs=("P1", "P2"),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
        Ms1FeatureRecord(
            feature_id="r-003",
            sample_id="s1",
            peptide="PEPC",
            canonical_peptide="PEPC",
            intensity=300.0,
            protein_refs=("P2",),
            missing_value_kind=MissingValueKind.OBSERVED,
        ),
    )


def test_protein_rollup_strategy_comparison_report_covers_expected_strategies() -> None:
    report = build_protein_rollup_strategy_comparison_report(_records(), top_n=2)

    assert len(report.entries) == 2
    first = report.entries[0]
    assert {value.strategy for value in first.strategy_values} == {
        ProteinRollupStrategyKind.SUM,
        ProteinRollupStrategyKind.TOP_N,
        ProteinRollupStrategyKind.MEDIAN_POLISH_LIKE,
        ProteinRollupStrategyKind.RAZOR_ONLY,
        ProteinRollupStrategyKind.SHARED_EXCLUDED,
        ProteinRollupStrategyKind.EVIDENCE_WEIGHTED,
    }
    assert first.max_strategy_difference >= 0.0

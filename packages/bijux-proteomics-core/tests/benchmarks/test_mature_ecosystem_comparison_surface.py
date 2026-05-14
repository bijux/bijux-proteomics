# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.benchmarks.adoption import (
    EcosystemComparisonEntry,
    build_mature_ecosystem_comparison_report,
)


def test_build_mature_ecosystem_comparison_report_computes_averages() -> None:
    report = build_mature_ecosystem_comparison_report(
        (
            EcosystemComparisonEntry(
                ecosystem_name="MaxQuant",
                scope_match_score=0.6,
                evidence_traceability_score=0.8,
                known_gap_summary="less mature GUI tooling",
            ),
            EcosystemComparisonEntry(
                ecosystem_name="DIA-NN",
                scope_match_score=0.5,
                evidence_traceability_score=0.7,
                known_gap_summary="fewer turn-key vendor import paths",
            ),
        )
    )

    assert round(report.average_scope_match_score, 2) == 0.55
    assert round(report.average_evidence_traceability_score, 2) == 0.75

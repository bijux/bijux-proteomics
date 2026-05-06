# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_intelligence.reviews.boards import (
    DecisionRelevantContradiction,
    build_contradiction_aware_lab_recommendation_report,
)


def test_build_contradiction_aware_lab_recommendation_report_orders_by_impact() -> None:
    report = build_contradiction_aware_lab_recommendation_report(
        (
            DecisionRelevantContradiction(
                contradiction_id="c-low",
                candidate_id="cand-2",
                decision_impact=0.4,
                unresolved_risk=0.3,
                suggested_experiment="orthogonal quant replicate",
            ),
            DecisionRelevantContradiction(
                contradiction_id="c-high",
                candidate_id="cand-1",
                decision_impact=0.9,
                unresolved_risk=0.6,
                suggested_experiment="targeted prm validation",
            ),
        )
    )

    assert report.recommendations[0].contradiction_id == "c-high"
    assert report.recommendations[0].resolution_priority_score > 0.7

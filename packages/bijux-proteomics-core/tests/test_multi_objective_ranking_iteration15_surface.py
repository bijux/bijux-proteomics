# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.intelligence_iteration15 import (
    MultiObjectiveRankingInput,
    build_multi_objective_ranking_report,
)


def test_build_multi_objective_ranking_report_accounts_for_penalties() -> None:
    report = build_multi_objective_ranking_report(
        (
            MultiObjectiveRankingInput(
                candidate_id="c1",
                evidence_score=0.8,
                novelty_score=0.6,
                lab_feasibility_score=0.8,
                cost_penalty=0.2,
                risk_penalty=0.2,
                expected_gain_score=0.8,
            ),
            MultiObjectiveRankingInput(
                candidate_id="c2",
                evidence_score=0.85,
                novelty_score=0.65,
                lab_feasibility_score=0.4,
                cost_penalty=0.8,
                risk_penalty=0.8,
                expected_gain_score=0.5,
            ),
        )
    )

    assert report.entries[0].candidate_id == "c1"
    assert report.entries[1].rank == 2

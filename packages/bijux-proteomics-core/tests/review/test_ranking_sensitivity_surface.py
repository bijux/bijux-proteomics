# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.review import (
    RankingPerturbationScenario,
    TrustScoreInput,
    build_ranking_sensitivity_report,
    decompose_trust_score,
)


def test_build_ranking_sensitivity_report_detects_unstable_priority() -> None:
    decompositions = (
        decompose_trust_score(
            TrustScoreInput(
                candidate_id="cand-a",
                evidence_inputs={"id": 0.8},
                weights={"id": 1.0},
                uncertainty=0.0,
            )
        ),
        decompose_trust_score(
            TrustScoreInput(
                candidate_id="cand-b",
                evidence_inputs={"id": 0.79},
                weights={"id": 1.0},
                uncertainty=0.0,
            )
        ),
    )

    report = build_ranking_sensitivity_report(
        decompositions,
        scenarios=(
            RankingPerturbationScenario(
                scenario_id="strict",
                weight_multiplier=0.95,
                extra_penalty=0.02,
                candidate_score_offsets={"cand-b": 0.04},
            ),
            RankingPerturbationScenario(
                scenario_id="lenient",
                weight_multiplier=1.05,
                extra_penalty=0.0,
            ),
        ),
    )

    assert report.scenario_count == 2
    assert report.stable_candidate_count == 0
    assert report.unstable_candidate_count == 2
    assert report.entries[0].base_rank == 1
    assert report.entries[0].max_rank == 2

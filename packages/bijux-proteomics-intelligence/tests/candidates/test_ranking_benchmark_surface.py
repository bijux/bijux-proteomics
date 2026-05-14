# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_intelligence.candidates.ranking_benchmarks import (
    build_flagship_ranking_policy,
    build_legacy_ranking_policy,
    build_reviewable_ranking_benchmark_corpus,
    compare_ranking_policies_against_benchmark_corpus,
    run_ranking_benchmark_corpus,
)


def test_ranking_benchmark_corpus_stays_reviewable_and_artifact_backed() -> None:
    corpus = build_reviewable_ranking_benchmark_corpus()

    assert corpus.corpus_id == "reviewable-ranking-corpus"
    assert corpus.artifact_path.startswith("artifacts/")
    assert len(corpus.scenarios) == 3
    assert all(scenario.expected_top_candidate_id for scenario in corpus.scenarios)


def test_flagship_ranking_policy_solves_reviewable_decision_traps() -> None:
    report = run_ranking_benchmark_corpus(build_flagship_ranking_policy())

    assert report.policy_id == "flagship-reviewable-ranking"
    assert report.scenario_count == 3
    assert report.solved_scenario_count == 3
    assert report.decision_quality_score == 1.0
    assert all(result.solved for result in report.results)


def test_flagship_policy_improves_decision_quality_over_legacy_baseline() -> None:
    improvement = compare_ranking_policies_against_benchmark_corpus(
        build_legacy_ranking_policy(),
        build_flagship_ranking_policy(),
    )

    assert improvement.decision_improved is True
    assert improvement.improved_scenario_ids
    assert improvement.regressed_scenario_ids == ()

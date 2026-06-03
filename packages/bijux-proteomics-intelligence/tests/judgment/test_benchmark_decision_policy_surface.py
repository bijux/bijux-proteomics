# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_intelligence.judgment.benchmark_corpora import (
    BenchmarkDisposition,
    build_do_not_recommend_benchmark_suite,
    build_lab_burden_aware_decision_corpus,
    build_recommendation_quality_corpus,
)
from bijux_proteomics_intelligence.judgment.benchmark_policies import (
    build_benchmark_refusal_policy,
    build_flagship_benchmark_decision_policy,
    run_benchmark_decision_corpus,
)


def test_flagship_policy_prefers_safer_recommendation_path() -> None:
    report = run_benchmark_decision_corpus(
        build_recommendation_quality_corpus(),
        build_flagship_benchmark_decision_policy(),
    )

    assert report.solved_scenario_count == 1
    outcome = report.results[0]
    assert outcome.disposition is BenchmarkDisposition.RECOMMEND_WITH_DOWNGRADE
    assert outcome.selected_option_id == "dda_reviewable_path"
    assert any(
        "external comparator claim support is still advisory" in reason
        for reason in outcome.downgrade_chain
    )


def test_lab_burden_corpus_keeps_one_known_failure_visible() -> None:
    report = run_benchmark_decision_corpus(
        build_lab_burden_aware_decision_corpus(),
        build_flagship_benchmark_decision_policy(),
    )

    assert report.scenario_count == 2
    assert report.solved_scenario_count == 1
    assert any(
        result.scenario_id == "borderline-dia-burden-still-confuses-current-policy"
        and result.solved is False
        for result in report.results
    )


def test_refusal_policy_solves_explicit_do_not_recommend_suite() -> None:
    report = run_benchmark_decision_corpus(
        build_do_not_recommend_benchmark_suite(),
        build_benchmark_refusal_policy(),
    )

    assert report.scenario_count == 2
    assert report.solved_scenario_count == 2
    assert all(
        result.disposition is BenchmarkDisposition.DO_NOT_RECOMMEND
        for result in report.results
    )


def test_flagship_policy_keeps_dia_vendor_gap_visible_on_borderline_case() -> None:
    report = run_benchmark_decision_corpus(
        build_lab_burden_aware_decision_corpus(),
        build_flagship_benchmark_decision_policy(),
    )

    dia_result = next(
        result
        for result in report.results
        if result.scenario_id == "borderline-dia-burden-still-confuses-current-policy"
    )

    assert dia_result.selected_option_id == "dia_borderline_path"
    assert dia_result.disposition is BenchmarkDisposition.RECOMMEND_WITH_DOWNGRADE
    assert dia_result.solved is False
    assert (
        "vendor and library comparison gaps remain open" in dia_result.downgrade_chain
    )
    assert (
        "operational burden remains too high for a justified recommendation"
        in dia_result.blocker_set
    )

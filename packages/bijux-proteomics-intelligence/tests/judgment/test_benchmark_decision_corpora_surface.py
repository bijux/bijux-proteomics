# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_intelligence.judgment.benchmark_corpora import (
    BenchmarkDecisionCorpusKind,
    BenchmarkDisposition,
    build_comparator_aware_decision_corpus,
    build_do_not_recommend_benchmark_suite,
    build_downgrade_chain_honesty_corpus,
    build_lab_burden_aware_decision_corpus,
    build_recommendation_quality_corpus,
    build_rejection_quality_corpus,
)
from bijux_proteomics_knowledge.references.workflows.benchmarks import (
    KnowledgeWorkflowFamily,
)


def test_recommendation_quality_corpus_prefers_safer_flagship_path() -> None:
    corpus = build_recommendation_quality_corpus()

    assert corpus.corpus_kind is BenchmarkDecisionCorpusKind.RECOMMENDATION_QUALITY
    assert corpus.artifact_path.startswith("artifacts/")
    assert len(corpus.scenarios) == 1
    scenario = corpus.scenarios[0]
    assert scenario.expected_selected_option_id == "dda_reviewable_path"
    assert (
        scenario.expected_disposition is BenchmarkDisposition.RECOMMEND_WITH_DOWNGRADE
    )


def test_rejection_quality_corpus_forces_explicit_refusal() -> None:
    corpus = build_rejection_quality_corpus()

    assert corpus.corpus_kind is BenchmarkDecisionCorpusKind.REJECTION_QUALITY
    scenario = corpus.scenarios[0]
    assert scenario.expected_selected_option_id is None
    assert scenario.expected_disposition is BenchmarkDisposition.DO_NOT_RECOMMEND
    assert "biological grounding remains thin" in scenario.required_blockers


def test_other_decision_corpora_stay_artifact_backed_and_goal_specific() -> None:
    comparator = build_comparator_aware_decision_corpus()
    burden = build_lab_burden_aware_decision_corpus()
    downgrade = build_downgrade_chain_honesty_corpus()
    refusal = build_do_not_recommend_benchmark_suite()

    assert comparator.corpus_kind is BenchmarkDecisionCorpusKind.COMPARATOR_AWARE
    assert burden.corpus_kind is BenchmarkDecisionCorpusKind.LAB_BURDEN_AWARE
    assert downgrade.corpus_kind is BenchmarkDecisionCorpusKind.DOWNGRADE_CHAIN_HONESTY
    assert refusal.corpus_kind is BenchmarkDecisionCorpusKind.DO_NOT_RECOMMEND
    assert len(burden.scenarios) == 2
    assert all(
        corpus.artifact_path.startswith("artifacts/")
        for corpus in (comparator, burden, downgrade, refusal)
    )


def test_lab_burden_corpus_keeps_dia_review_context_release_ready() -> None:
    corpus = build_lab_burden_aware_decision_corpus()

    scenario = next(
        item
        for item in corpus.scenarios
        if item.scenario_id == "borderline-dia-burden-still-confuses-current-policy"
    )
    dia_option = next(
        option
        for option in scenario.options
        if option.review.workflow_family is KnowledgeWorkflowFamily.DIA
    )

    assert dia_option.option_id == "dia_borderline_path"
    assert dia_option.review.public_claim_support_state.value == "advisory"
    assert dia_option.review.ready_for_release_review is True
    assert (
        dia_option.review.benchmark_package_id
        == "benchmark_package:dia_library_review_package"
    )

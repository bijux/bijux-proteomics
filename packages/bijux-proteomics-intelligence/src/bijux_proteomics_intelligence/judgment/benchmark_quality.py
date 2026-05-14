# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Honest quality reports over flagship benchmark-backed decision corpora."""

from __future__ import annotations

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel
from bijux_proteomics_intelligence.judgment.benchmark_corpora import (
    BenchmarkDecisionCorpus,
    build_comparator_aware_decision_corpus,
    build_downgrade_chain_honesty_corpus,
    build_lab_burden_aware_decision_corpus,
    build_recommendation_quality_corpus,
    build_rejection_quality_corpus,
)
from bijux_proteomics_intelligence.judgment.benchmark_policies import (
    BenchmarkDecisionPolicy,
    build_benchmark_surface_appeal_policy,
    build_flagship_benchmark_decision_policy,
    evaluate_benchmark_decision_scenario,
)

__all__ = [
    "BenchmarkDecisionTrapReport",
    "BenchmarkDecisionTrapReportEntry",
    "BenchmarkDecisionWinReport",
    "BenchmarkDecisionWinReportEntry",
    "build_benchmark_decision_traps_report",
    "build_benchmark_decision_wins_report",
]


class BenchmarkDecisionTrapReportEntry(JsonModel):
    """One scenario where the current flagship decision policy still fails."""

    model_config = ConfigDict(extra="forbid")

    scenario_id: str = Field(..., min_length=1)
    observed_disposition: str = Field(..., min_length=1)
    observed_selected_option_id: str | None = None
    expected_selected_option_id: str | None = None
    note: str = Field(..., min_length=1)


class BenchmarkDecisionTrapReport(JsonModel):
    """Honest record of where the flagship benchmark decision layer still fails."""

    model_config = ConfigDict(extra="forbid")

    policy_id: str = Field(..., min_length=1)
    artifact_path: str = Field(..., min_length=1)
    entries: tuple[BenchmarkDecisionTrapReportEntry, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


class BenchmarkDecisionWinReportEntry(JsonModel):
    """One scenario where the flagship policy beats a naive baseline."""

    model_config = ConfigDict(extra="forbid")

    scenario_id: str = Field(..., min_length=1)
    flagship_selected_option_id: str | None = None
    baseline_selected_option_id: str | None = None
    note: str = Field(..., min_length=1)


class BenchmarkDecisionWinReport(JsonModel):
    """Scenarios where the flagship policy makes safer calls than a baseline."""

    model_config = ConfigDict(extra="forbid")

    policy_id: str = Field(..., min_length=1)
    baseline_policy_id: str = Field(..., min_length=1)
    artifact_path: str = Field(..., min_length=1)
    entries: tuple[BenchmarkDecisionWinReportEntry, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


def _all_decision_corpora() -> tuple[BenchmarkDecisionCorpus, ...]:
    return (
        build_recommendation_quality_corpus(),
        build_rejection_quality_corpus(),
        build_comparator_aware_decision_corpus(),
        build_lab_burden_aware_decision_corpus(),
        build_downgrade_chain_honesty_corpus(),
    )


def build_benchmark_decision_traps_report(
    *,
    policy: BenchmarkDecisionPolicy | None = None,
) -> BenchmarkDecisionTrapReport:
    """Report where the current flagship policy still chooses badly."""

    active_policy = policy or build_flagship_benchmark_decision_policy()
    entries: list[BenchmarkDecisionTrapReportEntry] = []
    for corpus in _all_decision_corpora():
        for scenario in corpus.scenarios:
            outcome = evaluate_benchmark_decision_scenario(scenario, active_policy)
            if outcome.solved:
                continue
            entries.append(
                BenchmarkDecisionTrapReportEntry(
                    scenario_id=scenario.scenario_id,
                    observed_disposition=outcome.disposition.value,
                    observed_selected_option_id=outcome.selected_option_id,
                    expected_selected_option_id=scenario.expected_selected_option_id,
                    note=(
                        "Current flagship policy still misjudges this flagship benchmark scenario and should not be shielded by tidy recommendation prose."
                    ),
                )
            )
    return BenchmarkDecisionTrapReport(
        policy_id=active_policy.policy_id,
        artifact_path="artifacts/intelligence/benchmark-decisions/decision_traps.json",
        entries=tuple(entries),
        note=(
            "This report lists the flagship benchmark scenarios where the intelligence layer still chooses badly today."
        ),
    )


def build_benchmark_decision_wins_report(
    *,
    flagship_policy: BenchmarkDecisionPolicy | None = None,
    baseline_policy: BenchmarkDecisionPolicy | None = None,
) -> BenchmarkDecisionWinReport:
    """Report where the flagship policy beats a naive surface-heavy baseline."""

    active_flagship = flagship_policy or build_flagship_benchmark_decision_policy()
    active_baseline = baseline_policy or build_benchmark_surface_appeal_policy()
    entries: list[BenchmarkDecisionWinReportEntry] = []
    for corpus in _all_decision_corpora():
        for scenario in corpus.scenarios:
            flagship_outcome = evaluate_benchmark_decision_scenario(
                scenario, active_flagship
            )
            baseline_outcome = evaluate_benchmark_decision_scenario(
                scenario, active_baseline
            )
            if not flagship_outcome.solved or baseline_outcome.solved:
                continue
            entries.append(
                BenchmarkDecisionWinReportEntry(
                    scenario_id=scenario.scenario_id,
                    flagship_selected_option_id=flagship_outcome.selected_option_id,
                    baseline_selected_option_id=baseline_outcome.selected_option_id,
                    note=(
                        "Flagship policy makes the safer benchmark-backed call here while the naive baseline still chases surface appeal."
                    ),
                )
            )
    return BenchmarkDecisionWinReport(
        policy_id=active_flagship.policy_id,
        baseline_policy_id=active_baseline.policy_id,
        artifact_path="artifacts/intelligence/benchmark-decisions/decision_wins.json",
        entries=tuple(entries),
        note=(
            "This report lists where the flagship intelligence policy demonstrably beats a naive benchmark recommendation baseline."
        ),
    )

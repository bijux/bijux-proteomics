# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Recommendation sensitivity across policies on flagship benchmark-backed scenarios."""

from __future__ import annotations

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel
from bijux_proteomics_intelligence.judgment.benchmark_corpora import (
    BenchmarkDisposition,
    build_comparator_aware_decision_corpus,
    build_downgrade_chain_honesty_corpus,
    build_lab_burden_aware_decision_corpus,
    build_recommendation_quality_corpus,
    build_rejection_quality_corpus,
)
from bijux_proteomics_intelligence.judgment.benchmark_policies import (
    build_benchmark_refusal_policy,
    build_benchmark_surface_appeal_policy,
    build_flagship_benchmark_decision_policy,
    evaluate_benchmark_decision_scenario,
)

__all__ = [
    "FlagshipBenchmarkSensitivityReport",
    "FlagshipBenchmarkSensitivityScenario",
    "FlagshipBenchmarkSensitivityScenarioEntry",
    "build_flagship_benchmark_sensitivity_report",
]


class FlagshipBenchmarkSensitivityScenarioEntry(JsonModel):
    """Recommendation change for one policy on one benchmark-backed scenario."""

    model_config = ConfigDict(extra="forbid")

    policy_id: str = Field(..., min_length=1)
    disposition: BenchmarkDisposition
    selected_option_id: str | None = None
    selected_benchmark_id: str | None = None


class FlagshipBenchmarkSensitivityScenario(JsonModel):
    """Policy sensitivity entry for one benchmark-backed scenario."""

    model_config = ConfigDict(extra="forbid")

    scenario_id: str = Field(..., min_length=1)
    changed: bool
    entries: tuple[FlagshipBenchmarkSensitivityScenarioEntry, ...] = Field(
        default_factory=tuple
    )


class FlagshipBenchmarkSensitivityReport(JsonModel):
    """Recommendation sensitivity across ranking policies on flagship packages."""

    model_config = ConfigDict(extra="forbid")

    report_id: str = Field(..., min_length=1)
    artifact_path: str = Field(..., min_length=1)
    scenarios: tuple[FlagshipBenchmarkSensitivityScenario, ...] = Field(
        default_factory=tuple
    )
    changed_scenario_ids: tuple[str, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


def _all_decision_corpora():
    return (
        build_recommendation_quality_corpus(),
        build_rejection_quality_corpus(),
        build_comparator_aware_decision_corpus(),
        build_lab_burden_aware_decision_corpus(),
        build_downgrade_chain_honesty_corpus(),
    )


def build_flagship_benchmark_sensitivity_report() -> FlagshipBenchmarkSensitivityReport:
    """Show how policy changes alter downstream recommendations on flagship packages."""

    policies = (
        build_benchmark_surface_appeal_policy(),
        build_flagship_benchmark_decision_policy(),
        build_benchmark_refusal_policy(),
    )
    scenarios: list[FlagshipBenchmarkSensitivityScenario] = []
    changed: list[str] = []
    for corpus in _all_decision_corpora():
        for scenario in corpus.scenarios:
            entries = tuple(
                FlagshipBenchmarkSensitivityScenarioEntry(
                    policy_id=policy.policy_id,
                    disposition=outcome.disposition,
                    selected_option_id=outcome.selected_option_id,
                    selected_benchmark_id=outcome.selected_benchmark_id,
                )
                for policy in policies
                for outcome in (evaluate_benchmark_decision_scenario(scenario, policy),)
            )
            distinct_outcomes = {
                (entry.disposition, entry.selected_option_id) for entry in entries
            }
            scenario_changed = len(distinct_outcomes) > 1
            if scenario_changed:
                changed.append(scenario.scenario_id)
            scenarios.append(
                FlagshipBenchmarkSensitivityScenario(
                    scenario_id=scenario.scenario_id,
                    changed=scenario_changed,
                    entries=entries,
                )
            )
    return FlagshipBenchmarkSensitivityReport(
        report_id="flagship-benchmark-ranking-sensitivity",
        artifact_path="artifacts/intelligence/benchmark-decisions/ranking_sensitivity.json",
        scenarios=tuple(scenarios),
        changed_scenario_ids=tuple(changed),
        note=(
            "This report shows recommendation sensitivity across real flagship benchmark packages rather than abstract candidate fixtures."
        ),
    )

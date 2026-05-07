# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Scientific benchmark surfaces for protein inference credibility."""

from __future__ import annotations

from enum import StrEnum
import math

from pydantic import ConfigDict, Field

from bijux_proteomics.identification.confidence import (
    ProteinInferenceStrategyKind,
    compare_protein_inference_strategies,
)
from bijux_proteomics.identification.contracts import PsmRecord
from bijux_proteomics_foundation import JsonModel


class ProteinInferenceBenchmarkScenarioKind(StrEnum):
    """Pressure families that a protein-inference workflow must survive."""

    SHARED_PEPTIDE_HEAVY = "shared_peptide_heavy"
    ISOFORM_HEAVY = "isoform_heavy"
    FALSE_POSITIVE_PRESSURE = "false_positive_pressure"
    FALSE_NEGATIVE_PRESSURE = "false_negative_pressure"


class ProteinInferenceBenchmarkScenario(JsonModel):
    """One truth-scored protein-inference benchmark scenario."""

    model_config = ConfigDict(extra="forbid")

    scenario_id: str = Field(..., min_length=1)
    scenario_kind: ProteinInferenceBenchmarkScenarioKind
    records: tuple[PsmRecord, ...] = Field(default_factory=tuple)
    expected_present_proteins: tuple[str, ...] = Field(default_factory=tuple)
    expected_absent_proteins: tuple[str, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


class ProteinInferenceMethodAssessment(JsonModel):
    """Truth-scored assessment for one protein-inference strategy."""

    model_config = ConfigDict(extra="forbid")

    strategy_kind: ProteinInferenceStrategyKind
    strategy_label: str = Field(..., min_length=1)
    selected_proteins: tuple[str, ...] = Field(default_factory=tuple)
    true_positive_count: int = Field(..., ge=0)
    false_positive_count: int = Field(..., ge=0)
    false_negative_count: int = Field(..., ge=0)
    precision: float = Field(..., ge=0.0, le=1.0)
    precision_interval_low: float = Field(..., ge=0.0, le=1.0)
    precision_interval_high: float = Field(..., ge=0.0, le=1.0)
    recall: float = Field(..., ge=0.0, le=1.0)
    recall_interval_low: float = Field(..., ge=0.0, le=1.0)
    recall_interval_high: float = Field(..., ge=0.0, le=1.0)
    false_positive_proteins: tuple[str, ...] = Field(default_factory=tuple)
    missed_proteins: tuple[str, ...] = Field(default_factory=tuple)
    trustworthy_for_review: bool
    trust_note: str = Field(..., min_length=1)


class ProteinInferenceBenchmarkReport(JsonModel):
    """Benchmark result over one protein-inference truth scenario."""

    model_config = ConfigDict(extra="forbid")

    scenario_id: str = Field(..., min_length=1)
    scenario_kind: ProteinInferenceBenchmarkScenarioKind
    expected_present_proteins: tuple[str, ...] = Field(default_factory=tuple)
    expected_absent_proteins: tuple[str, ...] = Field(default_factory=tuple)
    shared_peptide_pressure: bool
    isoform_pressure: bool
    method_assessments: tuple[ProteinInferenceMethodAssessment, ...] = Field(
        default_factory=tuple
    )
    disagreement_count: int = Field(..., ge=0)
    scenario_note: str = Field(..., min_length=1)


class ProteinInferenceBenchmarkSuiteReport(JsonModel):
    """Aggregate benchmark proof across multiple pressure scenarios."""

    model_config = ConfigDict(extra="forbid")

    reports: tuple[ProteinInferenceBenchmarkReport, ...] = Field(default_factory=tuple)
    covered_strategy_kinds: tuple[ProteinInferenceStrategyKind, ...] = Field(
        default_factory=tuple
    )
    scenario_ids: tuple[str, ...] = Field(default_factory=tuple)
    scenario_kinds: tuple[ProteinInferenceBenchmarkScenarioKind, ...] = Field(
        default_factory=tuple
    )
    worst_precision_lower_bound: float = Field(..., ge=0.0, le=1.0)
    worst_recall_lower_bound: float = Field(..., ge=0.0, le=1.0)
    scenario_count: int = Field(..., ge=0)


def _wilson_interval(successes: int, total: int, *, z: float = 1.96) -> tuple[float, float]:
    if total <= 0:
        return (0.0, 0.0)
    proportion = successes / total
    denominator = 1.0 + (z * z) / total
    centre = proportion + (z * z) / (2.0 * total)
    margin = z * math.sqrt(
        (proportion * (1.0 - proportion) / total) + ((z * z) / (4.0 * total * total))
    )
    low = max(0.0, (centre - margin) / denominator)
    high = min(1.0, (centre + margin) / denominator)
    return (low, high)


def _base_accession(protein_ref: str) -> str:
    token = protein_ref.removeprefix("DECOY_").removeprefix("REV__").removeprefix(
        "CON__"
    )
    if "-" in token:
        return token.split("-", maxsplit=1)[0]
    return token


def build_protein_inference_benchmark_report(
    scenario: ProteinInferenceBenchmarkScenario,
    *,
    picked_threshold: float = 0.05,
) -> ProteinInferenceBenchmarkReport:
    """Truth-score multiple protein-inference strategies over one pressure scenario."""

    comparison = compare_protein_inference_strategies(
        scenario.records,
        picked_threshold=picked_threshold,
    )
    expected_present = set(scenario.expected_present_proteins)
    expected_absent = set(scenario.expected_absent_proteins)
    method_assessments: list[ProteinInferenceMethodAssessment] = []
    disagreement_count = 0
    for selection in comparison.selections:
        selected = set(selection.selected_proteins)
        true_positives = selected & expected_present
        false_positives = selected & expected_absent
        false_negatives = expected_present - selected
        precision_denominator = len(true_positives) + len(false_positives)
        recall_denominator = len(true_positives) + len(false_negatives)
        precision = (
            len(true_positives) / precision_denominator
            if precision_denominator
            else 0.0
        )
        recall = len(true_positives) / recall_denominator if recall_denominator else 0.0
        precision_low, precision_high = _wilson_interval(
            len(true_positives),
            precision_denominator,
        )
        recall_low, recall_high = _wilson_interval(
            len(true_positives),
            recall_denominator,
        )
        trustworthy = precision_low >= 0.5 and not false_positives
        note = (
            "strategy keeps the expected proteins without absent-protein bleed"
            if trustworthy
            else "strategy still shows absent-protein bleed or an unstable lower-bound interval"
        )
        if false_positives or false_negatives:
            disagreement_count += 1
        method_assessments.append(
            ProteinInferenceMethodAssessment(
                strategy_kind=selection.strategy_kind,
                strategy_label=selection.strategy_label,
                selected_proteins=selection.selected_proteins,
                true_positive_count=len(true_positives),
                false_positive_count=len(false_positives),
                false_negative_count=len(false_negatives),
                precision=precision,
                precision_interval_low=precision_low,
                precision_interval_high=precision_high,
                recall=recall,
                recall_interval_low=recall_low,
                recall_interval_high=recall_high,
                false_positive_proteins=tuple(sorted(false_positives)),
                missed_proteins=tuple(sorted(false_negatives)),
                trustworthy_for_review=trustworthy,
                trust_note=note,
            )
        )
    return ProteinInferenceBenchmarkReport(
        scenario_id=scenario.scenario_id,
        scenario_kind=scenario.scenario_kind,
        expected_present_proteins=tuple(sorted(expected_present)),
        expected_absent_proteins=tuple(sorted(expected_absent)),
        shared_peptide_pressure=any(len(record.protein_refs) > 1 for record in scenario.records),
        isoform_pressure=any(
            len({_base_accession(ref) for ref in record.protein_refs}) == 1
            and len(record.protein_refs) > 1
            for record in scenario.records
        ),
        method_assessments=tuple(method_assessments),
        disagreement_count=disagreement_count,
        scenario_note=scenario.note,
    )


def build_protein_inference_benchmark_suite(
    scenarios: tuple[ProteinInferenceBenchmarkScenario, ...],
    *,
    picked_threshold: float = 0.05,
) -> ProteinInferenceBenchmarkSuiteReport:
    """Aggregate multiple protein-inference pressure scenarios into one suite."""

    reports = tuple(
        build_protein_inference_benchmark_report(
            scenario,
            picked_threshold=picked_threshold,
        )
        for scenario in scenarios
    )
    lower_bounds = [
        assessment.precision_interval_low
        for report in reports
        for assessment in report.method_assessments
    ]
    recall_lower_bounds = [
        assessment.recall_interval_low
        for report in reports
        for assessment in report.method_assessments
    ]
    covered_strategy_kinds = tuple(
        sorted(
            {
                assessment.strategy_kind
                for report in reports
                for assessment in report.method_assessments
            },
            key=lambda kind: kind.value,
        )
    )
    return ProteinInferenceBenchmarkSuiteReport(
        reports=reports,
        covered_strategy_kinds=covered_strategy_kinds,
        scenario_ids=tuple(report.scenario_id for report in reports),
        scenario_kinds=tuple(report.scenario_kind for report in reports),
        worst_precision_lower_bound=min(lower_bounds) if lower_bounds else 0.0,
        worst_recall_lower_bound=min(recall_lower_bounds)
        if recall_lower_bounds
        else 0.0,
        scenario_count=len(reports),
    )

# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Benchmark surfaces that test whether QC findings matter scientifically."""

from __future__ import annotations

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel


class QcDecisionOutcomeObservation(JsonModel):
    """One benchmarked pairing of a QC flag with downstream scientific outcome."""

    model_config = ConfigDict(extra="forbid")

    run_id: str = Field(..., min_length=1)
    qc_flagged: bool
    downstream_evidence_failed: bool
    downstream_lab_follow_up_failed: bool


class QcDecisionValidityBenchmarkReport(JsonModel):
    """Benchmark whether QC findings actually predict downstream scientific failure."""

    model_config = ConfigDict(extra="forbid")

    true_positive_count: int = Field(..., ge=0)
    false_positive_count: int = Field(..., ge=0)
    true_negative_count: int = Field(..., ge=0)
    false_negative_count: int = Field(..., ge=0)
    predictive_precision: float = Field(..., ge=0.0, le=1.0)
    predictive_recall: float = Field(..., ge=0.0, le=1.0)
    qc_findings_predictive: bool
    note: str = Field(..., min_length=1)


class QcControlCoverageObservation(JsonModel):
    """One workflow run with required controls and actually observed controls."""

    model_config = ConfigDict(extra="forbid")

    run_id: str = Field(..., min_length=1)
    workflow_family: str = Field(..., min_length=1)
    required_controls: tuple[str, ...] = Field(default_factory=tuple)
    observed_controls: tuple[str, ...] = Field(default_factory=tuple)
    computationally_parseable: bool


class QcControlCoverageEntry(JsonModel):
    """One run-level control-coverage verdict."""

    model_config = ConfigDict(extra="forbid")

    run_id: str = Field(..., min_length=1)
    workflow_family: str = Field(..., min_length=1)
    missing_controls: tuple[str, ...] = Field(default_factory=tuple)
    computationally_parseable: bool
    scientifically_interpretable: bool
    promotion_blocked: bool


class QcControlCoverageReport(JsonModel):
    """Control-coverage report over computationally parseable versus interpretable runs."""

    model_config = ConfigDict(extra="forbid")

    entries: tuple[QcControlCoverageEntry, ...] = Field(default_factory=tuple)
    parseable_but_uninterpretable_count: int = Field(..., ge=0)
    promotion_blocked_count: int = Field(..., ge=0)
    note: str = Field(..., min_length=1)


class QcPromotionBlockObservation(JsonModel):
    """One decision-promotion attempt under failed or advisory QC posture."""

    model_config = ConfigDict(extra="forbid")

    run_id: str = Field(..., min_length=1)
    failed_qc: bool
    attempted_decision_promotion: bool
    promotion_prevented: bool
    blocking_reason: str = Field(..., min_length=1)


class QcPromotionBlockReport(JsonModel):
    """Benchmark whether failed QC truly blocks downstream decision promotion."""

    model_config = ConfigDict(extra="forbid")

    failed_qc_blocked_count: int = Field(..., ge=0)
    annotation_only_failure_count: int = Field(..., ge=0)
    ready_for_decision_promotion: bool
    note: str = Field(..., min_length=1)


def _fraction(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return numerator / denominator


def build_qc_decision_validity_benchmark_report(
    observations: tuple[QcDecisionOutcomeObservation, ...],
) -> QcDecisionValidityBenchmarkReport:
    """Benchmark whether QC findings predict bad downstream evidence or bad lab follow-up."""

    true_positive = 0
    false_positive = 0
    true_negative = 0
    false_negative = 0
    for observation in observations:
        downstream_failed = (
            observation.downstream_evidence_failed
            or observation.downstream_lab_follow_up_failed
        )
        if observation.qc_flagged and downstream_failed:
            true_positive += 1
        elif observation.qc_flagged and not downstream_failed:
            false_positive += 1
        elif not observation.qc_flagged and downstream_failed:
            false_negative += 1
        else:
            true_negative += 1
    precision = _fraction(true_positive, true_positive + false_positive)
    recall = _fraction(true_positive, true_positive + false_negative)
    predictive = true_positive > 0 and precision >= 0.75 and recall >= 0.75
    return QcDecisionValidityBenchmarkReport(
        true_positive_count=true_positive,
        false_positive_count=false_positive,
        true_negative_count=true_negative,
        false_negative_count=false_negative,
        predictive_precision=precision,
        predictive_recall=recall,
        qc_findings_predictive=predictive,
        note=(
            "QC findings predict downstream scientific failure strongly enough to justify decision blocking"
            if predictive
            else "QC findings remain too weakly predictive and risk becoming annotation-only"
        ),
    )


def build_qc_control_coverage_report(
    observations: tuple[QcControlCoverageObservation, ...],
) -> QcControlCoverageReport:
    """Separate computationally parseable runs from scientifically interpretable runs."""

    entries: list[QcControlCoverageEntry] = []
    for observation in observations:
        missing = tuple(
            sorted(set(observation.required_controls) - set(observation.observed_controls))
        )
        scientifically_interpretable = (
            observation.computationally_parseable and not missing
        )
        promotion_blocked = observation.computationally_parseable and bool(missing)
        entries.append(
            QcControlCoverageEntry(
                run_id=observation.run_id,
                workflow_family=observation.workflow_family,
                missing_controls=missing,
                computationally_parseable=observation.computationally_parseable,
                scientifically_interpretable=scientifically_interpretable,
                promotion_blocked=promotion_blocked,
            )
        )
    parseable_but_uninterpretable_count = sum(
        entry.computationally_parseable and not entry.scientifically_interpretable
        for entry in entries
    )
    promotion_blocked_count = sum(entry.promotion_blocked for entry in entries)
    return QcControlCoverageReport(
        entries=tuple(entries),
        parseable_but_uninterpretable_count=parseable_but_uninterpretable_count,
        promotion_blocked_count=promotion_blocked_count,
        note=(
            "control coverage distinguishes computationally parseable runs from scientifically interpretable runs before promotion"
        ),
    )


def build_qc_promotion_block_report(
    observations: tuple[QcPromotionBlockObservation, ...],
) -> QcPromotionBlockReport:
    """Benchmark whether failed QC truly blocks downstream decision promotion."""

    failed_qc_blocked_count = sum(
        observation.failed_qc and observation.promotion_prevented
        for observation in observations
    )
    annotation_only_failure_count = sum(
        observation.failed_qc
        and observation.attempted_decision_promotion
        and not observation.promotion_prevented
        for observation in observations
    )
    ready = annotation_only_failure_count == 0
    return QcPromotionBlockReport(
        failed_qc_blocked_count=failed_qc_blocked_count,
        annotation_only_failure_count=annotation_only_failure_count,
        ready_for_decision_promotion=ready,
        note=(
            "failed QC blocks downstream decision promotion rather than becoming annotation-only"
            if ready
            else "one or more failed-QC runs still slipped into decision promotion as annotation-only warnings"
        ),
    )

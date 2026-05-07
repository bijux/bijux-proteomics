# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Calibration drift surfaces for comparing benchmark updates over time."""

from __future__ import annotations

from enum import StrEnum

from pydantic import ConfigDict, Field

from bijux_proteomics.identification.contracts import (
    PsmRecord,
    TargetDecoyLabel,
    normalize_psm_score_orientation,
)
from bijux_proteomics_foundation.serialization.json_contracts import JsonModel


class CalibrationSnapshotBin(JsonModel):
    """One empirical score bin captured for drift comparison."""

    model_config = ConfigDict(extra="forbid")

    bin_index: int = Field(..., ge=1)
    lower_bound: float = Field(..., ge=0.0, le=1.0)
    upper_bound: float = Field(..., ge=0.0, le=1.0)
    total_count: int = Field(..., ge=0)
    target_count: int = Field(..., ge=0)
    decoy_count: int = Field(..., ge=0)
    mixed_count: int = Field(..., ge=0)
    unknown_count: int = Field(..., ge=0)
    decoy_fraction: float = Field(..., ge=0.0, le=1.0)


class EmpiricalCalibrationSnapshot(JsonModel):
    """Empirical calibration snapshot preserved for update-to-update comparison."""

    model_config = ConfigDict(extra="forbid")

    score_orientation: str = Field(..., pattern="^(higher_better|lower_better)$")
    total_records: int = Field(..., ge=0)
    bin_count: int = Field(..., ge=1)
    bins: tuple[CalibrationSnapshotBin, ...] = Field(default_factory=tuple)
    top_fraction: float = Field(..., ge=0.01, le=1.0)
    top_fraction_target_share: float = Field(..., ge=0.0, le=1.0)
    top_fraction_decoy_share: float = Field(..., ge=0.0, le=1.0)
    advisory: str = Field(..., min_length=1)


class CalibrationDriftBinDelta(JsonModel):
    """Per-bin calibration movement between two benchmark snapshots."""

    model_config = ConfigDict(extra="forbid")

    bin_index: int = Field(..., ge=1)
    previous_decoy_fraction: float = Field(..., ge=0.0, le=1.0)
    current_decoy_fraction: float = Field(..., ge=0.0, le=1.0)
    decoy_fraction_delta: float
    previous_total_count: int = Field(..., ge=0)
    current_total_count: int = Field(..., ge=0)


class CalibrationAcceptanceComparison(JsonModel):
    """Accepted-record comparison that can reveal silent calibration erosion."""

    model_config = ConfigDict(extra="forbid")

    previous_accepted_count: int = Field(..., ge=0)
    current_accepted_count: int = Field(..., ge=0)
    accepted_count_delta: int
    accepted_count_stable: bool
    previous_accepted_decoy_fraction: float = Field(..., ge=0.0, le=1.0)
    current_accepted_decoy_fraction: float = Field(..., ge=0.0, le=1.0)
    accepted_decoy_fraction_delta: float


class CalibrationDriftReport(JsonModel):
    """Drift comparison across empirical calibration and accepted-record behavior."""

    model_config = ConfigDict(extra="forbid")

    previous_report: EmpiricalCalibrationSnapshot
    current_report: EmpiricalCalibrationSnapshot
    bin_deltas: tuple[CalibrationDriftBinDelta, ...] = Field(default_factory=tuple)
    acceptance: CalibrationAcceptanceComparison
    distribution_shift_score: float = Field(..., ge=0.0)
    top_fraction_decoy_delta: float
    calibration_regression_detected: bool
    regression_reasons: tuple[str, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


class CalibrationReleaseAlertSeverity(StrEnum):
    """Severity for release-facing calibration alerts."""

    BLOCKING = "blocking"
    WARNING = "warning"


class CalibrationReleaseAlert(JsonModel):
    """One release-facing alert derived from a calibration drift report."""

    model_config = ConfigDict(extra="forbid")

    workflow_label: str = Field(..., min_length=1)
    severity: CalibrationReleaseAlertSeverity
    distribution_shift_score: float = Field(..., ge=0.0)
    accepted_decoy_fraction_delta: float
    top_fraction_decoy_delta: float
    reasons: tuple[str, ...] = Field(default_factory=tuple)


class CalibrationReleaseGateReport(JsonModel):
    """Release gate over one or more flagship calibration drift reports."""

    model_config = ConfigDict(extra="forbid")

    alerts: tuple[CalibrationReleaseAlert, ...] = Field(default_factory=tuple)
    release_blocked: bool
    note: str = Field(..., min_length=1)


def _accepted_records(
    records: tuple[PsmRecord, ...],
    *,
    accepted_q_value_threshold: float,
) -> tuple[PsmRecord, ...]:
    return tuple(
        record
        for record in records
        if record.q_value is not None and record.q_value <= accepted_q_value_threshold
    )


def _accepted_decoy_fraction(records: tuple[PsmRecord, ...]) -> float:
    if not records:
        return 0.0
    decoys = sum(
        record.target_decoy_label is TargetDecoyLabel.DECOY for record in records
    )
    return decoys / len(records)


def _build_empirical_calibration_snapshot(
    records: tuple[PsmRecord, ...],
    *,
    score_orientation: str,
    bin_count: int,
    top_fraction: float,
) -> EmpiricalCalibrationSnapshot:
    normalized = normalize_psm_score_orientation(
        records,
        score_orientation=score_orientation,
    )
    total = len(normalized)
    buckets: list[list[tuple[TargetDecoyLabel, float]]] = [[] for _ in range(bin_count)]
    for entry in normalized:
        index = min(int(entry.normalized_score * bin_count), bin_count - 1)
        buckets[index].append((entry.target_decoy_label, entry.normalized_score))
    bins: list[CalibrationSnapshotBin] = []
    for index, bucket in enumerate(buckets, start=1):
        target_count = sum(label is TargetDecoyLabel.TARGET for label, _ in bucket)
        decoy_count = sum(label is TargetDecoyLabel.DECOY for label, _ in bucket)
        mixed_count = sum(label is TargetDecoyLabel.MIXED for label, _ in bucket)
        unknown_count = sum(label is TargetDecoyLabel.UNKNOWN for label, _ in bucket)
        total_count = len(bucket)
        bins.append(
            CalibrationSnapshotBin(
                bin_index=index,
                lower_bound=(index - 1) / bin_count,
                upper_bound=index / bin_count,
                total_count=total_count,
                target_count=target_count,
                decoy_count=decoy_count,
                mixed_count=mixed_count,
                unknown_count=unknown_count,
                decoy_fraction=decoy_count / total_count if total_count else 0.0,
            )
        )
    top_count = max(1, int(total * top_fraction)) if total else 0
    top_ranked = normalized[:top_count]
    top_targets = sum(
        entry.target_decoy_label is TargetDecoyLabel.TARGET for entry in top_ranked
    )
    top_decoys = sum(
        entry.target_decoy_label is TargetDecoyLabel.DECOY for entry in top_ranked
    )
    if not top_ranked:
        advisory = "no records are available for empirical calibration"
    elif top_decoys == 0:
        advisory = "top-ranked evidence is target-dominant; retain calibration snapshots to verify stability across runs"
    else:
        advisory = "top-ranked evidence includes decoys; confidence cutoffs should be reviewed before biological promotion"
    return EmpiricalCalibrationSnapshot(
        score_orientation=score_orientation,
        total_records=total,
        bin_count=bin_count,
        bins=tuple(bins),
        top_fraction=top_fraction,
        top_fraction_target_share=top_targets / len(top_ranked) if top_ranked else 0.0,
        top_fraction_decoy_share=top_decoys / len(top_ranked) if top_ranked else 0.0,
        advisory=advisory,
    )


def build_calibration_drift_report(
    previous_records: tuple[PsmRecord, ...],
    current_records: tuple[PsmRecord, ...],
    *,
    score_orientation: str = "higher_better",
    bin_count: int = 10,
    top_fraction: float = 0.1,
    accepted_q_value_threshold: float = 0.01,
    stable_count_tolerance: int = 0,
    acceptable_distribution_shift: float = 0.1,
    acceptable_top_fraction_decoy_delta: float = 0.05,
) -> CalibrationDriftReport:
    """Compare two calibration snapshots and flag silent scientific regressions."""

    previous_report = _build_empirical_calibration_snapshot(
        previous_records,
        score_orientation=score_orientation,
        bin_count=bin_count,
        top_fraction=top_fraction,
    )
    current_report = _build_empirical_calibration_snapshot(
        current_records,
        score_orientation=score_orientation,
        bin_count=bin_count,
        top_fraction=top_fraction,
    )
    bin_deltas = tuple(
        CalibrationDriftBinDelta(
            bin_index=previous_bin.bin_index,
            previous_decoy_fraction=previous_bin.decoy_fraction,
            current_decoy_fraction=current_bin.decoy_fraction,
            decoy_fraction_delta=round(
                current_bin.decoy_fraction - previous_bin.decoy_fraction,
                4,
            ),
            previous_total_count=previous_bin.total_count,
            current_total_count=current_bin.total_count,
        )
        for previous_bin, current_bin in zip(
            previous_report.bins, current_report.bins, strict=False
        )
    )
    distribution_shift_score = round(
        sum(abs(entry.decoy_fraction_delta) for entry in bin_deltas)
        / max(1, len(bin_deltas)),
        4,
    )
    previous_accepted = _accepted_records(
        previous_records,
        accepted_q_value_threshold=accepted_q_value_threshold,
    )
    current_accepted = _accepted_records(
        current_records,
        accepted_q_value_threshold=accepted_q_value_threshold,
    )
    acceptance = CalibrationAcceptanceComparison(
        previous_accepted_count=len(previous_accepted),
        current_accepted_count=len(current_accepted),
        accepted_count_delta=len(current_accepted) - len(previous_accepted),
        accepted_count_stable=(
            abs(len(current_accepted) - len(previous_accepted))
            <= stable_count_tolerance
        ),
        previous_accepted_decoy_fraction=round(
            _accepted_decoy_fraction(previous_accepted),
            4,
        ),
        current_accepted_decoy_fraction=round(
            _accepted_decoy_fraction(current_accepted),
            4,
        ),
        accepted_decoy_fraction_delta=round(
            _accepted_decoy_fraction(current_accepted)
            - _accepted_decoy_fraction(previous_accepted),
            4,
        ),
    )
    regression_reasons: list[str] = []
    top_fraction_decoy_delta = round(
        current_report.top_fraction_decoy_share
        - previous_report.top_fraction_decoy_share,
        4,
    )
    if distribution_shift_score > acceptable_distribution_shift:
        regression_reasons.append(
            "empirical score distributions shifted beyond the acceptable decoy-fraction tolerance"
        )
    if top_fraction_decoy_delta > acceptable_top_fraction_decoy_delta:
        regression_reasons.append(
            "top-ranked evidence became more decoy-heavy under the updated benchmark snapshot"
        )
    if (
        acceptance.accepted_count_stable
        and acceptance.accepted_decoy_fraction_delta > 0.0
    ):
        regression_reasons.append(
            "accepted record counts stayed stable while accepted-set decoy pressure increased"
        )
    calibration_regression_detected = bool(regression_reasons)
    note = (
        "calibration drift report detected one or more scientific regressions across benchmark snapshots"
        if calibration_regression_detected
        else "calibration drift report did not detect a decoy-pressure regression across benchmark snapshots"
    )
    return CalibrationDriftReport(
        previous_report=previous_report,
        current_report=current_report,
        bin_deltas=bin_deltas,
        acceptance=acceptance,
        distribution_shift_score=distribution_shift_score,
        top_fraction_decoy_delta=top_fraction_decoy_delta,
        calibration_regression_detected=calibration_regression_detected,
        regression_reasons=tuple(regression_reasons),
        note=note,
    )


def build_calibration_release_gate_report(
    reports: tuple[tuple[str, CalibrationDriftReport], ...],
    *,
    blocking_distribution_shift: float = 0.1,
    blocking_decoy_fraction_delta: float = 0.05,
) -> CalibrationReleaseGateReport:
    """Turn calibration drift into explicit release-blocking or warning alerts."""
    alerts: list[CalibrationReleaseAlert] = []
    for workflow_label, report in reports:
        if not report.calibration_regression_detected:
            continue
        severity = (
            CalibrationReleaseAlertSeverity.BLOCKING
            if (
                report.distribution_shift_score > blocking_distribution_shift
                or report.acceptance.accepted_decoy_fraction_delta
                > blocking_decoy_fraction_delta
            )
            else CalibrationReleaseAlertSeverity.WARNING
        )
        alerts.append(
            CalibrationReleaseAlert(
                workflow_label=workflow_label,
                severity=severity,
                distribution_shift_score=report.distribution_shift_score,
                accepted_decoy_fraction_delta=(
                    report.acceptance.accepted_decoy_fraction_delta
                ),
                top_fraction_decoy_delta=report.top_fraction_decoy_delta,
                reasons=report.regression_reasons,
            )
        )
    release_blocked = any(
        alert.severity is CalibrationReleaseAlertSeverity.BLOCKING for alert in alerts
    )
    note = (
        "release is blocked because one or more flagship calibration reports exceeded justified drift tolerances"
        if release_blocked
        else "release gate recorded calibration warnings only"
        if alerts
        else "release gate found no calibration drift alerts"
    )
    return CalibrationReleaseGateReport(
        alerts=tuple(alerts),
        release_blocked=release_blocked,
        note=note,
    )


__all__ = [
    "CalibrationAcceptanceComparison",
    "CalibrationDriftBinDelta",
    "CalibrationReleaseAlert",
    "CalibrationReleaseAlertSeverity",
    "CalibrationReleaseGateReport",
    "CalibrationSnapshotBin",
    "CalibrationDriftReport",
    "EmpiricalCalibrationSnapshot",
    "build_calibration_drift_report",
    "build_calibration_release_gate_report",
]

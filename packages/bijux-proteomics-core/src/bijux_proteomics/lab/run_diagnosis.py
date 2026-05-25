# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Run-failure diagnosis over governed run-QC tables."""

from __future__ import annotations

import csv
from collections import Counter
from enum import StrEnum
from io import StringIO
from statistics import median

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel


class LabQcStatus(StrEnum):
    """Stable run-level outcome labels for laboratory action surfaces."""

    PASS = "pass"
    CAUTION = "caution"
    FAIL = "fail"


class RunFailureClass(StrEnum):
    """Stable major failure classes for LC-MS run diagnosis."""

    NO_FAILURE = "no_failure"
    CHROMATOGRAPHY_FAILURE = "chromatography_failure"
    IDENTIFICATION_FAILURE = "identification_failure"
    INTENSITY_FAILURE = "intensity_failure"
    MIXED_FAILURE = "mixed_failure"


class RunDiagnosisQcEntry(JsonModel):
    """One run-QC row used for laboratory-facing run diagnosis."""

    model_config = ConfigDict(extra="forbid")

    run_id: str = Field(..., min_length=1)
    tic: float = Field(..., ge=0.0)
    bpc: float = Field(..., ge=0.0)
    ms1_count: int = Field(..., ge=0)
    ms2_count: int = Field(..., ge=0)
    id_count: int = Field(..., ge=0)
    median_rt: float = Field(..., ge=0.0)
    median_peak_width: float = Field(..., ge=0.0)
    missingness: float = Field(..., ge=0.0, le=1.0)


class RunDiagnosisEntry(JsonModel):
    """One diagnosed run outcome with explicit primary and secondary reasons."""

    model_config = ConfigDict(extra="forbid")

    run_id: str = Field(..., min_length=1)
    status: LabQcStatus
    failure_class: RunFailureClass
    primary_reason: str = Field(..., min_length=1)
    secondary_reasons: tuple[str, ...] = Field(default_factory=tuple)


def classify_run_failure(
    run_qc: tuple[RunDiagnosisQcEntry, ...],
) -> tuple[RunDiagnosisEntry, ...]:
    """Separate chromatography, identification, and intensity failures."""

    if len(run_qc) < 3:
        raise ValueError("run diagnosis requires at least three run_qc rows")
    run_id_counts = Counter(entry.run_id for entry in run_qc)
    duplicate_run_ids = {
        run_id for run_id, count in run_id_counts.items() if count > 1
    }
    if duplicate_run_ids:
        raise ValueError(
            "run diagnosis requires unique run_id values and found duplicates for: "
            + ", ".join(sorted(duplicate_run_ids))
        )

    baselines = _baseline_profile(run_qc)
    diagnosed = [
        _diagnose_run(entry, baselines=baselines)
        for entry in sorted(run_qc, key=lambda item: item.run_id)
    ]
    return tuple(diagnosed)


def render_run_diagnosis_tsv(entries: tuple[RunDiagnosisEntry, ...]) -> str:
    """Render run diagnosis rows as a stable TSV table."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "run_id",
            "status",
            "failure_class",
            "primary_reason",
            "secondary_reasons",
        )
    )
    for entry in entries:
        writer.writerow(
            (
                entry.run_id,
                entry.status.value,
                entry.failure_class.value,
                entry.primary_reason,
                ";".join(entry.secondary_reasons),
            )
        )
    return buffer.getvalue()


class _BaselineProfile(JsonModel):
    """Cohort medians used for stable run-failure comparison."""

    model_config = ConfigDict(extra="forbid")

    tic: float = Field(..., ge=0.0)
    bpc: float = Field(..., ge=0.0)
    ms1_count: float = Field(..., ge=0.0)
    ms2_count: float = Field(..., ge=0.0)
    id_count: float = Field(..., ge=0.0)
    median_rt: float = Field(..., ge=0.0)
    median_peak_width: float = Field(..., ge=0.0)
    missingness: float = Field(..., ge=0.0, le=1.0)
    identification_yield: float = Field(..., ge=0.0)


def _baseline_profile(run_qc: tuple[RunDiagnosisQcEntry, ...]) -> _BaselineProfile:
    return _BaselineProfile(
        tic=median(entry.tic for entry in run_qc),
        bpc=median(entry.bpc for entry in run_qc),
        ms1_count=float(median(entry.ms1_count for entry in run_qc)),
        ms2_count=float(median(entry.ms2_count for entry in run_qc)),
        id_count=float(median(entry.id_count for entry in run_qc)),
        median_rt=median(entry.median_rt for entry in run_qc),
        median_peak_width=median(entry.median_peak_width for entry in run_qc),
        missingness=median(entry.missingness for entry in run_qc),
        identification_yield=median(
            _identification_yield(entry.id_count, entry.ms2_count) for entry in run_qc
        ),
    )


def _diagnose_run(
    entry: RunDiagnosisQcEntry,
    *,
    baselines: _BaselineProfile,
) -> RunDiagnosisEntry:
    chromatography_reasons = _chromatography_reasons(entry, baselines=baselines)
    identification_reasons = _identification_reasons(entry, baselines=baselines)
    intensity_reasons = _intensity_reasons(entry, baselines=baselines)
    score_by_class = {
        RunFailureClass.CHROMATOGRAPHY_FAILURE: _score_reasons(chromatography_reasons),
        RunFailureClass.IDENTIFICATION_FAILURE: _score_reasons(identification_reasons),
        RunFailureClass.INTENSITY_FAILURE: _score_reasons(intensity_reasons),
    }
    ranked = sorted(score_by_class.items(), key=lambda item: item[1], reverse=True)
    primary_class, primary_score = ranked[0]
    secondary_class, secondary_score = ranked[1]
    all_secondary_reasons = tuple(
        reason
        for _, reasons in (
            (RunFailureClass.CHROMATOGRAPHY_FAILURE, chromatography_reasons),
            (RunFailureClass.IDENTIFICATION_FAILURE, identification_reasons),
            (RunFailureClass.INTENSITY_FAILURE, intensity_reasons),
        )
        for reason, _ in reasons
    )

    if primary_score < 0.35:
        return RunDiagnosisEntry(
            run_id=entry.run_id,
            status=LabQcStatus.PASS,
            failure_class=RunFailureClass.NO_FAILURE,
            primary_reason="no_material_qc_failure_detected",
            secondary_reasons=(),
        )

    if primary_score >= 0.7:
        status = LabQcStatus.FAIL
    else:
        status = LabQcStatus.CAUTION

    if secondary_score >= 0.55 and primary_score - secondary_score <= 0.15:
        mixed_reasons = tuple(
            sorted(
                {
                    reason
                    for reason in all_secondary_reasons
                    if reason != "no_material_qc_failure_detected"
                }
            )
        )
        return RunDiagnosisEntry(
            run_id=entry.run_id,
            status=LabQcStatus.FAIL,
            failure_class=RunFailureClass.MIXED_FAILURE,
            primary_reason=_primary_reason_for_class(primary_class, entry, baselines),
            secondary_reasons=mixed_reasons,
        )

    secondary_reasons = tuple(
        reason
        for reason in sorted(
            {
                reason
                for failure_class, reasons in (
                    (RunFailureClass.CHROMATOGRAPHY_FAILURE, chromatography_reasons),
                    (RunFailureClass.IDENTIFICATION_FAILURE, identification_reasons),
                    (RunFailureClass.INTENSITY_FAILURE, intensity_reasons),
                )
                if failure_class is not primary_class
                for reason, _ in reasons
            }
        )
    )
    return RunDiagnosisEntry(
        run_id=entry.run_id,
        status=status,
        failure_class=primary_class,
        primary_reason=_primary_reason_for_class(primary_class, entry, baselines),
        secondary_reasons=secondary_reasons,
    )


def _chromatography_reasons(
    entry: RunDiagnosisQcEntry,
    *,
    baselines: _BaselineProfile,
) -> tuple[tuple[str, float], ...]:
    reasons: list[tuple[str, float]] = []
    peak_width_ratio = _ratio(entry.median_peak_width, baselines.median_peak_width)
    if peak_width_ratio >= 1.45:
        reasons.append(("broad_peak_width", min(1.0, (peak_width_ratio - 1.0) / 0.7)))
    rt_shift_fraction = abs(entry.median_rt - baselines.median_rt) / max(
        baselines.median_rt,
        1.0,
    )
    if rt_shift_fraction >= 0.08:
        reasons.append(
            ("retention_time_shift", min(1.0, rt_shift_fraction / 0.2))
        )
    if entry.missingness - baselines.missingness >= 0.18:
        reasons.append(
            (
                "high_missingness_after_chromatography_shift",
                min(1.0, (entry.missingness - baselines.missingness) / 0.4),
            )
        )
    return tuple(sorted(reasons, key=lambda item: (-item[1], item[0])))


def _identification_reasons(
    entry: RunDiagnosisQcEntry,
    *,
    baselines: _BaselineProfile,
) -> tuple[tuple[str, float], ...]:
    reasons: list[tuple[str, float]] = []
    identification_yield = _identification_yield(entry.id_count, entry.ms2_count)
    yield_ratio = _ratio(identification_yield, baselines.identification_yield)
    if yield_ratio <= 0.45:
        reasons.append(
            ("low_identification_yield", min(1.0, (1.0 - yield_ratio) / 0.8))
        )
    id_ratio = _ratio(float(entry.id_count), baselines.id_count)
    if id_ratio <= 0.45:
        reasons.append(("low_identification_count", min(1.0, (1.0 - id_ratio) / 0.8)))
    if _ratio(entry.ms2_count, baselines.ms2_count) >= 0.75 and yield_ratio <= 0.8:
        reasons.append(
            (
                "ms2_present_without_ids",
                min(0.65, (1.0 - yield_ratio) / 1.5),
            )
        )
    return tuple(sorted(reasons, key=lambda item: (-item[1], item[0])))


def _intensity_reasons(
    entry: RunDiagnosisQcEntry,
    *,
    baselines: _BaselineProfile,
) -> tuple[tuple[str, float], ...]:
    reasons: list[tuple[str, float]] = []
    tic_ratio = _ratio(entry.tic, baselines.tic)
    if tic_ratio <= 0.45:
        reasons.append(("low_tic", min(1.0, (1.0 - tic_ratio) / 0.8)))
    bpc_ratio = _ratio(entry.bpc, baselines.bpc)
    if bpc_ratio <= 0.45:
        reasons.append(("low_bpc", min(1.0, (1.0 - bpc_ratio) / 0.8)))
    ms1_ratio = _ratio(float(entry.ms1_count), baselines.ms1_count)
    if ms1_ratio <= 0.55:
        reasons.append(("low_ms1_count", min(1.0, (1.0 - ms1_ratio) / 0.7)))
    if entry.missingness - baselines.missingness >= 0.2:
        reasons.append(
            ("high_missingness_with_low_signal", min(1.0, (entry.missingness - baselines.missingness) / 0.45))
        )
    return tuple(sorted(reasons, key=lambda item: (-item[1], item[0])))


def _score_reasons(reasons: tuple[tuple[str, float], ...]) -> float:
    if not reasons:
        return 0.0
    strongest = reasons[0][1]
    support_bonus = min(0.2, 0.05 * (len(reasons) - 1))
    return round(min(1.0, strongest + support_bonus), 4)


def _primary_reason_for_class(
    failure_class: RunFailureClass,
    entry: RunDiagnosisQcEntry,
    baselines: _BaselineProfile,
) -> str:
    lookup = {
        RunFailureClass.CHROMATOGRAPHY_FAILURE: _chromatography_reasons(
            entry, baselines=baselines
        ),
        RunFailureClass.IDENTIFICATION_FAILURE: _identification_reasons(
            entry, baselines=baselines
        ),
        RunFailureClass.INTENSITY_FAILURE: _intensity_reasons(
            entry, baselines=baselines
        ),
    }
    reasons = lookup.get(failure_class, ())
    if not reasons:
        return "no_material_qc_failure_detected"
    return reasons[0][0]


def _identification_yield(id_count: int, ms2_count: int) -> float:
    if ms2_count <= 0:
        return 0.0
    return id_count / ms2_count


def _ratio(observed: float, baseline: float) -> float:
    if baseline <= 0.0:
        return 1.0 if observed <= 0.0 else observed
    return observed / baseline


__all__ = [
    "LabQcStatus",
    "RunDiagnosisQcEntry",
    "RunDiagnosisEntry",
    "RunFailureClass",
    "classify_run_failure",
    "render_run_diagnosis_tsv",
]

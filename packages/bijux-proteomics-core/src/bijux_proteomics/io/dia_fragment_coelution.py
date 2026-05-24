# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Score DIA fragment-trace coelution from chromatographic peak support."""

from __future__ import annotations

import csv
from io import StringIO
from pathlib import Path
from statistics import mean

from pydantic import ConfigDict, Field

from bijux_proteomics.io.chromatographic_peak_picking import (
    ChromatographicPeak,
    ChromatographicPeakPickingReport,
    extract_mzml_chromatographic_peaks,
)
from bijux_proteomics.io.xic_extraction import XicTargetEntry, XicTargetParseReport
from bijux_proteomics_foundation import JsonModel


class DiaFragmentCoelutionFragmentEntry(JsonModel):
    """One run-level fragment coelution assessment for a DIA precursor."""

    model_config = ConfigDict(extra="forbid")

    run_id: str = Field(..., min_length=1)
    precursor_id: str = Field(..., min_length=1)
    peptide_ref: str = Field(..., min_length=1)
    target_id: str = Field(..., min_length=1)
    fragment_id: str = Field(..., min_length=1)
    reference_fragment_id: str = Field(..., min_length=1)
    peak_id: str | None = None
    apex_time_seconds: float | None = Field(default=None, ge=0.0)
    apex_intensity: float = Field(..., ge=0.0)
    area: float = Field(..., ge=0.0)
    apex_shift_seconds: float | None = Field(default=None, ge=0.0)
    correlation_to_reference: float | None = Field(default=None, ge=-1.0, le=1.0)
    passed: bool
    failure_reason: str | None = None
    concern_codes: tuple[str, ...] = Field(default_factory=tuple)


class DiaFragmentCoelutionRunEntry(JsonModel):
    """One run-level precursor coelution summary over assigned fragment traces."""

    model_config = ConfigDict(extra="forbid")

    run_id: str = Field(..., min_length=1)
    precursor_id: str = Field(..., min_length=1)
    peptide_ref: str = Field(..., min_length=1)
    reference_fragment_id: str | None = None
    fragment_count: int = Field(..., ge=1)
    detected_fragment_count: int = Field(..., ge=0)
    passing_fragment_count: int = Field(..., ge=0)
    apex_spread_seconds: float = Field(..., ge=0.0)
    mean_correlation: float = Field(..., ge=-1.0, le=1.0)
    coelution_score: float = Field(..., ge=0.0, le=1.0)
    failed_fragment_ids: tuple[str, ...] = Field(default_factory=tuple)
    concern_codes: tuple[str, ...] = Field(default_factory=tuple)


class DiaFragmentCoelutionReport(JsonModel):
    """Stable DIA fragment coelution report over one or more mzML runs."""

    model_config = ConfigDict(extra="forbid")

    run_ids: tuple[str, ...] = Field(default_factory=tuple)
    run_entries: tuple[DiaFragmentCoelutionRunEntry, ...] = Field(default_factory=tuple)
    fragment_entries: tuple[DiaFragmentCoelutionFragmentEntry, ...] = Field(
        default_factory=tuple
    )


class DiaFragmentTracePoint(JsonModel):
    """One raw DIA fragment-trace intensity point."""

    model_config = ConfigDict(extra="forbid")

    precursor_id: str = Field(..., min_length=1)
    fragment_id: str = Field(..., min_length=1)
    rt: float = Field(..., ge=0.0)
    intensity: float = Field(..., ge=0.0)


class DiaFragmentTraceCoelutionScore(JsonModel):
    """One raw precursor-level coelution score over fragment traces."""

    model_config = ConfigDict(extra="forbid")

    precursor_id: str = Field(..., min_length=1)
    fragment_count: int = Field(..., ge=1)
    apex_rt_spread: float = Field(..., ge=0.0)
    mean_trace_correlation: float = Field(..., ge=-1.0, le=1.0)
    failed_fragments: tuple[str, ...] = Field(default_factory=tuple)
    coelution_score: float = Field(..., ge=0.0, le=1.0)


def score_fragment_coelution(
    fragment_xics: tuple[DiaFragmentTracePoint, ...],
    *,
    apex_tolerance_seconds: float = 5.0,
    min_correlation: float = 0.8,
) -> tuple[DiaFragmentTraceCoelutionScore, ...]:
    """Score precursor-level DIA fragment coelution directly from raw traces."""

    if not fragment_xics:
        raise ValueError("fragment_xics must not be empty")
    if apex_tolerance_seconds <= 0.0:
        raise ValueError("apex_tolerance_seconds must be greater than zero")
    if not -1.0 <= min_correlation <= 1.0:
        raise ValueError("min_correlation must be between minus one and one")

    traces_by_precursor: dict[str, dict[str, dict[float, float]]] = {}
    for point in fragment_xics:
        traces_by_precursor.setdefault(point.precursor_id, {}).setdefault(
            point.fragment_id,
            {},
        )[point.rt] = point.intensity

    rows: list[DiaFragmentTraceCoelutionScore] = []
    for precursor_id, traces_by_fragment in sorted(traces_by_precursor.items()):
        detected_traces_by_fragment = {
            fragment_id: trace
            for fragment_id, trace in traces_by_fragment.items()
            if max(trace.values(), default=0.0) > 0.0
        }
        if detected_traces_by_fragment:
            reference_fragment_id, reference_trace = max(
                detected_traces_by_fragment.items(),
                key=lambda item: (
                    sum(item[1].values()),
                    max(item[1].values(), default=0.0),
                    item[0],
                ),
            )
        else:
            reference_fragment_id, reference_trace = max(
                traces_by_fragment.items(),
                key=lambda item: item[0],
            )
        fragment_apexes = {
            fragment_id: _trace_apex_rt(trace)
            for fragment_id, trace in detected_traces_by_fragment.items()
        }
        apex_values = tuple(fragment_apexes.values())
        apex_rt_spread = (
            0.0
            if not apex_values
            else max(apex_values) - min(apex_values)
        )
        correlations: list[float] = []
        failed_fragments: list[str] = []
        reference_apex = (
            None
            if reference_fragment_id not in fragment_apexes
            else fragment_apexes[reference_fragment_id]
        )
        for fragment_id, trace in sorted(traces_by_fragment.items()):
            if max(trace.values(), default=0.0) <= 0.0:
                failed_fragments.append(fragment_id)
                continue
            if fragment_id == reference_fragment_id:
                correlations.append(1.0)
                continue
            correlation = _pearson_correlation(reference_trace, trace)
            correlations.append(correlation)
            apex_shift = (
                0.0
                if reference_apex is None
                else abs(fragment_apexes[fragment_id] - reference_apex)
            )
            if apex_shift > apex_tolerance_seconds or correlation < min_correlation:
                failed_fragments.append(fragment_id)

        rows.append(
            DiaFragmentTraceCoelutionScore(
                precursor_id=precursor_id,
                fragment_count=len(traces_by_fragment),
                apex_rt_spread=round(apex_rt_spread, 4),
                mean_trace_correlation=round(mean(correlations), 4),
                failed_fragments=tuple(sorted(failed_fragments)),
                coelution_score=_coelution_score(
                    fragment_count=len(traces_by_fragment),
                    passing_fragment_count=(
                        len(traces_by_fragment) - len(failed_fragments)
                    ),
                    correlations=correlations,
                    apex_spread_seconds=apex_rt_spread,
                    apex_tolerance_seconds=apex_tolerance_seconds,
                ),
            )
        )
    return tuple(rows)


def score_dia_fragment_trace_coelution(
    peak_reports: tuple[ChromatographicPeakPickingReport, ...],
    *,
    apex_tolerance_seconds: float = 5.0,
    min_correlation: float = 0.8,
    min_passing_fragment_count: int = 2,
) -> DiaFragmentCoelutionReport:
    """Score coelution among DIA fragment traces assigned to one precursor."""

    if not peak_reports:
        raise ValueError("DIA fragment coelution scoring requires at least one run report")
    if apex_tolerance_seconds <= 0.0:
        raise ValueError("apex_tolerance_seconds must be greater than zero")
    if not -1.0 <= min_correlation <= 1.0:
        raise ValueError("min_correlation must be between minus one and one")
    if min_passing_fragment_count <= 0:
        raise ValueError("min_passing_fragment_count must be greater than zero")

    run_entries: list[DiaFragmentCoelutionRunEntry] = []
    fragment_entries: list[DiaFragmentCoelutionFragmentEntry] = []
    run_ids: list[str] = []

    for peak_report in peak_reports:
        run_id = _run_id_from_peak_report(peak_report)
        run_ids.append(run_id)
        targets_by_precursor = _targets_by_precursor(peak_report.trace_report.accepted_targets)
        peaks_by_target = _peaks_by_target(peak_report)
        traces_by_target = _trace_series_by_target(peak_report)
        raw_scores_by_precursor = _raw_trace_scores_by_precursor(
            peak_report.trace_report.accepted_targets,
            traces_by_target,
            apex_tolerance_seconds=apex_tolerance_seconds,
            min_correlation=min_correlation,
        )

        for precursor_id, targets in sorted(targets_by_precursor.items()):
            peptide_ref = _peptide_ref(targets[0])
            selected_peaks: dict[str, ChromatographicPeak] = {}
            concern_codes: set[str] = set()
            for target in targets:
                target_peaks = peaks_by_target.get(target.target_id, ())
                if len(target_peaks) > 1:
                    concern_codes.add("multiple_peaks")
                if target_peaks:
                    selected_peaks[target.target_id] = max(
                        target_peaks,
                        key=lambda peak: (peak.area, peak.height),
                    )

            reference_target = _reference_target(targets, selected_peaks)
            reference_fragment_id = (
                None
                if reference_target is None
                else _fragment_id(reference_target)
            )
            reference_series = (
                None
                if reference_target is None
                else traces_by_target.get(reference_target.target_id)
            )
            reference_peak = (
                None
                if reference_target is None
                else selected_peaks.get(reference_target.target_id)
            )

            fragment_correlations: list[float] = []
            passing_fragment_ids: list[str] = []
            failed_fragment_ids: list[str] = []

            for target in targets:
                fragment_id = _fragment_id(target)
                peak = selected_peaks.get(target.target_id)
                fragment_concerns: set[str] = set()
                failure_reason: str | None = None
                apex_shift_seconds: float | None = None
                correlation_to_reference: float | None = None
                apex_intensity = 0.0
                area = 0.0
                peak_id: str | None = None
                apex_time_seconds: float | None = None

                if peak is None:
                    fragment_concerns.add("missing_peak")
                    failure_reason = "missing_peak"
                else:
                    peak_id = peak.peak_id
                    apex_time_seconds = peak.apex_time_seconds
                    apex_intensity = peak.apex_intensity
                    area = peak.area
                    if peak.overlap_flag:
                        fragment_concerns.add("overlap_detected")
                    if peak.shoulder_flag:
                        fragment_concerns.add("shoulder_detected")
                    if reference_peak is not None:
                        apex_shift_seconds = abs(
                            peak.apex_time_seconds - reference_peak.apex_time_seconds
                        )
                    if reference_series is not None:
                        correlation_to_reference = _pearson_correlation(
                            reference_series,
                            traces_by_target.get(target.target_id, {}),
                        )
                        fragment_correlations.append(correlation_to_reference)
                    if (
                        target.target_id != reference_target.target_id
                        if reference_target is not None
                        else False
                    ):
                        if (
                            apex_shift_seconds is not None
                            and apex_shift_seconds > apex_tolerance_seconds
                        ):
                            fragment_concerns.add("shifted_apex")
                            failure_reason = "shifted_apex"
                        if (
                            correlation_to_reference is not None
                            and correlation_to_reference < min_correlation
                            and failure_reason is None
                        ):
                            fragment_concerns.add("low_correlation")
                            failure_reason = "low_correlation"

                passed = failure_reason is None
                if passed:
                    passing_fragment_ids.append(fragment_id)
                else:
                    failed_fragment_ids.append(fragment_id)
                concern_codes.update(fragment_concerns)

                fragment_entries.append(
                    DiaFragmentCoelutionFragmentEntry(
                        run_id=run_id,
                        precursor_id=precursor_id,
                        peptide_ref=peptide_ref,
                        target_id=target.target_id,
                        fragment_id=fragment_id,
                        reference_fragment_id=reference_fragment_id or fragment_id,
                        peak_id=peak_id,
                        apex_time_seconds=apex_time_seconds,
                        apex_intensity=apex_intensity,
                        area=area,
                        apex_shift_seconds=apex_shift_seconds,
                        correlation_to_reference=(
                            1.0
                            if reference_target is not None
                            and target.target_id == reference_target.target_id
                            and peak is not None
                            else correlation_to_reference
                        ),
                        passed=passed,
                        failure_reason=failure_reason,
                        concern_codes=tuple(sorted(fragment_concerns)),
                    )
                )

            if len(passing_fragment_ids) < min_passing_fragment_count:
                concern_codes.add("insufficient_passing_fragments")

            run_entries.append(
                DiaFragmentCoelutionRunEntry(
                    run_id=run_id,
                    precursor_id=precursor_id,
                    peptide_ref=peptide_ref,
                    reference_fragment_id=reference_fragment_id,
                    fragment_count=len(targets),
                    detected_fragment_count=len(selected_peaks),
                    passing_fragment_count=len(passing_fragment_ids),
                    apex_spread_seconds=raw_scores_by_precursor[precursor_id].apex_rt_spread,
                    mean_correlation=raw_scores_by_precursor[
                        precursor_id
                    ].mean_trace_correlation,
                    coelution_score=raw_scores_by_precursor[precursor_id].coelution_score,
                    failed_fragment_ids=raw_scores_by_precursor[
                        precursor_id
                    ].failed_fragments,
                    concern_codes=tuple(sorted(concern_codes)),
                )
            )

    return DiaFragmentCoelutionReport(
        run_ids=tuple(sorted(set(run_ids))),
        run_entries=tuple(
            sorted(run_entries, key=lambda item: (item.precursor_id, item.run_id))
        ),
        fragment_entries=tuple(
            sorted(
                fragment_entries,
                key=lambda item: (
                    item.precursor_id,
                    item.run_id,
                    item.fragment_id,
                ),
            )
        ),
    )


def extract_mzml_dia_fragment_trace_coelution(
    mzml_paths: tuple[Path, ...],
    targets: Path | XicTargetParseReport | tuple[XicTargetEntry, ...],
    *,
    tolerance_da: float | None = None,
    tolerance_ppm: float | None = None,
    ms_level: int = 2,
    min_peak_height: float = 1.0,
    shoulder_boundary_fraction_threshold: float = 0.5,
    apex_tolerance_seconds: float = 5.0,
    min_correlation: float = 0.8,
    min_passing_fragment_count: int = 2,
) -> DiaFragmentCoelutionReport:
    """Extract DIA fragment traces from mzML and score precursor coelution."""

    if not mzml_paths:
        raise ValueError("DIA fragment coelution extraction requires at least one mzML file")

    peak_reports = tuple(
        extract_mzml_chromatographic_peaks(
            mzml_path,
            targets,
            tolerance_da=tolerance_da,
            tolerance_ppm=tolerance_ppm,
            ms_level=ms_level,
            min_peak_height=min_peak_height,
            shoulder_boundary_fraction_threshold=shoulder_boundary_fraction_threshold,
        )
        for mzml_path in mzml_paths
    )
    return score_dia_fragment_trace_coelution(
        peak_reports,
        apex_tolerance_seconds=apex_tolerance_seconds,
        min_correlation=min_correlation,
        min_passing_fragment_count=min_passing_fragment_count,
    )


def render_dia_fragment_coelution_runs_tsv(
    report: DiaFragmentCoelutionReport,
) -> str:
    """Render run-level DIA precursor coelution ledgers as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "run_id",
            "precursor_id",
            "peptide_ref",
            "reference_fragment_id",
            "fragment_count",
            "detected_fragment_count",
            "passing_fragment_count",
            "apex_spread_seconds",
            "mean_correlation",
            "coelution_score",
            "failed_fragment_ids",
            "concern_codes",
        )
    )
    for entry in report.run_entries:
        writer.writerow(
            (
                entry.run_id,
                entry.precursor_id,
                entry.peptide_ref,
                "" if entry.reference_fragment_id is None else entry.reference_fragment_id,
                entry.fragment_count,
                entry.detected_fragment_count,
                entry.passing_fragment_count,
                f"{entry.apex_spread_seconds:.4f}",
                f"{entry.mean_correlation:.4f}",
                f"{entry.coelution_score:.4f}",
                "|".join(entry.failed_fragment_ids),
                "|".join(entry.concern_codes),
            )
        )
    return buffer.getvalue()


def render_dia_fragment_coelution_fragments_tsv(
    report: DiaFragmentCoelutionReport,
) -> str:
    """Render fragment-level DIA coelution review rows as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "run_id",
            "precursor_id",
            "peptide_ref",
            "target_id",
            "fragment_id",
            "reference_fragment_id",
            "peak_id",
            "apex_time_seconds",
            "apex_intensity",
            "area",
            "apex_shift_seconds",
            "correlation_to_reference",
            "passed",
            "failure_reason",
            "concern_codes",
        )
    )
    for entry in report.fragment_entries:
        writer.writerow(
            (
                entry.run_id,
                entry.precursor_id,
                entry.peptide_ref,
                entry.target_id,
                entry.fragment_id,
                entry.reference_fragment_id,
                "" if entry.peak_id is None else entry.peak_id,
                "" if entry.apex_time_seconds is None else f"{entry.apex_time_seconds:.4f}",
                f"{entry.apex_intensity:.4f}",
                f"{entry.area:.4f}",
                "" if entry.apex_shift_seconds is None else f"{entry.apex_shift_seconds:.4f}",
                (
                    ""
                    if entry.correlation_to_reference is None
                    else f"{entry.correlation_to_reference:.4f}"
                ),
                str(entry.passed).lower(),
                "" if entry.failure_reason is None else entry.failure_reason,
                "|".join(entry.concern_codes),
            )
        )
    return buffer.getvalue()


def render_dia_fragment_trace_coelution_tsv(
    rows: tuple[DiaFragmentTraceCoelutionScore, ...],
) -> str:
    """Render raw DIA fragment-trace coelution scores as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "precursor_id",
            "fragment_count",
            "apex_rt_spread",
            "mean_trace_correlation",
            "failed_fragments",
            "coelution_score",
        )
    )
    for row in rows:
        writer.writerow(
            (
                row.precursor_id,
                row.fragment_count,
                f"{row.apex_rt_spread:.4f}",
                f"{row.mean_trace_correlation:.4f}",
                "|".join(row.failed_fragments),
                f"{row.coelution_score:.4f}",
            )
        )
    return buffer.getvalue()


def _run_id_from_peak_report(report: ChromatographicPeakPickingReport) -> str:
    return Path(report.trace_report.source_path).stem


def _targets_by_precursor(
    targets: tuple[XicTargetEntry, ...],
) -> dict[str, list[XicTargetEntry]]:
    grouped: dict[str, list[XicTargetEntry]] = {}
    for target in targets:
        precursor_id = _precursor_id(target)
        grouped.setdefault(precursor_id, []).append(target)
    return grouped


def _peaks_by_target(
    report: ChromatographicPeakPickingReport,
) -> dict[str, tuple[ChromatographicPeak, ...]]:
    grouped: dict[str, list[ChromatographicPeak]] = {}
    for peak in report.peaks:
        grouped.setdefault(peak.target_id, []).append(peak)
    return {key: tuple(value) for key, value in grouped.items()}


def _trace_series_by_target(
    report: ChromatographicPeakPickingReport,
) -> dict[str, dict[float, float]]:
    grouped: dict[str, dict[float, float]] = {}
    for point in report.trace_report.trace_points:
        grouped.setdefault(point.target_id, {})[point.time_seconds] = point.intensity
    return grouped


def _raw_trace_scores_by_precursor(
    targets: tuple[XicTargetEntry, ...],
    traces_by_target: dict[str, dict[float, float]],
    *,
    apex_tolerance_seconds: float,
    min_correlation: float,
) -> dict[str, DiaFragmentTraceCoelutionScore]:
    raw_points: list[DiaFragmentTracePoint] = []
    for target in targets:
        precursor_id = _precursor_id(target)
        fragment_id = _fragment_id(target)
        for rt, intensity in sorted(
            traces_by_target.get(target.target_id, {}).items()
        ):
            raw_points.append(
                DiaFragmentTracePoint(
                    precursor_id=precursor_id,
                    fragment_id=fragment_id,
                    rt=rt,
                    intensity=intensity,
                )
            )
    return {
        row.precursor_id: row
        for row in score_fragment_coelution(
            tuple(raw_points),
            apex_tolerance_seconds=apex_tolerance_seconds,
            min_correlation=min_correlation,
        )
    }


def _trace_apex_rt(trace: dict[float, float]) -> float:
    apex_rt, _ = max(
        trace.items(),
        key=lambda item: (item[1], -item[0]),
    )
    return apex_rt


def _reference_target(
    targets: list[XicTargetEntry],
    selected_peaks: dict[str, ChromatographicPeak],
) -> XicTargetEntry | None:
    detected_targets = [
        target for target in targets if target.target_id in selected_peaks
    ]
    if not detected_targets:
        return None
    return max(
        detected_targets,
        key=lambda target: (
            selected_peaks[target.target_id].area,
            selected_peaks[target.target_id].height,
        ),
    )


def _precursor_id(target: XicTargetEntry) -> str:
    precursor_id = (
        target.metadata.get("precursor_id")
        or target.metadata.get("precursor_ref")
        or target.metadata.get("precursor")
    )
    if precursor_id is None:
        raise ValueError(
            f"DIA fragment coelution target {target.target_id!r} requires precursor_id metadata"
        )
    return precursor_id


def _peptide_ref(target: XicTargetEntry) -> str:
    return (
        target.metadata.get("peptide_ref")
        or target.display_name
        or _precursor_id(target)
    )


def _fragment_id(target: XicTargetEntry) -> str:
    return (
        target.metadata.get("fragment_id")
        or target.metadata.get("transition_id")
        or target.target_id
    )


def _pearson_correlation(
    left_series: dict[float, float],
    right_series: dict[float, float],
) -> float:
    times = sorted(set(left_series) | set(right_series))
    if len(times) < 2:
        return 0.0
    left = [left_series.get(time, 0.0) for time in times]
    right = [right_series.get(time, 0.0) for time in times]
    left_mean = mean(left)
    right_mean = mean(right)
    left_centered = [value - left_mean for value in left]
    right_centered = [value - right_mean for value in right]
    numerator = sum(a * b for a, b in zip(left_centered, right_centered, strict=True))
    left_scale = sum(value * value for value in left_centered) ** 0.5
    right_scale = sum(value * value for value in right_centered) ** 0.5
    if left_scale == 0.0 or right_scale == 0.0:
        return 0.0
    correlation = numerator / (left_scale * right_scale)
    if abs(1.0 - correlation) < 1e-3:
        return 1.0
    if abs(-1.0 - correlation) < 1e-3:
        return -1.0
    return correlation


def _coelution_score(
    *,
    fragment_count: int,
    passing_fragment_count: int,
    correlations: list[float],
    apex_spread_seconds: float,
    apex_tolerance_seconds: float,
) -> float:
    passing_fraction = passing_fragment_count / fragment_count
    correlation_component = (
        0.0
        if not correlations
        else mean(max(0.0, correlation) for correlation in correlations)
    )
    apex_component = max(
        0.0,
        1.0 - (apex_spread_seconds / (apex_tolerance_seconds * 2.0)),
    )
    return round(mean((passing_fraction, correlation_component, apex_component)), 4)

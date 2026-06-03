# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Detect chromatographic peaks from extracted XIC traces."""

from __future__ import annotations

import csv
from enum import StrEnum
from io import StringIO

from pydantic import ConfigDict, Field

from bijux_proteomics.io.chromatography.xic import (
    XicExtractionPoint,
    XicTracePoint,
    XicTraceReport,
)
from bijux_proteomics.io.tables.xic_target_table import XicTargetEntry
from bijux_proteomics_foundation import JsonModel


class ChromatographicPeakQuality(StrEnum):
    """Quality classification for one picked chromatographic peak."""

    CLEAN = "clean"
    OVERLAP = "overlap"
    SHOULDER = "shoulder"
    WEAK = "weak"


class PeakShapeQualityTier(StrEnum):
    """Shape-quality classification for one chromatographic peak trace."""

    GAUSSIAN_LIKE = "gaussian_like"
    ACCEPTABLE = "acceptable"
    JAGGED_NOISY = "jagged_noisy"
    FLAT_BROAD = "flat_broad"


class PeakShapeScore(JsonModel):
    """One raw chromatographic peak-shape score over a peak trace."""

    model_config = ConfigDict(extra="forbid")

    symmetry_score: float = Field(..., ge=0.0, le=1.0)
    tailing_score: float = Field(..., ge=0.0, le=1.0)
    smoothness_score: float = Field(..., ge=0.0, le=1.0)
    apex_prominence: float = Field(..., ge=0.0, le=1.0)
    shape_quality_tier: PeakShapeQualityTier


class PickedChromatographicPeak(JsonModel):
    """One raw chromatographic peak with the engine output contract."""

    model_config = ConfigDict(extra="forbid")

    rt_start: float = Field(..., ge=0.0)
    rt_apex: float = Field(..., ge=0.0)
    rt_end: float = Field(..., ge=0.0)
    area: float = Field(..., ge=0.0)
    height: float = Field(..., ge=0.0)
    baseline: float = Field(..., ge=0.0)
    peak_width: float = Field(..., ge=0.0)
    overlap_flag: bool
    peak_quality: ChromatographicPeakQuality


class ChromatographicPeak(JsonModel):
    """One chromatographic peak detected for one precursor target."""

    model_config = ConfigDict(extra="forbid")

    peak_id: str = Field(..., min_length=1)
    target_id: str = Field(..., min_length=1)
    start_time_seconds: float = Field(..., ge=0.0)
    end_time_seconds: float = Field(..., ge=0.0)
    apex_time_seconds: float = Field(..., ge=0.0)
    apex_intensity: float = Field(..., ge=0.0)
    baseline_start_intensity: float = Field(..., ge=0.0)
    baseline_end_intensity: float = Field(..., ge=0.0)
    baseline_at_apex: float = Field(..., ge=0.0)
    height: float = Field(..., ge=0.0)
    area: float = Field(..., ge=0.0)
    point_count: int = Field(..., ge=2)
    overlap_flag: bool
    shoulder_flag: bool


class ChromatographicPeakPickingReport(JsonModel):
    """Stable peak-picking report over one extracted XIC trace set."""

    model_config = ConfigDict(extra="forbid")

    trace_report: XicTraceReport
    peaks: tuple[ChromatographicPeak, ...] = Field(default_factory=tuple)


def score_peak_shape(
    peak_trace: tuple[XicExtractionPoint | XicTracePoint, ...],
) -> PeakShapeScore:
    """Score one chromatographic peak trace for symmetry, tailing, and smoothness."""

    points = _normalize_trace_points(peak_trace)
    if not points:
        return PeakShapeScore(
            symmetry_score=0.0,
            tailing_score=0.0,
            smoothness_score=0.0,
            apex_prominence=0.0,
            shape_quality_tier=PeakShapeQualityTier.FLAT_BROAD,
        )
    apex_index = max(
        range(len(points)),
        key=lambda index: (points[index].intensity, -index),
    )
    baseline_values = _trace_baseline(points)
    corrected = [
        max(0.0, point.intensity - baseline)
        for point, baseline in zip(points, baseline_values, strict=True)
    ]
    corrected_apex = corrected[apex_index]
    if corrected_apex <= 0.0:
        return PeakShapeScore(
            symmetry_score=0.0,
            tailing_score=0.0,
            smoothness_score=0.0,
            apex_prominence=0.0,
            shape_quality_tier=PeakShapeQualityTier.FLAT_BROAD,
        )

    left_area = _trapezoid_area(points, corrected, 0, apex_index)
    right_area = _trapezoid_area(points, corrected, apex_index, len(points) - 1)
    total_area = max(left_area + right_area, 1e-9)
    symmetry_score = max(0.0, 1.0 - abs(left_area - right_area) / total_area)

    left_half_rt = _half_height_crossing(points, corrected, apex_index, left=True)
    right_half_rt = _half_height_crossing(points, corrected, apex_index, left=False)
    left_half_width = max(points[apex_index].time_seconds - left_half_rt, 0.0)
    right_half_width = max(right_half_rt - points[apex_index].time_seconds, 0.0)
    tailing_score = _bounded_ratio(
        min(left_half_width, right_half_width),
        max(left_half_width, right_half_width),
    )

    smoothness_score = _smoothness_score(corrected, apex_index)
    shoulder_max = max(
        max(corrected[:apex_index], default=0.0),
        max(corrected[apex_index + 1 :], default=0.0),
    )
    apex_prominence = max(
        0.0, min(1.0, (corrected_apex - shoulder_max) / corrected_apex)
    )
    tier = _classify_peak_shape_tier(
        symmetry_score=symmetry_score,
        tailing_score=tailing_score,
        smoothness_score=smoothness_score,
        apex_prominence=apex_prominence,
    )
    return PeakShapeScore(
        symmetry_score=round(symmetry_score, 4),
        tailing_score=round(tailing_score, 4),
        smoothness_score=round(smoothness_score, 4),
        apex_prominence=round(apex_prominence, 4),
        shape_quality_tier=tier,
    )


def pick_peak(
    xic_trace: tuple[XicExtractionPoint | XicTracePoint, ...],
    *,
    min_peak_height: float = 1.0,
    shoulder_boundary_fraction_threshold: float = 0.5,
) -> tuple[PickedChromatographicPeak, ...]:
    """Pick chromatographic peaks from one XIC trace."""

    normalized_points = _normalize_trace_points(xic_trace)
    fake_target = XicTargetEntry(
        target_id=_trace_target_id(xic_trace),
        precursor_mz=1.0,
    )
    legacy_peaks = _pick_target_peaks(
        fake_target,
        normalized_points,
        min_peak_height=min_peak_height,
        shoulder_boundary_fraction_threshold=shoulder_boundary_fraction_threshold,
    )
    return tuple(
        PickedChromatographicPeak(
            rt_start=peak.start_time_seconds,
            rt_apex=peak.apex_time_seconds,
            rt_end=peak.end_time_seconds,
            area=peak.area,
            height=peak.height,
            baseline=peak.baseline_at_apex,
            peak_width=peak.end_time_seconds - peak.start_time_seconds,
            overlap_flag=peak.overlap_flag,
            peak_quality=_classify_peak_quality(peak),
        )
        for peak in legacy_peaks
    )


def pick_chromatographic_peaks(
    trace_report: XicTraceReport,
    *,
    min_peak_height: float = 1.0,
    shoulder_boundary_fraction_threshold: float = 0.5,
) -> ChromatographicPeakPickingReport:
    """Detect chromatographic peaks from one extracted XIC trace report."""

    if min_peak_height <= 0.0:
        raise ValueError("min_peak_height must be greater than zero")
    if not 0.0 <= shoulder_boundary_fraction_threshold <= 1.0:
        raise ValueError(
            "shoulder_boundary_fraction_threshold must be between zero and one"
        )

    grouped_points: dict[str, list[XicTracePoint]] = {}
    for point in sorted(
        trace_report.trace_points,
        key=lambda item: (item.target_id, item.time_seconds, item.spectrum_id),
    ):
        grouped_points.setdefault(point.target_id, []).append(point)

    peaks: list[ChromatographicPeak] = []
    for target in trace_report.accepted_targets:
        target_points = grouped_points.get(target.target_id, [])
        peaks.extend(
            _pick_target_peaks(
                target,
                target_points,
                min_peak_height=min_peak_height,
                shoulder_boundary_fraction_threshold=(
                    shoulder_boundary_fraction_threshold
                ),
            )
        )

    return ChromatographicPeakPickingReport(
        trace_report=trace_report,
        peaks=tuple(
            sorted(peaks, key=lambda item: (item.target_id, item.apex_time_seconds))
        ),
    )


def render_chromatographic_peaks_tsv(
    report: ChromatographicPeakPickingReport,
) -> str:
    """Render one chromatographic peak report into deterministic TSV rows."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "peak_id",
            "target_id",
            "start_time_seconds",
            "end_time_seconds",
            "apex_time_seconds",
            "apex_intensity",
            "baseline_start_intensity",
            "baseline_end_intensity",
            "baseline_at_apex",
            "height",
            "area",
            "point_count",
            "overlap_flag",
            "shoulder_flag",
        )
    )
    for peak in report.peaks:
        writer.writerow(
            (
                peak.peak_id,
                peak.target_id,
                f"{peak.start_time_seconds:g}",
                f"{peak.end_time_seconds:g}",
                f"{peak.apex_time_seconds:g}",
                f"{peak.apex_intensity:g}",
                f"{peak.baseline_start_intensity:g}",
                f"{peak.baseline_end_intensity:g}",
                f"{peak.baseline_at_apex:g}",
                f"{peak.height:g}",
                f"{peak.area:g}",
                peak.point_count,
                str(peak.overlap_flag).lower(),
                str(peak.shoulder_flag).lower(),
            )
        )
    return buffer.getvalue()


def render_picked_chromatographic_peaks_tsv(
    peaks: tuple[PickedChromatographicPeak, ...],
) -> str:
    """Render raw picked chromatographic peaks with the engine column contract."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "rt_start",
            "rt_apex",
            "rt_end",
            "area",
            "height",
            "baseline",
            "peak_width",
            "overlap_flag",
            "peak_quality",
        )
    )
    for peak in peaks:
        writer.writerow(
            (
                f"{peak.rt_start:g}",
                f"{peak.rt_apex:g}",
                f"{peak.rt_end:g}",
                f"{peak.area:g}",
                f"{peak.height:g}",
                f"{peak.baseline:g}",
                f"{peak.peak_width:g}",
                str(peak.overlap_flag).lower(),
                peak.peak_quality.value,
            )
        )
    return buffer.getvalue()


def render_peak_shape_score_tsv(
    rows: tuple[PeakShapeScore, ...],
) -> str:
    """Render raw peak-shape score rows with the engine contract."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "symmetry_score",
            "tailing_score",
            "smoothness_score",
            "apex_prominence",
            "shape_quality_tier",
        )
    )
    for row in rows:
        writer.writerow(
            (
                f"{row.symmetry_score:.4f}",
                f"{row.tailing_score:.4f}",
                f"{row.smoothness_score:.4f}",
                f"{row.apex_prominence:.4f}",
                row.shape_quality_tier.value,
            )
        )
    return buffer.getvalue()


def _pick_target_peaks(
    target: XicTargetEntry,
    points: list[XicTracePoint],
    *,
    min_peak_height: float,
    shoulder_boundary_fraction_threshold: float,
) -> list[ChromatographicPeak]:
    if not points or all(point.intensity <= 0.0 for point in points):
        return []

    peaks: list[ChromatographicPeak] = []
    peak_counter = 0
    for segment_start, segment_end in _signal_segments(points):
        apex_indices = _local_apex_indices(points, segment_start, segment_end)
        if not apex_indices:
            continue
        valley_indices = [
            _lowest_intensity_index(points, left_apex, right_apex)
            for left_apex, right_apex in zip(
                apex_indices, apex_indices[1:], strict=False
            )
        ]
        segment_peaks: list[tuple[ChromatographicPeak, int, int, int]] = []
        for peak_index, apex_index in enumerate(apex_indices):
            left_index = (
                segment_start if peak_index == 0 else valley_indices[peak_index - 1]
            )
            right_index = (
                segment_end
                if peak_index == len(apex_indices) - 1
                else valley_indices[peak_index]
            )
            peak_counter += 1
            peak = _build_peak(
                target_id=target.target_id,
                peak_number=peak_counter,
                points=points,
                left_index=left_index,
                apex_index=apex_index,
                right_index=right_index,
                overlap_flag=len(apex_indices) > 1,
            )
            if peak.height >= min_peak_height and peak.area > 0.0:
                segment_peaks.append((peak, left_index, apex_index, right_index))

        peaks.extend(
            _flag_segment_shoulders(
                segment_peaks,
                points,
                shoulder_boundary_fraction_threshold=(
                    shoulder_boundary_fraction_threshold
                ),
            )
        )
    return peaks


def _normalize_trace_points(
    xic_trace: tuple[XicExtractionPoint | XicTracePoint, ...],
) -> list[XicTracePoint]:
    normalized: list[XicTracePoint] = []
    target_id = _trace_target_id(xic_trace)
    for point in xic_trace:
        if isinstance(point, XicExtractionPoint):
            normalized.append(
                XicTracePoint(
                    target_id=target_id,
                    spectrum_id=point.scan_id,
                    time_seconds=point.rt,
                    precursor_mz=(point.mz_lower + point.mz_upper) / 2.0,
                    mz_window_lower=point.mz_lower,
                    mz_window_upper=point.mz_upper,
                    intensity=point.intensity,
                    matched_peak_count=0,
                )
            )
        else:
            normalized.append(point)
    return sorted(
        normalized,
        key=lambda point: (point.time_seconds, point.spectrum_id),
    )


def _trace_baseline(points: list[XicTracePoint]) -> list[float]:
    if len(points) == 1:
        return [points[0].intensity]
    left_point = points[0]
    right_point = points[-1]
    return [
        _baseline_intensity_at_time(
            left_point,
            right_point,
            point.time_seconds,
        )
        for point in points
    ]


def _trapezoid_area(
    points: list[XicTracePoint],
    corrected: list[float],
    start_index: int,
    end_index: int,
) -> float:
    if end_index <= start_index:
        return 0.0
    area = 0.0
    for index in range(start_index, end_index):
        area += (
            (corrected[index] + corrected[index + 1])
            * (points[index + 1].time_seconds - points[index].time_seconds)
            / 2.0
        )
    return area


def _half_height_crossing(
    points: list[XicTracePoint],
    corrected: list[float],
    apex_index: int,
    *,
    left: bool,
) -> float:
    target_height = corrected[apex_index] / 2.0
    if left:
        for index in range(apex_index, 0, -1):
            if corrected[index - 1] <= target_height <= corrected[index]:
                return _interpolate_time(
                    points[index - 1].time_seconds,
                    corrected[index - 1],
                    points[index].time_seconds,
                    corrected[index],
                    target_height,
                )
        return points[0].time_seconds
    for index in range(apex_index, len(points) - 1):
        if corrected[index + 1] <= target_height <= corrected[index]:
            return _interpolate_time(
                points[index].time_seconds,
                corrected[index],
                points[index + 1].time_seconds,
                corrected[index + 1],
                target_height,
            )
    return points[-1].time_seconds


def _interpolate_time(
    left_time: float,
    left_value: float,
    right_time: float,
    right_value: float,
    target_value: float,
) -> float:
    if right_value == left_value:
        return right_time
    fraction = (target_value - left_value) / (right_value - left_value)
    return left_time + fraction * (right_time - left_time)


def _smoothness_score(
    corrected: list[float],
    apex_index: int,
) -> float:
    if len(corrected) <= 2:
        return 1.0
    violations = 0
    comparisons = 0
    for index in range(1, apex_index + 1):
        comparisons += 1
        if corrected[index] < corrected[index - 1]:
            violations += 1
    for index in range(apex_index + 1, len(corrected)):
        comparisons += 1
        if corrected[index] > corrected[index - 1]:
            violations += 1
    if comparisons == 0:
        return 1.0
    return max(0.0, 1.0 - (violations / comparisons))


def _classify_peak_shape_tier(
    *,
    symmetry_score: float,
    tailing_score: float,
    smoothness_score: float,
    apex_prominence: float,
) -> PeakShapeQualityTier:
    if smoothness_score < 0.7:
        return PeakShapeQualityTier.JAGGED_NOISY
    if apex_prominence < 0.2:
        return PeakShapeQualityTier.FLAT_BROAD
    if symmetry_score >= 0.85 and tailing_score >= 0.8 and smoothness_score >= 0.9:
        return PeakShapeQualityTier.GAUSSIAN_LIKE
    return PeakShapeQualityTier.ACCEPTABLE


def _bounded_ratio(
    numerator: float,
    denominator: float,
) -> float:
    if denominator <= 0.0:
        return 1.0
    return max(0.0, min(1.0, numerator / denominator))


def _trace_target_id(
    xic_trace: tuple[XicExtractionPoint | XicTracePoint, ...],
) -> str:
    if not xic_trace:
        return "xic_trace"
    first = xic_trace[0]
    return first.target_id


def _classify_peak_quality(
    peak: ChromatographicPeak,
) -> ChromatographicPeakQuality:
    if peak.height < 1.0:
        return ChromatographicPeakQuality.WEAK
    if peak.shoulder_flag:
        return ChromatographicPeakQuality.SHOULDER
    if peak.overlap_flag:
        return ChromatographicPeakQuality.OVERLAP
    return ChromatographicPeakQuality.CLEAN


def _signal_segments(points: list[XicTracePoint]) -> tuple[tuple[int, int], ...]:
    segments: list[tuple[int, int]] = []
    run_start: int | None = None
    for index, point in enumerate(points):
        if point.intensity > 0.0:
            if run_start is None:
                run_start = index
            continue
        if run_start is not None:
            segments.append(
                (
                    max(0, run_start - 1),
                    min(len(points) - 1, index),
                )
            )
            run_start = None
    if run_start is not None:
        segments.append((max(0, run_start - 1), len(points) - 1))
    return tuple(segments)


def _local_apex_indices(
    points: list[XicTracePoint],
    segment_start: int,
    segment_end: int,
) -> tuple[int, ...]:
    candidate_indices: list[int] = []
    for index in range(segment_start + 1, segment_end):
        left_intensity = points[index - 1].intensity
        current_intensity = points[index].intensity
        right_intensity = points[index + 1].intensity
        if current_intensity <= 0.0:
            continue
        if (
            current_intensity > left_intensity and current_intensity >= right_intensity
        ) or (
            current_intensity >= left_intensity and current_intensity > right_intensity
        ):
            candidate_indices.append(index)
    if candidate_indices:
        return tuple(candidate_indices)
    positive_indices = [
        index
        for index in range(segment_start, segment_end + 1)
        if points[index].intensity > 0.0
    ]
    if not positive_indices:
        return ()
    return (
        max(
            positive_indices,
            key=lambda index: (points[index].intensity, -index),
        ),
    )


def _lowest_intensity_index(
    points: list[XicTracePoint],
    left_index: int,
    right_index: int,
) -> int:
    return min(
        range(left_index + 1, right_index),
        key=lambda index: (points[index].intensity, points[index].time_seconds),
    )


def _build_peak(
    *,
    target_id: str,
    peak_number: int,
    points: list[XicTracePoint],
    left_index: int,
    apex_index: int,
    right_index: int,
    overlap_flag: bool,
) -> ChromatographicPeak:
    left_point = points[left_index]
    apex_point = points[apex_index]
    right_point = points[right_index]
    baseline_at_apex = _baseline_intensity_at_time(
        left_point,
        right_point,
        apex_point.time_seconds,
    )
    height = max(0.0, apex_point.intensity - baseline_at_apex)
    area = _baseline_corrected_area(points, left_index, right_index)
    return ChromatographicPeak(
        peak_id=f"{target_id}_peak_{peak_number:03d}",
        target_id=target_id,
        start_time_seconds=left_point.time_seconds,
        end_time_seconds=right_point.time_seconds,
        apex_time_seconds=apex_point.time_seconds,
        apex_intensity=apex_point.intensity,
        baseline_start_intensity=left_point.intensity,
        baseline_end_intensity=right_point.intensity,
        baseline_at_apex=baseline_at_apex,
        height=height,
        area=area,
        point_count=right_index - left_index + 1,
        overlap_flag=overlap_flag,
        shoulder_flag=False,
    )


def _flag_segment_shoulders(
    segment_peaks: list[tuple[ChromatographicPeak, int, int, int]],
    points: list[XicTracePoint],
    *,
    shoulder_boundary_fraction_threshold: float,
) -> list[ChromatographicPeak]:
    if not segment_peaks:
        return []
    flagged: list[ChromatographicPeak] = []
    for index, (peak, left_index, _apex_index, right_index) in enumerate(segment_peaks):
        shoulder_flag = False
        if peak.overlap_flag and index < len(segment_peaks) - 1:
            next_peak = segment_peaks[index + 1][0]
            if (
                peak.apex_intensity < next_peak.apex_intensity
                and points[right_index].intensity
                >= peak.apex_intensity * shoulder_boundary_fraction_threshold
            ):
                shoulder_flag = True
        if peak.overlap_flag and index > 0:
            previous_peak = segment_peaks[index - 1][0]
            if (
                peak.apex_intensity < previous_peak.apex_intensity
                and points[left_index].intensity
                >= peak.apex_intensity * shoulder_boundary_fraction_threshold
            ):
                shoulder_flag = True
        flagged.append(peak.model_copy(update={"shoulder_flag": shoulder_flag}))
    return flagged


def _baseline_intensity_at_time(
    left_point: XicTracePoint,
    right_point: XicTracePoint,
    time_seconds: float,
) -> float:
    if right_point.time_seconds == left_point.time_seconds:
        return max(left_point.intensity, right_point.intensity)
    fraction = (time_seconds - left_point.time_seconds) / (
        right_point.time_seconds - left_point.time_seconds
    )
    return left_point.intensity + (
        (right_point.intensity - left_point.intensity) * fraction
    )


def _baseline_corrected_area(
    points: list[XicTracePoint],
    left_index: int,
    right_index: int,
) -> float:
    left_point = points[left_index]
    right_point = points[right_index]
    area = 0.0
    for index in range(left_index, right_index):
        first = points[index]
        second = points[index + 1]
        first_corrected = max(
            0.0,
            first.intensity
            - _baseline_intensity_at_time(
                left_point,
                right_point,
                first.time_seconds,
            ),
        )
        second_corrected = max(
            0.0,
            second.intensity
            - _baseline_intensity_at_time(
                left_point,
                right_point,
                second.time_seconds,
            ),
        )
        area += (
            (first_corrected + second_corrected)
            * (second.time_seconds - first.time_seconds)
            / 2.0
        )
    return area

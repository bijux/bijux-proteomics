# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Align chromatographic retention times across runs using common anchors."""

from __future__ import annotations

import csv
from collections import Counter
from enum import StrEnum
from io import StringIO
from pathlib import Path
from statistics import median

from pydantic import ConfigDict, Field

from bijux_proteomics.io.chromatographic_peak_picking import (
    ChromatographicPeak,
    ChromatographicPeakPickingReport,
    extract_mzml_chromatographic_peaks,
)
from bijux_proteomics.io.xic_extraction import (
    XicTargetEntry,
    XicTargetParseReport,
    parse_xic_target_table,
)
from bijux_proteomics_foundation import JsonModel


class RetentionTimeAlignmentModelStatus(StrEnum):
    """Supported retention-time alignment model outcomes."""

    REFERENCE = "reference"
    ALIGNED = "aligned"
    FAILED = "failed"


class RetentionTimeAlignmentRunModel(JsonModel):
    """One per-run retention-time shift model."""

    model_config = ConfigDict(extra="forbid")

    run_id: str = Field(..., min_length=1)
    source_path: str = Field(..., min_length=1)
    reference_run_id: str = Field(..., min_length=1)
    status: RetentionTimeAlignmentModelStatus
    anchor_count: int = Field(..., ge=0)
    shift_seconds: float | None = None
    median_absolute_residual_seconds: float | None = Field(default=None, ge=0.0)
    max_absolute_residual_seconds: float | None = Field(default=None, ge=0.0)
    failure_reason: str | None = None


class RetentionTimeAlignmentResidual(JsonModel):
    """One anchor residual after applying one run-alignment shift model."""

    model_config = ConfigDict(extra="forbid")

    run_id: str = Field(..., min_length=1)
    source_path: str = Field(..., min_length=1)
    target_id: str = Field(..., min_length=1)
    reference_peak_id: str = Field(..., min_length=1)
    run_peak_id: str = Field(..., min_length=1)
    reference_apex_time_seconds: float = Field(..., ge=0.0)
    observed_apex_time_seconds: float = Field(..., ge=0.0)
    aligned_apex_time_seconds: float = Field(..., ge=0.0)
    shift_seconds: float
    residual_seconds: float
    absolute_residual_seconds: float = Field(..., ge=0.0)
    outside_aligned_tolerance: bool


class RetentionTimeAlignmentFailedAnchor(JsonModel):
    """One anchor excluded from one run-alignment model with explicit reason."""

    model_config = ConfigDict(extra="forbid")

    run_id: str = Field(..., min_length=1)
    source_path: str = Field(..., min_length=1)
    target_id: str = Field(..., min_length=1)
    reason: str = Field(..., min_length=1)
    reference_peak_count: int = Field(..., ge=0)
    run_peak_count: int = Field(..., ge=0)


class RetentionTimeAlignmentReport(JsonModel):
    """Stable retention-time alignment report over multiple chromatographic runs."""

    model_config = ConfigDict(extra="forbid")

    reference_run_id: str = Field(..., min_length=1)
    aligned_rt_tolerance_seconds: float = Field(..., gt=0.0)
    min_anchor_count: int = Field(..., ge=1)
    peak_reports: tuple[ChromatographicPeakPickingReport, ...] = Field(default_factory=tuple)
    run_models: tuple[RetentionTimeAlignmentRunModel, ...] = Field(default_factory=tuple)
    residuals: tuple[RetentionTimeAlignmentResidual, ...] = Field(default_factory=tuple)
    failed_anchors: tuple[RetentionTimeAlignmentFailedAnchor, ...] = Field(
        default_factory=tuple
    )
    flagged_residuals: tuple[RetentionTimeAlignmentResidual, ...] = Field(
        default_factory=tuple
    )


def align_chromatographic_peak_retention_times(
    peak_reports: tuple[ChromatographicPeakPickingReport, ...],
    *,
    reference_run_id: str | None = None,
    aligned_rt_tolerance_seconds: float = 5.0,
    min_anchor_count: int = 2,
) -> RetentionTimeAlignmentReport:
    """Align chromatographic peak apex times across runs using common anchors."""

    if len(peak_reports) < 2:
        raise ValueError("retention-time alignment requires at least two run reports")
    if aligned_rt_tolerance_seconds <= 0.0:
        raise ValueError("aligned_rt_tolerance_seconds must be greater than zero")
    if min_anchor_count <= 0:
        raise ValueError("min_anchor_count must be greater than zero")

    run_entries = _build_run_entries(peak_reports)
    reference_entry = _select_reference_run(run_entries, reference_run_id)
    valid_reference_peaks = _valid_anchor_peaks(reference_entry.report)
    reference_targets = sorted(
        {
            target.target_id
            for target in reference_entry.report.trace_report.accepted_targets
        }
        | set(valid_reference_peaks)
    )

    run_models = [
        RetentionTimeAlignmentRunModel(
            run_id=reference_entry.run_id,
            source_path=reference_entry.source_path,
            reference_run_id=reference_entry.run_id,
            status=RetentionTimeAlignmentModelStatus.REFERENCE,
            anchor_count=len(valid_reference_peaks),
            shift_seconds=0.0,
            median_absolute_residual_seconds=0.0,
            max_absolute_residual_seconds=0.0,
            failure_reason=None,
        )
    ]
    residuals: list[RetentionTimeAlignmentResidual] = []
    failed_anchors: list[RetentionTimeAlignmentFailedAnchor] = []

    for run_entry in run_entries:
        if run_entry.run_id == reference_entry.run_id:
            continue
        run_peak_index = _peaks_by_target(run_entry.report)
        candidate_pairs: list[tuple[str, ChromatographicPeak, ChromatographicPeak]] = []
        for target_id in reference_targets:
            reference_peak = valid_reference_peaks.get(target_id)
            run_peaks = run_peak_index.get(target_id, ())
            if reference_peak is None:
                failed_anchors.append(
                    RetentionTimeAlignmentFailedAnchor(
                        run_id=run_entry.run_id,
                        source_path=run_entry.source_path,
                        target_id=target_id,
                        reason="reference_peak_unresolved",
                        reference_peak_count=len(
                            _peaks_by_target(reference_entry.report).get(target_id, ())
                        ),
                        run_peak_count=len(run_peaks),
                    )
                )
                continue
            if len(run_peaks) == 0:
                failed_anchors.append(
                    RetentionTimeAlignmentFailedAnchor(
                        run_id=run_entry.run_id,
                        source_path=run_entry.source_path,
                        target_id=target_id,
                        reason="missing_run_peak",
                        reference_peak_count=1,
                        run_peak_count=0,
                    )
                )
                continue
            if len(run_peaks) > 1:
                failed_anchors.append(
                    RetentionTimeAlignmentFailedAnchor(
                        run_id=run_entry.run_id,
                        source_path=run_entry.source_path,
                        target_id=target_id,
                        reason="multiple_run_peaks_detected",
                        reference_peak_count=1,
                        run_peak_count=len(run_peaks),
                    )
                )
                continue
            candidate_pairs.append((target_id, reference_peak, run_peaks[0]))

        if len(candidate_pairs) < min_anchor_count:
            run_models.append(
                RetentionTimeAlignmentRunModel(
                    run_id=run_entry.run_id,
                    source_path=run_entry.source_path,
                    reference_run_id=reference_entry.run_id,
                    status=RetentionTimeAlignmentModelStatus.FAILED,
                    anchor_count=len(candidate_pairs),
                    shift_seconds=None,
                    median_absolute_residual_seconds=None,
                    max_absolute_residual_seconds=None,
                    failure_reason="insufficient_anchor_count",
                )
            )
            continue

        shift_seconds = median(
            run_peak.apex_time_seconds - reference_peak.apex_time_seconds
            for _, reference_peak, run_peak in candidate_pairs
        )
        run_residuals = tuple(
            _build_residual(
                run_id=run_entry.run_id,
                source_path=run_entry.source_path,
                target_id=target_id,
                reference_peak=reference_peak,
                run_peak=run_peak,
                shift_seconds=shift_seconds,
                aligned_rt_tolerance_seconds=aligned_rt_tolerance_seconds,
            )
            for target_id, reference_peak, run_peak in sorted(
                candidate_pairs, key=lambda item: item[0]
            )
        )
        absolute_residuals = tuple(
            item.absolute_residual_seconds for item in run_residuals
        )
        residuals.extend(run_residuals)
        run_models.append(
            RetentionTimeAlignmentRunModel(
                run_id=run_entry.run_id,
                source_path=run_entry.source_path,
                reference_run_id=reference_entry.run_id,
                status=RetentionTimeAlignmentModelStatus.ALIGNED,
                anchor_count=len(candidate_pairs),
                shift_seconds=shift_seconds,
                median_absolute_residual_seconds=median(absolute_residuals),
                max_absolute_residual_seconds=max(absolute_residuals),
                failure_reason=None,
            )
        )

    flagged_residuals = tuple(
        residual
        for residual in sorted(
            residuals,
            key=lambda item: (
                item.run_id,
                item.outside_aligned_tolerance is False,
                item.target_id,
            ),
        )
        if residual.outside_aligned_tolerance
    )
    return RetentionTimeAlignmentReport(
        reference_run_id=reference_entry.run_id,
        aligned_rt_tolerance_seconds=aligned_rt_tolerance_seconds,
        min_anchor_count=min_anchor_count,
        peak_reports=peak_reports,
        run_models=tuple(
            sorted(run_models, key=lambda item: (item.run_id != reference_entry.run_id, item.run_id))
        ),
        residuals=tuple(
            sorted(residuals, key=lambda item: (item.run_id, item.target_id))
        ),
        failed_anchors=tuple(
            sorted(failed_anchors, key=lambda item: (item.run_id, item.target_id))
        ),
        flagged_residuals=flagged_residuals,
    )


def extract_mzml_retention_time_alignment(
    mzml_paths: tuple[Path, ...],
    targets: Path | XicTargetParseReport | tuple[XicTargetEntry, ...],
    *,
    tolerance_da: float | None = None,
    tolerance_ppm: float | None = None,
    reference_run_id: str | None = None,
    aligned_rt_tolerance_seconds: float = 5.0,
    min_anchor_count: int = 2,
) -> RetentionTimeAlignmentReport:
    """Extract chromatographic peaks from multiple mzML runs and align them."""

    if len(mzml_paths) < 2:
        raise ValueError("retention-time alignment requires at least two mzML files")
    target_source = targets
    if isinstance(targets, Path):
        target_source = parse_xic_target_table(targets)
    peak_reports = tuple(
        extract_mzml_chromatographic_peaks(
            mzml_path,
            target_source,
            tolerance_da=tolerance_da,
            tolerance_ppm=tolerance_ppm,
        )
        for mzml_path in mzml_paths
    )
    return align_chromatographic_peak_retention_times(
        peak_reports,
        reference_run_id=reference_run_id,
        aligned_rt_tolerance_seconds=aligned_rt_tolerance_seconds,
        min_anchor_count=min_anchor_count,
    )


def render_retention_time_alignment_models_tsv(
    report: RetentionTimeAlignmentReport,
) -> str:
    """Render per-run retention-time shift models into deterministic TSV rows."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "run_id",
            "source_path",
            "reference_run_id",
            "status",
            "anchor_count",
            "shift_seconds",
            "median_absolute_residual_seconds",
            "max_absolute_residual_seconds",
            "failure_reason",
        )
    )
    for model in report.run_models:
        writer.writerow(
            (
                model.run_id,
                model.source_path,
                model.reference_run_id,
                model.status.value,
                model.anchor_count,
                "" if model.shift_seconds is None else f"{model.shift_seconds:g}",
                ""
                if model.median_absolute_residual_seconds is None
                else f"{model.median_absolute_residual_seconds:g}",
                ""
                if model.max_absolute_residual_seconds is None
                else f"{model.max_absolute_residual_seconds:g}",
                "" if model.failure_reason is None else model.failure_reason,
            )
        )
    return buffer.getvalue()


def render_retention_time_alignment_residuals_tsv(
    report: RetentionTimeAlignmentReport,
) -> str:
    """Render aligned anchor residuals into deterministic TSV rows."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "run_id",
            "source_path",
            "target_id",
            "reference_peak_id",
            "run_peak_id",
            "reference_apex_time_seconds",
            "observed_apex_time_seconds",
            "aligned_apex_time_seconds",
            "shift_seconds",
            "residual_seconds",
            "absolute_residual_seconds",
            "outside_aligned_tolerance",
        )
    )
    for residual in report.residuals:
        writer.writerow(
            (
                residual.run_id,
                residual.source_path,
                residual.target_id,
                residual.reference_peak_id,
                residual.run_peak_id,
                f"{residual.reference_apex_time_seconds:g}",
                f"{residual.observed_apex_time_seconds:g}",
                f"{residual.aligned_apex_time_seconds:g}",
                f"{residual.shift_seconds:g}",
                f"{residual.residual_seconds:g}",
                f"{residual.absolute_residual_seconds:g}",
                str(residual.outside_aligned_tolerance).lower(),
            )
        )
    return buffer.getvalue()


def render_retention_time_alignment_failed_anchors_tsv(
    report: RetentionTimeAlignmentReport,
) -> str:
    """Render failed anchor rows into deterministic TSV output."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "run_id",
            "source_path",
            "target_id",
            "reason",
            "reference_peak_count",
            "run_peak_count",
        )
    )
    for failed_anchor in report.failed_anchors:
        writer.writerow(
            (
                failed_anchor.run_id,
                failed_anchor.source_path,
                failed_anchor.target_id,
                failed_anchor.reason,
                failed_anchor.reference_peak_count,
                failed_anchor.run_peak_count,
            )
        )
    return buffer.getvalue()


class _RunEntry(JsonModel):
    model_config = ConfigDict(extra="forbid")

    run_id: str = Field(..., min_length=1)
    source_path: str = Field(..., min_length=1)
    report: ChromatographicPeakPickingReport


def _build_run_entries(
    peak_reports: tuple[ChromatographicPeakPickingReport, ...],
) -> tuple[_RunEntry, ...]:
    stem_counts = Counter(
        Path(report.trace_report.source_path).stem for report in peak_reports
    )
    return tuple(
        _RunEntry(
            run_id=(
                Path(report.trace_report.source_path).stem
                if stem_counts[Path(report.trace_report.source_path).stem] == 1
                else report.trace_report.source_path
            ),
            source_path=report.trace_report.source_path,
            report=report,
        )
        for report in peak_reports
    )


def _select_reference_run(
    run_entries: tuple[_RunEntry, ...],
    reference_run_id: str | None,
) -> _RunEntry:
    if reference_run_id is None:
        return run_entries[0]
    try:
        return next(
            entry for entry in run_entries if entry.run_id == reference_run_id
        )
    except StopIteration as exc:
        raise ValueError(f"unknown reference_run_id {reference_run_id!r}") from exc


def _valid_anchor_peaks(
    report: ChromatographicPeakPickingReport,
) -> dict[str, ChromatographicPeak]:
    return {
        target_id: peaks[0]
        for target_id, peaks in _peaks_by_target(report).items()
        if len(peaks) == 1
    }


def _peaks_by_target(
    report: ChromatographicPeakPickingReport,
) -> dict[str, tuple[ChromatographicPeak, ...]]:
    grouped: dict[str, list[ChromatographicPeak]] = {}
    for peak in report.peaks:
        grouped.setdefault(peak.target_id, []).append(peak)
    return {
        target_id: tuple(sorted(peaks, key=lambda item: item.apex_time_seconds))
        for target_id, peaks in grouped.items()
    }


def _build_residual(
    *,
    run_id: str,
    source_path: str,
    target_id: str,
    reference_peak: ChromatographicPeak,
    run_peak: ChromatographicPeak,
    shift_seconds: float,
    aligned_rt_tolerance_seconds: float,
) -> RetentionTimeAlignmentResidual:
    aligned_apex_time_seconds = run_peak.apex_time_seconds - shift_seconds
    residual_seconds = (
        aligned_apex_time_seconds - reference_peak.apex_time_seconds
    )
    absolute_residual_seconds = abs(residual_seconds)
    return RetentionTimeAlignmentResidual(
        run_id=run_id,
        source_path=source_path,
        target_id=target_id,
        reference_peak_id=reference_peak.peak_id,
        run_peak_id=run_peak.peak_id,
        reference_apex_time_seconds=reference_peak.apex_time_seconds,
        observed_apex_time_seconds=run_peak.apex_time_seconds,
        aligned_apex_time_seconds=aligned_apex_time_seconds,
        shift_seconds=shift_seconds,
        residual_seconds=residual_seconds,
        absolute_residual_seconds=absolute_residual_seconds,
        outside_aligned_tolerance=(
            absolute_residual_seconds > aligned_rt_tolerance_seconds
        ),
    )

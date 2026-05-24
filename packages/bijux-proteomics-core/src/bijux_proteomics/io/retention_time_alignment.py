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


class RetentionTimeAlignmentAnchor(JsonModel):
    """One anchor-peptide row for raw RT-alignment fitting."""

    model_config = ConfigDict(extra="forbid")

    run_id: str = Field(..., min_length=1)
    peptide_id: str = Field(..., min_length=1)
    observed_rt: float = Field(..., ge=0.0)
    reference_rt: float = Field(..., ge=0.0)
    anchor_confidence: float = Field(..., ge=0.0)


class RetentionTimeAlignmentFitModel(JsonModel):
    """One fitted run-level RT alignment model from an anchor table."""

    model_config = ConfigDict(extra="forbid")

    run_id: str = Field(..., min_length=1)
    alignment_model: str = Field(..., min_length=1)
    rt_shift: float | None = None
    rt_residual_median: float | None = Field(default=None, ge=0.0)
    failed_anchor_count: int = Field(..., ge=0)
    anchor_count: int = Field(..., ge=0)
    unaligned_rt_residual_median: float | None = Field(default=None, ge=0.0)
    failure_reason: str | None = None


class RetentionTimeAlignmentFitResidual(JsonModel):
    """One anchor residual before and after applying a fitted RT shift."""

    model_config = ConfigDict(extra="forbid")

    run_id: str = Field(..., min_length=1)
    peptide_id: str = Field(..., min_length=1)
    observed_rt: float = Field(..., ge=0.0)
    reference_rt: float = Field(..., ge=0.0)
    anchor_confidence: float = Field(..., ge=0.0)
    aligned_rt: float = Field(..., ge=0.0)
    unaligned_rt_residual: float
    rt_residual: float
    absolute_unaligned_rt_residual: float = Field(..., ge=0.0)
    absolute_rt_residual: float = Field(..., ge=0.0)
    excluded_from_fit: bool = False
    exclusion_reason: str | None = None


class RetentionTimeAlignmentFitReport(JsonModel):
    """Stable raw RT-alignment fit report over one anchor table."""

    model_config = ConfigDict(extra="forbid")

    min_anchor_count: int = Field(..., ge=1)
    models: tuple[RetentionTimeAlignmentFitModel, ...] = Field(default_factory=tuple)
    residuals: tuple[RetentionTimeAlignmentFitResidual, ...] = Field(default_factory=tuple)


class RetentionTimeIdentificationRow(JsonModel):
    """One imported identification row eligible for RT residual downgrade."""

    model_config = ConfigDict(extra="forbid")

    entity_id: str = Field(..., min_length=1)
    run_id: str = Field(..., min_length=1)
    observed_rt: float = Field(..., ge=0.0)
    expected_rt: float = Field(..., ge=0.0)
    imported_confidence: float = Field(..., ge=0.0, le=1.0)


class RetentionTimeConfidencePenalty(JsonModel):
    """One RT residual downgrade result for an imported identification row."""

    model_config = ConfigDict(extra="forbid")

    entity_id: str = Field(..., min_length=1)
    observed_rt: float = Field(..., ge=0.0)
    expected_rt: float = Field(..., ge=0.0)
    rt_residual: float
    rt_outlier: bool
    rt_confidence_penalty: float = Field(..., ge=0.0, le=1.0)


class RetentionTimeAlignmentRunModel(JsonModel):
    """One per-run retention-time shift model."""

    model_config = ConfigDict(extra="forbid")

    run_id: str = Field(..., min_length=1)
    source_path: str = Field(..., min_length=1)
    reference_run_id: str = Field(..., min_length=1)
    status: RetentionTimeAlignmentModelStatus
    anchor_count: int = Field(..., ge=0)
    alignment_model: str = Field(..., min_length=1)
    rt_shift: float | None = None
    rt_residual_median: float | None = Field(default=None, ge=0.0)
    failed_anchor_count: int = Field(default=0, ge=0)
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


def apply_rt_residuals(
    psm_or_precursor_table: tuple[RetentionTimeIdentificationRow, ...],
    alignment_model: (
        RetentionTimeAlignmentFitReport
        | tuple[RetentionTimeAlignmentFitModel, ...]
        | RetentionTimeAlignmentFitModel
    ),
    *,
    aligned_rt_tolerance_seconds: float = 5.0,
    high_confidence_threshold: float = 0.9,
) -> tuple[RetentionTimeConfidencePenalty, ...]:
    """Downgrade imported IDs when aligned RT residuals contradict high confidence."""

    if aligned_rt_tolerance_seconds <= 0.0:
        raise ValueError("aligned_rt_tolerance_seconds must be greater than zero")
    if not 0.0 <= high_confidence_threshold <= 1.0:
        raise ValueError("high_confidence_threshold must be between zero and one")

    model_by_run = _fit_models_by_run(alignment_model)
    rows: list[RetentionTimeConfidencePenalty] = []
    for entry in psm_or_precursor_table:
        fit_model = model_by_run.get(entry.run_id)
        if fit_model is None or fit_model.rt_shift is None:
            rows.append(
                RetentionTimeConfidencePenalty(
                    entity_id=entry.entity_id,
                    observed_rt=entry.observed_rt,
                    expected_rt=entry.expected_rt,
                    rt_residual=entry.observed_rt - entry.expected_rt,
                    rt_outlier=False,
                    rt_confidence_penalty=1.0,
                )
            )
            continue

        expected_rt = entry.expected_rt + fit_model.rt_shift
        rt_residual = entry.observed_rt - expected_rt
        rt_outlier = abs(rt_residual) > aligned_rt_tolerance_seconds
        rows.append(
            RetentionTimeConfidencePenalty(
                entity_id=entry.entity_id,
                observed_rt=entry.observed_rt,
                expected_rt=expected_rt,
                rt_residual=rt_residual,
                rt_outlier=rt_outlier,
                rt_confidence_penalty=_rt_confidence_penalty(
                    imported_confidence=entry.imported_confidence,
                    absolute_rt_residual=abs(rt_residual),
                    aligned_rt_tolerance_seconds=aligned_rt_tolerance_seconds,
                    high_confidence_threshold=high_confidence_threshold,
                ),
            )
        )
    return tuple(
        sorted(
            rows,
            key=lambda item: (
                item.entity_id,
                item.rt_outlier is False,
                item.expected_rt,
            ),
        )
    )


def fit_rt_alignment(
    anchor_table: tuple[RetentionTimeAlignmentAnchor, ...],
    *,
    min_anchor_count: int = 2,
) -> RetentionTimeAlignmentFitReport:
    """Fit one RT-shift model per run from an anchor-peptide table."""

    if not anchor_table:
        raise ValueError("rt alignment fit requires at least one anchor row")
    if min_anchor_count <= 0:
        raise ValueError("min_anchor_count must be greater than zero")

    grouped: dict[str, list[RetentionTimeAlignmentAnchor]] = {}
    for anchor in anchor_table:
        grouped.setdefault(anchor.run_id, []).append(anchor)

    models: list[RetentionTimeAlignmentFitModel] = []
    residuals: list[RetentionTimeAlignmentFitResidual] = []
    for run_id in sorted(grouped):
        run_anchors = sorted(grouped[run_id], key=lambda item: item.peptide_id)
        usable_anchors = [
            anchor for anchor in run_anchors if anchor.anchor_confidence > 0.0
        ]
        excluded_anchors = [
            anchor for anchor in run_anchors if anchor.anchor_confidence <= 0.0
        ]
        for anchor in excluded_anchors:
            residuals.append(
                RetentionTimeAlignmentFitResidual(
                    run_id=anchor.run_id,
                    peptide_id=anchor.peptide_id,
                    observed_rt=anchor.observed_rt,
                    reference_rt=anchor.reference_rt,
                    anchor_confidence=anchor.anchor_confidence,
                    aligned_rt=anchor.observed_rt,
                    unaligned_rt_residual=anchor.observed_rt - anchor.reference_rt,
                    rt_residual=anchor.observed_rt - anchor.reference_rt,
                    absolute_unaligned_rt_residual=abs(
                        anchor.observed_rt - anchor.reference_rt
                    ),
                    absolute_rt_residual=abs(anchor.observed_rt - anchor.reference_rt),
                    excluded_from_fit=True,
                    exclusion_reason="nonpositive_anchor_confidence",
                )
            )

        if len(usable_anchors) < min_anchor_count:
            for anchor in usable_anchors:
                residuals.append(
                    RetentionTimeAlignmentFitResidual(
                        run_id=anchor.run_id,
                        peptide_id=anchor.peptide_id,
                        observed_rt=anchor.observed_rt,
                        reference_rt=anchor.reference_rt,
                        anchor_confidence=anchor.anchor_confidence,
                        aligned_rt=anchor.observed_rt,
                        unaligned_rt_residual=anchor.observed_rt - anchor.reference_rt,
                        rt_residual=anchor.observed_rt - anchor.reference_rt,
                        absolute_unaligned_rt_residual=abs(
                            anchor.observed_rt - anchor.reference_rt
                        ),
                        absolute_rt_residual=abs(
                            anchor.observed_rt - anchor.reference_rt
                        ),
                        excluded_from_fit=True,
                        exclusion_reason="insufficient_anchor_count",
                    )
                )
            models.append(
                RetentionTimeAlignmentFitModel(
                    run_id=run_id,
                    alignment_model="insufficient_anchor_count",
                    rt_shift=None,
                    rt_residual_median=None,
                    failed_anchor_count=len(run_anchors),
                    anchor_count=len(usable_anchors),
                    unaligned_rt_residual_median=(
                        None
                        if not usable_anchors
                        else median(
                            abs(anchor.observed_rt - anchor.reference_rt)
                            for anchor in usable_anchors
                        )
                    ),
                    failure_reason="insufficient_anchor_count",
                )
            )
            continue

        shift = _weighted_median(
            tuple(
                anchor.observed_rt - anchor.reference_rt
                for anchor in usable_anchors
            ),
            tuple(anchor.anchor_confidence for anchor in usable_anchors),
        )
        absolute_residuals: list[float] = []
        absolute_unaligned_residuals: list[float] = []
        for anchor in usable_anchors:
            unaligned_residual = anchor.observed_rt - anchor.reference_rt
            aligned_rt = anchor.observed_rt - shift
            rt_residual = aligned_rt - anchor.reference_rt
            absolute_residuals.append(abs(rt_residual))
            absolute_unaligned_residuals.append(abs(unaligned_residual))
            residuals.append(
                RetentionTimeAlignmentFitResidual(
                    run_id=anchor.run_id,
                    peptide_id=anchor.peptide_id,
                    observed_rt=anchor.observed_rt,
                    reference_rt=anchor.reference_rt,
                    anchor_confidence=anchor.anchor_confidence,
                    aligned_rt=aligned_rt,
                    unaligned_rt_residual=unaligned_residual,
                    rt_residual=rt_residual,
                    absolute_unaligned_rt_residual=abs(unaligned_residual),
                    absolute_rt_residual=abs(rt_residual),
                    excluded_from_fit=False,
                    exclusion_reason=None,
                )
            )
        models.append(
            RetentionTimeAlignmentFitModel(
                run_id=run_id,
                alignment_model="confidence_weighted_shift",
                rt_shift=shift,
                rt_residual_median=median(absolute_residuals),
                failed_anchor_count=len(excluded_anchors),
                anchor_count=len(usable_anchors),
                unaligned_rt_residual_median=median(absolute_unaligned_residuals),
                failure_reason=None,
            )
        )

    return RetentionTimeAlignmentFitReport(
        min_anchor_count=min_anchor_count,
        models=tuple(models),
        residuals=tuple(
            sorted(
                residuals,
                key=lambda item: (
                    item.run_id,
                    item.excluded_from_fit,
                    item.peptide_id,
                ),
            )
        ),
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
            alignment_model="reference_identity",
            rt_shift=0.0,
            rt_residual_median=0.0,
            failed_anchor_count=0,
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
        run_failed_anchor_count = 0
        run_peak_index = _peaks_by_target(run_entry.report)
        candidate_pairs: list[tuple[str, ChromatographicPeak, ChromatographicPeak]] = []
        anchor_rows: list[RetentionTimeAlignmentAnchor] = []
        for target_id in reference_targets:
            reference_peak = valid_reference_peaks.get(target_id)
            run_peaks = run_peak_index.get(target_id, ())
            if reference_peak is None:
                run_failed_anchor_count += 1
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
                run_failed_anchor_count += 1
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
                run_failed_anchor_count += 1
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
            run_peak = run_peaks[0]
            candidate_pairs.append((target_id, reference_peak, run_peak))
            anchor_rows.append(
                RetentionTimeAlignmentAnchor(
                    run_id=run_entry.run_id,
                    peptide_id=target_id,
                    observed_rt=run_peak.apex_time_seconds,
                    reference_rt=reference_peak.apex_time_seconds,
                    anchor_confidence=_anchor_confidence(reference_peak, run_peak),
                )
            )

        fit_report = (
            None
            if not anchor_rows
            else fit_rt_alignment(tuple(anchor_rows), min_anchor_count=min_anchor_count)
        )
        fit_model = None if fit_report is None else fit_report.models[0]
        if fit_model is None or fit_model.rt_shift is None:
            run_models.append(
                RetentionTimeAlignmentRunModel(
                    run_id=run_entry.run_id,
                    source_path=run_entry.source_path,
                    reference_run_id=reference_entry.run_id,
                    status=RetentionTimeAlignmentModelStatus.FAILED,
                    anchor_count=len(candidate_pairs),
                    alignment_model=(
                        "insufficient_anchor_count"
                        if fit_model is None
                        else fit_model.alignment_model
                    ),
                    rt_shift=None,
                    rt_residual_median=None,
                    failed_anchor_count=(
                        run_failed_anchor_count
                        if fit_model is None
                        else run_failed_anchor_count + fit_model.failed_anchor_count
                    ),
                    shift_seconds=None,
                    median_absolute_residual_seconds=None,
                    max_absolute_residual_seconds=None,
                    failure_reason=(
                        "insufficient_anchor_count"
                        if fit_model is None
                        else fit_model.failure_reason
                    ),
                )
            )
            continue

        shift_seconds = fit_model.rt_shift
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
                alignment_model=fit_model.alignment_model,
                rt_shift=fit_model.rt_shift,
                rt_residual_median=fit_model.rt_residual_median,
                failed_anchor_count=run_failed_anchor_count + fit_model.failed_anchor_count,
                shift_seconds=shift_seconds,
                median_absolute_residual_seconds=(
                    fit_model.rt_residual_median
                    if fit_model.rt_residual_median is not None
                    else median(absolute_residuals)
                ),
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
            "alignment_model",
            "rt_shift",
            "rt_residual_median",
            "failed_anchor_count",
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
                model.alignment_model,
                "" if model.rt_shift is None else f"{model.rt_shift:g}",
                ""
                if model.rt_residual_median is None
                else f"{model.rt_residual_median:g}",
                model.failed_anchor_count,
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


def render_rt_alignment_fit_models_tsv(
    report: RetentionTimeAlignmentFitReport,
) -> str:
    """Render raw anchor-table RT fit models into deterministic TSV rows."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "run_id",
            "alignment_model",
            "rt_shift",
            "rt_residual_median",
            "failed_anchor_count",
        )
    )
    for model in report.models:
        writer.writerow(
            (
                model.run_id,
                model.alignment_model,
                "" if model.rt_shift is None else f"{model.rt_shift:g}",
                ""
                if model.rt_residual_median is None
                else f"{model.rt_residual_median:g}",
                model.failed_anchor_count,
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


def _anchor_confidence(
    reference_peak: ChromatographicPeak,
    run_peak: ChromatographicPeak,
) -> float:
    return min(
        _peak_anchor_confidence(reference_peak),
        _peak_anchor_confidence(run_peak),
    )


def _peak_anchor_confidence(peak: ChromatographicPeak) -> float:
    confidence = 1.0
    if peak.overlap_flag:
        confidence *= 0.6
    if peak.shoulder_flag:
        confidence *= 0.75
    return confidence


def _weighted_median(
    values: tuple[float, ...],
    weights: tuple[float, ...],
) -> float:
    if not values or not weights or len(values) != len(weights):
        raise ValueError("weighted median requires matched non-empty values and weights")
    ordered = sorted(zip(values, weights, strict=True), key=lambda item: item[0])
    total_weight = sum(weight for _, weight in ordered)
    if total_weight <= 0.0:
        raise ValueError("weighted median requires positive total weight")
    threshold = total_weight / 2.0
    cumulative = 0.0
    for value, weight in ordered:
        cumulative += weight
        if cumulative >= threshold:
            return value
    return ordered[-1][0]


def _fit_models_by_run(
    alignment_model: (
        RetentionTimeAlignmentFitReport
        | tuple[RetentionTimeAlignmentFitModel, ...]
        | RetentionTimeAlignmentFitModel
    ),
) -> dict[str, RetentionTimeAlignmentFitModel]:
    if isinstance(alignment_model, RetentionTimeAlignmentFitReport):
        models = alignment_model.models
    elif isinstance(alignment_model, RetentionTimeAlignmentFitModel):
        models = (alignment_model,)
    else:
        models = alignment_model
    return {model.run_id: model for model in models}


def _rt_confidence_penalty(
    *,
    imported_confidence: float,
    absolute_rt_residual: float,
    aligned_rt_tolerance_seconds: float,
    high_confidence_threshold: float,
) -> float:
    if (
        imported_confidence < high_confidence_threshold
        or absolute_rt_residual <= aligned_rt_tolerance_seconds
    ):
        return 1.0
    excess_ratio = min(
        1.0,
        (absolute_rt_residual - aligned_rt_tolerance_seconds)
        / aligned_rt_tolerance_seconds,
    )
    return max(0.2, round(0.5 - (0.3 * excess_ratio), 4))

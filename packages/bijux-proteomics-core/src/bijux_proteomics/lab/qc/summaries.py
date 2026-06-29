# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Batch- and study-level summary owners for laboratory QC."""

from __future__ import annotations

from statistics import median

from bijux_proteomics.lab.qc.models import (
    InstrumentBatchQcReport,
    InstrumentBatchQcRunEntry,
    LcmsRunQcReport,
    StudyQcBatchSummary,
    StudyQcConditionSummary,
    StudyQcSummaryReport,
)
from bijux_proteomics.lab.qc.support import build_document_schema


def build_instrument_batch_qc_report(
    run_reports: tuple[LcmsRunQcReport, ...],
    *,
    batch_id: str | None = None,
    instrument: str | None = None,
    identification_rate_floor_ratio: float = 0.85,
    spectrum_count_floor_ratio: float = 0.8,
    median_abs_mass_error_multiplier: float = 2.0,
) -> InstrumentBatchQcReport:
    """Build a typed batch-level QC summary and outlier flags."""
    if not run_reports:
        raise ValueError("batch QC requires at least one run report")

    resolved_batch_id = batch_id
    if resolved_batch_id is None:
        batch_ids = {report.batch for report in run_reports if report.batch}
        resolved_batch_id = next(iter(batch_ids)) if len(batch_ids) == 1 else None
    resolved_instrument = instrument
    if resolved_instrument is None:
        instruments = {report.instrument for report in run_reports if report.instrument}
        resolved_instrument = next(iter(instruments)) if len(instruments) == 1 else None

    spectrum_count_values = [report.spectrum_count for report in run_reports]
    identification_rate_values = [report.identification_rate for report in run_reports]
    median_spectrum_count = float(median(spectrum_count_values))
    median_identification_rate = float(median(identification_rate_values))

    median_abs_mass_error_values = [
        report.mass_error.median_abs_ppm
        for report in run_reports
        if report.mass_error.median_abs_ppm is not None
    ]
    median_abs_mass_error_ppm = (
        None
        if not median_abs_mass_error_values
        else float(median(median_abs_mass_error_values))
    )
    identified_median_rt_values = [
        report.retention_time.identified_median_retention_time_seconds
        for report in run_reports
        if report.retention_time.identified_median_retention_time_seconds is not None
    ]
    median_identified_retention_time_seconds = (
        None
        if not identified_median_rt_values
        else float(median(identified_median_rt_values))
    )

    run_entries: list[InstrumentBatchQcRunEntry] = []
    outlier_run_ids: list[str] = []
    for report in sorted(run_reports, key=lambda item: item.run_id):
        reasons: list[str] = []
        if median_spectrum_count > 0 and report.spectrum_count < (
            median_spectrum_count * spectrum_count_floor_ratio
        ):
            reasons.append("low_spectrum_count")
        if median_identification_rate > 0 and report.identification_rate < (
            median_identification_rate * identification_rate_floor_ratio
        ):
            reasons.append("low_identification_rate")
        if (
            median_abs_mass_error_ppm is not None
            and report.mass_error.median_abs_ppm is not None
            and report.mass_error.median_abs_ppm
            > max(5.0, median_abs_mass_error_ppm * median_abs_mass_error_multiplier)
        ):
            reasons.append("high_mass_error")
        retention_time_shift_seconds = None
        if (
            median_identified_retention_time_seconds is not None
            and report.retention_time.identified_median_retention_time_seconds
            is not None
        ):
            retention_time_shift_seconds = (
                report.retention_time.identified_median_retention_time_seconds
                - median_identified_retention_time_seconds
            )
        if reasons:
            outlier_run_ids.append(report.run_id)
        run_entries.append(
            InstrumentBatchQcRunEntry(
                run_id=report.run_id,
                sample_id=report.sample_id,
                batch=report.batch,
                instrument=report.instrument,
                spectrum_count=report.spectrum_count,
                identification_rate=report.identification_rate,
                median_abs_mass_error_ppm=report.mass_error.median_abs_ppm,
                identified_retention_time_span_seconds=report.retention_time.identified_span_seconds,
                retention_time_shift_seconds=retention_time_shift_seconds,
                outlier_reasons=tuple(reasons),
            )
        )

    return InstrumentBatchQcReport(
        document_schema=build_document_schema("instrument_batch_qc_report"),
        batch_id=resolved_batch_id,
        instrument=resolved_instrument,
        run_count=len(run_reports),
        median_spectrum_count=median_spectrum_count,
        median_identification_rate=median_identification_rate,
        median_abs_mass_error_ppm=median_abs_mass_error_ppm,
        median_identified_retention_time_seconds=median_identified_retention_time_seconds,
        outlier_run_ids=tuple(sorted(outlier_run_ids)),
        runs=tuple(run_entries),
    )


def build_study_qc_summary(
    run_reports: tuple[LcmsRunQcReport, ...],
    *,
    study_id: str = "study",
) -> StudyQcSummaryReport:
    """Build a study-level QC summary across conditions and batches."""
    if not run_reports:
        raise ValueError("study QC summary requires at least one run report")

    condition_groups: dict[str, list[LcmsRunQcReport]] = {}
    batch_groups: dict[str, list[LcmsRunQcReport]] = {}
    for report in run_reports:
        condition_groups.setdefault(report.condition or "unknown", []).append(report)
        batch_groups.setdefault(report.batch or "unbatched", []).append(report)

    condition_summaries = tuple(
        StudyQcConditionSummary(
            condition=condition,
            run_ids=tuple(sorted(report.run_id for report in reports)),
            median_identification_rate=float(
                median([report.identification_rate for report in reports])
            ),
            median_spectrum_count=float(
                median([report.spectrum_count for report in reports])
            ),
            median_abs_mass_error_ppm=(
                None
                if not [
                    report.mass_error.median_abs_ppm
                    for report in reports
                    if report.mass_error.median_abs_ppm is not None
                ]
                else float(
                    median(
                        [
                            report.mass_error.median_abs_ppm
                            for report in reports
                            if report.mass_error.median_abs_ppm is not None
                        ]
                    )
                )
            ),
        )
        for condition, reports in sorted(condition_groups.items())
    )

    batch_summaries = tuple(
        StudyQcBatchSummary(
            batch_id=batch_id,
            run_ids=tuple(sorted(report.run_id for report in reports)),
            median_identification_rate=float(
                median([report.identification_rate for report in reports])
            ),
            median_spectrum_count=float(
                median([report.spectrum_count for report in reports])
            ),
            outlier_run_ids=tuple(
                sorted(
                    build_instrument_batch_qc_report(
                        tuple(reports), batch_id=batch_id
                    ).outlier_run_ids
                )
            ),
        )
        for batch_id, reports in sorted(batch_groups.items())
    )

    identification_rates = [report.identification_rate for report in run_reports]
    spectrum_counts = [float(report.spectrum_count) for report in run_reports]
    return StudyQcSummaryReport(
        document_schema=build_document_schema("study_qc_summary_report"),
        study_id=study_id,
        run_count=len(run_reports),
        condition_summaries=condition_summaries,
        batch_summaries=batch_summaries,
        overall_identification_rate_span=max(identification_rates)
        - min(identification_rates),
        overall_spectrum_count_span=max(spectrum_counts) - min(spectrum_counts),
    )


__all__ = [
    "build_instrument_batch_qc_report",
    "build_study_qc_summary",
]

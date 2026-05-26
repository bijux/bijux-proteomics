# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Run-level QC contracts built directly from accepted spectra."""

from __future__ import annotations

import csv
import io
from enum import StrEnum
from math import floor

from pydantic import ConfigDict, Field

from bijux_proteomics.domain import ConfidenceTier
from bijux_proteomics.io.formats import MzmlChromatogramReport
from bijux_proteomics.io.spectra import SpectrumDistributionRow, SpectrumModel
from bijux_proteomics.io.spectra.spectrum_entropy import score_spectrum_entropy
from bijux_proteomics_foundation import DocumentSchema, JsonModel


class SpectrumQcTracePoint(JsonModel):
    """One plot-ready TIC/BPC or count-over-time point."""

    model_config = ConfigDict(extra="forbid")

    time_seconds: float = Field(..., ge=0.0)
    value: float = Field(..., ge=0.0)


class SpectrumQcTimeBin(JsonModel):
    """One fixed-width MS/MS count bin over retention time."""

    model_config = ConfigDict(extra="forbid")

    start_seconds: float = Field(..., ge=0.0)
    end_seconds: float = Field(..., ge=0.0)
    ms2_spectrum_count: int = Field(..., ge=0)


SpectrumQualityTier = ConfidenceTier


class FlaggedSpectrumIssueKind(StrEnum):
    """Explicit run-QC issue kinds carried by flagged spectra."""

    EMPTY = "empty"
    NOISY = "noisy"
    SINGLE_DOMINANT_PEAK = "single_dominant_peak"


class SpectrumQcMetricRow(JsonModel):
    """One per-spectrum QC metric row."""

    model_config = ConfigDict(extra="forbid")

    spectrum_id: str = Field(..., min_length=1)
    ms_level: int | None = Field(default=None, ge=1)
    retention_time_seconds: float | None = Field(default=None, ge=0.0)
    precursor_mz: float = Field(..., gt=0.0)
    precursor_intensity: float | None = Field(default=None, ge=0.0)
    precursor_charge: int | None = Field(default=None, ge=1)
    peak_count: int = Field(..., ge=0)
    total_ion_current: float = Field(..., ge=0.0)
    base_peak_intensity: float = Field(..., ge=0.0)
    top_peak_dominance: float = Field(..., ge=0.0, le=1.0)
    spectral_entropy: float = Field(..., ge=0.0, le=1.0)
    quality_tier: SpectrumQualityTier
    is_empty: bool
    is_noisy: bool
    is_single_dominant_peak: bool


class SpectrumQcFlaggedSpectrum(JsonModel):
    """One spectrum flagged as empty or noisy for run-level review."""

    model_config = ConfigDict(extra="forbid")

    spectrum_id: str = Field(..., min_length=1)
    issue_kind: FlaggedSpectrumIssueKind
    peak_count: int = Field(..., ge=0)
    total_ion_current: float = Field(..., ge=0.0)
    base_peak_intensity: float = Field(..., ge=0.0)
    retention_time_seconds: float | None = Field(default=None, ge=0.0)


class SpectrumRunQcPlotPayload(JsonModel):
    """Plot-ready run-QC payload over traces and time bins."""

    model_config = ConfigDict(extra="forbid")

    source_kind: str = Field(..., min_length=1)
    chromatogram_source: str = Field(..., min_length=1)
    ms2_count_over_time: tuple[SpectrumQcTimeBin, ...] = Field(default_factory=tuple)
    tic_trace: tuple[SpectrumQcTracePoint, ...] = Field(default_factory=tuple)
    bpc_trace: tuple[SpectrumQcTracePoint, ...] = Field(default_factory=tuple)


class SpectrumRunQcReport(JsonModel):
    """Raw-spectrum QC report over one MGF or mzML run."""

    model_config = ConfigDict(extra="forbid")

    document_schema: DocumentSchema
    source_kind: str = Field(..., min_length=1)
    chromatogram_source: str = Field(..., min_length=1)
    spectrum_count: int = Field(..., ge=0)
    rejected_count: int = Field(..., ge=0)
    ms2_spectrum_count: int = Field(..., ge=0)
    precursor_intensity_observation_count: int = Field(..., ge=0)
    empty_spectrum_count: int = Field(..., ge=0)
    noisy_spectrum_count: int = Field(..., ge=0)
    single_dominant_peak_count: int = Field(..., ge=0)
    quality_distribution: tuple[SpectrumDistributionRow, ...] = Field(
        default_factory=tuple
    )
    ms2_count_over_time: tuple[SpectrumQcTimeBin, ...] = Field(default_factory=tuple)
    tic_trace: tuple[SpectrumQcTracePoint, ...] = Field(default_factory=tuple)
    bpc_trace: tuple[SpectrumQcTracePoint, ...] = Field(default_factory=tuple)
    precursor_intensity_distribution: tuple[SpectrumDistributionRow, ...] = Field(
        default_factory=tuple
    )
    charge_distribution: tuple[SpectrumDistributionRow, ...] = Field(
        default_factory=tuple
    )
    spectrum_metrics: tuple[SpectrumQcMetricRow, ...] = Field(default_factory=tuple)
    flagged_spectra: tuple[SpectrumQcFlaggedSpectrum, ...] = Field(
        default_factory=tuple
    )
    diagnostics: tuple[str, ...] = Field(default_factory=tuple)


def build_spectrum_run_qc_report(
    spectra: tuple[SpectrumModel, ...],
    *,
    source_kind: str,
    rejected_count: int = 0,
    chromatograms: MzmlChromatogramReport | None = None,
    time_bin_seconds: float = 60.0,
    noisy_peak_count_threshold: int = 3,
    noisy_total_ion_current_threshold: float = 100.0,
    single_dominant_peak_threshold: float = 0.85,
    medium_quality_peak_count_threshold: int = 4,
    medium_quality_total_ion_current_threshold: float = 100.0,
    medium_quality_entropy_threshold: float = 0.35,
    high_quality_peak_count_threshold: int = 8,
    high_quality_total_ion_current_threshold: float = 500.0,
    high_quality_entropy_threshold: float = 0.65,
) -> SpectrumRunQcReport:
    """Build a raw-spectrum run-QC report from accepted spectra and optional chromatograms."""
    if time_bin_seconds <= 0:
        raise ValueError("time_bin_seconds must be greater than zero")
    if noisy_peak_count_threshold <= 0:
        raise ValueError("noisy_peak_count_threshold must be greater than zero")
    if noisy_total_ion_current_threshold < 0:
        raise ValueError("noisy_total_ion_current_threshold must be zero or greater")
    if not 0.0 <= single_dominant_peak_threshold <= 1.0:
        raise ValueError("single_dominant_peak_threshold must be between zero and one")
    if medium_quality_peak_count_threshold <= 0:
        raise ValueError(
            "medium_quality_peak_count_threshold must be greater than zero"
        )
    if medium_quality_total_ion_current_threshold < 0:
        raise ValueError(
            "medium_quality_total_ion_current_threshold must be zero or greater"
        )
    if not 0.0 <= medium_quality_entropy_threshold <= 1.0:
        raise ValueError(
            "medium_quality_entropy_threshold must be between zero and one"
        )
    if high_quality_peak_count_threshold <= 0:
        raise ValueError(
            "high_quality_peak_count_threshold must be greater than zero"
        )
    if high_quality_total_ion_current_threshold < 0:
        raise ValueError(
            "high_quality_total_ion_current_threshold must be zero or greater"
        )
    if not 0.0 <= high_quality_entropy_threshold <= 1.0:
        raise ValueError("high_quality_entropy_threshold must be between zero and one")

    charge_counts: dict[str, int] = {}
    quality_counts = {
        SpectrumQualityTier.HIGH.value: 0,
        SpectrumQualityTier.MEDIUM.value: 0,
        SpectrumQualityTier.LOW.value: 0,
    }
    precursor_intensity_counts = {
        "unknown": 0,
        "0-999": 0,
        "1000-9999": 0,
        "10000-99999": 0,
        "100000+": 0,
    }
    flagged: list[SpectrumQcFlaggedSpectrum] = []
    spectrum_metrics: list[SpectrumQcMetricRow] = []
    ms2_spectra_with_rt: list[SpectrumModel] = []
    derived_tic_points: list[SpectrumQcTracePoint] = []
    derived_bpc_points: list[SpectrumQcTracePoint] = []
    diagnostics: list[str] = []

    ms2_spectrum_count = 0
    precursor_intensity_observation_count = 0
    empty_spectrum_count = 0
    noisy_spectrum_count = 0
    single_dominant_peak_count = 0

    for spectrum in spectra:
        ms_level = spectrum.ms_level
        is_ms2 = ms_level == 2 or (source_kind == "mgf" and ms_level is None)
        if is_ms2:
            ms2_spectrum_count += 1
            if spectrum.retention_time_seconds is not None:
                ms2_spectra_with_rt.append(spectrum)

        charge_key = (
            "unknown"
            if spectrum.precursor_charge is None
            else "5+"
            if spectrum.precursor_charge >= 5
            else str(spectrum.precursor_charge)
        )
        charge_counts[charge_key] = charge_counts.get(charge_key, 0) + 1

        intensity = spectrum.precursor_intensity
        if intensity is None:
            precursor_intensity_counts["unknown"] += 1
        else:
            precursor_intensity_observation_count += 1
            if intensity < 1000.0:
                precursor_intensity_counts["0-999"] += 1
            elif intensity < 10000.0:
                precursor_intensity_counts["1000-9999"] += 1
            elif intensity < 100000.0:
                precursor_intensity_counts["10000-99999"] += 1
            else:
                precursor_intensity_counts["100000+"] += 1

        total_ion_current = sum(peak.intensity for peak in spectrum.peaks)
        base_peak_intensity = max(
            (peak.intensity for peak in spectrum.peaks), default=0.0
        )
        entropy_score = score_spectrum_entropy(spectrum.peaks)
        top_peak_dominance = entropy_score.top_peak_fraction
        spectral_entropy = entropy_score.normalized_entropy
        is_empty = len(spectrum.peaks) == 0
        is_noisy = len(spectrum.peaks) < noisy_peak_count_threshold or (
            total_ion_current < noisy_total_ion_current_threshold
        )
        is_single_dominant_peak = (
            len(spectrum.peaks) > 0
            and top_peak_dominance >= single_dominant_peak_threshold
        )
        quality_tier = _classify_spectrum_quality(
            peak_count=len(spectrum.peaks),
            total_ion_current=total_ion_current,
            spectral_entropy=spectral_entropy,
            is_empty=is_empty,
            is_noisy=is_noisy,
            is_single_dominant_peak=is_single_dominant_peak,
            medium_quality_peak_count_threshold=medium_quality_peak_count_threshold,
            medium_quality_total_ion_current_threshold=(
                medium_quality_total_ion_current_threshold
            ),
            medium_quality_entropy_threshold=medium_quality_entropy_threshold,
            high_quality_peak_count_threshold=high_quality_peak_count_threshold,
            high_quality_total_ion_current_threshold=(
                high_quality_total_ion_current_threshold
            ),
            high_quality_entropy_threshold=high_quality_entropy_threshold,
        )
        quality_counts[quality_tier.value] += 1
        spectrum_metrics.append(
            SpectrumQcMetricRow(
                spectrum_id=spectrum.spectrum_id,
                ms_level=spectrum.ms_level,
                retention_time_seconds=spectrum.retention_time_seconds,
                precursor_mz=spectrum.precursor_mz,
                precursor_intensity=spectrum.precursor_intensity,
                precursor_charge=spectrum.precursor_charge,
                peak_count=len(spectrum.peaks),
                total_ion_current=total_ion_current,
                base_peak_intensity=base_peak_intensity,
                top_peak_dominance=top_peak_dominance,
                spectral_entropy=spectral_entropy,
                quality_tier=quality_tier,
                is_empty=is_empty,
                is_noisy=is_noisy,
                is_single_dominant_peak=is_single_dominant_peak,
            )
        )
        if spectrum.retention_time_seconds is not None:
            derived_tic_points.append(
                SpectrumQcTracePoint(
                    time_seconds=spectrum.retention_time_seconds,
                    value=total_ion_current,
                )
            )
            derived_bpc_points.append(
                SpectrumQcTracePoint(
                    time_seconds=spectrum.retention_time_seconds,
                    value=base_peak_intensity,
                )
            )

        if is_empty:
            empty_spectrum_count += 1
            flagged.append(
                SpectrumQcFlaggedSpectrum(
                    spectrum_id=spectrum.spectrum_id,
                    issue_kind=FlaggedSpectrumIssueKind.EMPTY,
                    peak_count=0,
                    total_ion_current=0.0,
                    base_peak_intensity=0.0,
                    retention_time_seconds=spectrum.retention_time_seconds,
                )
            )
            continue
        if is_noisy:
            noisy_spectrum_count += 1
            flagged.append(
                SpectrumQcFlaggedSpectrum(
                    spectrum_id=spectrum.spectrum_id,
                    issue_kind=FlaggedSpectrumIssueKind.NOISY,
                    peak_count=len(spectrum.peaks),
                    total_ion_current=total_ion_current,
                    base_peak_intensity=base_peak_intensity,
                    retention_time_seconds=spectrum.retention_time_seconds,
                )
            )
        if is_single_dominant_peak:
            single_dominant_peak_count += 1
            flagged.append(
                SpectrumQcFlaggedSpectrum(
                    spectrum_id=spectrum.spectrum_id,
                    issue_kind=FlaggedSpectrumIssueKind.SINGLE_DOMINANT_PEAK,
                    peak_count=len(spectrum.peaks),
                    total_ion_current=total_ion_current,
                    base_peak_intensity=base_peak_intensity,
                    retention_time_seconds=spectrum.retention_time_seconds,
                )
            )

    ms2_count_over_time = _build_ms2_count_over_time(
        ms2_spectra_with_rt,
        time_bin_seconds=time_bin_seconds,
    )
    tic_trace, bpc_trace, chromatogram_source = _resolve_qc_traces(
        spectra,
        chromatograms=chromatograms,
        derived_tic_points=derived_tic_points,
        derived_bpc_points=derived_bpc_points,
    )
    if not ms2_count_over_time:
        diagnostics.append(
            "no retention-time-bearing MS/MS spectra were available for count-over-time QC"
        )
    if not tic_trace and not bpc_trace:
        diagnostics.append(
            "no TIC/BPC trace could be built because chromatograms and retention-time-bearing spectra were both absent"
        )
    if precursor_intensity_observation_count == 0:
        diagnostics.append(
            "precursor intensity distribution is unknown because the parsed spectra did not carry precursor intensity values"
        )

    report = SpectrumRunQcReport(
        document_schema=DocumentSchema(
            created_by="bijux-proteomics-core",
            document_kind="spectrum_run_qc_report",
            package_name="bijux-proteomics-core",
            status="generated",
        ),
        source_kind=source_kind,
        chromatogram_source=chromatogram_source,
        spectrum_count=len(spectra),
        rejected_count=rejected_count,
        ms2_spectrum_count=ms2_spectrum_count,
        precursor_intensity_observation_count=precursor_intensity_observation_count,
        empty_spectrum_count=empty_spectrum_count,
        noisy_spectrum_count=noisy_spectrum_count,
        single_dominant_peak_count=single_dominant_peak_count,
        quality_distribution=tuple(
            SpectrumDistributionRow(bucket=bucket, count=count)
            for bucket, count in quality_counts.items()
        ),
        ms2_count_over_time=ms2_count_over_time,
        tic_trace=tic_trace,
        bpc_trace=bpc_trace,
        precursor_intensity_distribution=tuple(
            SpectrumDistributionRow(bucket=bucket, count=count)
            for bucket, count in precursor_intensity_counts.items()
        ),
        charge_distribution=tuple(
            SpectrumDistributionRow(bucket=bucket, count=charge_counts.get(bucket, 0))
            for bucket in ("unknown", "1", "2", "3", "4", "5+")
            if bucket != "5+" or charge_counts.get("5+", 0) > 0
        ),
        spectrum_metrics=tuple(
            sorted(
                spectrum_metrics,
                key=lambda row: (
                    row.retention_time_seconds is None,
                    row.retention_time_seconds or 0.0,
                    row.spectrum_id,
                ),
            )
        ),
        flagged_spectra=tuple(
            sorted(
                flagged,
                key=lambda item: (
                    item.issue_kind.value,
                    item.retention_time_seconds is None,
                    item.retention_time_seconds or 0.0,
                    item.spectrum_id,
                ),
            )
        ),
        diagnostics=tuple(diagnostics),
    )
    payload = report.to_dict()
    return report.model_copy(
        update={
            "document_schema": report.document_schema.with_content_hash(payload),
        }
    )


def build_spectrum_run_qc_plot_payload(
    report: SpectrumRunQcReport,
) -> SpectrumRunQcPlotPayload:
    """Return the plot-ready subset of the run-QC report."""
    return SpectrumRunQcPlotPayload(
        source_kind=report.source_kind,
        chromatogram_source=report.chromatogram_source,
        ms2_count_over_time=report.ms2_count_over_time,
        tic_trace=report.tic_trace,
        bpc_trace=report.bpc_trace,
    )


def render_spectrum_run_qc_summary_tsv(report: SpectrumRunQcReport) -> str:
    """Render a one-row run-QC summary table."""
    return _render_tsv(
        (
            "source_kind",
            "chromatogram_source",
            "spectrum_count",
            "rejected_count",
            "ms2_spectrum_count",
            "precursor_intensity_observation_count",
            "empty_spectrum_count",
            "noisy_spectrum_count",
            "single_dominant_peak_count",
        ),
        (
            (
                report.source_kind,
                report.chromatogram_source,
                report.spectrum_count,
                report.rejected_count,
                report.ms2_spectrum_count,
                report.precursor_intensity_observation_count,
                report.empty_spectrum_count,
                report.noisy_spectrum_count,
                report.single_dominant_peak_count,
            ),
        ),
    )


def render_spectrum_run_qc_spectra_tsv(report: SpectrumRunQcReport) -> str:
    """Render the per-spectrum QC metric table."""

    return _render_tsv(
        (
            "spectrum_id",
            "ms_level",
            "retention_time_seconds",
            "precursor_mz",
            "precursor_intensity",
            "precursor_charge",
            "peak_count",
            "total_ion_current",
            "base_peak_intensity",
            "top_peak_dominance",
            "spectral_entropy",
            "quality_tier",
            "is_empty",
            "is_noisy",
            "is_single_dominant_peak",
        ),
        tuple(
            (
                row.spectrum_id,
                row.ms_level,
                row.retention_time_seconds,
                row.precursor_mz,
                row.precursor_intensity,
                row.precursor_charge,
                row.peak_count,
                row.total_ion_current,
                row.base_peak_intensity,
                row.top_peak_dominance,
                row.spectral_entropy,
                row.quality_tier.value,
                row.is_empty,
                row.is_noisy,
                row.is_single_dominant_peak,
            )
            for row in report.spectrum_metrics
        ),
    )


def render_spectrum_run_qc_time_bins_tsv(report: SpectrumRunQcReport) -> str:
    """Render the MS/MS count-over-time table."""
    return _render_tsv(
        ("start_seconds", "end_seconds", "ms2_spectrum_count"),
        tuple(
            (row.start_seconds, row.end_seconds, row.ms2_spectrum_count)
            for row in report.ms2_count_over_time
        ),
    )


def render_spectrum_run_qc_distribution_tsv(
    rows: tuple[SpectrumDistributionRow, ...],
    *,
    distribution_name: str,
) -> str:
    """Render one named QC distribution table."""
    return _render_tsv(
        (distribution_name, "count"),
        tuple((row.bucket, row.count) for row in rows),
    )


def render_spectrum_run_qc_trace_tsv(
    rows: tuple[SpectrumQcTracePoint, ...],
    *,
    trace_name: str,
) -> str:
    """Render one TIC/BPC trace table."""
    return _render_tsv(
        ("time_seconds", trace_name),
        tuple((row.time_seconds, row.value) for row in rows),
    )


def render_spectrum_run_qc_flagged_spectra_tsv(report: SpectrumRunQcReport) -> str:
    """Render the flagged empty/noisy spectrum table."""
    return _render_tsv(
        (
            "spectrum_id",
            "issue_kind",
            "peak_count",
            "total_ion_current",
            "base_peak_intensity",
            "retention_time_seconds",
        ),
        tuple(
            (
                row.spectrum_id,
                row.issue_kind.value,
                row.peak_count,
                row.total_ion_current,
                row.base_peak_intensity,
                row.retention_time_seconds,
            )
            for row in report.flagged_spectra
        ),
    )


def _build_ms2_count_over_time(
    spectra: list[SpectrumModel],
    *,
    time_bin_seconds: float,
) -> tuple[SpectrumQcTimeBin, ...]:
    if not spectra:
        return ()
    sorted_spectra = sorted(
        spectra,
        key=lambda item: (item.retention_time_seconds or 0.0, item.spectrum_id),
    )
    start_time = sorted_spectra[0].retention_time_seconds or 0.0
    end_time = sorted_spectra[-1].retention_time_seconds or 0.0
    start_bin = floor(start_time / time_bin_seconds) * time_bin_seconds
    end_bin = floor(end_time / time_bin_seconds) * time_bin_seconds
    counts: dict[float, int] = dict.fromkeys(
        _float_range(start_bin, end_bin + time_bin_seconds, time_bin_seconds), 0
    )
    for spectrum in sorted_spectra:
        retention_time = spectrum.retention_time_seconds or 0.0
        bucket_start = floor(retention_time / time_bin_seconds) * time_bin_seconds
        counts[bucket_start] = counts.get(bucket_start, 0) + 1
    return tuple(
        SpectrumQcTimeBin(
            start_seconds=bucket_start,
            end_seconds=bucket_start + time_bin_seconds,
            ms2_spectrum_count=counts.get(bucket_start, 0),
        )
        for bucket_start in sorted(counts)
    )


def _resolve_qc_traces(
    spectra: tuple[SpectrumModel, ...],
    *,
    chromatograms: MzmlChromatogramReport | None,
    derived_tic_points: list[SpectrumQcTracePoint],
    derived_bpc_points: list[SpectrumQcTracePoint],
) -> tuple[tuple[SpectrumQcTracePoint, ...], tuple[SpectrumQcTracePoint, ...], str]:
    if chromatograms is not None and chromatograms.accepted_traces:
        tic_trace = next(
            (
                tuple(
                    SpectrumQcTracePoint(
                        time_seconds=point.time_seconds,
                        value=point.intensity,
                    )
                    for point in trace.points
                )
                for trace in chromatograms.accepted_traces
                if trace.kind == "tic"
            ),
            (),
        )
        bpc_trace = next(
            (
                tuple(
                    SpectrumQcTracePoint(
                        time_seconds=point.time_seconds,
                        value=point.intensity,
                    )
                    for point in trace.points
                )
                for trace in chromatograms.accepted_traces
                if trace.kind == "bpc"
            ),
            (),
        )
        if tic_trace or bpc_trace:
            return tic_trace, bpc_trace, "reported_mzml_chromatograms"

    if derived_tic_points or derived_bpc_points:
        ordered_tic = tuple(
            sorted(derived_tic_points, key=lambda item: (item.time_seconds, item.value))
        )
        ordered_bpc = tuple(
            sorted(derived_bpc_points, key=lambda item: (item.time_seconds, item.value))
        )
        return ordered_tic, ordered_bpc, "spectrum_derived"

    return (), (), "unavailable"


def _classify_spectrum_quality(
    *,
    peak_count: int,
    total_ion_current: float,
    spectral_entropy: float,
    is_empty: bool,
    is_noisy: bool,
    is_single_dominant_peak: bool,
    medium_quality_peak_count_threshold: int,
    medium_quality_total_ion_current_threshold: float,
    medium_quality_entropy_threshold: float,
    high_quality_peak_count_threshold: int,
    high_quality_total_ion_current_threshold: float,
    high_quality_entropy_threshold: float,
) -> SpectrumQualityTier:
    if is_empty or is_noisy or is_single_dominant_peak:
        return SpectrumQualityTier.LOW
    if (
        peak_count >= high_quality_peak_count_threshold
        and total_ion_current >= high_quality_total_ion_current_threshold
        and spectral_entropy >= high_quality_entropy_threshold
    ):
        return SpectrumQualityTier.HIGH
    if (
        peak_count >= medium_quality_peak_count_threshold
        and total_ion_current >= medium_quality_total_ion_current_threshold
        and spectral_entropy >= medium_quality_entropy_threshold
    ):
        return SpectrumQualityTier.MEDIUM
    return SpectrumQualityTier.LOW


def _float_range(start: float, stop: float, step: float) -> list[float]:
    values: list[float] = []
    current = start
    while current < stop:
        values.append(current)
        current += step
    return values


def _render_tsv(header: tuple[str, ...], rows: tuple[tuple[object, ...], ...]) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(header)
    writer.writerows(rows)
    return buffer.getvalue()

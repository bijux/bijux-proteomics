# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Score chromatographic precursor and peptide evidence from XIC peak support."""

from __future__ import annotations

from collections import Counter
import csv
from io import StringIO
from pathlib import Path
from statistics import mean

from pydantic import ConfigDict, Field

from bijux_proteomics.io.chromatography.chromatographic_peak_picking import (
    ChromatographicPeak,
    ChromatographicPeakPickingReport,
    PeakShapeQualityTier,
    score_peak_shape,
)
from bijux_proteomics.io.chromatography.retention_time_alignment import (
    RetentionTimeAlignmentReport,
)
from bijux_proteomics.io.chromatography.xic import XicTracePoint
from bijux_proteomics.io.tables.xic_target_table import XicTargetEntry
from bijux_proteomics_foundation import JsonModel


class ChromatographicTargetEvidenceEntry(JsonModel):
    """One precursor-target chromatographic evidence score summary."""

    model_config = ConfigDict(extra="forbid")

    target_id: str = Field(..., min_length=1)
    peptide_ref: str = Field(..., min_length=1)
    precursor_mz: float = Field(..., gt=0.0)
    total_run_count: int = Field(..., ge=1)
    detected_run_count: int = Field(..., ge=0)
    missing_run_count: int = Field(..., ge=0)
    peak_shape_score: float = Field(..., ge=0.0, le=1.0)
    apex_intensity_score: float = Field(..., ge=0.0, le=1.0)
    signal_to_noise_score: float = Field(..., ge=0.0, le=1.0)
    rt_agreement_score: float = Field(..., ge=0.0, le=1.0)
    missingness_score: float = Field(..., ge=0.0, le=1.0)
    chromatographic_evidence_score: float = Field(..., ge=0.0, le=1.0)
    flagged_run_ids: tuple[str, ...] = Field(default_factory=tuple)
    missing_run_ids: tuple[str, ...] = Field(default_factory=tuple)
    concern_codes: tuple[str, ...] = Field(default_factory=tuple)


class ChromatographicPeptideEvidenceEntry(JsonModel):
    """One peptide-level chromatographic evidence score aggregated over targets."""

    model_config = ConfigDict(extra="forbid")

    peptide_ref: str = Field(..., min_length=1)
    target_ids: tuple[str, ...] = Field(default_factory=tuple)
    total_run_count: int = Field(..., ge=1)
    detected_run_count: int = Field(..., ge=0)
    peak_shape_score: float = Field(..., ge=0.0, le=1.0)
    apex_intensity_score: float = Field(..., ge=0.0, le=1.0)
    signal_to_noise_score: float = Field(..., ge=0.0, le=1.0)
    rt_agreement_score: float = Field(..., ge=0.0, le=1.0)
    missingness_score: float = Field(..., ge=0.0, le=1.0)
    chromatographic_evidence_score: float = Field(..., ge=0.0, le=1.0)
    concern_codes: tuple[str, ...] = Field(default_factory=tuple)


class ChromatographicEvidenceScoreReport(JsonModel):
    """Stable chromatographic evidence score report over peak and RT reports."""

    model_config = ConfigDict(extra="forbid")

    run_ids: tuple[str, ...] = Field(default_factory=tuple)
    target_entries: tuple[ChromatographicTargetEvidenceEntry, ...] = Field(
        default_factory=tuple
    )
    peptide_entries: tuple[ChromatographicPeptideEvidenceEntry, ...] = Field(
        default_factory=tuple
    )


def score_chromatographic_evidence(
    peak_reports: tuple[ChromatographicPeakPickingReport, ...],
    *,
    alignment_report: RetentionTimeAlignmentReport | None = None,
) -> ChromatographicEvidenceScoreReport:
    """Score chromatographic precursor and peptide evidence across one or more runs."""

    if not peak_reports:
        raise ValueError(
            "chromatographic evidence scoring requires at least one run report"
        )

    run_entries = _build_run_entries(peak_reports)
    target_entries: list[ChromatographicTargetEvidenceEntry] = []
    peptide_index: dict[str, list[ChromatographicTargetEvidenceEntry]] = {}
    total_run_count = len(run_entries)
    max_apex_by_run = {
        entry.run_id: max(
            (peak.apex_intensity for peak in entry.report.peaks), default=1.0
        )
        for entry in run_entries
    }
    residuals_by_target_run = _alignment_residual_scores(alignment_report)
    target_specs = _target_specs(peak_reports)

    for target_id, target in sorted(target_specs.items()):
        peptide_ref = (
            target.metadata.get("peptide_ref")
            or target.display_name
            or target.target_id
        )
        run_peaks_by_run = {
            entry.run_id: _peaks_for_target(entry.report, target_id)
            for entry in run_entries
        }
        per_run_shape_scores: list[float] = []
        per_run_apex_scores: list[float] = []
        per_run_snr_scores: list[float] = []
        flagged_run_ids: list[str] = []
        missing_run_ids: list[str] = []
        concern_codes: set[str] = set()
        detected_run_count = 0

        for entry in run_entries:
            run_peaks = run_peaks_by_run[entry.run_id]
            if not run_peaks:
                missing_run_ids.append(entry.run_id)
                concern_codes.add("missing_peak")
                continue

            detected_run_count += 1
            selected_peak = max(run_peaks, key=lambda peak: (peak.area, peak.height))
            ambiguous_run = len(run_peaks) > 1
            run_shape_score = _shape_score(
                selected_peak,
                entry.report,
                ambiguous_run=ambiguous_run,
            )
            run_apex_score = _bounded_fraction(
                selected_peak.apex_intensity,
                max_apex_by_run[entry.run_id],
            )
            run_snr_score = _signal_to_noise_score(selected_peak)
            per_run_shape_scores.append(run_shape_score)
            per_run_apex_scores.append(run_apex_score)
            per_run_snr_scores.append(run_snr_score)

            if (
                ambiguous_run
                or selected_peak.overlap_flag
                or selected_peak.shoulder_flag
            ):
                flagged_run_ids.append(entry.run_id)
            if ambiguous_run:
                concern_codes.add("multiple_peaks")
            if selected_peak.overlap_flag:
                concern_codes.add("overlap_detected")
            if selected_peak.shoulder_flag:
                concern_codes.add("shoulder_detected")
            if run_snr_score < 0.5:
                concern_codes.add("low_signal_to_noise")

        missingness_score = _bounded_fraction(detected_run_count, total_run_count)
        rt_agreement_score = _rt_agreement_score(
            target_id,
            total_run_count=total_run_count,
            residuals_by_target_run=residuals_by_target_run,
            missing_run_count=total_run_count - detected_run_count,
            aligned_rt_tolerance_seconds=(
                5.0
                if alignment_report is None
                else alignment_report.aligned_rt_tolerance_seconds
            ),
            concern_codes=concern_codes,
        )
        target_entry = ChromatographicTargetEvidenceEntry(
            target_id=target_id,
            peptide_ref=peptide_ref,
            precursor_mz=target.precursor_mz,
            total_run_count=total_run_count,
            detected_run_count=detected_run_count,
            missing_run_count=total_run_count - detected_run_count,
            peak_shape_score=_mean_or_zero(per_run_shape_scores),
            apex_intensity_score=_mean_or_zero(per_run_apex_scores),
            signal_to_noise_score=_mean_or_zero(per_run_snr_scores),
            rt_agreement_score=rt_agreement_score,
            missingness_score=missingness_score,
            chromatographic_evidence_score=_weighted_score(
                shape_score=_mean_or_zero(per_run_shape_scores),
                apex_score=_mean_or_zero(per_run_apex_scores),
                snr_score=_mean_or_zero(per_run_snr_scores),
                rt_score=rt_agreement_score,
                missingness_score=missingness_score,
            ),
            flagged_run_ids=tuple(sorted(flagged_run_ids)),
            missing_run_ids=tuple(sorted(missing_run_ids)),
            concern_codes=tuple(sorted(concern_codes)),
        )
        target_entries.append(target_entry)
        peptide_index.setdefault(peptide_ref, []).append(target_entry)

    peptide_entries = [
        _build_peptide_entry(peptide_ref, entries)
        for peptide_ref, entries in sorted(peptide_index.items())
    ]
    return ChromatographicEvidenceScoreReport(
        run_ids=tuple(entry.run_id for entry in run_entries),
        target_entries=tuple(sorted(target_entries, key=lambda item: item.target_id)),
        peptide_entries=tuple(
            sorted(peptide_entries, key=lambda item: item.peptide_ref)
        ),
    )


def render_chromatographic_target_evidence_tsv(
    report: ChromatographicEvidenceScoreReport,
) -> str:
    """Render precursor-target chromatographic scores into stable TSV rows."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "target_id",
            "peptide_ref",
            "precursor_mz",
            "total_run_count",
            "detected_run_count",
            "missing_run_count",
            "peak_shape_score",
            "apex_intensity_score",
            "signal_to_noise_score",
            "rt_agreement_score",
            "missingness_score",
            "chromatographic_evidence_score",
            "flagged_run_ids",
            "missing_run_ids",
            "concern_codes",
        )
    )
    for entry in report.target_entries:
        writer.writerow(
            (
                entry.target_id,
                entry.peptide_ref,
                f"{entry.precursor_mz:.6f}",
                entry.total_run_count,
                entry.detected_run_count,
                entry.missing_run_count,
                f"{entry.peak_shape_score:.4f}",
                f"{entry.apex_intensity_score:.4f}",
                f"{entry.signal_to_noise_score:.4f}",
                f"{entry.rt_agreement_score:.4f}",
                f"{entry.missingness_score:.4f}",
                f"{entry.chromatographic_evidence_score:.4f}",
                "|".join(entry.flagged_run_ids),
                "|".join(entry.missing_run_ids),
                "|".join(entry.concern_codes),
            )
        )
    return buffer.getvalue()


def render_chromatographic_peptide_evidence_tsv(
    report: ChromatographicEvidenceScoreReport,
) -> str:
    """Render peptide-level chromatographic scores into stable TSV rows."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "peptide_ref",
            "target_ids",
            "total_run_count",
            "detected_run_count",
            "peak_shape_score",
            "apex_intensity_score",
            "signal_to_noise_score",
            "rt_agreement_score",
            "missingness_score",
            "chromatographic_evidence_score",
            "concern_codes",
        )
    )
    for entry in report.peptide_entries:
        writer.writerow(
            (
                entry.peptide_ref,
                "|".join(entry.target_ids),
                entry.total_run_count,
                entry.detected_run_count,
                f"{entry.peak_shape_score:.4f}",
                f"{entry.apex_intensity_score:.4f}",
                f"{entry.signal_to_noise_score:.4f}",
                f"{entry.rt_agreement_score:.4f}",
                f"{entry.missingness_score:.4f}",
                f"{entry.chromatographic_evidence_score:.4f}",
                "|".join(entry.concern_codes),
            )
        )
    return buffer.getvalue()


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
            report=report,
        )
        for report in peak_reports
    )


def _target_specs(
    peak_reports: tuple[ChromatographicPeakPickingReport, ...],
) -> dict[str, XicTargetEntry]:
    targets: dict[str, XicTargetEntry] = {}
    for report in peak_reports:
        for target in report.trace_report.accepted_targets:
            targets.setdefault(target.target_id, target)
    return targets


def _peaks_for_target(
    report: ChromatographicPeakPickingReport,
    target_id: str,
) -> tuple[ChromatographicPeak, ...]:
    return tuple(peak for peak in report.peaks if peak.target_id == target_id)


def _shape_score(
    peak: ChromatographicPeak,
    report: ChromatographicPeakPickingReport,
    *,
    ambiguous_run: bool,
) -> float:
    shape = score_peak_shape(_peak_trace(report, peak))
    raw_shape_score = shape.symmetry_score
    if shape.shape_quality_tier is PeakShapeQualityTier.JAGGED_NOISY:
        raw_shape_score *= 0.8
    elif shape.shape_quality_tier is PeakShapeQualityTier.FLAT_BROAD:
        raw_shape_score *= 0.6
    penalty = 1.0
    if peak.overlap_flag:
        penalty *= 0.6
    if peak.shoulder_flag:
        penalty *= 0.7
    if ambiguous_run:
        penalty *= 0.4
    return round(max(0.0, min(1.0, raw_shape_score * penalty)), 4)


def _peak_trace(
    report: ChromatographicPeakPickingReport,
    peak: ChromatographicPeak,
) -> tuple[XicTracePoint, ...]:
    return tuple(
        point
        for point in report.trace_report.trace_points
        if point.target_id == peak.target_id
        and peak.start_time_seconds <= point.time_seconds <= peak.end_time_seconds
    )


def _signal_to_noise_score(peak: ChromatographicPeak) -> float:
    noise_floor = max(
        (
            peak.baseline_start_intensity
            + peak.baseline_end_intensity
            + peak.baseline_at_apex
        )
        / 3.0,
        1.0,
    )
    return round(max(0.0, min(1.0, (peak.height / noise_floor) / 10.0)), 4)


def _alignment_residual_scores(
    alignment_report: RetentionTimeAlignmentReport | None,
) -> dict[tuple[str, str], float]:
    if alignment_report is None:
        return {}
    return {
        (residual.target_id, residual.run_id): residual.absolute_residual_seconds
        for residual in alignment_report.residuals
    }


def _rt_agreement_score(
    target_id: str,
    *,
    total_run_count: int,
    residuals_by_target_run: dict[tuple[str, str], float],
    missing_run_count: int,
    aligned_rt_tolerance_seconds: float,
    concern_codes: set[str],
) -> float:
    if total_run_count == 1:
        return 1.0
    residuals = [
        residual
        for (residual_target_id, _run_id), residual in residuals_by_target_run.items()
        if residual_target_id == target_id
    ]
    if not residuals:
        concern_codes.add("rt_alignment_unresolved")
        return 0.0
    max_residual = max(residuals)
    score = max(0.0, 1.0 - (max_residual / aligned_rt_tolerance_seconds))
    if max_residual > aligned_rt_tolerance_seconds:
        concern_codes.add("rt_outside_tolerance")
    if missing_run_count > 0:
        score *= max(0.0, 1.0 - (missing_run_count / total_run_count))
    return round(score, 4)


def _weighted_score(
    *,
    shape_score: float,
    apex_score: float,
    snr_score: float,
    rt_score: float,
    missingness_score: float,
) -> float:
    return round(
        (
            shape_score * 0.25
            + apex_score * 0.15
            + snr_score * 0.25
            + rt_score * 0.20
            + missingness_score * 0.15
        ),
        4,
    )


def _build_peptide_entry(
    peptide_ref: str,
    entries: list[ChromatographicTargetEvidenceEntry],
) -> ChromatographicPeptideEvidenceEntry:
    total_run_count = entries[0].total_run_count
    detected_run_count = max(entry.detected_run_count for entry in entries)
    concern_codes = {code for entry in entries for code in entry.concern_codes}
    return ChromatographicPeptideEvidenceEntry(
        peptide_ref=peptide_ref,
        target_ids=tuple(sorted(entry.target_id for entry in entries)),
        total_run_count=total_run_count,
        detected_run_count=detected_run_count,
        peak_shape_score=round(mean(entry.peak_shape_score for entry in entries), 4),
        apex_intensity_score=round(
            mean(entry.apex_intensity_score for entry in entries), 4
        ),
        signal_to_noise_score=round(
            mean(entry.signal_to_noise_score for entry in entries), 4
        ),
        rt_agreement_score=round(
            mean(entry.rt_agreement_score for entry in entries), 4
        ),
        missingness_score=round(mean(entry.missingness_score for entry in entries), 4),
        chromatographic_evidence_score=round(
            mean(entry.chromatographic_evidence_score for entry in entries), 4
        ),
        concern_codes=tuple(sorted(concern_codes)),
    )


def _bounded_fraction(numerator: float, denominator: float) -> float:
    if denominator <= 0.0:
        return 0.0
    return round(max(0.0, min(1.0, numerator / denominator)), 4)


def _mean_or_zero(values: list[float]) -> float:
    if not values:
        return 0.0
    return round(mean(values), 4)


class _RunEntry(JsonModel):
    model_config = ConfigDict(extra="forbid")

    run_id: str = Field(..., min_length=1)
    report: ChromatographicPeakPickingReport

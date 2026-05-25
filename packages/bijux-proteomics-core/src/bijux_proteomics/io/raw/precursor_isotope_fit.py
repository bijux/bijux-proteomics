# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Compare predicted precursor isotope envelopes against observed MS1 peaks."""

from __future__ import annotations

import csv
from io import StringIO
from pathlib import Path

from pydantic import ConfigDict, Field

from bijux_proteomics.chemistry import (
    IsotopeEnvelopePeakPrediction,
    predict_peptide_isotope_envelope,
)
from bijux_proteomics.io.chromatography.chromatographic_peak_picking import (
    ChromatographicPeak,
    ChromatographicPeakPickingReport,
)
from bijux_proteomics.io.raw.chromatographic_peak_picking import (
    extract_mzml_chromatographic_peaks,
)
from bijux_proteomics.io.raw.mzml_reader import parse_mzml
from bijux_proteomics.io.raw.xic_extraction import extract_mzml_xic_traces
from bijux_proteomics.io.spectra import SpectrumModel, calculate_precursor_mass_error
from bijux_proteomics.io.tables.xic_target_table import (
    XicTargetEntry,
    XicTargetParseReport,
    coerce_xic_target_report,
)
from bijux_proteomics.io.chromatography.xic import (
    XicTracePoint,
    XicTraceReport,
    XicToleranceUnit,
)
from bijux_proteomics_foundation import JsonModel

_C13_NEUTRON_SHIFT = 1.0033548378
_DEFAULT_MASS_ERROR_LIMIT_PPM = 10.0
_DEFAULT_PATTERN_SCORE_THRESHOLD = 0.6
_DEFAULT_CHARGE_SCORE_THRESHOLD = 0.5
_DEFAULT_FLAGGED_SCORE_THRESHOLD = 0.75


class PrecursorIsotopePeakObservation(JsonModel):
    """One predicted isotope peak compared against one observed MS1 peak."""

    model_config = ConfigDict(extra="forbid")

    isotope_index: int = Field(..., ge=0)
    expected_mz: float = Field(..., gt=0.0)
    expected_probability: float = Field(..., ge=0.0, le=1.0)
    observed_mz: float | None = Field(default=None, gt=0.0)
    observed_intensity: float | None = Field(default=None, ge=0.0)
    mass_error_da: float | None = None
    mass_error_ppm: float | None = None
    matched: bool


class PrecursorIsotopeFitEntry(JsonModel):
    """One run-level isotope-fit assessment for one precursor target."""

    model_config = ConfigDict(extra="forbid")

    run_id: str = Field(..., min_length=1)
    source_path: str = Field(..., min_length=1)
    target_id: str = Field(..., min_length=1)
    precursor_id: str = Field(..., min_length=1)
    peptide_ref: str = Field(..., min_length=1)
    charge: int = Field(..., ge=1)
    chromatographic_peak_id: str | None = None
    apex_spectrum_id: str | None = None
    apex_time_seconds: float | None = Field(default=None, ge=0.0)
    theoretical_monoisotopic_mz: float = Field(..., gt=0.0)
    observed_monoisotopic_mz: float | None = Field(default=None, gt=0.0)
    monoisotopic_mass_error_da: float | None = None
    monoisotopic_mass_error_ppm: float | None = None
    isotope_pattern_score: float = Field(..., ge=0.0, le=1.0)
    charge_consistency_score: float = Field(..., ge=0.0, le=1.0)
    matched_isotope_fraction: float = Field(..., ge=0.0, le=1.0)
    isotope_fit_score: float = Field(..., ge=0.0, le=1.0)
    missing_isotope_indices: tuple[int, ...] = Field(default_factory=tuple)
    concern_codes: tuple[str, ...] = Field(default_factory=tuple)
    isotope_peaks: tuple[PrecursorIsotopePeakObservation, ...] = Field(
        default_factory=tuple
    )


class PrecursorIsotopeFitSummary(JsonModel):
    """Compact summary over one precursor-isotope-fit scoring pass."""

    model_config = ConfigDict(extra="forbid")

    run_count: int = Field(..., ge=0)
    entry_count: int = Field(..., ge=0)
    flagged_entry_count: int = Field(..., ge=0)
    missing_peak_entry_count: int = Field(..., ge=0)
    weak_charge_entry_count: int = Field(..., ge=0)
    weak_pattern_entry_count: int = Field(..., ge=0)


class PrecursorIsotopeFitReport(JsonModel):
    """Stable isotope-fit report over one or more mzML runs and precursor targets."""

    model_config = ConfigDict(extra="forbid")

    run_ids: tuple[str, ...] = Field(default_factory=tuple)
    entries: tuple[PrecursorIsotopeFitEntry, ...] = Field(default_factory=tuple)
    summary: PrecursorIsotopeFitSummary
    note: str = Field(..., min_length=1)


class _RunIsotopeFitContext(JsonModel):
    """Internal grouped run context for isotope-fit scoring."""

    model_config = ConfigDict(extra="forbid")

    run_id: str
    source_path: str
    trace_report: XicTraceReport
    peak_report: ChromatographicPeakPickingReport
    spectra: tuple[SpectrumModel, ...]


def build_precursor_isotope_fit_report(
    run_contexts: tuple[_RunIsotopeFitContext, ...],
    *,
    fit_tolerance_da: float | None = None,
    fit_tolerance_ppm: float | None = None,
    max_isotope_index: int = 2,
    mass_error_limit_ppm: float = _DEFAULT_MASS_ERROR_LIMIT_PPM,
) -> PrecursorIsotopeFitReport:
    """Score precursor isotope-envelope agreement from prepared run contexts."""

    if not run_contexts:
        raise ValueError("precursor isotope fit requires at least one run context")
    if max_isotope_index < 1:
        raise ValueError("max_isotope_index must be at least one")
    tolerance_unit, tolerance_value = _resolve_tolerance(
        tolerance_da=fit_tolerance_da,
        tolerance_ppm=fit_tolerance_ppm,
    )

    entries: list[PrecursorIsotopeFitEntry] = []
    for context in run_contexts:
        peaks_by_target = _peaks_by_target_id(context.peak_report)
        traces_by_target = _trace_points_by_target_id(context.trace_report)
        spectra_by_id = {
            spectrum.spectrum_id: spectrum
            for spectrum in context.spectra
            if spectrum.ms_level == 1 and spectrum.retention_time_seconds is not None
        }
        spectra_by_time = tuple(
            sorted(
                spectra_by_id.values(),
                key=lambda spectrum: (
                    spectrum.retention_time_seconds or 0.0,
                    spectrum.spectrum_id,
                ),
            )
        )

        for target in context.trace_report.accepted_targets:
            peptide_ref = _required_peptide_ref(target)
            charge = _required_charge(target)
            envelope = predict_peptide_isotope_envelope(
                peptide_ref,
                charge=charge,
                max_isotope_index=max_isotope_index,
            )
            selected_peak = _select_peak_for_target(
                peaks_by_target.get(target.target_id, ())
            )
            target_trace_points = traces_by_target.get(target.target_id, ())
            apex_trace_point = _select_apex_trace_point(
                target_trace_points,
                selected_peak=selected_peak,
            )
            apex_spectrum = _resolve_apex_spectrum(
                apex_trace_point=apex_trace_point,
                spectra_by_id=spectra_by_id,
                spectra_by_time=spectra_by_time,
                selected_peak=selected_peak,
            )
            peak_observations = _build_peak_observations(
                envelope.peaks,
                spectrum=apex_spectrum,
                tolerance_unit=tolerance_unit,
                tolerance_value=tolerance_value,
            )
            entry = _build_fit_entry(
                context=context,
                target=target,
                charge=charge,
                peptide_ref=peptide_ref,
                theoretical_monoisotopic_mz=envelope.monoisotopic_mz,
                selected_peak=selected_peak,
                apex_trace_point=apex_trace_point,
                apex_spectrum=apex_spectrum,
                peak_observations=peak_observations,
                mass_error_limit_ppm=mass_error_limit_ppm,
            )
            entries.append(entry)

    sorted_entries = tuple(
        sorted(
            entries,
            key=lambda entry: (entry.run_id, entry.target_id, entry.precursor_id),
        )
    )
    return PrecursorIsotopeFitReport(
        run_ids=tuple(context.run_id for context in run_contexts),
        entries=sorted_entries,
        summary=PrecursorIsotopeFitSummary(
            run_count=len(run_contexts),
            entry_count=len(sorted_entries),
            flagged_entry_count=sum(
                1
                for entry in sorted_entries
                if entry.isotope_fit_score < _DEFAULT_FLAGGED_SCORE_THRESHOLD
                or entry.concern_codes
            ),
            missing_peak_entry_count=sum(
                1 for entry in sorted_entries if "missing_peak" in entry.concern_codes
            ),
            weak_charge_entry_count=sum(
                1
                for entry in sorted_entries
                if "inconsistent_charge_spacing" in entry.concern_codes
            ),
            weak_pattern_entry_count=sum(
                1 for entry in sorted_entries if "weak_isotope_pattern" in entry.concern_codes
            ),
        ),
        note=(
            "precursor isotope-fit scoring compares predicted isotope envelopes against "
            "observed MS1 apex spectra, preserving missing isotope peaks, monoisotopic "
            "mass error, charge-spacing consistency, and one deterministic fit score "
            "per run-level precursor target"
        ),
    )


def extract_mzml_precursor_isotope_fit(
    mzml_paths: tuple[Path, ...],
    targets: Path | XicTargetParseReport | tuple[XicTargetEntry, ...],
    *,
    extraction_tolerance_da: float | None = None,
    extraction_tolerance_ppm: float | None = None,
    fit_tolerance_da: float | None = None,
    fit_tolerance_ppm: float | None = None,
    max_isotope_index: int = 2,
    mass_error_limit_ppm: float = _DEFAULT_MASS_ERROR_LIMIT_PPM,
) -> PrecursorIsotopeFitReport:
    """Extract chromatographic apex spectra and score precursor isotope fit."""

    if not mzml_paths:
        raise ValueError("precursor isotope fit requires at least one mzML file")

    target_report = _coerce_target_report(targets)
    run_contexts = tuple(
        _build_run_context(
            mzml_path,
            target_report,
            extraction_tolerance_da=extraction_tolerance_da,
            extraction_tolerance_ppm=extraction_tolerance_ppm,
        )
        for mzml_path in mzml_paths
    )
    return build_precursor_isotope_fit_report(
        run_contexts,
        fit_tolerance_da=fit_tolerance_da,
        fit_tolerance_ppm=fit_tolerance_ppm,
        max_isotope_index=max_isotope_index,
        mass_error_limit_ppm=mass_error_limit_ppm,
    )


def render_precursor_isotope_fit_summary_tsv(
    report: PrecursorIsotopeFitReport,
) -> str:
    """Render a compact precursor isotope-fit summary TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "run_count",
            "entry_count",
            "flagged_entry_count",
            "missing_peak_entry_count",
            "weak_charge_entry_count",
            "weak_pattern_entry_count",
        )
    )
    writer.writerow(
        (
            report.summary.run_count,
            report.summary.entry_count,
            report.summary.flagged_entry_count,
            report.summary.missing_peak_entry_count,
            report.summary.weak_charge_entry_count,
            report.summary.weak_pattern_entry_count,
        )
    )
    return buffer.getvalue()


def render_precursor_isotope_fit_entries_tsv(
    report: PrecursorIsotopeFitReport,
) -> str:
    """Render one flat precursor isotope-fit ledger."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "run_id",
            "target_id",
            "precursor_id",
            "peptide_ref",
            "charge",
            "apex_spectrum_id",
            "apex_time_seconds",
            "theoretical_monoisotopic_mz",
            "observed_monoisotopic_mz",
            "monoisotopic_mass_error_da",
            "monoisotopic_mass_error_ppm",
            "isotope_pattern_score",
            "charge_consistency_score",
            "matched_isotope_fraction",
            "isotope_fit_score",
            "missing_isotope_indices",
            "concern_codes",
        )
    )
    for entry in report.entries:
        writer.writerow(
            (
                entry.run_id,
                entry.target_id,
                entry.precursor_id,
                entry.peptide_ref,
                entry.charge,
                entry.apex_spectrum_id or "",
                ""
                if entry.apex_time_seconds is None
                else f"{entry.apex_time_seconds:.4f}",
                f"{entry.theoretical_monoisotopic_mz:.6f}",
                ""
                if entry.observed_monoisotopic_mz is None
                else f"{entry.observed_monoisotopic_mz:.6f}",
                ""
                if entry.monoisotopic_mass_error_da is None
                else f"{entry.monoisotopic_mass_error_da:.6f}",
                ""
                if entry.monoisotopic_mass_error_ppm is None
                else f"{entry.monoisotopic_mass_error_ppm:.4f}",
                f"{entry.isotope_pattern_score:.4f}",
                f"{entry.charge_consistency_score:.4f}",
                f"{entry.matched_isotope_fraction:.4f}",
                f"{entry.isotope_fit_score:.4f}",
                "|".join(str(index) for index in entry.missing_isotope_indices),
                "|".join(entry.concern_codes),
            )
        )
    return buffer.getvalue()


def render_precursor_isotope_fit_peaks_tsv(report: PrecursorIsotopeFitReport) -> str:
    """Render one per-isotope peak comparison ledger."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "run_id",
            "target_id",
            "precursor_id",
            "peptide_ref",
            "isotope_index",
            "expected_mz",
            "expected_probability",
            "observed_mz",
            "observed_intensity",
            "mass_error_da",
            "mass_error_ppm",
            "matched",
        )
    )
    for entry in report.entries:
        for peak in entry.isotope_peaks:
            writer.writerow(
                (
                    entry.run_id,
                    entry.target_id,
                    entry.precursor_id,
                    entry.peptide_ref,
                    peak.isotope_index,
                    f"{peak.expected_mz:.6f}",
                    f"{peak.expected_probability:.6f}",
                    "" if peak.observed_mz is None else f"{peak.observed_mz:.6f}",
                    ""
                    if peak.observed_intensity is None
                    else f"{peak.observed_intensity:.4f}",
                    "" if peak.mass_error_da is None else f"{peak.mass_error_da:.6f}",
                    ""
                    if peak.mass_error_ppm is None
                    else f"{peak.mass_error_ppm:.4f}",
                    str(peak.matched).lower(),
                )
            )
    return buffer.getvalue()


def _build_run_context(
    mzml_path: Path,
    target_report: XicTargetParseReport,
    *,
    extraction_tolerance_da: float | None,
    extraction_tolerance_ppm: float | None,
) -> _RunIsotopeFitContext:
    trace_report = extract_mzml_xic_traces(
        mzml_path,
        target_report,
        tolerance_da=extraction_tolerance_da,
        tolerance_ppm=extraction_tolerance_ppm,
        ms_level=1,
    )
    peak_report = extract_mzml_chromatographic_peaks(
        mzml_path,
        target_report,
        tolerance_da=extraction_tolerance_da,
        tolerance_ppm=extraction_tolerance_ppm,
    )
    spectra = parse_mzml(mzml_path).accepted_spectra
    return _RunIsotopeFitContext(
        run_id=Path(trace_report.source_path).stem,
        source_path=trace_report.source_path,
        trace_report=trace_report,
        peak_report=peak_report,
        spectra=spectra,
    )


def _build_fit_entry(
    *,
    context: _RunIsotopeFitContext,
    target: XicTargetEntry,
    charge: int,
    peptide_ref: str,
    theoretical_monoisotopic_mz: float,
    selected_peak: ChromatographicPeak | None,
    apex_trace_point: XicTracePoint | None,
    apex_spectrum: SpectrumModel | None,
    peak_observations: tuple[PrecursorIsotopePeakObservation, ...],
    mass_error_limit_ppm: float,
) -> PrecursorIsotopeFitEntry:
    monoisotopic_peak = next(
        (peak for peak in peak_observations if peak.isotope_index == 0),
        None,
    )
    matched_count = sum(1 for peak in peak_observations if peak.matched)
    matched_isotope_fraction = matched_count / len(peak_observations)
    isotope_pattern_score = _pattern_score(peak_observations)
    charge_consistency_score = _charge_consistency_score(
        peak_observations,
        charge=charge,
        mass_error_limit_ppm=mass_error_limit_ppm,
    )
    mass_error_score = _mass_error_score(
        monoisotopic_peak.mass_error_ppm if monoisotopic_peak is not None else None,
        limit_ppm=mass_error_limit_ppm,
    )
    isotope_fit_score = (
        (0.40 * isotope_pattern_score)
        + (0.25 * mass_error_score)
        + (0.20 * charge_consistency_score)
        + (0.15 * matched_isotope_fraction)
    )

    concern_codes: set[str] = set()
    if selected_peak is None:
        concern_codes.add("missing_peak")
    if apex_spectrum is None:
        concern_codes.add("missing_apex_spectrum")
    if monoisotopic_peak is None or not monoisotopic_peak.matched:
        concern_codes.add("missing_monoisotopic_peak")
    if any(
        peak.isotope_index > 0 and not peak.matched for peak in peak_observations
    ):
        concern_codes.add("missing_isotope_peak")
    if (
        monoisotopic_peak is not None
        and monoisotopic_peak.mass_error_ppm is not None
        and abs(monoisotopic_peak.mass_error_ppm) > mass_error_limit_ppm
    ):
        concern_codes.add("shifted_monoisotopic_mz")
    if charge_consistency_score < _DEFAULT_CHARGE_SCORE_THRESHOLD:
        concern_codes.add("inconsistent_charge_spacing")
    if isotope_pattern_score < _DEFAULT_PATTERN_SCORE_THRESHOLD:
        concern_codes.add("weak_isotope_pattern")

    return PrecursorIsotopeFitEntry(
        run_id=context.run_id,
        source_path=context.source_path,
        target_id=target.target_id,
        precursor_id=target.metadata.get("precursor_id") or target.target_id,
        peptide_ref=peptide_ref,
        charge=charge,
        chromatographic_peak_id=None if selected_peak is None else selected_peak.peak_id,
        apex_spectrum_id=None if apex_spectrum is None else apex_spectrum.spectrum_id,
        apex_time_seconds=(
            apex_trace_point.time_seconds
            if apex_trace_point is not None
            else (
                None
                if selected_peak is None
                else selected_peak.apex_time_seconds
            )
        ),
        theoretical_monoisotopic_mz=theoretical_monoisotopic_mz,
        observed_monoisotopic_mz=(
            None if monoisotopic_peak is None else monoisotopic_peak.observed_mz
        ),
        monoisotopic_mass_error_da=(
            None if monoisotopic_peak is None else monoisotopic_peak.mass_error_da
        ),
        monoisotopic_mass_error_ppm=(
            None if monoisotopic_peak is None else monoisotopic_peak.mass_error_ppm
        ),
        isotope_pattern_score=isotope_pattern_score,
        charge_consistency_score=charge_consistency_score,
        matched_isotope_fraction=matched_isotope_fraction,
        isotope_fit_score=max(0.0, min(1.0, isotope_fit_score)),
        missing_isotope_indices=tuple(
            peak.isotope_index for peak in peak_observations if not peak.matched
        ),
        concern_codes=tuple(sorted(concern_codes)),
        isotope_peaks=peak_observations,
    )


def _build_peak_observations(
    predicted_peaks: tuple[IsotopeEnvelopePeakPrediction, ...],
    *,
    spectrum: SpectrumModel | None,
    tolerance_unit: XicToleranceUnit,
    tolerance_value: float,
) -> tuple[PrecursorIsotopePeakObservation, ...]:
    if spectrum is None:
        return tuple(
            PrecursorIsotopePeakObservation(
                isotope_index=peak.isotope_index,
                expected_mz=peak.mz,
                expected_probability=peak.probability,
                observed_mz=None,
                observed_intensity=None,
                mass_error_da=None,
                mass_error_ppm=None,
                matched=False,
            )
            for peak in predicted_peaks
        )

    remaining_peaks = list(spectrum.peaks)
    observations: list[PrecursorIsotopePeakObservation] = []
    for predicted in predicted_peaks:
        lower_bound, upper_bound = _mz_window(
            predicted.mz,
            tolerance_unit=tolerance_unit,
            tolerance_value=tolerance_value,
        )
        candidates = [
            peak
            for peak in remaining_peaks
            if lower_bound <= peak.mz <= upper_bound
        ]
        if not candidates:
            observations.append(
                PrecursorIsotopePeakObservation(
                    isotope_index=predicted.isotope_index,
                    expected_mz=predicted.mz,
                    expected_probability=predicted.probability,
                    observed_mz=None,
                    observed_intensity=None,
                    mass_error_da=None,
                    mass_error_ppm=None,
                    matched=False,
                )
            )
            continue
        selected_peak = min(
            candidates,
            key=lambda peak: (
                abs(peak.mz - predicted.mz),
                -peak.intensity,
                peak.mz,
            ),
        )
        remaining_peaks.remove(selected_peak)
        mass_error = calculate_precursor_mass_error(
            observed_mz=selected_peak.mz,
            theoretical_mz=predicted.mz,
        )
        observations.append(
            PrecursorIsotopePeakObservation(
                isotope_index=predicted.isotope_index,
                expected_mz=predicted.mz,
                expected_probability=predicted.probability,
                observed_mz=selected_peak.mz,
                observed_intensity=selected_peak.intensity,
                mass_error_da=mass_error.delta_da,
                mass_error_ppm=mass_error.delta_ppm,
                matched=True,
            )
        )
    return tuple(observations)


def _charge_consistency_score(
    peak_observations: tuple[PrecursorIsotopePeakObservation, ...],
    *,
    charge: int,
    mass_error_limit_ppm: float,
) -> float:
    matched = [peak for peak in peak_observations if peak.matched and peak.observed_mz is not None]
    if len(matched) < 2:
        return 0.0
    expected_spacing = _C13_NEUTRON_SHIFT / charge
    spacing_limit_da = max(
        0.01,
        (peak_observations[0].expected_mz * mass_error_limit_ppm) / 1_000_000.0,
    )
    scores: list[float] = []
    for previous, current in zip(matched, matched[1:]):
        isotope_gap = current.isotope_index - previous.isotope_index
        if isotope_gap <= 0:
            continue
        if isotope_gap > 1:
            scores.append(0.0)
            continue
        observed_spacing = (current.observed_mz or 0.0) - (previous.observed_mz or 0.0)
        expected_gap = expected_spacing * isotope_gap
        scores.append(
            _bounded_score(abs(observed_spacing - expected_gap), spacing_limit_da)
        )
    return 0.0 if not scores else sum(scores) / len(scores)


def _pattern_score(
    peak_observations: tuple[PrecursorIsotopePeakObservation, ...],
) -> float:
    expected = [peak.expected_probability for peak in peak_observations]
    observed_intensities = [
        0.0 if peak.observed_intensity is None else peak.observed_intensity
        for peak in peak_observations
    ]
    expected_total = sum(expected)
    observed_total = sum(observed_intensities)
    if expected_total <= 0.0 or observed_total <= 0.0:
        return 0.0
    normalized_expected = [value / expected_total for value in expected]
    normalized_observed = [value / observed_total for value in observed_intensities]
    distance = sum(
        abs(observed_value - expected_value)
        for observed_value, expected_value in zip(
            normalized_observed,
            normalized_expected,
            strict=True,
        )
    )
    return max(0.0, min(1.0, 1.0 - (distance / 2.0)))


def _mass_error_score(mass_error_ppm: float | None, *, limit_ppm: float) -> float:
    if mass_error_ppm is None:
        return 0.0
    return _bounded_score(abs(mass_error_ppm), limit_ppm)


def _bounded_score(delta: float, limit: float) -> float:
    if limit <= 0.0:
        return 0.0
    return max(0.0, min(1.0, 1.0 - (delta / limit)))


def _required_peptide_ref(target: XicTargetEntry) -> str:
    peptide_ref = target.metadata.get("peptide_ref")
    if peptide_ref is None or not peptide_ref.strip():
        raise ValueError(
            f"target {target.target_id!r} requires peptide_ref metadata for isotope fit"
        )
    return peptide_ref.strip()


def _required_charge(target: XicTargetEntry) -> int:
    if target.expected_charge is None:
        raise ValueError(
            f"target {target.target_id!r} requires expected_charge for isotope fit"
        )
    return target.expected_charge


def _trace_points_by_target_id(
    trace_report: XicTraceReport,
) -> dict[str, tuple[XicTracePoint, ...]]:
    grouped: dict[str, list[XicTracePoint]] = {}
    for point in trace_report.trace_points:
        grouped.setdefault(point.target_id, []).append(point)
    return {
        target_id: tuple(
            sorted(points, key=lambda point: (point.time_seconds, point.spectrum_id))
        )
        for target_id, points in grouped.items()
    }


def _peaks_by_target_id(
    peak_report: ChromatographicPeakPickingReport,
) -> dict[str, tuple[ChromatographicPeak, ...]]:
    grouped: dict[str, list[ChromatographicPeak]] = {}
    for peak in peak_report.peaks:
        grouped.setdefault(peak.target_id, []).append(peak)
    return {
        target_id: tuple(
            sorted(
                peaks,
                key=lambda peak: (-peak.area, -peak.height, peak.peak_id),
            )
        )
        for target_id, peaks in grouped.items()
    }


def _select_peak_for_target(
    peaks: tuple[ChromatographicPeak, ...],
) -> ChromatographicPeak | None:
    if not peaks:
        return None
    return max(peaks, key=lambda peak: (peak.area, peak.height, -peak.start_time_seconds))


def _select_apex_trace_point(
    trace_points: tuple[XicTracePoint, ...],
    *,
    selected_peak: ChromatographicPeak | None,
) -> XicTracePoint | None:
    if not trace_points:
        return None
    if selected_peak is None:
        return max(
            trace_points,
            key=lambda point: (point.intensity, -point.time_seconds, point.spectrum_id),
        )
    in_peak = tuple(
        point
        for point in trace_points
        if selected_peak.start_time_seconds
        <= point.time_seconds
        <= selected_peak.end_time_seconds
    )
    candidates = in_peak or trace_points
    return max(
        candidates,
        key=lambda point: (
            point.intensity,
            -abs(point.time_seconds - selected_peak.apex_time_seconds),
            point.spectrum_id,
        ),
    )


def _resolve_apex_spectrum(
    *,
    apex_trace_point: XicTracePoint | None,
    spectra_by_id: dict[str, SpectrumModel],
    spectra_by_time: tuple[SpectrumModel, ...],
    selected_peak: ChromatographicPeak | None,
) -> SpectrumModel | None:
    if apex_trace_point is not None and apex_trace_point.spectrum_id in spectra_by_id:
        return spectra_by_id[apex_trace_point.spectrum_id]
    if selected_peak is None or not spectra_by_time:
        return None
    return min(
        spectra_by_time,
        key=lambda spectrum: (
            abs((spectrum.retention_time_seconds or 0.0) - selected_peak.apex_time_seconds),
            spectrum.spectrum_id,
        ),
    )


def _coerce_target_report(
    targets: Path | XicTargetParseReport | tuple[XicTargetEntry, ...],
) -> XicTargetParseReport:
    return coerce_xic_target_report(targets)


def _resolve_tolerance(
    *,
    tolerance_da: float | None,
    tolerance_ppm: float | None,
) -> tuple[XicToleranceUnit, float]:
    if tolerance_da is not None and tolerance_ppm is not None:
        raise ValueError("provide either tolerance_da or tolerance_ppm, not both")
    if tolerance_da is None and tolerance_ppm is None:
        raise ValueError("one of tolerance_da or tolerance_ppm is required")
    if tolerance_da is not None:
        if tolerance_da <= 0.0:
            raise ValueError("tolerance_da must be greater than zero")
        return XicToleranceUnit.DALTON, tolerance_da
    assert tolerance_ppm is not None
    if tolerance_ppm <= 0.0:
        raise ValueError("tolerance_ppm must be greater than zero")
    return XicToleranceUnit.PPM, tolerance_ppm


def _mz_window(
    target_mz: float,
    *,
    tolerance_unit: XicToleranceUnit,
    tolerance_value: float,
) -> tuple[float, float]:
    half_width = tolerance_value
    if tolerance_unit is XicToleranceUnit.PPM:
        half_width = target_mz * tolerance_value / 1_000_000.0
    return target_mz - half_width, target_mz + half_width

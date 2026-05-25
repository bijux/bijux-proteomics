# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Validate precursor isotope spacing and charge assignment from MS1 windows."""

from __future__ import annotations

import csv
from enum import StrEnum
from io import StringIO

from pydantic import ConfigDict, Field

from bijux_proteomics.io.spectra import SpectrumPeak
from bijux_proteomics_foundation import JsonModel

_C13_NEUTRON_SHIFT = 1.0033548378
_PROTON_MONOISOTOPIC_MASS = 1.007276466812


class PrecursorValidationTier(StrEnum):
    """Stable interpretation tier for one precursor charge validation row."""

    VALIDATED = "validated"
    WEAK = "weak"
    CHARGE_MISMATCH = "charge_mismatch"
    UNSUPPORTED = "unsupported"


class PrecursorValidationWindow(JsonModel):
    """One MS1 peak window around one precursor observation."""

    model_config = ConfigDict(extra="forbid")

    precursor_id: str = Field(..., min_length=1)
    rt: float = Field(..., ge=0.0)
    peaks: tuple[SpectrumPeak, ...] = Field(default_factory=tuple)


class PrecursorValidationQuery(JsonModel):
    """One precursor assignment to validate against an MS1 peak window."""

    model_config = ConfigDict(extra="forbid")

    precursor_id: str = Field(..., min_length=1)
    assigned_mz: float = Field(..., gt=0.0)
    assigned_charge: int = Field(..., ge=1)
    rt: float = Field(..., ge=0.0)
    peptide_mass: float = Field(..., gt=0.0)


class PrecursorValidationEntry(JsonModel):
    """One validated precursor row with inferred charge and isotope evidence."""

    model_config = ConfigDict(extra="forbid")

    precursor_id: str = Field(..., min_length=1)
    assigned_charge: int = Field(..., ge=1)
    inferred_charge: int = Field(..., ge=1)
    isotope_spacing_error: float = Field(..., ge=0.0)
    monoisotope_fit_score: float = Field(..., ge=0.0, le=1.0)
    charge_mismatch: bool
    precursor_validation_tier: PrecursorValidationTier


class PrecursorValidationSummary(JsonModel):
    """Compact summary over one precursor isotope-charge validation pass."""

    model_config = ConfigDict(extra="forbid")

    precursor_count: int = Field(..., ge=0)
    mismatch_count: int = Field(..., ge=0)
    validated_count: int = Field(..., ge=0)
    weak_count: int = Field(..., ge=0)
    unsupported_count: int = Field(..., ge=0)


class PrecursorValidationReport(JsonModel):
    """Stable report over precursor isotope-charge validation rows."""

    model_config = ConfigDict(extra="forbid")

    entries: tuple[PrecursorValidationEntry, ...] = Field(default_factory=tuple)
    summary: PrecursorValidationSummary


class _ChargeCandidate(JsonModel):
    """Internal candidate charge interpretation for one precursor query."""

    model_config = ConfigDict(extra="forbid")

    charge: int = Field(..., ge=1)
    isotope_spacing_error: float = Field(..., ge=0.0)
    spacing_score: float = Field(..., ge=0.0, le=1.0)
    monoisotope_fit_score: float = Field(..., ge=0.0, le=1.0)
    combined_score: float = Field(..., ge=0.0, le=1.0)


def validate_precursor_isotope_charge(
    ms1_windows: tuple[PrecursorValidationWindow, ...],
    precursor_table: tuple[PrecursorValidationQuery, ...],
    *,
    charge_range: tuple[int, int] = (1, 6),
    isotope_tolerance_da: float = 0.02,
    monoisotope_tolerance_ppm: float = 20.0,
    rt_tolerance_seconds: float = 5.0,
    max_isotope_index: int = 2,
) -> PrecursorValidationReport:
    """Validate precursor charge assignments from isotope spacing and peptide mass."""

    if not ms1_windows:
        raise ValueError("ms1_windows must not be empty")
    if not precursor_table:
        raise ValueError("precursor_table must not be empty")
    if isotope_tolerance_da <= 0.0:
        raise ValueError("isotope_tolerance_da must be greater than zero")
    if monoisotope_tolerance_ppm <= 0.0:
        raise ValueError("monoisotope_tolerance_ppm must be greater than zero")
    if rt_tolerance_seconds < 0.0:
        raise ValueError("rt_tolerance_seconds must not be negative")
    if max_isotope_index < 1:
        raise ValueError("max_isotope_index must be at least one")
    minimum_charge, maximum_charge = charge_range
    if minimum_charge < 1 or maximum_charge < minimum_charge:
        raise ValueError("charge_range must start at one and end at or above its start")

    entries = tuple(
        _validate_precursor_query(
            query=query,
            ms1_windows=ms1_windows,
            minimum_charge=minimum_charge,
            maximum_charge=maximum_charge,
            isotope_tolerance_da=isotope_tolerance_da,
            monoisotope_tolerance_ppm=monoisotope_tolerance_ppm,
            rt_tolerance_seconds=rt_tolerance_seconds,
            max_isotope_index=max_isotope_index,
        )
        for query in precursor_table
    )
    return PrecursorValidationReport(
        entries=entries,
        summary=PrecursorValidationSummary(
            precursor_count=len(entries),
            mismatch_count=sum(1 for entry in entries if entry.charge_mismatch),
            validated_count=sum(
                1
                for entry in entries
                if entry.precursor_validation_tier is PrecursorValidationTier.VALIDATED
            ),
            weak_count=sum(
                1
                for entry in entries
                if entry.precursor_validation_tier is PrecursorValidationTier.WEAK
            ),
            unsupported_count=sum(
                1
                for entry in entries
                if entry.precursor_validation_tier is PrecursorValidationTier.UNSUPPORTED
            ),
        ),
    )


def render_precursor_validation_entries_tsv(report: PrecursorValidationReport) -> str:
    """Render one stable TSV row per precursor validation entry."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "precursor_id",
            "assigned_charge",
            "inferred_charge",
            "isotope_spacing_error",
            "monoisotope_fit_score",
            "charge_mismatch",
            "precursor_validation_tier",
        )
    )
    for entry in report.entries:
        writer.writerow(
            (
                entry.precursor_id,
                entry.assigned_charge,
                entry.inferred_charge,
                entry.isotope_spacing_error,
                entry.monoisotope_fit_score,
                str(entry.charge_mismatch).lower(),
                entry.precursor_validation_tier.value,
            )
        )
    return buffer.getvalue()


def render_precursor_validation_summary_tsv(report: PrecursorValidationReport) -> str:
    """Render a compact precursor validation summary TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "precursor_count",
            "mismatch_count",
            "validated_count",
            "weak_count",
            "unsupported_count",
        )
    )
    writer.writerow(
        (
            report.summary.precursor_count,
            report.summary.mismatch_count,
            report.summary.validated_count,
            report.summary.weak_count,
            report.summary.unsupported_count,
        )
    )
    return buffer.getvalue()


def _validate_precursor_query(
    *,
    query: PrecursorValidationQuery,
    ms1_windows: tuple[PrecursorValidationWindow, ...],
    minimum_charge: int,
    maximum_charge: int,
    isotope_tolerance_da: float,
    monoisotope_tolerance_ppm: float,
    rt_tolerance_seconds: float,
    max_isotope_index: int,
) -> PrecursorValidationEntry:
    window = _select_window(
        ms1_windows=ms1_windows,
        precursor_id=query.precursor_id,
        rt=query.rt,
        rt_tolerance_seconds=rt_tolerance_seconds,
    )
    if window is None or not window.peaks:
        return PrecursorValidationEntry(
            precursor_id=query.precursor_id,
            assigned_charge=query.assigned_charge,
            inferred_charge=query.assigned_charge,
            isotope_spacing_error=isotope_tolerance_da * float(max_isotope_index),
            monoisotope_fit_score=0.0,
            charge_mismatch=False,
            precursor_validation_tier=PrecursorValidationTier.UNSUPPORTED,
        )

    observed_monoisotopic_mz = _observed_monoisotopic_mz(
        peaks=window.peaks,
        assigned_mz=query.assigned_mz,
        tolerance_da=isotope_tolerance_da,
    )
    candidates = tuple(
        _score_charge_candidate(
            charge=charge,
            observed_monoisotopic_mz=observed_monoisotopic_mz,
            peaks=window.peaks,
            peptide_mass=query.peptide_mass,
            isotope_tolerance_da=isotope_tolerance_da,
            monoisotope_tolerance_ppm=monoisotope_tolerance_ppm,
            max_isotope_index=max_isotope_index,
        )
        for charge in range(minimum_charge, maximum_charge + 1)
    )
    inferred = max(
        candidates,
        key=lambda candidate: (
            candidate.combined_score,
            candidate.monoisotope_fit_score,
            -candidate.isotope_spacing_error,
            -candidate.charge,
        ),
    )
    assigned_candidate = next(
        candidate for candidate in candidates if candidate.charge == query.assigned_charge
    )
    charge_mismatch = (
        inferred.charge != query.assigned_charge
        and inferred.combined_score >= assigned_candidate.combined_score + 0.15
        and inferred.spacing_score >= 0.5
    )
    tier = _validation_tier(inferred=inferred, charge_mismatch=charge_mismatch)
    return PrecursorValidationEntry(
        precursor_id=query.precursor_id,
        assigned_charge=query.assigned_charge,
        inferred_charge=inferred.charge,
        isotope_spacing_error=inferred.isotope_spacing_error,
        monoisotope_fit_score=inferred.monoisotope_fit_score,
        charge_mismatch=charge_mismatch,
        precursor_validation_tier=tier,
    )


def _select_window(
    *,
    ms1_windows: tuple[PrecursorValidationWindow, ...],
    precursor_id: str,
    rt: float,
    rt_tolerance_seconds: float,
) -> PrecursorValidationWindow | None:
    matching = tuple(window for window in ms1_windows if window.precursor_id == precursor_id)
    if matching:
        return min(
            matching,
            key=lambda window: (abs(window.rt - rt), window.rt, window.precursor_id),
        )
    eligible = tuple(
        window
        for window in ms1_windows
        if abs(window.rt - rt) <= rt_tolerance_seconds
    )
    if not eligible:
        return None
    return min(
        eligible,
        key=lambda window: (abs(window.rt - rt), window.rt, window.precursor_id),
    )


def _observed_monoisotopic_mz(
    *,
    peaks: tuple[SpectrumPeak, ...],
    assigned_mz: float,
    tolerance_da: float,
) -> float:
    nearby = tuple(
        peak
        for peak in peaks
        if abs(peak.mz - assigned_mz) <= tolerance_da
    )
    if nearby:
        return max(nearby, key=lambda peak: (peak.intensity, -abs(peak.mz - assigned_mz))).mz
    return min(
        peaks,
        key=lambda peak: (abs(peak.mz - assigned_mz), -peak.intensity, peak.mz),
    ).mz


def _score_charge_candidate(
    *,
    charge: int,
    observed_monoisotopic_mz: float,
    peaks: tuple[SpectrumPeak, ...],
    peptide_mass: float,
    isotope_tolerance_da: float,
    monoisotope_tolerance_ppm: float,
    max_isotope_index: int,
) -> _ChargeCandidate:
    expected_monoisotopic_mz = _mz_from_neutral_mass(peptide_mass, charge)
    monoisotopic_error_ppm = abs(
        ((observed_monoisotopic_mz - expected_monoisotopic_mz) / expected_monoisotopic_mz)
        * 1_000_000.0
    )
    monoisotope_fit_score = max(
        0.0,
        1.0 - (monoisotopic_error_ppm / monoisotope_tolerance_ppm),
    )
    matched_errors = []
    for isotope_index in range(1, max_isotope_index + 1):
        expected_mz = observed_monoisotopic_mz + ((_C13_NEUTRON_SHIFT * isotope_index) / charge)
        peak = _nearest_peak(peaks=peaks, expected_mz=expected_mz, tolerance_da=isotope_tolerance_da)
        if peak is None:
            continue
        matched_errors.append(abs(peak.mz - expected_mz))
    if matched_errors:
        isotope_spacing_error = sum(matched_errors) / len(matched_errors)
        spacing_score = (
            max(0.0, 1.0 - (isotope_spacing_error / isotope_tolerance_da))
            * (len(matched_errors) / max_isotope_index)
        )
    else:
        isotope_spacing_error = isotope_tolerance_da * float(max_isotope_index)
        spacing_score = 0.0
    combined_score = min(
        1.0,
        (0.6 * spacing_score) + (0.4 * monoisotope_fit_score),
    )
    return _ChargeCandidate(
        charge=charge,
        isotope_spacing_error=isotope_spacing_error,
        spacing_score=spacing_score,
        monoisotope_fit_score=monoisotope_fit_score,
        combined_score=combined_score,
    )


def _nearest_peak(
    *,
    peaks: tuple[SpectrumPeak, ...],
    expected_mz: float,
    tolerance_da: float,
) -> SpectrumPeak | None:
    matches = tuple(
        peak
        for peak in peaks
        if abs(peak.mz - expected_mz) <= tolerance_da
    )
    if not matches:
        return None
    return min(matches, key=lambda peak: (abs(peak.mz - expected_mz), -peak.intensity, peak.mz))


def _mz_from_neutral_mass(neutral_mass: float, charge: int) -> float:
    return (neutral_mass + (charge * _PROTON_MONOISOTOPIC_MASS)) / charge


def _validation_tier(
    *,
    inferred: _ChargeCandidate,
    charge_mismatch: bool,
) -> PrecursorValidationTier:
    if charge_mismatch:
        return PrecursorValidationTier.CHARGE_MISMATCH
    if inferred.combined_score >= 0.8:
        return PrecursorValidationTier.VALIDATED
    if inferred.combined_score >= 0.45:
        return PrecursorValidationTier.WEAK
    return PrecursorValidationTier.UNSUPPORTED

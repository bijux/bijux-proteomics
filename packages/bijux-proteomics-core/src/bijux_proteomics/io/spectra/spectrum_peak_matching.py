# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Spectrum peak matching against theoretical fragment ions."""

from __future__ import annotations

import csv
from enum import StrEnum
from pathlib import Path
from typing import TYPE_CHECKING

from pydantic import ConfigDict, Field

from bijux_proteomics.chemistry import (
    FragmentIon,
    ParsedModifiedPeptide,
    calculate_fragment_ions,
    canonicalize_modified_peptide,
)
from bijux_proteomics.io.raw.noise import SpectrumPeakClass, estimate_peak_noise
from bijux_proteomics_foundation import DocumentSchema, JsonModel

if TYPE_CHECKING:
    from bijux_proteomics.io.spectra import SpectrumModel


class SpectrumPeakMatch(JsonModel):
    """One theoretical fragment matched to one observed peak."""

    model_config = ConfigDict(extra="forbid")

    fragment: FragmentIon
    fragment_label: str = Field(..., min_length=1)
    observed_mz: float = Field(..., gt=0.0)
    observed_intensity: float = Field(..., ge=0.0)
    mass_error_da: float
    mass_error_ppm: float


class UnmatchedSpectrumPeak(JsonModel):
    """One observed peak that remained unmatched after peak matching."""

    model_config = ConfigDict(extra="forbid")

    mz: float = Field(..., gt=0.0)
    intensity: float = Field(..., ge=0.0)


class SpectrumPeakMatchAmbiguityKind(StrEnum):
    """Supported ambiguity warnings for fragment-to-peak matching."""

    PEAK_TO_MULTIPLE_FRAGMENTS = "peak_to_multiple_fragments"
    FRAGMENT_TO_MULTIPLE_PEAKS = "fragment_to_multiple_peaks"


class SpectrumPeakMatchToleranceMode(StrEnum):
    """Supported peak-matching tolerance modes."""

    DA = "da"
    PPM = "ppm"


class SpectrumPeakMatchAmbiguityWarning(JsonModel):
    """One ambiguity warning caused by a permissive matching tolerance."""

    model_config = ConfigDict(extra="forbid")

    kind: SpectrumPeakMatchAmbiguityKind
    fragment_labels: tuple[str, ...] = Field(default_factory=tuple)
    peak_mzs: tuple[float, ...] = Field(default_factory=tuple)
    tolerance_mode: SpectrumPeakMatchToleranceMode
    tolerance_da: float | None = Field(default=None, gt=0.0)
    tolerance_ppm: float | None = Field(default=None, gt=0.0)
    note: str = Field(..., min_length=1)


class SpectrumPeakMatchReport(JsonModel):
    """Stable peak-matching report for one spectrum and peptide."""

    model_config = ConfigDict(extra="forbid")

    document_schema: DocumentSchema
    spectrum_id: str = Field(..., min_length=1)
    peptide: str = Field(..., min_length=1)
    precursor_mz: float = Field(..., gt=0.0)
    precursor_charge: int | None = Field(default=None, ge=1)
    tolerance_mode: SpectrumPeakMatchToleranceMode
    tolerance_da: float | None = Field(default=None, gt=0.0)
    tolerance_ppm: float | None = Field(default=None, gt=0.0)
    matches: tuple[SpectrumPeakMatch, ...] = Field(default_factory=tuple)
    unmatched_peaks: tuple[UnmatchedSpectrumPeak, ...] = Field(default_factory=tuple)
    ambiguity_warnings: tuple[SpectrumPeakMatchAmbiguityWarning, ...] = Field(
        default_factory=tuple
    )
    matched_peak_count: int = Field(..., ge=0)
    unmatched_peak_count: int = Field(..., ge=0)
    explained_intensity: float = Field(..., ge=0.0)
    total_observed_intensity: float = Field(..., ge=0.0)
    explained_intensity_fraction: float = Field(..., ge=0.0, le=1.0)


def _canonical_peptide_text(peptide: str | ParsedModifiedPeptide) -> str:
    if isinstance(peptide, ParsedModifiedPeptide):
        return canonicalize_modified_peptide(peptide)
    return canonicalize_modified_peptide(peptide)


def _fragment_label(fragment: FragmentIon) -> str:
    return f"{fragment.series.value}{fragment.ordinal}+{fragment.charge}"


def _resolve_peak_matching_tolerance(
    *,
    tolerance_da: float | None,
    tolerance_ppm: float | None,
) -> tuple[SpectrumPeakMatchToleranceMode, float | None, float | None]:
    if tolerance_da is not None and tolerance_ppm is not None:
        raise ValueError("choose either tolerance_da or tolerance_ppm, not both")
    if tolerance_ppm is not None:
        if tolerance_ppm <= 0:
            raise ValueError("tolerance_ppm must be greater than zero")
        return SpectrumPeakMatchToleranceMode.PPM, None, tolerance_ppm
    if tolerance_da is None or tolerance_da <= 0:
        raise ValueError("tolerance_da must be greater than zero")
    return SpectrumPeakMatchToleranceMode.DA, tolerance_da, None


def _peak_matches_tolerance(
    *,
    observed_mz: float,
    fragment_mz: float,
    tolerance_mode: SpectrumPeakMatchToleranceMode,
    tolerance_da: float | None,
    tolerance_ppm: float | None,
) -> bool:
    error_da = observed_mz - fragment_mz
    if tolerance_mode is SpectrumPeakMatchToleranceMode.PPM:
        if tolerance_ppm is None:
            raise ValueError("tolerance_ppm must be resolved for ppm peak matching")
        return abs((error_da / fragment_mz) * 1_000_000.0) <= tolerance_ppm
    if tolerance_da is None:
        raise ValueError("tolerance_da must be resolved for dalton peak matching")
    return abs(error_da) <= tolerance_da


def match_spectrum_peaks_to_fragments(
    spectrum: SpectrumModel,
    *,
    peptide: str | ParsedModifiedPeptide,
    theoretical_fragments: tuple[FragmentIon, ...],
    tolerance_da: float | None = 0.5,
    tolerance_ppm: float | None = None,
) -> SpectrumPeakMatchReport:
    """Match one theoretical fragment set against one observed spectrum."""

    canonical = _canonical_peptide_text(peptide)
    tolerance_mode, resolved_tolerance_da, resolved_tolerance_ppm = (
        _resolve_peak_matching_tolerance(
            tolerance_da=tolerance_da,
            tolerance_ppm=tolerance_ppm,
        )
    )
    matches: list[SpectrumPeakMatch] = []
    ambiguity_warnings: list[SpectrumPeakMatchAmbiguityWarning] = []
    matched_peak_indexes: set[int] = set()
    candidate_fragments_by_peak_index: dict[int, list[str]] = {}
    indexed_peaks = tuple(enumerate(spectrum.peaks))
    peak_noise_rows = estimate_peak_noise(spectrum.peaks)
    non_noise_peak_indexes = {
        row.peak_index
        for row in peak_noise_rows
        if row.peak_class is not SpectrumPeakClass.NOISE
    }
    for fragment in theoretical_fragments:
        candidate_peak_indexes = tuple(
            peak_index
            for peak_index, peak in indexed_peaks
            if _peak_matches_tolerance(
                observed_mz=peak.mz,
                fragment_mz=fragment.mz_monoisotopic,
                tolerance_mode=tolerance_mode,
                tolerance_da=resolved_tolerance_da,
                tolerance_ppm=resolved_tolerance_ppm,
            )
        )
        preferred_candidate_peak_indexes = tuple(
            peak_index
            for peak_index in candidate_peak_indexes
            if peak_index in non_noise_peak_indexes
        )
        effective_candidate_peak_indexes = (
            preferred_candidate_peak_indexes if preferred_candidate_peak_indexes else ()
        )
        fragment_label = _fragment_label(fragment)
        if len(effective_candidate_peak_indexes) > 1:
            ambiguity_warnings.append(
                SpectrumPeakMatchAmbiguityWarning(
                    kind=SpectrumPeakMatchAmbiguityKind.FRAGMENT_TO_MULTIPLE_PEAKS,
                    fragment_labels=(fragment_label,),
                    peak_mzs=tuple(
                        sorted(
                            spectrum.peaks[peak_index].mz
                            for peak_index in effective_candidate_peak_indexes
                        )
                    ),
                    tolerance_mode=tolerance_mode,
                    tolerance_da=resolved_tolerance_da,
                    tolerance_ppm=resolved_tolerance_ppm,
                    note="one fragment is compatible with multiple observed peaks under the requested tolerance",
                )
            )
        for peak_index in effective_candidate_peak_indexes:
            candidate_fragments_by_peak_index.setdefault(peak_index, []).append(
                fragment_label
            )
        best_peak_index: int | None = None
        best_error: float | None = None
        for peak_index, peak in indexed_peaks:
            if peak_index not in non_noise_peak_indexes:
                continue
            error = peak.mz - fragment.mz_monoisotopic
            if not _peak_matches_tolerance(
                observed_mz=peak.mz,
                fragment_mz=fragment.mz_monoisotopic,
                tolerance_mode=tolerance_mode,
                tolerance_da=resolved_tolerance_da,
                tolerance_ppm=resolved_tolerance_ppm,
            ):
                continue
            if (
                best_peak_index is None
                or best_error is None
                or abs(error) < abs(best_error)
                or (
                    abs(error) == abs(best_error)
                    and peak.intensity > spectrum.peaks[best_peak_index].intensity
                )
            ):
                best_peak_index = peak_index
                best_error = error
        if best_peak_index is None or best_error is None:
            continue
        best_peak = spectrum.peaks[best_peak_index]
        matched_peak_indexes.add(best_peak_index)
        matches.append(
            SpectrumPeakMatch(
                fragment=fragment,
                fragment_label=fragment_label,
                observed_mz=best_peak.mz,
                observed_intensity=best_peak.intensity,
                mass_error_da=best_error,
                mass_error_ppm=(best_error / fragment.mz_monoisotopic) * 1_000_000.0,
            )
        )
    for peak_index, fragment_labels in sorted(
        candidate_fragments_by_peak_index.items(),
        key=lambda item: (
            spectrum.peaks[item[0]].mz,
            spectrum.peaks[item[0]].intensity,
        ),
    ):
        unique_labels = tuple(sorted(set(fragment_labels)))
        if len(unique_labels) < 2:
            continue
        ambiguity_warnings.append(
            SpectrumPeakMatchAmbiguityWarning(
                kind=SpectrumPeakMatchAmbiguityKind.PEAK_TO_MULTIPLE_FRAGMENTS,
                fragment_labels=unique_labels,
                peak_mzs=(spectrum.peaks[peak_index].mz,),
                tolerance_mode=tolerance_mode,
                tolerance_da=resolved_tolerance_da,
                tolerance_ppm=resolved_tolerance_ppm,
                note="one observed peak is compatible with multiple theoretical fragments under the requested tolerance",
            )
        )
    total_observed_intensity = sum(peak.intensity for peak in spectrum.peaks)
    explained_intensity = sum(
        spectrum.peaks[peak_index].intensity
        for peak_index in sorted(matched_peak_indexes)
    )
    unmatched_peaks = tuple(
        UnmatchedSpectrumPeak(
            mz=peak.mz,
            intensity=peak.intensity,
        )
        for peak_index, peak in indexed_peaks
        if peak_index not in matched_peak_indexes
    )
    schema = DocumentSchema(
        created_by="bijux-proteomics-core",
        document_kind="spectrum_peak_matching_report",
        package_name="bijux-proteomics-core",
        status="generated",
    )
    report = SpectrumPeakMatchReport(
        document_schema=schema,
        spectrum_id=spectrum.spectrum_id,
        peptide=canonical,
        precursor_mz=spectrum.precursor_mz,
        precursor_charge=spectrum.precursor_charge,
        tolerance_mode=tolerance_mode,
        tolerance_da=resolved_tolerance_da,
        tolerance_ppm=resolved_tolerance_ppm,
        matches=tuple(
            sorted(
                matches,
                key=lambda match: (
                    match.fragment.series.value,
                    match.fragment.ordinal,
                    match.fragment.charge,
                    match.observed_mz,
                    match.observed_intensity,
                ),
            )
        ),
        unmatched_peaks=tuple(
            sorted(
                unmatched_peaks,
                key=lambda peak: (peak.mz, peak.intensity),
            )
        ),
        ambiguity_warnings=tuple(
            sorted(
                ambiguity_warnings,
                key=lambda warning: (
                    warning.kind.value,
                    warning.fragment_labels,
                    warning.peak_mzs,
                ),
            )
        ),
        matched_peak_count=len(matched_peak_indexes),
        unmatched_peak_count=len(unmatched_peaks),
        explained_intensity=explained_intensity,
        total_observed_intensity=total_observed_intensity,
        explained_intensity_fraction=(
            explained_intensity / total_observed_intensity
            if total_observed_intensity > 0.0
            else 0.0
        ),
    )
    payload = report.to_dict()
    return report.model_copy(
        update={"document_schema": report.document_schema.with_content_hash(payload)}
    )


def build_spectrum_peak_match_report(
    spectrum: SpectrumModel,
    *,
    peptide: str | ParsedModifiedPeptide,
    tolerance_da: float | None = 0.5,
    tolerance_ppm: float | None = None,
    include_neutral_losses: bool = True,
) -> SpectrumPeakMatchReport:
    """Build one self-contained spectrum peak-matching report from a peptide."""

    theoretical_fragments = calculate_fragment_ions(
        peptide,
        include_neutral_losses=include_neutral_losses,
    )
    return match_spectrum_peaks_to_fragments(
        spectrum,
        peptide=peptide,
        theoretical_fragments=theoretical_fragments,
        tolerance_da=tolerance_da,
        tolerance_ppm=tolerance_ppm,
    )


def export_spectrum_peak_match_tsv(report: SpectrumPeakMatchReport, path: Path) -> None:
    """Write one stable TSV table for matched fragment ions."""

    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t")
        writer.writerow(
            [
                "spectrum_id",
                "peptide",
                "tolerance_mode",
                "series",
                "ordinal",
                "fragment_charge",
                "span_start",
                "span_end",
                "fragment_sequence",
                "fragment_mz",
                "neutral_loss",
                "observed_mz",
                "observed_intensity",
                "mass_error_da",
                "mass_error_ppm",
                "label",
            ]
        )
        for match in report.matches:
            writer.writerow(
                [
                    report.spectrum_id,
                    report.peptide,
                    report.tolerance_mode.value,
                    match.fragment.series.value,
                    match.fragment.ordinal,
                    match.fragment.charge,
                    match.fragment.span_start,
                    match.fragment.span_end,
                    match.fragment.sequence,
                    match.fragment.mz_monoisotopic,
                    (
                        None
                        if match.fragment.neutral_loss is None
                        else match.fragment.neutral_loss
                    ),
                    match.observed_mz,
                    match.observed_intensity,
                    match.mass_error_da,
                    match.mass_error_ppm,
                    match.fragment_label,
                ]
            )


def export_spectrum_unmatched_peak_tsv(
    report: SpectrumPeakMatchReport,
    path: Path,
) -> None:
    """Write one stable TSV table for peaks left unmatched by the report."""

    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t")
        writer.writerow(
            [
                "spectrum_id",
                "peptide",
                "tolerance_mode",
                "mz",
                "intensity",
            ]
        )
        for peak in report.unmatched_peaks:
            writer.writerow(
                [
                    report.spectrum_id,
                    report.peptide,
                    report.tolerance_mode.value,
                    peak.mz,
                    peak.intensity,
                ]
            )

# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Empirical observed-versus-library fragment-intensity agreement."""

from __future__ import annotations

import csv
from enum import StrEnum
from io import StringIO

from pydantic import ConfigDict, Field

from bijux_proteomics.io.spectra import (
    SpectralSimilarityMethod,
    SpectrumModel,
    SpectrumPeak,
    SpectrumSimilarityMode,
    calculate_spectral_similarity,
)
from bijux_proteomics.io.formats.spectral_library import SpectralLibraryEntry
from bijux_proteomics_foundation import JsonModel


class SpectralLibraryIntensityAgreementTier(StrEnum):
    """Agreement tier between one observed spectrum and one library entry."""

    ALIGNED = "aligned"
    PARTIAL = "partial"
    DOWNGRADED = "downgraded"
    INSUFFICIENT_SIGNAL = "insufficient_signal"


class SpectralLibraryIntensityAgreement(JsonModel):
    """One intensity-agreement assessment against a spectral-library entry."""

    model_config = ConfigDict(extra="forbid")

    library_entry_id: str = Field(..., min_length=1)
    cosine_similarity: float = Field(..., ge=0.0, le=1.0)
    ranked_fragment_agreement: float = Field(..., ge=0.0, le=1.0)
    missing_dominant_fragments: tuple[str, ...] = Field(default_factory=tuple)
    intensity_agreement_tier: SpectralLibraryIntensityAgreementTier


def compare_observed_to_library(
    observed_spectrum: SpectrumModel,
    library_spectrum: SpectralLibraryEntry,
    *,
    tolerance_da: float = 0.02,
    dominant_fraction: float = 0.4,
) -> SpectralLibraryIntensityAgreement:
    """Compare one observed spectrum against one library entry's intensity pattern."""

    if tolerance_da <= 0.0:
        raise ValueError("tolerance_da must be greater than zero")
    if not 0.0 < dominant_fraction <= 1.0:
        raise ValueError("dominant_fraction must be within (0.0, 1.0]")

    cosine_similarity = calculate_spectral_similarity(
        library_spectrum.spectrum,
        observed_spectrum,
        tolerance_da=tolerance_da,
        method=SpectralSimilarityMethod.COSINE,
        mode=SpectrumSimilarityMode.NORMALIZED,
    ).score
    matches = _match_library_peaks(
        library_spectrum.spectrum.peaks,
        observed_spectrum.peaks,
        tolerance_da=tolerance_da,
    )
    ranked_fragment_agreement = _ranked_fragment_agreement(matches)
    missing_dominant_fragments = _missing_dominant_fragments(
        library_spectrum.spectrum.peaks,
        matches,
        dominant_fraction=dominant_fraction,
    )
    tier = _classify_intensity_agreement(
        library_peak_count=len(library_spectrum.spectrum.peaks),
        observed_peak_count=len(observed_spectrum.peaks),
        matched_peak_count=len(matches),
        cosine_similarity=cosine_similarity,
        ranked_fragment_agreement=ranked_fragment_agreement,
        missing_dominant_count=len(missing_dominant_fragments),
    )
    return SpectralLibraryIntensityAgreement(
        library_entry_id=library_spectrum.library_entry_id,
        cosine_similarity=cosine_similarity,
        ranked_fragment_agreement=ranked_fragment_agreement,
        missing_dominant_fragments=missing_dominant_fragments,
        intensity_agreement_tier=tier,
    )


def render_spectral_library_intensity_agreement_tsv(
    rows: tuple[SpectralLibraryIntensityAgreement, ...],
) -> str:
    """Render spectral-library intensity-agreement rows as a stable TSV ledger."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "library_entry_id",
            "cosine_similarity",
            "ranked_fragment_agreement",
            "missing_dominant_fragments",
            "intensity_agreement_tier",
        )
    )
    for row in rows:
        writer.writerow(
            (
                row.library_entry_id,
                row.cosine_similarity,
                row.ranked_fragment_agreement,
                ";".join(row.missing_dominant_fragments),
                row.intensity_agreement_tier.value,
            )
        )
    return buffer.getvalue()


class _MatchedFragment(JsonModel):
    model_config = ConfigDict(extra="forbid")

    library_rank: int = Field(..., ge=1)
    library_peak: SpectrumPeak
    observed_peak: SpectrumPeak


def _match_library_peaks(
    library_peaks: tuple[SpectrumPeak, ...],
    observed_peaks: tuple[SpectrumPeak, ...],
    *,
    tolerance_da: float,
) -> tuple[_MatchedFragment, ...]:
    ranked_library = tuple(
        sorted(
            enumerate(library_peaks, start=1),
            key=lambda item: (-item[1].intensity, item[1].mz),
        )
    )
    available_observed = list(enumerate(observed_peaks))
    matches: list[_MatchedFragment] = []
    for library_rank, library_peak in ranked_library:
        best_choice: tuple[int, int, SpectrumPeak, float] | None = None
        for available_index, (observed_index, observed_peak) in enumerate(
            available_observed
        ):
            delta = abs(observed_peak.mz - library_peak.mz)
            if delta > tolerance_da:
                continue
            candidate = (available_index, observed_index, observed_peak, delta)
            if best_choice is None or candidate[3] < best_choice[3] or (
                candidate[3] == best_choice[3]
                and candidate[2].intensity > best_choice[2].intensity
            ):
                best_choice = candidate
        if best_choice is None:
            continue
        available_observed.pop(best_choice[0])
        matches.append(
            _MatchedFragment(
                library_rank=library_rank,
                library_peak=library_peak,
                observed_peak=best_choice[2],
            )
        )
    return tuple(sorted(matches, key=lambda entry: entry.library_rank))


def _ranked_fragment_agreement(matches: tuple[_MatchedFragment, ...]) -> float:
    if len(matches) <= 1:
        return 1.0
    pair_count = 0
    agreement_score = 0.0
    for left_index, left in enumerate(matches[:-1]):
        for right in matches[left_index + 1 :]:
            pair_count += 1
            library_delta = left.library_peak.intensity - right.library_peak.intensity
            observed_delta = left.observed_peak.intensity - right.observed_peak.intensity
            if library_delta == 0.0 and observed_delta == 0.0:
                agreement_score += 1.0
            elif library_delta == 0.0 or observed_delta == 0.0:
                agreement_score += 0.5
            elif library_delta * observed_delta > 0.0:
                agreement_score += 1.0
    return 0.0 if pair_count == 0 else agreement_score / pair_count


def _missing_dominant_fragments(
    library_peaks: tuple[SpectrumPeak, ...],
    matches: tuple[_MatchedFragment, ...],
    *,
    dominant_fraction: float,
) -> tuple[str, ...]:
    if not library_peaks:
        return ()
    base_intensity = max(peak.intensity for peak in library_peaks)
    matched_ranks = {entry.library_rank for entry in matches}
    ranked_library = tuple(
        sorted(
            enumerate(library_peaks, start=1),
            key=lambda item: (-item[1].intensity, item[1].mz),
        )
    )
    dominant = tuple(
        (rank, peak)
        for rank, peak in ranked_library
        if base_intensity > 0.0 and peak.intensity / base_intensity >= dominant_fraction
    )
    if not dominant and ranked_library:
        dominant = ranked_library[:1]
    return tuple(
        f"rank{rank}@{peak.mz:.4f}"
        for rank, peak in dominant
        if rank not in matched_ranks
    )


def _classify_intensity_agreement(
    *,
    library_peak_count: int,
    observed_peak_count: int,
    matched_peak_count: int,
    cosine_similarity: float,
    ranked_fragment_agreement: float,
    missing_dominant_count: int,
) -> SpectralLibraryIntensityAgreementTier:
    if library_peak_count == 0 or observed_peak_count == 0 or matched_peak_count == 0:
        return SpectralLibraryIntensityAgreementTier.INSUFFICIENT_SIGNAL
    if missing_dominant_count > 0 or cosine_similarity < 0.8 or ranked_fragment_agreement < 0.6:
        return SpectralLibraryIntensityAgreementTier.DOWNGRADED
    if cosine_similarity >= 0.95 and ranked_fragment_agreement >= 0.9:
        return SpectralLibraryIntensityAgreementTier.ALIGNED
    return SpectralLibraryIntensityAgreementTier.PARTIAL

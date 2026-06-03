# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""De-isotoping for centroided peak lists."""

from __future__ import annotations

import csv
from io import StringIO
from typing import TYPE_CHECKING

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel

if TYPE_CHECKING:
    from bijux_proteomics.io.spectra import SpectrumPeak

_ISOTOPE_SPACING_DA = 1.0033548378


class DeisotopedPeakCluster(JsonModel):
    """One inferred isotope cluster anchored on a monoisotopic peak."""

    model_config = ConfigDict(extra="forbid")

    monoisotopic_mz: float = Field(..., gt=0.0)
    charge: int = Field(..., ge=1)
    cluster_peak_indices: tuple[int, ...] = Field(default_factory=tuple)
    cluster_intensity: float = Field(..., ge=0.0)
    isotope_count: int = Field(..., ge=1)
    deisotoping_confidence: float = Field(..., ge=0.0, le=1.0)


def deisotope_peaks(
    peaks: tuple[SpectrumPeak, ...],
    charge_range: tuple[int, int] = (1, 4),
    *,
    tolerance_da: float = 0.015,
    min_isotope_count: int = 2,
    max_isotope_count: int = 4,
) -> tuple[DeisotopedPeakCluster, ...]:
    """Infer conservative isotope clusters from a raw peak list."""

    min_charge, max_charge = charge_range
    if min_charge < 1:
        raise ValueError("charge_range lower bound must be at least one")
    if max_charge < min_charge:
        raise ValueError("charge_range upper bound must be at least the lower bound")
    if tolerance_da <= 0.0:
        raise ValueError("tolerance_da must be greater than zero")
    if min_isotope_count < 1:
        raise ValueError("min_isotope_count must be at least one")
    if max_isotope_count < min_isotope_count:
        raise ValueError("max_isotope_count must be at least min_isotope_count")
    if not peaks:
        return ()

    indexed_peaks = tuple(sorted(enumerate(peaks), key=lambda item: item[1].mz))
    candidates: list[DeisotopedPeakCluster] = []
    for sorted_position, (peak_index, peak) in enumerate(indexed_peaks):
        for charge in range(min_charge, max_charge + 1):
            candidate = _candidate_cluster(
                indexed_peaks=indexed_peaks,
                sorted_position=sorted_position,
                peak_index=peak_index,
                monoisotopic_mz=peak.mz,
                monoisotopic_intensity=peak.intensity,
                charge=charge,
                tolerance_da=tolerance_da,
                min_isotope_count=min_isotope_count,
                max_isotope_count=max_isotope_count,
            )
            if candidate is not None:
                candidates.append(candidate)
    if not candidates:
        return ()

    accepted_clusters: list[DeisotopedPeakCluster] = []
    used_peak_indexes: set[int] = set()
    for candidate in sorted(
        candidates,
        key=lambda cluster: (
            -cluster.deisotoping_confidence,
            -cluster.isotope_count,
            -cluster.cluster_intensity,
            cluster.monoisotopic_mz,
        ),
    ):
        cluster_peak_index_set = set(candidate.cluster_peak_indices)
        if cluster_peak_index_set & used_peak_indexes:
            continue
        accepted_clusters.append(candidate)
        used_peak_indexes.update(cluster_peak_index_set)
    return tuple(sorted(accepted_clusters, key=lambda cluster: cluster.monoisotopic_mz))


def render_deisotoped_peaks_tsv(clusters: tuple[DeisotopedPeakCluster, ...]) -> str:
    """Render inferred isotope clusters as a stable TSV ledger."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "monoisotopic_mz",
            "charge",
            "cluster_peak_indices",
            "cluster_intensity",
            "isotope_count",
            "deisotoping_confidence",
        )
    )
    for cluster in clusters:
        writer.writerow(
            (
                cluster.monoisotopic_mz,
                cluster.charge,
                "|".join(str(index) for index in cluster.cluster_peak_indices),
                cluster.cluster_intensity,
                cluster.isotope_count,
                cluster.deisotoping_confidence,
            )
        )
    return buffer.getvalue()


def _candidate_cluster(
    *,
    indexed_peaks: tuple[tuple[int, SpectrumPeak], ...],
    sorted_position: int,
    peak_index: int,
    monoisotopic_mz: float,
    monoisotopic_intensity: float,
    charge: int,
    tolerance_da: float,
    min_isotope_count: int,
    max_isotope_count: int,
) -> DeisotopedPeakCluster | None:
    spacing_da = _ISOTOPE_SPACING_DA / charge
    cluster_peak_indices = [peak_index]
    cluster_intensities = [monoisotopic_intensity]
    spacing_errors: list[float] = []
    last_search_position = sorted_position
    for isotope_number in range(1, max_isotope_count + 1):
        expected_mz = monoisotopic_mz + (spacing_da * isotope_number)
        match = _nearest_peak_within_tolerance(
            indexed_peaks=indexed_peaks,
            start_position=last_search_position + 1,
            expected_mz=expected_mz,
            tolerance_da=tolerance_da,
        )
        if match is None:
            break
        matched_position, matched_peak_index, matched_peak = match
        cluster_peak_indices.append(matched_peak_index)
        cluster_intensities.append(matched_peak.intensity)
        spacing_errors.append(matched_peak.mz - expected_mz)
        last_search_position = matched_position
    isotope_count = len(cluster_peak_indices) - 1
    # Require two isotope satellites so dense random regions do not harden into clusters.
    if isotope_count < min_isotope_count:
        return None
    confidence = _deisotoping_confidence(
        intensities=tuple(cluster_intensities),
        spacing_errors=tuple(spacing_errors),
        tolerance_da=tolerance_da,
        isotope_count=isotope_count,
    )
    return DeisotopedPeakCluster(
        monoisotopic_mz=monoisotopic_mz,
        charge=charge,
        cluster_peak_indices=tuple(cluster_peak_indices),
        cluster_intensity=sum(cluster_intensities),
        isotope_count=isotope_count,
        deisotoping_confidence=confidence,
    )


def _nearest_peak_within_tolerance(
    *,
    indexed_peaks: tuple[tuple[int, SpectrumPeak], ...],
    start_position: int,
    expected_mz: float,
    tolerance_da: float,
) -> tuple[int, int, SpectrumPeak] | None:
    best_match: tuple[int, int, SpectrumPeak] | None = None
    best_error: float | None = None
    for sorted_position in range(start_position, len(indexed_peaks)):
        peak_index, peak = indexed_peaks[sorted_position]
        error = peak.mz - expected_mz
        if error > tolerance_da:
            break
        if abs(error) > tolerance_da:
            continue
        if best_error is None or abs(error) < abs(best_error):
            best_match = (sorted_position, peak_index, peak)
            best_error = error
    return best_match


def _deisotoping_confidence(
    *,
    intensities: tuple[float, ...],
    spacing_errors: tuple[float, ...],
    tolerance_da: float,
    isotope_count: int,
) -> float:
    mean_absolute_error = sum(abs(error) for error in spacing_errors) / len(
        spacing_errors
    )
    spacing_score = max(0.0, 1.0 - (mean_absolute_error / tolerance_da))
    support_score = min(1.0, isotope_count / 3.0)
    intensity_ratio_scores = []
    for left_intensity, right_intensity in zip(
        intensities, intensities[1:], strict=False
    ):
        dominant_intensity = max(left_intensity, right_intensity, 1.0)
        intensity_ratio_scores.append(
            min(left_intensity, right_intensity) / dominant_intensity
        )
    envelope_score = (
        sum(intensity_ratio_scores) / len(intensity_ratio_scores)
        if intensity_ratio_scores
        else 0.0
    )
    confidence = (0.5 * spacing_score) + (0.3 * support_score) + (0.2 * envelope_score)
    return round(confidence, 6)

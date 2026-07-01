# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Spectrum peak processing and precursor-quality support."""

from __future__ import annotations

from bijux_proteomics.chemistry.mass import calculate_peptide_mz
from bijux_proteomics.chemistry.modifications import (
    ModificationRegistryDocument,
    canonicalize_modified_peptide,
)
from bijux_proteomics.io.spectra.spectrum_contracts.collection import (
    _bucket_float,
    _render_tsv,
)
from bijux_proteomics.io.spectra.spectrum_contracts.models import (
    PeakNormalizationPolicy,
    PrecursorIsotopeOffsetAdvisory,
    PrecursorIsotopeOffsetCandidate,
    PrecursorMassError,
    PrecursorMassErrorDistributionRow,
    PrecursorMassErrorObservation,
    PrecursorMassErrorQuery,
    PrecursorMassErrorReport,
    SpectrumFilterReport,
    SpectrumMetrics,
    SpectrumModel,
    SpectrumPeak,
)


def normalize_spectrum_peaks(
    spectrum: SpectrumModel,
    *,
    policy: PeakNormalizationPolicy | None = None,
) -> SpectrumModel:
    """Sort peaks, merge near-duplicate m/z values, and optionally scale intensity."""
    active_policy = policy or PeakNormalizationPolicy()
    merged: list[SpectrumPeak] = []
    for peak in sorted(spectrum.peaks, key=lambda item: (item.mz, item.intensity)):
        if active_policy.drop_zero_intensity and peak.intensity == 0.0:
            continue
        if merged and abs(merged[-1].mz - peak.mz) <= active_policy.merge_tolerance_da:
            previous = merged[-1]
            weighted_mz = (
                (previous.mz * previous.intensity) + (peak.mz * peak.intensity)
            ) / max(previous.intensity + peak.intensity, 1e-12)
            merged[-1] = SpectrumPeak(
                mz=weighted_mz,
                intensity=previous.intensity + peak.intensity,
            )
        else:
            merged.append(peak)
    if active_policy.scale_to_base_peak and merged:
        base_peak = max(merged, key=lambda item: item.intensity)
        if base_peak.intensity > 0.0:
            merged = [
                SpectrumPeak(mz=peak.mz, intensity=peak.intensity / base_peak.intensity)
                for peak in merged
            ]
    return spectrum.model_copy(
        update={"peaks": tuple(sorted(merged, key=lambda item: item.mz))}
    )


def filter_spectrum_peaks(
    spectrum: SpectrumModel,
    *,
    top_n: int | None = None,
    min_relative_intensity: float | None = None,
    mz_min: float | None = None,
    mz_max: float | None = None,
) -> SpectrumFilterReport:
    """Filter peaks by m/z window, relative intensity, and top-N rank."""
    peaks = list(spectrum.peaks)
    removed_by_mz_window = 0
    removed_by_intensity = 0
    removed_by_rank = 0

    if mz_min is not None or mz_max is not None:
        filtered_window: list[SpectrumPeak] = []
        for peak in peaks:
            if mz_min is not None and peak.mz < mz_min:
                removed_by_mz_window += 1
                continue
            if mz_max is not None and peak.mz > mz_max:
                removed_by_mz_window += 1
                continue
            filtered_window.append(peak)
        peaks = filtered_window

    if min_relative_intensity is not None and peaks:
        base_peak_intensity = max(peak.intensity for peak in peaks)
        threshold = base_peak_intensity * min_relative_intensity
        retained: list[SpectrumPeak] = []
        for peak in peaks:
            if peak.intensity < threshold:
                removed_by_intensity += 1
                continue
            retained.append(peak)
        peaks = retained

    if top_n is not None and top_n >= 0 and len(peaks) > top_n:
        ranked = sorted(peaks, key=lambda item: (-item.intensity, item.mz))
        keep_ids = {(peak.mz, peak.intensity) for peak in ranked[:top_n]}
        retained = []
        for peak in peaks:
            if (peak.mz, peak.intensity) in keep_ids:
                retained.append(peak)
                keep_ids.remove((peak.mz, peak.intensity))
            else:
                removed_by_rank += 1
        peaks = retained

    filtered_spectrum = spectrum.model_copy(
        update={"peaks": tuple(sorted(peaks, key=lambda item: item.mz))}
    )
    return SpectrumFilterReport(
        input_peak_count=len(spectrum.peaks),
        output_peak_count=len(filtered_spectrum.peaks),
        removed_by_mz_window=removed_by_mz_window,
        removed_by_intensity=removed_by_intensity,
        removed_by_rank=removed_by_rank,
        spectrum=filtered_spectrum,
    )


def build_spectrum_metrics(spectrum: SpectrumModel) -> SpectrumMetrics:
    """Compute basic TIC and base-peak metrics."""
    if not spectrum.peaks:
        return SpectrumMetrics(
            spectrum_id=spectrum.spectrum_id,
            peak_count=0,
            total_ion_current=0.0,
        )
    base_peak = max(spectrum.peaks, key=lambda peak: (peak.intensity, -peak.mz))
    return SpectrumMetrics(
        spectrum_id=spectrum.spectrum_id,
        peak_count=len(spectrum.peaks),
        total_ion_current=sum(peak.intensity for peak in spectrum.peaks),
        base_peak_mz=base_peak.mz,
        base_peak_intensity=base_peak.intensity,
        mz_min=min(peak.mz for peak in spectrum.peaks),
        mz_max=max(peak.mz for peak in spectrum.peaks),
    )


def calculate_precursor_mass_error(
    *,
    observed_mz: float,
    theoretical_mz: float,
) -> PrecursorMassError:
    """Calculate precursor mass error in Dalton and ppm."""
    delta_da = observed_mz - theoretical_mz
    delta_ppm = (delta_da / theoretical_mz) * 1_000_000.0
    return PrecursorMassError(
        observed_mz=observed_mz,
        theoretical_mz=theoretical_mz,
        delta_da=delta_da,
        delta_ppm=delta_ppm,
    )


def detect_precursor_isotope_offset_advisory(
    *,
    observed_mz: float,
    theoretical_mz: float,
    charge: int,
    max_offset: int = 3,
) -> PrecursorIsotopeOffsetAdvisory:
    """Rank precursor isotope offset candidates without enforcing any correction."""
    isotope_delta = 1.0033548378 / charge
    candidates = tuple(
        PrecursorIsotopeOffsetCandidate(
            isotope_offset=offset,
            expected_mz=theoretical_mz + (isotope_delta * offset),
            delta_da=observed_mz - (theoretical_mz + (isotope_delta * offset)),
            delta_ppm=(
                (observed_mz - (theoretical_mz + (isotope_delta * offset)))
                / (theoretical_mz + (isotope_delta * offset))
            )
            * 1_000_000.0,
        )
        for offset in range(max_offset + 1)
    )
    ranked = tuple(
        sorted(
            candidates,
            key=lambda candidate: (
                abs(candidate.delta_da),
                candidate.isotope_offset,
            ),
        )
    )
    best = ranked[0]
    note = (
        "observed precursor is closest to the monoisotopic assignment"
        if best.isotope_offset == 0
        else f"observed precursor is closest to isotope offset +{best.isotope_offset}"
    )
    return PrecursorIsotopeOffsetAdvisory(
        advisory_only=True,
        recommended_offset=best.isotope_offset,
        candidates=ranked,
        note=note,
    )


def build_precursor_mass_error_report(
    queries: tuple[PrecursorMassErrorQuery, ...],
    *,
    registry: ModificationRegistryDocument | None = None,
    max_isotope_offset: int = 3,
) -> PrecursorMassErrorReport:
    """Build a precursor mass-error report over one set of observations."""
    observations: list[PrecursorMassErrorObservation] = []
    charge_counts: dict[str, int] = {}
    ppm_counts: dict[str, int] = {}
    isotope_counts: dict[str, int] = {}
    delta_ppm_values: list[float] = []
    delta_da_values: list[float] = []
    abs_ppm_values: list[float] = []

    ppm_buckets = (
        ("0-5", 0.0, 5.0),
        ("5-10", 5.0, 10.0),
        ("10-20", 10.0, 20.0),
        ("20-50", 20.0, 50.0),
        ("50+", 50.0, None),
    )

    for query in queries:
        theoretical_mz = calculate_peptide_mz(
            query.peptide,
            charge=query.charge,
            registry=registry,
        )
        error = calculate_precursor_mass_error(
            observed_mz=query.observed_mz,
            theoretical_mz=theoretical_mz,
        )
        advisory = detect_precursor_isotope_offset_advisory(
            observed_mz=query.observed_mz,
            theoretical_mz=theoretical_mz,
            charge=query.charge,
            max_offset=max_isotope_offset,
        )
        observations.append(
            PrecursorMassErrorObservation(
                peptide=query.peptide,
                canonical_peptide=canonicalize_modified_peptide(
                    query.peptide,
                    registry=registry,
                ),
                observed_mz=query.observed_mz,
                theoretical_mz=theoretical_mz,
                charge=query.charge,
                spectrum_id=query.spectrum_id,
                delta_da=error.delta_da,
                delta_ppm=error.delta_ppm,
                absolute_delta_da=abs(error.delta_da),
                absolute_delta_ppm=abs(error.delta_ppm),
                isotope_offset_advisory=advisory,
            )
        )
        charge_key = str(query.charge) if query.charge < 5 else "5+"
        charge_counts[charge_key] = charge_counts.get(charge_key, 0) + 1

        ppm_bucket = _bucket_float(abs(error.delta_ppm), buckets=ppm_buckets)
        ppm_counts[ppm_bucket] = ppm_counts.get(ppm_bucket, 0) + 1

        isotope_key = str(advisory.recommended_offset)
        isotope_counts[isotope_key] = isotope_counts.get(isotope_key, 0) + 1

        delta_ppm_values.append(error.delta_ppm)
        delta_da_values.append(error.delta_da)
        abs_ppm_values.append(abs(error.delta_ppm))

    charge_distribution = tuple(
        PrecursorMassErrorDistributionRow(
            bucket=bucket,
            count=charge_counts.get(bucket, 0),
        )
        for bucket in ("1", "2", "3", "4", "5+")
        if bucket != "5+" or charge_counts.get("5+", 0) > 0
    )
    ppm_distribution = tuple(
        PrecursorMassErrorDistributionRow(
            bucket=label,
            count=ppm_counts.get(label, 0),
        )
        for label, _lower, _upper in ppm_buckets
    )
    isotope_distribution = tuple(
        PrecursorMassErrorDistributionRow(
            bucket=str(offset),
            count=isotope_counts.get(str(offset), 0),
        )
        for offset in range(max_isotope_offset + 1)
    )

    sorted_delta_ppm = sorted(delta_ppm_values)
    sorted_abs_ppm = sorted(abs_ppm_values)

    return PrecursorMassErrorReport(
        observation_count=len(observations),
        charge_distribution=charge_distribution,
        ppm_error_distribution=ppm_distribution,
        isotope_offset_distribution=isotope_distribution,
        mean_delta_ppm=(
            sum(delta_ppm_values) / len(delta_ppm_values) if delta_ppm_values else None
        ),
        mean_delta_da=(
            sum(delta_da_values) / len(delta_da_values) if delta_da_values else None
        ),
        median_delta_ppm=(
            sorted_delta_ppm[len(sorted_delta_ppm) // 2] if sorted_delta_ppm else None
        ),
        median_abs_delta_ppm=(
            sorted_abs_ppm[len(sorted_abs_ppm) // 2] if sorted_abs_ppm else None
        ),
        max_abs_delta_ppm=max(sorted_abs_ppm) if sorted_abs_ppm else None,
        observations=tuple(observations),
    )


def render_precursor_mass_error_summary_tsv(report: PrecursorMassErrorReport) -> str:
    """Render one summary row for a precursor mass-error report."""
    return _render_tsv(
        (
            "observation_count",
            "mean_delta_ppm",
            "mean_delta_da",
            "median_delta_ppm",
            "median_abs_delta_ppm",
            "max_abs_delta_ppm",
        ),
        (
            (
                report.observation_count,
                report.mean_delta_ppm,
                report.mean_delta_da,
                report.median_delta_ppm,
                report.median_abs_delta_ppm,
                report.max_abs_delta_ppm,
            ),
        ),
    )


def render_precursor_mass_error_distribution_tsv(
    rows: tuple[PrecursorMassErrorDistributionRow, ...],
    *,
    distribution_name: str,
) -> str:
    """Render one stable precursor mass-error distribution table."""
    return _render_tsv(
        ("distribution", "bucket", "count"),
        tuple((distribution_name, row.bucket, row.count) for row in rows),
    )


def render_precursor_mass_error_observations_tsv(
    observations: tuple[PrecursorMassErrorObservation, ...],
) -> str:
    """Render per-observation precursor mass-error rows."""
    return _render_tsv(
        (
            "spectrum_id",
            "peptide",
            "canonical_peptide",
            "charge",
            "observed_mz",
            "theoretical_mz",
            "delta_da",
            "delta_ppm",
            "absolute_delta_da",
            "absolute_delta_ppm",
            "recommended_isotope_offset",
        ),
        tuple(
            (
                observation.spectrum_id,
                observation.peptide,
                observation.canonical_peptide,
                observation.charge,
                observation.observed_mz,
                observation.theoretical_mz,
                observation.delta_da,
                observation.delta_ppm,
                observation.absolute_delta_da,
                observation.absolute_delta_ppm,
                observation.isotope_offset_advisory.recommended_offset,
            )
            for observation in observations
        ),
    )

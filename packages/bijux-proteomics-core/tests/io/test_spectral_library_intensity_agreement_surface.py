# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.identification import TargetDecoyLabel
from bijux_proteomics.io.spectra import SpectrumModel, SpectrumPeak
from bijux_proteomics.io.spectral_library import (
    SpectralLibraryEntry,
    SpectralLibraryFormat,
)
from bijux_proteomics.io.spectral_library_intensity_agreement import (
    SpectralLibraryIntensityAgreementTier,
    compare_observed_to_library,
    render_spectral_library_intensity_agreement_tsv,
)


def test_intensity_agreement_keeps_matching_library_pattern_aligned() -> None:
    agreement = compare_observed_to_library(
        _observed_spectrum(
            "observed-aligned",
            ((100.001, 980.0), (150.001, 790.0), (200.001, 610.0), (250.001, 180.0)),
        ),
        _library_entry(
            "library:aligned",
            ((100.0, 1000.0), (150.0, 800.0), (200.0, 600.0), (250.0, 200.0)),
        ),
    )
    rendered = render_spectral_library_intensity_agreement_tsv((agreement,))

    assert agreement.intensity_agreement_tier is SpectralLibraryIntensityAgreementTier.ALIGNED
    assert agreement.cosine_similarity > 0.99
    assert agreement.ranked_fragment_agreement == 1.0
    assert agreement.missing_dominant_fragments == ()
    assert "intensity_agreement_tier" in rendered


def test_intensity_agreement_downgrades_wrong_fragment_pattern_at_same_precursor() -> None:
    agreement = compare_observed_to_library(
        _observed_spectrum(
            "observed-mismatched",
            ((100.001, 220.0), (150.001, 610.0), (200.001, 1000.0), (250.001, 790.0)),
        ),
        _library_entry(
            "library:mismatched",
            ((100.0, 1000.0), (150.0, 800.0), (200.0, 600.0), (250.0, 200.0)),
        ),
    )

    assert agreement.intensity_agreement_tier is SpectralLibraryIntensityAgreementTier.DOWNGRADED
    assert agreement.cosine_similarity < 0.8
    assert agreement.ranked_fragment_agreement < 0.6
    assert agreement.missing_dominant_fragments == ()


def _observed_spectrum(
    spectrum_id: str,
    peaks: tuple[tuple[float, float], ...],
) -> SpectrumModel:
    return SpectrumModel(
        spectrum_id=spectrum_id,
        precursor_mz=500.2,
        precursor_charge=2,
        peaks=tuple(SpectrumPeak(mz=mz, intensity=intensity) for mz, intensity in peaks),
    )


def _library_entry(
    library_entry_id: str,
    peaks: tuple[tuple[float, float], ...],
) -> SpectralLibraryEntry:
    return SpectralLibraryEntry(
        library_entry_id=library_entry_id,
        source_format=SpectralLibraryFormat.MSP,
        spectrum_id=f"{library_entry_id}:spectrum",
        precursor_mz=500.2,
        precursor_charge=2,
        peptide_sequence="PEPTIDE",
        canonical_peptide="PEPTIDE",
        modification_count=0,
        protein_refs=("P11111",),
        target_decoy_label=TargetDecoyLabel.TARGET,
        spectrum=SpectrumModel(
            spectrum_id=f"{library_entry_id}:spectrum",
            precursor_mz=500.2,
            precursor_charge=2,
            peaks=tuple(
                SpectrumPeak(mz=mz, intensity=intensity) for mz, intensity in peaks
            ),
        ),
    )

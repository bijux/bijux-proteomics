# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.io.spectra import (
    SpectralSimilarityMethod,
    SpectrumLibrarySimilarityReport,
    SpectrumModel,
    SpectrumPeak,
    SpectrumSimilarityClassification,
    SpectrumSimilarityMatchingMode,
    SpectrumSimilarityMode,
    build_spectrum_library_similarity_report,
    build_spectrum_similarity_comparison_report,
    calculate_spectral_similarity,
    render_spectrum_similarity_tsv,
)


def _spectrum(
    spectrum_id: str,
    peaks: tuple[tuple[float, float], ...],
    *,
    precursor_mz: float = 500.2,
    precursor_charge: int = 2,
) -> SpectrumModel:
    return SpectrumModel(
        spectrum_id=spectrum_id,
        precursor_mz=precursor_mz,
        precursor_charge=precursor_charge,
        peaks=tuple(SpectrumPeak(mz=mz, intensity=intensity) for mz, intensity in peaks),
    )


def test_similarity_comparison_classifies_duplicate_like_and_similar_examples() -> None:
    duplicate_reference = _spectrum(
        "duplicate-reference",
        ((100.0, 1.0), (150.0, 0.9), (200.0, 0.7)),
    )
    duplicate_query = _spectrum(
        "duplicate-query",
        ((100.01, 1.0), (150.01, 0.9), (200.01, 0.7)),
    )
    noisy_query = _spectrum(
        "noisy-query",
        ((100.01, 1.0), (150.01, 0.9), (200.01, 0.7), (320.0, 0.6)),
    )

    duplicate = build_spectrum_similarity_comparison_report(
        duplicate_reference,
        duplicate_query,
        tolerance_da=0.02,
        method=SpectralSimilarityMethod.COSINE,
        mode=SpectrumSimilarityMode.NORMALIZED,
    )
    similar = build_spectrum_similarity_comparison_report(
        duplicate_reference,
        noisy_query,
        tolerance_da=0.02,
        method=SpectralSimilarityMethod.COSINE,
        mode=SpectrumSimilarityMode.NORMALIZED,
    )

    assert duplicate.classification is SpectrumSimilarityClassification.DUPLICATE_LIKE
    assert duplicate.score > 0.99
    assert duplicate.reference_explained_intensity_fraction == 1.0
    assert similar.classification is SpectrumSimilarityClassification.SIMILAR
    assert 0.7 <= similar.score < duplicate.score
    assert similar.query_explained_intensity_fraction < 1.0
    assert (
        duplicate.document_schema.document_kind == "spectrum_similarity_comparison"
    )


def test_similarity_supports_binning_and_empty_signal_cases() -> None:
    reference = _spectrum(
        "reference",
        ((100.0, 1.0), (150.0, 0.8), (200.0, 0.6)),
    )
    shifted_query = _spectrum(
        "shifted-query",
        ((100.21, 1.0), (150.19, 0.8), (200.18, 0.6)),
    )
    empty_query = _spectrum("empty-query", ())

    tolerance = calculate_spectral_similarity(
        reference,
        shifted_query,
        tolerance_da=0.02,
        method=SpectralSimilarityMethod.COSINE,
        mode=SpectrumSimilarityMode.NORMALIZED,
    )
    binned = calculate_spectral_similarity(
        reference,
        shifted_query,
        bin_width_da=1.0,
        method=SpectralSimilarityMethod.COSINE,
        mode=SpectrumSimilarityMode.NORMALIZED,
    )
    empty = build_spectrum_similarity_comparison_report(
        reference,
        empty_query,
        tolerance_da=0.02,
        method=SpectralSimilarityMethod.COSINE,
        mode=SpectrumSimilarityMode.NORMALIZED,
    )

    assert tolerance.matched_peak_count == 0
    assert tolerance.score == 0.0
    assert binned.matching_mode is SpectrumSimilarityMatchingMode.BINNED
    assert binned.bin_width_da == 1.0
    assert binned.matched_peak_count == 3
    assert binned.score > 0.99
    assert empty.classification is SpectrumSimilarityClassification.INSUFFICIENT_SIGNAL
    assert empty.score == 0.0


def test_library_similarity_report_ranks_best_match_and_renders_tsv() -> None:
    query = _spectrum(
        "query",
        ((100.01, 1.0), (150.01, 0.9), (200.01, 0.7)),
    )
    duplicate_reference = _spectrum(
        "duplicate-reference",
        ((100.0, 1.0), (150.0, 0.9), (200.0, 0.7)),
    )
    similar_reference = _spectrum(
        "similar-reference",
        ((100.0, 1.0), (150.0, 0.8), (200.0, 0.6), (350.0, 0.5)),
    )
    distinct_reference = _spectrum(
        "distinct-reference",
        ((400.0, 1.0), (450.0, 0.8), (500.0, 0.6)),
    )

    report = build_spectrum_library_similarity_report(
        query,
        (similar_reference, distinct_reference, duplicate_reference),
        tolerance_da=0.02,
        method=SpectralSimilarityMethod.COSINE,
        mode=SpectrumSimilarityMode.NORMALIZED,
        max_matches=3,
    )
    tsv = render_spectrum_similarity_tsv(report)

    assert isinstance(report, SpectrumLibrarySimilarityReport)
    assert report.matches[0].reference_spectrum_id == "duplicate-reference"
    assert report.matches[0].classification is SpectrumSimilarityClassification.DUPLICATE_LIKE
    assert report.matches[1].reference_spectrum_id == "similar-reference"
    assert report.matches[2].classification is SpectrumSimilarityClassification.DISTINCT
    assert report.duplicate_like_match_count == 1
    assert report.similar_match_count == 2
    assert "reference_spectrum_id" in tsv
    assert "duplicate-reference" in tsv

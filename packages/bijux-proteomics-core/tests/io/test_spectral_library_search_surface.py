# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.io.spectra import (
    SpectralSimilarityMethod,
    SpectrumModel,
    SpectrumPeak,
    parse_mgf,
)
from bijux_proteomics.io.spectral_library import (
    SpectralLibrarySearchStrategy,
    build_spectral_library_index,
    build_spectral_library_summary,
    import_spectral_library,
    render_spectral_library_search_tsv,
    search_spectral_library,
)


def _format_fixture(name: str) -> Path:
    return Path(__file__).resolve().parents[1] / "fixtures" / "formats" / name


def _query_spectrum() -> SpectrumModel:
    return SpectrumModel(
        spectrum_id="review-query",
        precursor_mz=500.205,
        precursor_charge=2,
        peaks=(
            SpectrumPeak(mz=100.01, intensity=1500.0),
            SpectrumPeak(mz=150.01, intensity=1300.0),
            SpectrumPeak(mz=200.01, intensity=900.0),
        ),
    )


def test_spectral_library_search_ranks_target_match_and_scores_decoy_competition() -> (
    None
):
    report = import_spectral_library(_format_fixture("library_search_reference.msp"))
    summary = build_spectral_library_summary(report)
    index = build_spectral_library_index(report.entries)
    query = parse_mgf(_format_fixture("library_search_query.mgf")).accepted_spectra[0]

    search_report = search_spectral_library(
        query,
        index,
        precursor_tolerance_da=0.03,
        similarity_tolerance_da=0.02,
        method=SpectralSimilarityMethod.COSINE,
        max_matches=3,
    )
    rendered = render_spectral_library_search_tsv(search_report)

    assert summary.decoy_entry_count == 1
    assert report.entries[1].target_decoy_label.value == "decoy"
    assert search_report.search_strategy is SpectralLibrarySearchStrategy.CONCATENATED
    assert search_report.candidate_count == 3
    assert search_report.decoy_candidate_count == 1
    assert search_report.top_match_library_entry_id == "msp:1:PEPTIDE/2"
    assert search_report.top_match_canonical_peptide == "PEPTIDE"
    assert search_report.top_match_similarity_score is not None
    assert search_report.top_match_similarity_score > 0.99
    assert search_report.top_match_q_value == 0.0
    assert search_report.advisory_warning is None
    assert search_report.matches[0].target_decoy_label.value == "target"
    assert search_report.matches[1].target_decoy_label.value == "decoy"
    assert search_report.matches[1].q_value is not None
    assert search_report.matches[2].similarity_classification.value == "distinct"
    assert "search_strategy\tadvisory_warning\trank" in rendered
    assert "target_decoy_label" in rendered
    assert "msp:1:PEPTIDE/2" in rendered


def test_spectral_library_search_reports_no_decoy_advisory_without_decoy_entries() -> (
    None
):
    report = import_spectral_library(_format_fixture("review_library.msp"))
    index = build_spectral_library_index(report.entries)

    search_report = search_spectral_library(
        _query_spectrum(),
        index,
        precursor_tolerance_da=10.0,
        similarity_tolerance_da=0.02,
        method=SpectralSimilarityMethod.COSINE,
        max_matches=1,
    )

    assert (
        search_report.search_strategy is SpectralLibrarySearchStrategy.NO_DECOY_ADVISORY
    )
    assert search_report.candidate_count == 2
    assert len(search_report.matches) == 1
    assert search_report.decoy_candidate_count == 0
    assert search_report.top_match_canonical_peptide == "PEPTIDE"
    assert search_report.top_match_q_value is None
    assert search_report.advisory_warning == (
        "library search ran without decoy entries; q-values are withheld and this report is advisory only"
    )
    assert all(match.q_value is None for match in search_report.matches)
    rendered = render_spectral_library_search_tsv(search_report)
    assert "no_decoy_advisory\tlibrary search ran without decoy entries;" in rendered

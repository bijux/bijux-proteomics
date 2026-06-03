# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.io.spectral_library import (
    SpectralLibraryFormat,
    build_spectral_library_index,
    build_spectral_library_summary,
    find_spectral_library_candidates,
    import_spectral_library,
    render_spectral_library_candidates_tsv,
    render_spectral_library_summary_tsv,
)


def _format_fixture(name: str) -> Path:
    return Path(__file__).resolve().parents[1] / "fixtures" / "formats" / name


def test_import_msp_spectral_library_reads_peptides_modifications_and_peaks() -> None:
    report = import_spectral_library(_format_fixture("review_library.msp"))
    summary = build_spectral_library_summary(report)

    assert report.source_format is SpectralLibraryFormat.MSP
    assert report.accepted_entry_count == 2
    assert report.rejected_entry_count == 0
    assert report.entries[0].peptide_sequence == "PEPTIDE"
    assert report.entries[0].precursor_charge == 2
    assert report.entries[0].protein_refs == ("P11111",)
    assert report.entries[1].canonical_peptide == "PEPM[Oxidation]TIDE"
    assert report.entries[1].modification_count == 1
    assert report.entries[1].protein_refs == ("P22222",)
    assert len(report.entries[1].spectrum.peaks) == 2
    assert summary.entry_count == 2
    assert summary.modified_entry_count == 1


def test_import_mgf_spectral_library_indexes_precursor_and_peptide_candidates() -> None:
    report = import_spectral_library(_format_fixture("review_library.mgf"))
    index = build_spectral_library_index(report.entries)
    candidates = find_spectral_library_candidates(
        index,
        precursor_mz=508.18,
        tolerance_da=0.05,
        peptide_query="PEPM[Oxidation]TIDE",
    )
    summary_tsv = render_spectral_library_summary_tsv(
        build_spectral_library_summary(report)
    )
    candidates_tsv = render_spectral_library_candidates_tsv(candidates)

    assert report.source_format is SpectralLibraryFormat.MGF
    assert report.accepted_entry_count == 2
    assert index.peptide_index["PEPTIDE"] == (
        "mgf:1:SEQ=PEPTIDE|PEPTIDE=PEPTIDE|PROTEINS=P11111",
    )
    assert report.entries[0].protein_refs == ("P11111",)
    assert candidates.candidate_count == 1
    assert candidates.matches[0].canonical_peptide == "PEPM[Oxidation]TIDE"
    assert candidates.matches[0].precursor_delta_da <= 0.05
    assert "entry_count" in summary_tsv
    assert "canonical_peptide" in candidates_tsv


def test_candidate_lookup_without_peptide_query_returns_precursor_neighbors() -> None:
    report = import_spectral_library(_format_fixture("review_library.msp"))
    index = build_spectral_library_index(report.entries)
    candidates = find_spectral_library_candidates(
        index,
        precursor_mz=504.0,
        tolerance_da=5.0,
    )

    assert candidates.candidate_count == 2
    assert (
        candidates.matches[0].precursor_delta_da
        <= candidates.matches[1].precursor_delta_da
    )

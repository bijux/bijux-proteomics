# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.io.mzml_reader import (
    build_mzml_collection_summary,
    build_mzml_practical_review_report,
    extract_mzml_chromatograms,
    inspect_mzml_decoding_support,
    parse_mzml,
    stream_mzml_spectra,
)


def _format_fixture(name: str) -> Path:
    return Path(__file__).resolve().parents[1] / "fixtures" / "formats" / name


def test_mzml_reader_parses_uncompressed_arrays_through_owner_surface() -> None:
    report = parse_mzml(_format_fixture("simple.mzml"))
    streamed = tuple(stream_mzml_spectra(_format_fixture("simple.mzml")))
    summary = build_mzml_collection_summary(report)

    assert report.metadata.run_id == "RUN_001"
    assert len(report.accepted_spectra) == 2
    assert streamed[0].spectrum_id == "scan=5001"
    assert streamed[1].precursor_charge == 3
    assert summary.spectrum_count == 2
    assert summary.issue_counts == {}


def test_mzml_reader_parses_compressed_spectra_and_uncompressed_chromatograms() -> None:
    report = parse_mzml(_format_fixture("practical_review.mzml"))
    chromatograms = extract_mzml_chromatograms(_format_fixture("practical_review.mzml"))
    decoding = inspect_mzml_decoding_support(_format_fixture("practical_review.mzml"))
    review = build_mzml_practical_review_report(
        _format_fixture("practical_review.mzml")
    )

    assert len(report.accepted_spectra) == 2
    assert report.accepted_spectra[0].peaks[0].mz == 100.0
    assert report.accepted_spectra[1].precursor_charge == 3
    assert decoding.supported is True
    assert "MS:1000574" in decoding.compression_accessions
    assert chromatograms.total_chromatograms == 2
    assert {trace.kind for trace in chromatograms.accepted_traces} == {"tic", "bpc"}
    assert review.chromatograms.accepted_traces[0].points[1].time_seconds == 30.0

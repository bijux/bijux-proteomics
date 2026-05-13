# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.io.formats import extract_mzml_chromatograms, parse_mzml
from bijux_proteomics.io.ingestion import (
    build_mzml_practical_review_report,
    inspect_mzml_decoding_support,
)


def _format_fixture(name: str) -> Path:
    return Path(__file__).resolve().parents[1] / "fixtures" / "formats" / name


def test_practical_mzml_fixture_preserves_ms1_ms2_and_precursor_context() -> None:
    report = parse_mzml(_format_fixture("practical_review.mzml"))

    assert report.total_spectra == 2
    assert len(report.accepted_spectra) == 2
    assert report.accepted_spectra[0].ms_level == 1
    assert report.accepted_spectra[0].retention_time_seconds == 60.0
    assert report.accepted_spectra[0].precursor_mz == 445.3
    assert report.accepted_spectra[0].precursor_intensity == 120000.0
    assert report.accepted_spectra[0].peaks[0].mz == 100.0
    assert report.accepted_spectra[1].ms_level == 2
    assert report.accepted_spectra[1].parent_spectrum_id == "scan=6000"
    assert report.accepted_spectra[1].precursor_charge == 3
    assert report.accepted_spectra[1].precursor_intensity == 45000.0
    assert report.accepted_spectra[1].peaks[-1].intensity == 50.0


def test_practical_mzml_review_reports_decoding_and_chromatograms() -> None:
    chromatograms = extract_mzml_chromatograms(_format_fixture("practical_review.mzml"))
    decoding = inspect_mzml_decoding_support(_format_fixture("practical_review.mzml"))
    review = build_mzml_practical_review_report(_format_fixture("practical_review.mzml"))

    assert chromatograms.total_chromatograms == 2
    assert len(chromatograms.accepted_traces) == 2
    assert {trace.kind for trace in chromatograms.accepted_traces} == {"tic", "bpc"}
    assert chromatograms.accepted_traces[0].point_count == 3
    assert chromatograms.accepted_traces[0].points[1].time_seconds == 30.0
    assert decoding.supported is True
    assert decoding.accepted_spectrum_count == 2
    assert review.metadata.run_id == "RUN_PRACTICAL_01"
    assert review.summary["spectrum_count"] == 2
    assert review.chromatograms.total_chromatograms == 2

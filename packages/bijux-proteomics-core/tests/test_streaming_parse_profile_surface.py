# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.io.ingestion import (
    build_streaming_parse_profile,
    stream_mgf_spectra,
)


def _format_fixture(name: str) -> Path:
    return Path(__file__).parent / "fixtures" / "formats" / name


def _spectra_fixture(name: str) -> Path:
    return Path(__file__).parent / "fixtures" / "spectra" / name


def test_stream_mgf_spectra_parses_without_full_table_contracts() -> None:
    spectra = stream_mgf_spectra(_spectra_fixture("simple.mgf"))

    assert len(spectra) >= 1
    assert spectra[0].spectrum_id
    assert spectra[0].peaks


def test_build_streaming_parse_profile_reports_chunking_for_mgf_and_mzml() -> None:
    mgf = build_streaming_parse_profile(
        _spectra_fixture("multi.mgf"),
        format_name="mgf",
        chunk_size=2,
    )
    mzml = build_streaming_parse_profile(
        _format_fixture("simple.mzml"),
        format_name="mzml",
        chunk_size=1,
    )

    assert mgf.spectrum_count >= 2
    assert mgf.chunk_count >= 1
    assert mzml.spectrum_count == 2
    assert mzml.chunk_count == 2

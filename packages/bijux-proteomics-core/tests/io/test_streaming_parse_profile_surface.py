# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.io.ingestion import (
    build_streaming_parse_profile,
    stream_mgf_spectra,
)


def _format_fixture(name: str) -> Path:
    return Path(__file__).resolve().parents[1] / "fixtures" / "formats" / name


def _spectra_fixture(name: str) -> Path:
    return Path(__file__).resolve().parents[1] / "fixtures" / "spectra" / name


def test_stream_mgf_spectra_parses_without_full_table_contracts() -> None:
    spectra = tuple(stream_mgf_spectra(_spectra_fixture("simple.mgf")))

    assert len(spectra) >= 1
    assert spectra[0].spectrum_id
    assert spectra[0].peaks
    assert spectra[0].retention_time_seconds == 123.4


def test_stream_mgf_spectra_avoids_full_file_read_text(monkeypatch) -> None:
    fixture = _spectra_fixture("simple.mgf")
    original_read_text = Path.read_text

    def _forbid_read_text(self: Path, *args: object, **kwargs: object) -> str:
        if self == fixture:
            raise AssertionError("stream_mgf_spectra should not use Path.read_text")
        return original_read_text(self, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", _forbid_read_text)

    spectra = tuple(stream_mgf_spectra(fixture))

    assert len(spectra) == 1
    assert spectra[0].spectrum_id == "scan=5001"


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


def test_build_streaming_parse_profile_counts_large_generated_mgf(
    tmp_path: Path,
) -> None:
    path = tmp_path / "large_profile_input.mgf"
    with path.open("w", encoding="utf-8") as handle:
        for index in range(1, 1201):
            handle.write("BEGIN IONS\n")
            handle.write(f"SCANS=scan={index}\n")
            handle.write(f"PEPMASS={400.0 + index / 1000.0:.4f}\n")
            handle.write("CHARGE=2+\n")
            handle.write(f"RTINSECONDS={10.0 + index:.2f}\n")
            handle.write("100.0 10.0\n")
            handle.write("200.0 20.0\n")
            handle.write("END IONS\n")

    profile = build_streaming_parse_profile(path, format_name="mgf", chunk_size=128)

    assert profile.spectrum_count == 1200
    assert profile.chunk_count == 10
    assert profile.first_spectrum_id == "scan=1"
    assert profile.last_spectrum_id == "scan=1200"

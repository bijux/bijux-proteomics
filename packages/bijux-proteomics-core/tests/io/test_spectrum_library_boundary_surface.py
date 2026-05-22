# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from pytest import MonkeyPatch

from bijux_proteomics.io.ingestion import (
    evaluate_spectrum_library_boundary,
)


def _format_fixture(name: str) -> Path:
    return Path(__file__).resolve().parents[1] / "fixtures" / "formats" / name


def test_evaluate_spectrum_library_boundary_supports_msp_parse_mode() -> None:
    report = evaluate_spectrum_library_boundary(_format_fixture("review_library.msp"))

    assert report.format_name == "MSP"
    assert report.supported is True
    assert report.support_mode == "importable"
    assert report.entry_count == 2


def test_evaluate_spectrum_library_boundary_supports_mgf_import_mode() -> None:
    report = evaluate_spectrum_library_boundary(_format_fixture("review_library.mgf"))

    assert report.format_name == "MGF"
    assert report.supported is True
    assert report.support_mode == "importable"
    assert report.entry_count == 2


def test_evaluate_spectrum_library_boundary_counts_mgf_without_read_text(
    monkeypatch: MonkeyPatch,
) -> None:
    fixture = _format_fixture("review_library.mgf")
    original_read_text = Path.read_text

    def _forbid_read_text(
        self: Path,
        encoding: str | None = None,
        errors: str | None = None,
    ) -> str:
        if self == fixture:
            raise AssertionError(
                "evaluate_spectrum_library_boundary should not use Path.read_text for mgf"
            )
        return original_read_text(self, encoding=encoding, errors=errors)

    monkeypatch.setattr(Path, "read_text", _forbid_read_text)

    report = evaluate_spectrum_library_boundary(fixture)

    assert report.format_name == "MGF"
    assert report.entry_count == 2


def test_evaluate_spectrum_library_boundary_refuses_unimplemented_formats() -> None:
    report = evaluate_spectrum_library_boundary(
        _format_fixture("unsupported_library.sptxt")
    )

    assert report.supported is False
    assert "not yet implemented" in report.diagnostics[0]

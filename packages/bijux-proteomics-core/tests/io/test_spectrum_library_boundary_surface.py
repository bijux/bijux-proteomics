# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.io.ingestion import (
    evaluate_spectrum_library_boundary,
)


def _format_fixture(name: str) -> Path:
    return Path(__file__).resolve().parents[1] / "fixtures" / "formats" / name


def test_evaluate_spectrum_library_boundary_supports_msp_parse_mode() -> None:
    report = evaluate_spectrum_library_boundary(_format_fixture("simple.msp"))

    assert report.format_name == "MSP"
    assert report.supported is True
    assert report.support_mode == "parse_only"
    assert report.entry_count == 2


def test_evaluate_spectrum_library_boundary_refuses_unimplemented_formats() -> None:
    report = evaluate_spectrum_library_boundary(
        _format_fixture("unsupported_library.sptxt")
    )

    assert report.supported is False
    assert "not yet implemented" in report.diagnostics[0]

# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.io.ingestion import parse_mzidentml_or_refuse


def _format_fixture(name: str) -> Path:
    return Path(__file__).resolve().parents[1] / "fixtures" / "formats" / name


def test_parse_mzidentml_or_refuse_parses_supported_core_identification_surface() -> (
    None
):
    report = parse_mzidentml_or_refuse(_format_fixture("simple.mzid"))

    assert report.supported is True
    assert report.spectrum_identification_result_count == 2
    assert report.spectrum_identification_item_count == 2


def test_parse_mzidentml_or_refuse_returns_precise_refusal_for_missing_results() -> (
    None
):
    report = parse_mzidentml_or_refuse(_format_fixture("invalid_missing_results.mzid"))

    assert report.supported is False
    assert report.spectrum_identification_result_count == 0
    assert "missing SpectrumIdentificationResult entries" in report.diagnostics[0]

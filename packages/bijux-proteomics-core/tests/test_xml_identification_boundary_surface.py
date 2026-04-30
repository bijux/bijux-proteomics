# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.advanced_format_ingestion import (
    evaluate_pepxml_idxml_boundary,
)


def _format_fixture(name: str) -> Path:
    return Path(__file__).parent / "fixtures" / "formats" / name


def test_evaluate_pepxml_idxml_boundary_detects_pepxml_and_requires_conversion() -> (
    None
):
    report = evaluate_pepxml_idxml_boundary(_format_fixture("simple.pepxml"))

    assert report.detected_format == "pepXML"
    assert report.supported is False
    assert report.record_count == 2
    assert "convert pepXML" in (report.required_conversion or "")


def test_evaluate_pepxml_idxml_boundary_detects_idxml_and_requires_conversion() -> (
    None
):
    report = evaluate_pepxml_idxml_boundary(_format_fixture("simple.idxml"))

    assert report.detected_format == "idXML"
    assert report.supported is False
    assert report.record_count == 2
    assert "convert idXML" in (report.required_conversion or "")

# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.advanced_format_ingestion import (
    build_format_capability_matrix_from_fixtures,
)


def _fixtures_dir() -> Path:
    return Path(__file__).parent / "fixtures" / "formats"


def test_build_format_capability_matrix_from_fixtures_reports_expected_states() -> None:
    report = build_format_capability_matrix_from_fixtures(_fixtures_dir())
    states = {entry.format_name: entry.state for entry in report.entries}

    assert states["mzml"] == "parse_and_normalize"
    assert states["mzid"] == "parse_only"
    assert states["mztab"] == "parse_only"
    assert states["pepxml"] == "unsupported_with_conversion"
    assert states["idxml"] == "unsupported_with_conversion"
    assert states["msp"] == "parse_only"

# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.advanced_format_ingestion import parse_mztab_or_refuse


def _format_fixture(name: str) -> Path:
    return Path(__file__).parent / "fixtures" / "formats" / name


def test_parse_mztab_or_refuse_reports_section_counts_and_field_coverage() -> None:
    report = parse_mztab_or_refuse(_format_fixture("simple.mztab"))

    assert report.supported is True
    assert report.variant == "P"
    assert report.row_counts["PSM"] == 2
    assert "sequence" in report.mapped_fields
    assert "opt_global_confidence" in report.unsupported_fields


def test_parse_mztab_or_refuse_refuses_metadata_only_tables() -> None:
    report = parse_mztab_or_refuse(_format_fixture("invalid_missing_sections.mztab"))

    assert report.supported is False
    assert "lacks PSM/PEP/PRT data sections" in report.diagnostics[0]

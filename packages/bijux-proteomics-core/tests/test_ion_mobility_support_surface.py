# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.io.ingestion import extract_ion_mobility_support


def _format_fixture(name: str) -> Path:
    return Path(__file__).parent / "fixtures" / "formats" / name


def test_extract_ion_mobility_support_reports_mobility_fields_with_units() -> None:
    report = extract_ion_mobility_support(_format_fixture("ion_mobility.mzml"))

    assert report.supported is True
    assert report.total_spectra == 1
    assert report.observed_count == 1
    assert report.observations[0].accession == "MS:1002476"
    assert report.observations[0].unit_name == "millisecond"


def test_extract_ion_mobility_support_reports_absence_for_standard_fixture() -> None:
    report = extract_ion_mobility_support(_format_fixture("simple.mzml"))

    assert report.supported is False
    assert report.observed_count == 0

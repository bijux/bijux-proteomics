# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.advanced_format_ingestion import inspect_mzml_decoding_support


def _format_fixture(name: str) -> Path:
    return Path(__file__).parent / "fixtures" / "formats" / name


def test_inspect_mzml_decoding_support_reports_supported_simple_fixture() -> None:
    report = inspect_mzml_decoding_support(_format_fixture("simple.mzml"))

    assert report.supported is True
    assert report.accepted_spectrum_count == 2
    assert "MS:1000576" in report.compression_accessions
    assert "MS:1000523" in report.precision_accessions


def test_inspect_mzml_decoding_support_reports_unsupported_numpress_precision() -> None:
    numpress = inspect_mzml_decoding_support(_format_fixture("unsupported_numpress.mzml"))
    integer = inspect_mzml_decoding_support(
        _format_fixture("unsupported_integer_precision.mzml")
    )

    assert numpress.supported is False
    assert integer.supported is False
    assert numpress.rejected_spectrum_count >= 1
    assert integer.rejected_spectrum_count >= 1

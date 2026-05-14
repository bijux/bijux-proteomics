# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.io.ingestion import (
    RawSpectraDialectRealityState,
    build_raw_spectra_dialect_reality_report,
)


def _format_fixture(name: str) -> Path:
    return Path(__file__).resolve().parents[1] / "fixtures" / "formats" / name


def test_build_raw_spectra_dialect_reality_report_keeps_vendor_boundaries_explicit() -> (
    None
):
    report = build_raw_spectra_dialect_reality_report(
        (
            _format_fixture("simple.mzml"),
            _format_fixture("unsupported_numpress.mzml"),
            _format_fixture("unsupported_vendor.raw"),
            Path(__file__).resolve().parents[1] / "fixtures" / "spectra" / "simple.mgf",
        )
    )

    states = {entry.input_name: entry.support_state for entry in report.entries}

    assert states["simple.mzml"] is RawSpectraDialectRealityState.SUPPORTED
    assert states["unsupported_numpress.mzml"] is RawSpectraDialectRealityState.PARTIAL
    assert states["unsupported_vendor.raw"] is RawSpectraDialectRealityState.REFUSED
    assert states["simple.mgf"] is RawSpectraDialectRealityState.PARTIAL
    assert report.supported_count == 1
    assert report.partial_count == 2
    assert report.refused_count == 1
    assert "vendor-native raw surfaces" in report.note

# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics import io


def _format_fixture(name: str) -> Path:
    return Path(__file__).resolve().parents[1] / "fixtures" / "formats" / name


def test_io_package_exports_mzml_reader_owner_surface() -> None:
    report = io.parse_mzml(_format_fixture("simple.mzml"))
    review = io.build_mzml_practical_review_report(_format_fixture("practical_review.mzml"))

    assert hasattr(io, "parse_mzml")
    assert hasattr(io, "inspect_mzml_decoding_support")
    assert hasattr(io, "build_mzml_practical_review_report")
    assert report.metadata.instrument_names == ("Q Exactive",)
    assert review.decoding_support.supported is True

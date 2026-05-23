# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics import io
from bijux_proteomics.io.spectra import SpectrumModel, SpectrumPeak


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


def test_io_package_exports_spectrum_quality_owner_surface() -> None:
    report = io.build_spectrum_run_qc_report(
        (
            SpectrumModel(
                spectrum_id="scan=1",
                precursor_mz=500.2,
                precursor_intensity=50000.0,
                precursor_charge=2,
                peaks=tuple(
                    SpectrumPeak(mz=100.0 + offset, intensity=100.0)
                    for offset in range(8)
                ),
            ),
        ),
        source_kind="mgf",
    )
    rendered = io.render_spectrum_run_qc_spectra_tsv(report)

    assert hasattr(io, "build_spectrum_run_qc_report")
    assert hasattr(io, "render_spectrum_run_qc_spectra_tsv")
    assert report.spectrum_metrics[0].quality_tier.value == "high"
    assert "quality_tier" in rendered


def test_io_package_exports_transition_table_owner_surface() -> None:
    report = io.parse_transition_table(_format_fixture("transition_quant.tsv"))
    first_entry = report.accepted_entries[0]
    domain_record = first_entry.to_domain_record()

    assert hasattr(io, "parse_transition_table")
    assert len(report.accepted_entries) == 7
    assert first_entry.precursor_charge == 2
    assert first_entry.retention_time_minutes == 12.5
    assert domain_record.precursor_charge == 2
    assert domain_record.retention_time_minutes == 12.5


def test_io_package_exports_xic_extraction_owner_surface() -> None:
    report = io.extract_mzml_xic_traces(
        _format_fixture("xic_review.mzml"),
        _format_fixture("xic_targets.tsv"),
        tolerance_ppm=10.0,
    )
    rendered = io.render_xic_traces_tsv(report)

    assert hasattr(io, "parse_xic_target_table")
    assert hasattr(io, "extract_mzml_xic_traces")
    assert hasattr(io, "render_xic_traces_tsv")
    assert report.eligible_spectra == 3
    assert len(report.trace_points) == 8
    assert "target_alpha\tscan=7000\t10\t500.000000" in rendered

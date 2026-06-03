# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.io.run_qc import (
    build_spectrum_run_qc_report,
    render_spectrum_run_qc_spectra_tsv,
)
from bijux_proteomics.io.spectra import SpectrumModel, SpectrumPeak


def test_empty_and_single_dominant_peak_spectra_cannot_receive_high_quality() -> None:
    report = build_spectrum_run_qc_report(
        (
            SpectrumModel(
                spectrum_id="empty",
                precursor_mz=500.2,
                precursor_intensity=2000.0,
                precursor_charge=2,
                peaks=(),
            ),
            SpectrumModel(
                spectrum_id="dominant",
                precursor_mz=510.2,
                precursor_intensity=2500.0,
                precursor_charge=2,
                peaks=(
                    SpectrumPeak(mz=100.0, intensity=990.0),
                    SpectrumPeak(mz=101.0, intensity=5.0),
                    SpectrumPeak(mz=102.0, intensity=5.0),
                    SpectrumPeak(mz=103.0, intensity=1.0),
                    SpectrumPeak(mz=104.0, intensity=1.0),
                    SpectrumPeak(mz=105.0, intensity=1.0),
                    SpectrumPeak(mz=106.0, intensity=1.0),
                    SpectrumPeak(mz=107.0, intensity=1.0),
                ),
            ),
            SpectrumModel(
                spectrum_id="balanced",
                precursor_mz=520.2,
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

    rows = {row.spectrum_id: row for row in report.spectrum_metrics}

    assert rows["empty"].quality_tier.value == "low"
    assert rows["empty"].is_empty is True
    assert rows["dominant"].quality_tier.value == "low"
    assert rows["dominant"].is_single_dominant_peak is True
    assert rows["dominant"].top_peak_dominance > 0.95
    assert rows["balanced"].quality_tier.value == "high"
    assert rows["balanced"].spectral_entropy > 0.99


def test_spectrum_quality_metric_table_renders_governed_per_spectrum_rows() -> None:
    report = build_spectrum_run_qc_report(
        (
            SpectrumModel(
                spectrum_id="scan=2",
                precursor_mz=500.2,
                precursor_intensity=800.0,
                precursor_charge=3,
                retention_time_seconds=22.0,
                peaks=(
                    SpectrumPeak(mz=150.0, intensity=60.0),
                    SpectrumPeak(mz=175.0, intensity=40.0),
                    SpectrumPeak(mz=200.0, intensity=20.0),
                    SpectrumPeak(mz=225.0, intensity=10.0),
                ),
            ),
        ),
        source_kind="mgf",
    )

    rendered = render_spectrum_run_qc_spectra_tsv(report)

    assert rendered.splitlines()[0].startswith(
        "spectrum_id\tms_level\tretention_time_seconds"
    )
    assert "quality_tier" in rendered
    assert "scan=2" in rendered

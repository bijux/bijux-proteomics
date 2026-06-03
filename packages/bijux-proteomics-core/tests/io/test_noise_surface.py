# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.io.noise import (
    SpectrumPeakClass,
    estimate_peak_noise,
    render_peak_noise_tsv,
)
from bijux_proteomics.io.spectra import SpectrumPeak


def test_estimate_peak_noise_classifies_noise_weak_signal_and_signal() -> None:
    rows = estimate_peak_noise(
        (
            SpectrumPeak(mz=100.0, intensity=5.0),
            SpectrumPeak(mz=101.0, intensity=10.0),
            SpectrumPeak(mz=102.0, intensity=18.0),
            SpectrumPeak(mz=103.0, intensity=26.0),
            SpectrumPeak(mz=104.0, intensity=60.0),
        )
    )
    rendered = render_peak_noise_tsv(rows)
    by_mz = {row.mz: row for row in rows}

    assert by_mz[100.0].peak_class is SpectrumPeakClass.NOISE
    assert by_mz[102.0].peak_class is SpectrumPeakClass.WEAK_SIGNAL
    assert by_mz[104.0].peak_class is SpectrumPeakClass.SIGNAL
    assert by_mz[104.0].signal_to_noise > by_mz[102.0].signal_to_noise
    assert "signal_to_noise" in rendered
    assert "peak_class" in rendered

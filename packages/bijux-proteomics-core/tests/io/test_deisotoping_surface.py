# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.io.deisotoping import (
    deisotope_peaks,
    render_deisotoped_peaks_tsv,
)
from bijux_proteomics.io.spectra import SpectrumPeak


def test_deisotope_peaks_assigns_charge_one_two_and_three_clusters() -> None:
    clusters = deisotope_peaks(
        (
            SpectrumPeak(mz=500.00000, intensity=120.0),
            SpectrumPeak(mz=501.00335, intensity=90.0),
            SpectrumPeak(mz=502.00671, intensity=45.0),
            SpectrumPeak(mz=600.00000, intensity=110.0),
            SpectrumPeak(mz=600.50168, intensity=85.0),
            SpectrumPeak(mz=601.00335, intensity=43.0),
            SpectrumPeak(mz=700.00000, intensity=105.0),
            SpectrumPeak(mz=700.33445, intensity=81.0),
            SpectrumPeak(mz=700.66890, intensity=39.0),
            SpectrumPeak(mz=820.00000, intensity=20.0),
        ),
        charge_range=(1, 4),
    )
    rendered = render_deisotoped_peaks_tsv(clusters)
    by_charge = {cluster.charge: cluster for cluster in clusters}

    assert tuple(sorted(by_charge)) == (1, 2, 3)
    assert by_charge[1].cluster_peak_indices == (0, 1, 2)
    assert by_charge[2].cluster_peak_indices == (3, 4, 5)
    assert by_charge[3].cluster_peak_indices == (6, 7, 8)
    assert by_charge[1].isotope_count == 2
    assert by_charge[2].isotope_count == 2
    assert by_charge[3].isotope_count == 2
    assert by_charge[1].deisotoping_confidence > 0.8
    assert "deisotoping_confidence" in rendered


def test_deisotope_peaks_does_not_overcluster_random_dense_peaks() -> None:
    clusters = deisotope_peaks(
        (
            SpectrumPeak(mz=500.00000, intensity=50.0),
            SpectrumPeak(mz=500.08200, intensity=47.0),
            SpectrumPeak(mz=500.16100, intensity=44.0),
            SpectrumPeak(mz=500.24700, intensity=49.0),
            SpectrumPeak(mz=500.31800, intensity=41.0),
            SpectrumPeak(mz=500.40700, intensity=45.0),
            SpectrumPeak(mz=500.48600, intensity=43.0),
        ),
        charge_range=(1, 4),
    )

    assert clusters == ()

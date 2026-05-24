# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.io.spectrum_entropy import (
    SpectrumEntropyQualityTier,
    render_spectrum_entropy_tsv,
    score_spectrum_entropy,
)
from bijux_proteomics.io.spectra import SpectrumPeak


def test_spectrum_entropy_scoring_distinguishes_empty_dominant_and_rich_fragment_peaks() -> (
    None
):
    empty_score = score_spectrum_entropy(())
    dominant_score = score_spectrum_entropy(
        (
            SpectrumPeak(mz=100.0, intensity=990.0),
            SpectrumPeak(mz=101.0, intensity=5.0),
            SpectrumPeak(mz=102.0, intensity=5.0),
            SpectrumPeak(mz=103.0, intensity=1.0),
            SpectrumPeak(mz=104.0, intensity=1.0),
            SpectrumPeak(mz=105.0, intensity=1.0),
        )
    )
    rich_fragment_score = score_spectrum_entropy(
        tuple(
            SpectrumPeak(mz=200.0 + offset, intensity=100.0)
            for offset in range(8)
        )
    )
    rendered = render_spectrum_entropy_tsv(rich_fragment_score)

    assert empty_score.entropy_quality_tier is SpectrumEntropyQualityTier.EMPTY
    assert dominant_score.entropy_quality_tier is SpectrumEntropyQualityTier.SINGLE_DOMINANT
    assert rich_fragment_score.entropy_quality_tier is SpectrumEntropyQualityTier.RICH_FRAGMENT
    assert dominant_score.top_peak_fraction > 0.95
    assert rich_fragment_score.normalized_entropy > 0.99
    assert rich_fragment_score.effective_peak_count > dominant_score.effective_peak_count
    assert "entropy_quality_tier" in rendered

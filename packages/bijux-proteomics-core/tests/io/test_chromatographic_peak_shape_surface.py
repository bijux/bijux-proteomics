# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.io.chromatographic_peak_picking import (
    PeakShapeQualityTier,
    render_peak_shape_score_tsv,
    score_peak_shape,
)
from bijux_proteomics.io.xic_extraction import XicExtractionPoint


def test_score_peak_shape_distinguishes_gaussian_like_and_jagged_traces() -> None:
    gaussian_like = score_peak_shape(
        _trace(
            "smooth_peak",
            (
                (0.0, 0.0),
                (10.0, 25.0),
                (20.0, 90.0),
                (30.0, 160.0),
                (40.0, 90.0),
                (50.0, 25.0),
                (60.0, 0.0),
            ),
        )
    )
    jagged_noisy = score_peak_shape(
        _trace(
            "jagged_peak",
            (
                (0.0, 0.0),
                (10.0, 60.0),
                (20.0, 35.0),
                (30.0, 150.0),
                (40.0, 45.0),
                (50.0, 110.0),
                (60.0, 0.0),
            ),
        )
    )
    rendered = render_peak_shape_score_tsv((gaussian_like, jagged_noisy))

    assert gaussian_like.shape_quality_tier is PeakShapeQualityTier.GAUSSIAN_LIKE
    assert gaussian_like.smoothness_score > jagged_noisy.smoothness_score
    assert gaussian_like.symmetry_score > jagged_noisy.symmetry_score
    assert jagged_noisy.shape_quality_tier is PeakShapeQualityTier.JAGGED_NOISY
    assert "shape_quality_tier" in rendered


def _trace(
    target_id: str,
    points: tuple[tuple[float, float], ...],
) -> tuple[XicExtractionPoint, ...]:
    return tuple(
        XicExtractionPoint(
            target_id=target_id,
            rt=rt,
            mz_lower=499.99,
            mz_upper=500.01,
            intensity=intensity,
            scan_id=f"scan={index}",
        )
        for index, (rt, intensity) in enumerate(points, start=1)
    )

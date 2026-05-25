# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Spectrum entropy scoring for centroided peak lists."""

from __future__ import annotations

import csv
from enum import StrEnum
from io import StringIO
from math import exp
from math import log
from typing import TYPE_CHECKING

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel

if TYPE_CHECKING:
    from bijux_proteomics.io.spectra import SpectrumPeak


class SpectrumEntropyQualityTier(StrEnum):
    """Stable entropy-derived quality tiers for one peak list."""

    EMPTY = "empty"
    SINGLE_DOMINANT = "single_dominant"
    RICH_FRAGMENT = "rich_fragment"
    MIXED_FRAGMENT = "mixed_fragment"


class SpectrumEntropyScore(JsonModel):
    """Entropy summary over one peak list."""

    model_config = ConfigDict(extra="forbid")

    entropy: float = Field(..., ge=0.0)
    normalized_entropy: float = Field(..., ge=0.0, le=1.0)
    top_peak_fraction: float = Field(..., ge=0.0, le=1.0)
    effective_peak_count: float = Field(..., ge=0.0)
    entropy_quality_tier: SpectrumEntropyQualityTier


def score_spectrum_entropy(
    peaks: tuple[SpectrumPeak, ...],
    *,
    single_dominant_top_peak_threshold: float = 0.85,
    rich_fragment_normalized_entropy_threshold: float = 0.75,
    rich_fragment_effective_peak_count_threshold: float = 4.0,
    rich_fragment_peak_count_threshold: int = 6,
) -> SpectrumEntropyScore:
    """Score one peak list by Shannon entropy and intensity concentration."""

    if not 0.0 <= single_dominant_top_peak_threshold <= 1.0:
        raise ValueError(
            "single_dominant_top_peak_threshold must be between zero and one"
        )
    if not 0.0 <= rich_fragment_normalized_entropy_threshold <= 1.0:
        raise ValueError(
            "rich_fragment_normalized_entropy_threshold must be between zero and one"
        )
    if rich_fragment_effective_peak_count_threshold < 0.0:
        raise ValueError(
            "rich_fragment_effective_peak_count_threshold must be zero or greater"
        )
    if rich_fragment_peak_count_threshold < 1:
        raise ValueError("rich_fragment_peak_count_threshold must be at least one")

    peak_count = len(peaks)
    total_intensity = sum(peak.intensity for peak in peaks)
    if peak_count == 0 or total_intensity <= 0.0:
        return SpectrumEntropyScore(
            entropy=0.0,
            normalized_entropy=0.0,
            top_peak_fraction=0.0,
            effective_peak_count=0.0,
            entropy_quality_tier=SpectrumEntropyQualityTier.EMPTY,
        )

    entropy = 0.0
    base_peak_intensity = max(peak.intensity for peak in peaks)
    for peak in peaks:
        proportion = peak.intensity / total_intensity
        if proportion > 0.0:
            entropy -= proportion * log(proportion)
    maximum_entropy = log(peak_count) if peak_count > 1 else 0.0
    normalized_entropy = entropy / maximum_entropy if maximum_entropy > 0.0 else 0.0
    top_peak_fraction = base_peak_intensity / total_intensity
    effective_peak_count = exp(entropy) if entropy > 0.0 else 1.0
    tier = _classify_entropy_quality(
        peak_count=peak_count,
        normalized_entropy=normalized_entropy,
        top_peak_fraction=top_peak_fraction,
        effective_peak_count=effective_peak_count,
        single_dominant_top_peak_threshold=single_dominant_top_peak_threshold,
        rich_fragment_normalized_entropy_threshold=(
            rich_fragment_normalized_entropy_threshold
        ),
        rich_fragment_effective_peak_count_threshold=(
            rich_fragment_effective_peak_count_threshold
        ),
        rich_fragment_peak_count_threshold=rich_fragment_peak_count_threshold,
    )
    return SpectrumEntropyScore(
        entropy=entropy,
        normalized_entropy=normalized_entropy,
        top_peak_fraction=top_peak_fraction,
        effective_peak_count=effective_peak_count,
        entropy_quality_tier=tier,
    )


def render_spectrum_entropy_tsv(score: SpectrumEntropyScore) -> str:
    """Render one entropy score as a stable one-row TSV table."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "entropy",
            "normalized_entropy",
            "top_peak_fraction",
            "effective_peak_count",
            "entropy_quality_tier",
        )
    )
    writer.writerow(
        (
            score.entropy,
            score.normalized_entropy,
            score.top_peak_fraction,
            score.effective_peak_count,
            score.entropy_quality_tier.value,
        )
    )
    return buffer.getvalue()


def _classify_entropy_quality(
    *,
    peak_count: int,
    normalized_entropy: float,
    top_peak_fraction: float,
    effective_peak_count: float,
    single_dominant_top_peak_threshold: float,
    rich_fragment_normalized_entropy_threshold: float,
    rich_fragment_effective_peak_count_threshold: float,
    rich_fragment_peak_count_threshold: int,
) -> SpectrumEntropyQualityTier:
    if top_peak_fraction >= single_dominant_top_peak_threshold:
        return SpectrumEntropyQualityTier.SINGLE_DOMINANT
    if (
        peak_count >= rich_fragment_peak_count_threshold
        and normalized_entropy >= rich_fragment_normalized_entropy_threshold
        and effective_peak_count >= rich_fragment_effective_peak_count_threshold
    ):
        return SpectrumEntropyQualityTier.RICH_FRAGMENT
    return SpectrumEntropyQualityTier.MIXED_FRAGMENT

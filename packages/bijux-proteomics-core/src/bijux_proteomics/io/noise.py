# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Spectrum noise-floor estimation for centroided peak lists."""

from __future__ import annotations

import csv
from enum import StrEnum
from io import StringIO
from statistics import median
from typing import TYPE_CHECKING

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel

if TYPE_CHECKING:
    from bijux_proteomics.io.spectra import SpectrumPeak


class SpectrumPeakClass(StrEnum):
    """Stable peak classes after signal-to-noise estimation."""

    NOISE = "noise"
    WEAK_SIGNAL = "weak_signal"
    SIGNAL = "signal"


class SpectrumPeakNoiseRow(JsonModel):
    """One peak with its estimated noise floor and signal class."""

    model_config = ConfigDict(extra="forbid")

    peak_index: int = Field(..., ge=0)
    mz: float = Field(..., gt=0.0)
    intensity: float = Field(..., ge=0.0)
    noise_floor: float = Field(..., ge=0.0)
    signal_to_noise: float = Field(..., ge=0.0)
    peak_class: SpectrumPeakClass


def estimate_peak_noise(
    peaks: tuple[SpectrumPeak, ...],
    *,
    weak_signal_threshold: float = 2.0,
    signal_threshold: float = 5.0,
) -> tuple[SpectrumPeakNoiseRow, ...]:
    """Estimate one stable noise floor and signal class per observed peak."""

    if weak_signal_threshold <= 0.0:
        raise ValueError("weak_signal_threshold must be greater than zero")
    if signal_threshold <= weak_signal_threshold:
        raise ValueError("signal_threshold must be greater than weak_signal_threshold")
    if not peaks:
        return ()

    intensities = tuple(float(peak.intensity) for peak in peaks)
    noise_floor = _estimate_noise_floor(intensities)
    rows = []
    for peak_index, peak in enumerate(peaks):
        signal_to_noise = peak.intensity / noise_floor if noise_floor > 0.0 else 0.0
        rows.append(
            SpectrumPeakNoiseRow(
                peak_index=peak_index,
                mz=peak.mz,
                intensity=peak.intensity,
                noise_floor=noise_floor,
                signal_to_noise=signal_to_noise,
                peak_class=_peak_class(
                    signal_to_noise=signal_to_noise,
                    weak_signal_threshold=weak_signal_threshold,
                    signal_threshold=signal_threshold,
                ),
            )
        )
    return tuple(rows)


def render_peak_noise_tsv(rows: tuple[SpectrumPeakNoiseRow, ...]) -> str:
    """Render peak noise estimates as a stable TSV ledger."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "peak_index",
            "mz",
            "intensity",
            "noise_floor",
            "signal_to_noise",
            "peak_class",
        )
    )
    for row in rows:
        writer.writerow(
            (
                row.peak_index,
                row.mz,
                row.intensity,
                row.noise_floor,
                row.signal_to_noise,
                row.peak_class.value,
            )
        )
    return buffer.getvalue()


def _estimate_noise_floor(intensities: tuple[float, ...]) -> float:
    positive = tuple(sorted(intensity for intensity in intensities if intensity > 0.0))
    if not positive:
        return 1.0
    lower_half_count = max(1, len(positive) // 2)
    baseline = positive[:lower_half_count]
    estimated = float(median(baseline))
    return estimated if estimated > 0.0 else max(min(positive), 1.0)


def _peak_class(
    *,
    signal_to_noise: float,
    weak_signal_threshold: float,
    signal_threshold: float,
) -> SpectrumPeakClass:
    if signal_to_noise < weak_signal_threshold:
        return SpectrumPeakClass.NOISE
    if signal_to_noise < signal_threshold:
        return SpectrumPeakClass.WEAK_SIGNAL
    return SpectrumPeakClass.SIGNAL

# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Confidence segmentation helpers."""

from __future__ import annotations


def low_confidence_segments(
    plddt: list[float], thresh: float = 70, min_len: int = 8
) -> list[tuple[int, int]]:
    """Identifies low-confidence segments below threshold."""
    segs = []
    start = None
    for idx, value in enumerate(plddt):
        if value < thresh and start is None:
            start = idx
        if (value >= thresh or idx == len(plddt) - 1) and start is not None:
            end = idx if value >= thresh else idx + 1
            if end - start >= min_len:
                segs.append((start, end))
            start = None
    return segs

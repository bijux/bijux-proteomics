# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Structure-confidence helpers used by intelligence-owned interpretation flows."""

from __future__ import annotations


def low_confidence_segments(
    plddt: list[float], thresh: float = 70, min_len: int = 8
) -> list[tuple[int, int]]:
    """Return contiguous low-confidence pLDDT regions below the threshold."""
    segments: list[tuple[int, int]] = []
    start: int | None = None
    for idx, value in enumerate(plddt):
        if value < thresh and start is None:
            start = idx
        if (value >= thresh or idx == len(plddt) - 1) and start is not None:
            end = idx if value >= thresh else idx + 1
            if end - start >= min_len:
                segments.append((start, end))
            start = None
    return segments

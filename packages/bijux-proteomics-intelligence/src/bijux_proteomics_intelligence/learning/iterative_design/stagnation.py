# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Stagnation tracking utilities for the design loop."""

from __future__ import annotations


def update_stagnation_count(
    stagnation_count: int, improvement_delta: float, threshold: float
) -> int:
    """update_stagnation_count."""
    if abs(improvement_delta) < threshold:
        return stagnation_count + 1
    return 0

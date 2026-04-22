# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Determinism helpers."""

from __future__ import annotations

from enum import StrEnum


class DeterminismLevel(StrEnum):
    """DeterminismLevel."""

    DETERMINISTIC = "deterministic"
    STOCHASTIC = "stochastic"


def stable_sort(items: list[str]) -> list[str]:
    """stable_sort."""
    return sorted(items)

# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Shared generic confidence tiers used across scientific outputs."""

from __future__ import annotations

from enum import StrEnum


class ConfidenceTier(StrEnum):
    """Canonical generic confidence tiers for proteins, pathways, QC, and claims."""

    HIGH = "high"
    HIGH_CONFIDENCE = "high"
    MODERATE = "moderate"
    MODERATE_CONFIDENCE = "moderate"
    MEDIUM = "moderate"
    LOW = "low"
    LOW_CONFIDENCE = "low"


def coerce_confidence_tier(value: str | ConfidenceTier | None) -> ConfidenceTier | None:
    """Normalize legacy and canonical confidence strings onto the shared tier."""

    if value is None:
        return None
    if isinstance(value, ConfidenceTier):
        return value

    normalized = value.strip().lower()
    if normalized in {"high", "high_confidence"}:
        return ConfidenceTier.HIGH
    if normalized in {"moderate", "moderate_confidence", "medium"}:
        return ConfidenceTier.MODERATE
    if normalized in {"low", "low_confidence"}:
        return ConfidenceTier.LOW
    raise ValueError(f"unsupported confidence tier: {value}")


__all__ = ["ConfidenceTier", "coerce_confidence_tier"]

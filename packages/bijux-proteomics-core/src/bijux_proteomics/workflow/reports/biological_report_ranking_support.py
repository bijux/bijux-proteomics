# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Shared scoring helpers for biological report ranking builders."""

from __future__ import annotations

from collections.abc import Iterable, Sequence

from bijux_proteomics.workflow.cards.protein_evidence_cards import ProteinEvidenceCard


def _mean(value_groups: Iterable[Sequence[float]]) -> float:
    values: list[float] = []
    for group in value_groups:
        values.extend(group)
    if not values:
        return 0.0
    return sum(values) / len(values)


def _tier_score(value: str) -> float:
    return {
        "high": 1.0,
        "high_support": 1.0,
        "moderate": 0.72,
        "moderate_support": 0.72,
        "review": 0.45,
        "low": 0.3,
    }.get(value, 0.5)


def _biological_result_uncertainty(card: ProteinEvidenceCard) -> float:
    uncertainty = 0.0
    if card.differential_result.adjusted_p_value is None:
        uncertainty += 0.08
    if card.differential_result.uncertainty_note:
        uncertainty += 0.08
    if (
        min(
            card.differential_result.observations_a,
            card.differential_result.observations_b,
        )
        < 2
    ):
        uncertainty += 0.06
    return min(0.3, uncertainty)

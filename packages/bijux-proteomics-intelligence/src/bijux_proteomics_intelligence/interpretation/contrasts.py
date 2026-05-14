# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Analytical contrast recommendation owners over experimental designs."""

from __future__ import annotations

from collections import defaultdict
from enum import StrEnum

from pydantic import ConfigDict, Field

from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics_foundation import JsonModel


class AnalyticalContrastRejectionReason(StrEnum):
    """Reasons an analytical contrast recommendation is not valid yet."""

    INSUFFICIENT_REPLICATES = "insufficient_replicates"
    BATCH_CONFOUNDED = "batch_confounded"
    SINGLE_CONDITION = "single_condition"


class AnalyticalContrastRecommendation(JsonModel):
    """One recommended or rejected analytical contrast."""

    model_config = ConfigDict(extra="forbid")

    condition_a: str = Field(..., min_length=1)
    condition_b: str = Field(..., min_length=1)
    valid: bool
    replicate_counts: dict[str, int] = Field(default_factory=dict)
    shared_batches: tuple[str, ...] = Field(default_factory=tuple)
    rejection_reasons: tuple[AnalyticalContrastRejectionReason, ...] = Field(
        default_factory=tuple
    )
    rationale: str = Field(..., min_length=1)


class AnalyticalContrastRecommendationReport(JsonModel):
    """Recommended and rejected analytical contrasts over a design table."""

    model_config = ConfigDict(extra="forbid")

    condition_count: int = Field(..., ge=0)
    valid_contrasts: tuple[AnalyticalContrastRecommendation, ...] = Field(
        default_factory=tuple
    )
    rejected_contrasts: tuple[AnalyticalContrastRecommendation, ...] = Field(
        default_factory=tuple
    )


def recommend_experimental_contrasts(
    entries: tuple[ExperimentalDesignEntry, ...],
    *,
    min_replicates: int = 2,
) -> AnalyticalContrastRecommendationReport:
    """Recommend valid pairwise contrasts from an experimental design."""
    conditions = sorted({entry.condition for entry in entries})
    if len(conditions) < 2:
        rejected_contrast = AnalyticalContrastRecommendation(
            condition_a=conditions[0] if conditions else "condition-a",
            condition_b=conditions[0] if conditions else "condition-b",
            valid=False,
            replicate_counts=dict.fromkeys(conditions, 0),
            shared_batches=(),
            rejection_reasons=(AnalyticalContrastRejectionReason.SINGLE_CONDITION,),
            rationale="at least two conditions are required for a contrast",
        )
        return AnalyticalContrastRecommendationReport(
            condition_count=len(conditions),
            valid_contrasts=(),
            rejected_contrasts=(rejected_contrast,),
        )
    grouped: dict[str, list[ExperimentalDesignEntry]] = defaultdict(list)
    for entry in entries:
        grouped[entry.condition].append(entry)
    valid: list[AnalyticalContrastRecommendation] = []
    rejected_contrasts: list[AnalyticalContrastRecommendation] = []
    for index, left in enumerate(conditions):
        for right in conditions[index + 1 :]:
            left_entries = grouped[left]
            right_entries = grouped[right]
            left_batches = {entry.batch for entry in left_entries if entry.batch}
            right_batches = {entry.batch for entry in right_entries if entry.batch}
            shared_batches = tuple(sorted(left_batches & right_batches))
            reasons: list[AnalyticalContrastRejectionReason] = []
            if (
                len(left_entries) < min_replicates
                or len(right_entries) < min_replicates
            ):
                reasons.append(
                    AnalyticalContrastRejectionReason.INSUFFICIENT_REPLICATES
                )
            if left_batches and right_batches and not shared_batches:
                reasons.append(AnalyticalContrastRejectionReason.BATCH_CONFOUNDED)
            recommendation = AnalyticalContrastRecommendation(
                condition_a=left,
                condition_b=right,
                valid=not reasons,
                replicate_counts={left: len(left_entries), right: len(right_entries)},
                shared_batches=shared_batches,
                rejection_reasons=tuple(reasons),
                rationale=(
                    "replicates and batch overlap support a valid contrast"
                    if not reasons
                    else ", ".join(reason.value for reason in reasons)
                ),
            )
            if recommendation.valid:
                valid.append(recommendation)
            else:
                rejected_contrasts.append(recommendation)
    return AnalyticalContrastRecommendationReport(
        condition_count=len(conditions),
        valid_contrasts=tuple(valid),
        rejected_contrasts=tuple(rejected_contrasts),
    )

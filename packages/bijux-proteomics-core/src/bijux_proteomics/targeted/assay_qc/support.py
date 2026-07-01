# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Internal helper contracts for targeted assay-QC analysis."""

from __future__ import annotations

from bijux_proteomics.targeted.fragment_ratios import TargetedFragmentRatioMatrixEntry
from bijux_proteomics.targeted.result_import import TargetedResultImportReport
from bijux_proteomics.targeted.transition_coelution import (
    TargetedTransitionCoelutionTargetEntry,
    TargetedTransitionCoelutionTier,
    TargetedTransitionCoelutionTransitionEntry,
)


def missing_target_coelution_entry(
    *,
    target_id: str,
    sample_id: str,
    expected_transition_count: int,
) -> TargetedTransitionCoelutionTargetEntry:
    """Build the explicit target-level coelution placeholder for missing signal."""

    return TargetedTransitionCoelutionTargetEntry(
        target_id=target_id,
        sample_id=sample_id,
        expected_transition_count=expected_transition_count,
        observed_transition_count=0,
        coeluting_transition_count=0,
        coeluting_transition_ids=(),
        noncoeluting_transition_ids=(),
        anchor_transition_id=None,
        anchor_retention_time_minutes=None,
        mean_retention_time_minutes=None,
        reference_retention_time_minutes=None,
        absolute_alignment_delta_minutes=None,
        alignment_flagged=False,
        coelution_tier=TargetedTransitionCoelutionTier.MISSING,
        reliable_transition_support=False,
        reliability_reasons=("target is not detected in this sample",),
    )


def missing_transition_coelution_entry(
    *,
    target_id: str,
    sample_id: str,
    transition_id: str,
) -> TargetedTransitionCoelutionTransitionEntry:
    """Build the explicit transition-level coelution placeholder for missing signal."""

    return TargetedTransitionCoelutionTransitionEntry(
        target_id=target_id,
        sample_id=sample_id,
        transition_id=transition_id,
        detected=False,
        retention_time_minutes=None,
        anchor_transition_id=None,
        anchor_retention_time_minutes=None,
        reference_retention_time_minutes=None,
        coelution_delta_minutes=None,
        reference_delta_minutes=None,
        coeluting=False,
        failure_reasons=("transition is not detected in this sample",),
    )


def coefficient_of_variation(values: list[float]) -> float | None:
    """Return the sample coefficient of variation for positive replicate values."""

    if len(values) < 2:
        return None
    mean_value = sum(values) / len(values)
    if mean_value <= 0.0:
        return None
    squared_distance_sum = sum((value - mean_value) ** 2 for value in values)
    variance = squared_distance_sum / (len(values) - 1)
    return float(variance**0.5 / mean_value)


def fragment_ratio_matrix(
    import_report: TargetedResultImportReport,
) -> tuple[TargetedFragmentRatioMatrixEntry, ...]:
    """Project imported targeted observations into fragment-ratio matrix rows."""

    return tuple(
        TargetedFragmentRatioMatrixEntry(
            target_id=observation.precursor_id,
            sample_id=observation.sample_id,
            transition_id=observation.transition_id,
            intensity=observation.intensity,
        )
        for observation in import_report.observations
    )

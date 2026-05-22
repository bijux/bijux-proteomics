# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owned assay-QC surfaces over imported targeted observations."""

from __future__ import annotations

from pathlib import Path

from pydantic import ConfigDict, Field

from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics.targeted.result_import import (
    TargetedResultImportReport,
    build_skyline_result_import_report,
    build_transition_table_result_import_report,
)
from bijux_proteomics_foundation import JsonModel


class TargetedTransitionConsistencyEntry(JsonModel):
    """One sample-level transition consistency record for a targeted precursor."""

    model_config = ConfigDict(extra="forbid")

    target_id: str = Field(..., min_length=1)
    sample_id: str = Field(..., min_length=1)
    detected_transition_count: int = Field(..., ge=0)
    expected_transition_count: int = Field(..., ge=0)
    consistency_fraction: float = Field(..., ge=0.0, le=1.0)


class TargetedFragmentRatioEntry(JsonModel):
    """One transition share inside a targeted precursor for one sample."""

    model_config = ConfigDict(extra="forbid")

    target_id: str = Field(..., min_length=1)
    sample_id: str = Field(..., min_length=1)
    transition_id: str = Field(..., min_length=1)
    intensity: float = Field(..., ge=0.0)
    total_target_intensity: float = Field(..., ge=0.0)
    relative_share: float = Field(..., ge=0.0, le=1.0)
    reference_relative_share: float = Field(..., ge=0.0, le=1.0)
    absolute_share_delta: float = Field(..., ge=0.0, le=1.0)
    flagged: bool = False


class TargetedRetentionTimeConsistencyEntry(JsonModel):
    """One sample-level retention-time consistency record for a targeted precursor."""

    model_config = ConfigDict(extra="forbid")

    target_id: str = Field(..., min_length=1)
    sample_id: str = Field(..., min_length=1)
    observed_transition_count: int = Field(..., ge=0)
    mean_retention_time_minutes: float | None = Field(default=None, ge=0.0)
    reference_retention_time_minutes: float | None = Field(default=None, ge=0.0)
    absolute_delta_minutes: float | None = Field(default=None, ge=0.0)
    flagged: bool = False


class TargetedReplicateCvEntry(JsonModel):
    """One condition-level replicate-CV record for a targeted precursor."""

    model_config = ConfigDict(extra="forbid")

    target_id: str = Field(..., min_length=1)
    condition: str = Field(..., min_length=1)
    replicate_count: int = Field(..., ge=0)
    detected_replicate_count: int = Field(..., ge=0)
    mean_intensity: float | None = Field(default=None, ge=0.0)
    coefficient_of_variation: float | None = Field(default=None, ge=0.0)
    flagged: bool = False


class TargetedUnreliableTargetEntry(JsonModel):
    """One explicitly flagged targeted precursor under sample or condition review."""

    model_config = ConfigDict(extra="forbid")

    target_id: str = Field(..., min_length=1)
    sample_id: str | None = None
    condition: str | None = None
    flagged_transition_ids: tuple[str, ...] = Field(default_factory=tuple)
    quality_flags: tuple[str, ...] = Field(default_factory=tuple)
    reasons: tuple[str, ...] = Field(default_factory=tuple)


class TargetedAssayQcSummary(JsonModel):
    """Compact summary over one targeted assay QC report."""

    model_config = ConfigDict(extra="forbid")

    target_count: int = Field(..., ge=0)
    sample_count: int = Field(..., ge=0)
    transition_consistency_entry_count: int = Field(..., ge=0)
    fragment_ratio_entry_count: int = Field(..., ge=0)
    retention_time_entry_count: int = Field(..., ge=0)
    flagged_retention_time_entry_count: int = Field(..., ge=0)
    replicate_cv_entry_count: int = Field(..., ge=0)
    flagged_replicate_cv_entry_count: int = Field(..., ge=0)
    unreliable_target_entry_count: int = Field(..., ge=0)
    unreliable_target_count: int = Field(..., ge=0)


class TargetedAssayQcReport(JsonModel):
    """Targeted assay QC report over transition consistency and fragment ratios."""

    model_config = ConfigDict(extra="forbid")

    source_name: str = Field(..., min_length=1)
    transition_consistency: tuple[TargetedTransitionConsistencyEntry, ...] = Field(
        default_factory=tuple
    )
    fragment_ratios: tuple[TargetedFragmentRatioEntry, ...] = Field(default_factory=tuple)
    retention_time_consistency: tuple[TargetedRetentionTimeConsistencyEntry, ...] = Field(
        default_factory=tuple
    )
    replicate_cv: tuple[TargetedReplicateCvEntry, ...] = Field(default_factory=tuple)
    unreliable_targets: tuple[TargetedUnreliableTargetEntry, ...] = Field(
        default_factory=tuple
    )
    summary: TargetedAssayQcSummary
    note: str = Field(..., min_length=1)


def build_targeted_assay_qc_report(
    import_report: TargetedResultImportReport,
    design_entries: tuple[ExperimentalDesignEntry, ...] = (),
    *,
    retention_time_delta_threshold_minutes: float = 0.75,
    fragment_ratio_delta_threshold: float = 0.12,
    high_replicate_cv_threshold: float = 0.3,
) -> TargetedAssayQcReport:
    """Build targeted assay QC ledgers over one imported targeted result bundle."""

    target_ids = sorted({item.precursor_id for item in import_report.observations})
    sample_ids = sorted({item.sample_id for item in import_report.observations})
    target_to_transitions = {
        target_id: sorted(
            {
                item.transition_id
                for item in import_report.observations
                if item.precursor_id == target_id
            }
        )
        for target_id in target_ids
    }

    consistency_entries: list[TargetedTransitionConsistencyEntry] = []
    ratio_entries: list[TargetedFragmentRatioEntry] = []
    retention_time_entries: list[TargetedRetentionTimeConsistencyEntry] = []
    ratio_flags_by_target_sample: dict[tuple[str, str], set[str]] = {}
    missing_transitions_by_target_sample: dict[tuple[str, str], set[str]] = {}
    quality_flags_by_target_sample: dict[tuple[str, str], set[str]] = {}
    for target_id in target_ids:
        expected_transition_ids = target_to_transitions[target_id]
        expected_count = len(expected_transition_ids)
        observations_by_sample = {
            sample_id: [
                item
                for item in import_report.observations
                if item.precursor_id == target_id and item.sample_id == sample_id
            ]
            for sample_id in sample_ids
        }
        reference_relative_shares = {
            transition_id: _median(
                [
                    item.intensity / total_target_intensity
                    for sample_id in sample_ids
                    for item in observations_by_sample[sample_id]
                    if item.transition_id == transition_id
                    and (
                        total_target_intensity := sum(
                            candidate.intensity
                            for candidate in observations_by_sample[sample_id]
                        )
                    )
                    > 0.0
                ]
            )
            or 0.0
            for transition_id in expected_transition_ids
        }
        reference_retention_time = _median(
            [
                item.retention_time_minutes
                for item in import_report.observations
                if item.precursor_id == target_id and item.retention_time_minutes is not None
            ]
        )
        for sample_id in sample_ids:
            sample_observations = observations_by_sample[sample_id]
            detected_transition_ids = {item.transition_id for item in sample_observations}
            detected_count = len(detected_transition_ids)
            missing_transition_ids = set(expected_transition_ids) - detected_transition_ids
            if missing_transition_ids:
                missing_transitions_by_target_sample[(target_id, sample_id)] = (
                    missing_transition_ids
                )
            consistency_entries.append(
                TargetedTransitionConsistencyEntry(
                    target_id=target_id,
                    sample_id=sample_id,
                    detected_transition_count=detected_count,
                    expected_transition_count=expected_count,
                    consistency_fraction=(
                        detected_count / expected_count if expected_count else 0.0
                    ),
                )
            )
            total_target_intensity = sum(item.intensity for item in sample_observations)
            sample_quality_flags = {
                item.quality_flag
                for item in sample_observations
                if item.quality_flag is not None and item.quality_flag != "pass"
            }
            if sample_quality_flags:
                quality_flags_by_target_sample[(target_id, sample_id)] = sample_quality_flags
            for item in sorted(sample_observations, key=lambda record: record.transition_id):
                relative_share = (
                    item.intensity / total_target_intensity
                    if total_target_intensity > 0.0
                    else 0.0
                )
                reference_relative_share = reference_relative_shares[item.transition_id]
                absolute_share_delta = abs(relative_share - reference_relative_share)
                ratio_flagged = absolute_share_delta > fragment_ratio_delta_threshold
                if ratio_flagged:
                    ratio_flags_by_target_sample.setdefault((target_id, sample_id), set()).add(
                        item.transition_id
                    )
                ratio_entries.append(
                    TargetedFragmentRatioEntry(
                        target_id=target_id,
                        sample_id=sample_id,
                        transition_id=item.transition_id,
                        intensity=item.intensity,
                        total_target_intensity=total_target_intensity,
                        relative_share=relative_share,
                        reference_relative_share=reference_relative_share,
                        absolute_share_delta=absolute_share_delta,
                        flagged=ratio_flagged,
                    )
                )
            sample_retention_times = [
                item.retention_time_minutes
                for item in sample_observations
                if item.retention_time_minutes is not None
            ]
            mean_retention_time = (
                sum(sample_retention_times) / len(sample_retention_times)
                if sample_retention_times
                else None
            )
            absolute_delta = (
                abs(mean_retention_time - reference_retention_time)
                if mean_retention_time is not None and reference_retention_time is not None
                else None
            )
            retention_time_entries.append(
                TargetedRetentionTimeConsistencyEntry(
                    target_id=target_id,
                    sample_id=sample_id,
                    observed_transition_count=len(sample_observations),
                    mean_retention_time_minutes=mean_retention_time,
                    reference_retention_time_minutes=reference_retention_time,
                    absolute_delta_minutes=absolute_delta,
                    flagged=(
                        absolute_delta is not None
                        and absolute_delta > retention_time_delta_threshold_minutes
                    ),
                )
            )

    condition_by_sample = {
        entry.sample_id: entry.condition
        for entry in design_entries
        if entry.sample_id in sample_ids
    }
    sample_ids_by_condition: dict[str, list[str]] = {}
    for sample_id in sample_ids:
        condition = condition_by_sample.get(sample_id)
        if condition is not None:
            sample_ids_by_condition.setdefault(condition, []).append(sample_id)
    total_intensity_by_target_sample = {
        (entry.target_id, entry.sample_id): entry.total_target_intensity
        for entry in ratio_entries
        if entry.total_target_intensity > 0.0
    }
    replicate_cv_entries: list[TargetedReplicateCvEntry] = []
    unreliable_target_entries: list[TargetedUnreliableTargetEntry] = []
    for target_id in target_ids:
        for sample_id in sample_ids:
            reasons: list[str] = []
            flagged_transition_ids = set(
                missing_transitions_by_target_sample.get((target_id, sample_id), set())
            )
            flagged_transition_ids.update(
                ratio_flags_by_target_sample.get((target_id, sample_id), set())
            )
            quality_flags = tuple(
                sorted(quality_flags_by_target_sample.get((target_id, sample_id), set()))
            )
            consistency_entry = next(
                entry
                for entry in consistency_entries
                if entry.target_id == target_id and entry.sample_id == sample_id
            )
            if consistency_entry.consistency_fraction < 1.0:
                reasons.append("transition detection is incomplete")
            if ratio_flags_by_target_sample.get((target_id, sample_id)):
                reasons.append("fragment-ion ratios deviate from the target reference pattern")
            retention_entry = next(
                entry
                for entry in retention_time_entries
                if entry.target_id == target_id and entry.sample_id == sample_id
            )
            if retention_entry.flagged:
                reasons.append("retention time deviates from the target reference window")
            if quality_flags:
                reasons.append("source quality flags require review")
            if reasons:
                unreliable_target_entries.append(
                    TargetedUnreliableTargetEntry(
                        target_id=target_id,
                        sample_id=sample_id,
                        condition=condition_by_sample.get(sample_id),
                        flagged_transition_ids=tuple(sorted(flagged_transition_ids)),
                        quality_flags=quality_flags,
                        reasons=tuple(sorted(reasons)),
                    )
                )
        for condition, condition_sample_ids in sorted(sample_ids_by_condition.items()):
            replicate_intensities = [
                total_intensity_by_target_sample[(target_id, sample_id)]
                for sample_id in condition_sample_ids
                if (target_id, sample_id) in total_intensity_by_target_sample
            ]
            mean_intensity = (
                sum(replicate_intensities) / len(replicate_intensities)
                if replicate_intensities
                else None
            )
            coefficient_of_variation = _coefficient_of_variation(replicate_intensities)
            flagged = (
                coefficient_of_variation is not None
                and coefficient_of_variation > high_replicate_cv_threshold
            )
            replicate_cv_entries.append(
                TargetedReplicateCvEntry(
                    target_id=target_id,
                    condition=condition,
                    replicate_count=len(condition_sample_ids),
                    detected_replicate_count=len(replicate_intensities),
                    mean_intensity=mean_intensity,
                    coefficient_of_variation=coefficient_of_variation,
                    flagged=flagged,
                )
            )
            if flagged:
                unreliable_target_entries.append(
                    TargetedUnreliableTargetEntry(
                        target_id=target_id,
                        condition=condition,
                        reasons=("replicate cv is above the configured threshold",),
                    )
                )

    return TargetedAssayQcReport(
        source_name=import_report.source_name,
        transition_consistency=tuple(consistency_entries),
        fragment_ratios=tuple(ratio_entries),
        retention_time_consistency=tuple(retention_time_entries),
        replicate_cv=tuple(replicate_cv_entries),
        unreliable_targets=tuple(
            sorted(
                unreliable_target_entries,
                key=lambda entry: (
                    entry.target_id,
                    "" if entry.condition is None else entry.condition,
                    "" if entry.sample_id is None else entry.sample_id,
                ),
            )
        ),
        summary=TargetedAssayQcSummary(
            target_count=len(target_ids),
            sample_count=len(sample_ids),
            transition_consistency_entry_count=len(consistency_entries),
            fragment_ratio_entry_count=len(ratio_entries),
            retention_time_entry_count=len(retention_time_entries),
            flagged_retention_time_entry_count=sum(
                entry.flagged for entry in retention_time_entries
            ),
            replicate_cv_entry_count=len(replicate_cv_entries),
            flagged_replicate_cv_entry_count=sum(
                entry.flagged for entry in replicate_cv_entries
            ),
            unreliable_target_entry_count=len(unreliable_target_entries),
            unreliable_target_count=len(
                {entry.target_id for entry in unreliable_target_entries}
            ),
        ),
        note=(
            "targeted assay qc keeps transition consistency, fragment-ion ratio, retention-time consistency, replicate cv, and explicit unreliable-target review visible before any sample or target is trusted"
        ),
    )


def build_skyline_targeted_assay_qc_report(path: Path) -> TargetedAssayQcReport:
    """Build targeted assay QC directly from one Skyline-style export."""

    return build_targeted_assay_qc_report(build_skyline_result_import_report(path))


def build_transition_table_targeted_assay_qc_report(path: Path) -> TargetedAssayQcReport:
    """Build targeted assay QC directly from one exported transition table."""

    return build_targeted_assay_qc_report(build_transition_table_result_import_report(path))


def _median(values: list[float]) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    midpoint = len(ordered) // 2
    if len(ordered) % 2 == 1:
        return ordered[midpoint]
    return (ordered[midpoint - 1] + ordered[midpoint]) / 2.0


def _coefficient_of_variation(values: list[float]) -> float | None:
    if len(values) < 2:
        return None
    mean_value = sum(values) / len(values)
    if mean_value <= 0.0:
        return None
    squared_distance_sum = sum((value - mean_value) ** 2 for value in values)
    variance = squared_distance_sum / (len(values) - 1)
    return variance**0.5 / mean_value

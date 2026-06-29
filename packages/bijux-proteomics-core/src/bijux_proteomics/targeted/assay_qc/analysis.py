# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owned assay-QC surfaces over imported targeted observations."""

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics.io.fragment_ratio_stability import (
    build_targeted_fragment_ratio_stability_report,
)
from bijux_proteomics.targeted.assay_qc.models import (
    TargetedAssayQcReport,
    TargetedAssayQcSummary,
    TargetedFragmentRatioEntry,
    TargetedReplicateCvEntry,
    TargetedRetentionTimeConsistencyEntry,
    TargetedTargetQcEntry,
    TargetedTransitionConsistencyEntry,
    TargetedTransitionQcEntry,
    TargetedUnreliableTargetEntry,
)
from bijux_proteomics.targeted.fragment_ratios import (
    TargetedFragmentRatioMatrixEntry,
    score_fragment_ratio_drift,
)
from bijux_proteomics.targeted.result_import import (
    TargetedResultImportReport,
    build_skyline_result_import_report,
    build_transition_table_result_import_report,
)
from bijux_proteomics.targeted.transition_coelution import (
    TargetedTransitionCoelutionTargetEntry,
    TargetedTransitionCoelutionTier,
    TargetedTransitionCoelutionTransitionEntry,
    build_targeted_transition_coelution_report,
)


def _missing_target_coelution_entry(
    *,
    target_id: str,
    sample_id: str,
    expected_transition_count: int,
) -> TargetedTransitionCoelutionTargetEntry:
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


def _missing_transition_coelution_entry(
    *,
    target_id: str,
    sample_id: str,
    transition_id: str,
) -> TargetedTransitionCoelutionTransitionEntry:
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


def build_targeted_assay_qc_report(
    import_report: TargetedResultImportReport,
    design_entries: tuple[ExperimentalDesignEntry, ...] = (),
    *,
    retention_time_delta_threshold_minutes: float = 0.75,
    transition_coelution_delta_threshold_minutes: float = 0.2,
    fragment_ratio_delta_threshold: float = 0.12,
    fragment_ratio_cv_threshold: float = 0.25,
    high_replicate_cv_threshold: float = 0.3,
) -> TargetedAssayQcReport:
    """Build targeted assay QC ledgers over one imported targeted result bundle."""

    target_ids = sorted({item.precursor_id for item in import_report.observations})
    sample_ids = sorted({item.sample_id for item in import_report.observations})
    condition_by_sample = {
        entry.sample_id: entry.condition
        for entry in design_entries
        if entry.sample_id in sample_ids
    }
    transition_coelution = build_targeted_transition_coelution_report(
        import_report,
        coelution_rt_delta_threshold_minutes=transition_coelution_delta_threshold_minutes,
        alignment_rt_delta_threshold_minutes=retention_time_delta_threshold_minutes,
    )
    fragment_ratio_stability = build_targeted_fragment_ratio_stability_report(
        import_report,
        absolute_ratio_delta_threshold=fragment_ratio_delta_threshold,
        ratio_cv_threshold=fragment_ratio_cv_threshold,
    )
    fragment_ratio_drift_by_target_transition = {
        (entry.target_id, entry.transition_id): entry
        for entry in score_fragment_ratio_drift(
            _fragment_ratio_matrix(import_report),
            observed_ratio_cv_threshold=fragment_ratio_cv_threshold,
        )
    }
    target_coelution_by_target_sample = {
        (entry.target_id, entry.sample_id): entry
        for entry in transition_coelution.target_entries
    }
    transition_coelution_by_target_sample_transition = {
        (entry.target_id, entry.sample_id, entry.transition_id): entry
        for entry in transition_coelution.transition_entries
    }
    ratio_observation_by_target_sample_transition = {
        (entry.analyte_id, entry.run_id, entry.fragment_id): entry
        for entry in fragment_ratio_stability.observation_entries
    }
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

    target_qc_entries: list[TargetedTargetQcEntry] = []
    consistency_entries: list[TargetedTransitionConsistencyEntry] = []
    transition_qc_entries: list[TargetedTransitionQcEntry] = []
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
        for sample_id in sample_ids:
            sample_observations = observations_by_sample[sample_id]
            observations_by_transition_id = {
                item.transition_id: item for item in sample_observations
            }
            target_coelution_entry = target_coelution_by_target_sample.get(
                (target_id, sample_id),
                _missing_target_coelution_entry(
                    target_id=target_id,
                    sample_id=sample_id,
                    expected_transition_count=expected_count,
                ),
            )
            detected_transition_ids = {
                item.transition_id for item in sample_observations
            }
            detected_count = len(detected_transition_ids)
            missing_transition_ids = (
                set(expected_transition_ids) - detected_transition_ids
            )
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
                quality_flags_by_target_sample[(target_id, sample_id)] = (
                    sample_quality_flags
                )
            ratio_flags_for_sample: set[str] = set()
            for item in sorted(
                sample_observations, key=lambda record: record.transition_id
            ):
                ratio_observation = ratio_observation_by_target_sample_transition[
                    (target_id, sample_id, item.transition_id)
                ]
                ratio_drift_entry = fragment_ratio_drift_by_target_transition[
                    (target_id, item.transition_id)
                ]
                ratio_flagged = ratio_drift_entry.drift_flag
                if ratio_flagged:
                    ratio_flags_by_target_sample.setdefault(
                        (target_id, sample_id), set()
                    ).add(item.transition_id)
                    ratio_flags_for_sample.add(item.transition_id)
                ratio_entries.append(
                    TargetedFragmentRatioEntry(
                        target_id=target_id,
                        sample_id=sample_id,
                        transition_id=item.transition_id,
                        intensity=item.intensity,
                        total_target_intensity=total_target_intensity,
                        relative_share=ratio_observation.observed_ratio,
                        reference_relative_share=ratio_observation.expected_ratio,
                        absolute_share_delta=ratio_observation.absolute_ratio_delta,
                        ratio_cv=ratio_observation.ratio_cv,
                        drift_flag=ratio_observation.drift_flag,
                        unstable_transition_flagged=ratio_drift_entry.drift_flag,
                        flagged=ratio_flagged,
                    )
                )
            retention_time_entries.append(
                TargetedRetentionTimeConsistencyEntry(
                    target_id=target_id,
                    sample_id=sample_id,
                    observed_transition_count=len(sample_observations),
                    mean_retention_time_minutes=(
                        target_coelution_entry.mean_retention_time_minutes
                    ),
                    reference_retention_time_minutes=(
                        target_coelution_entry.reference_retention_time_minutes
                    ),
                    absolute_delta_minutes=(
                        target_coelution_entry.absolute_alignment_delta_minutes
                    ),
                    flagged=target_coelution_entry.alignment_flagged,
                )
            )

            coeluting_transition_ids: list[str] = []
            passing_transition_ids: list[str] = []
            failing_transition_ids: list[str] = []
            passing_total_intensity = 0.0
            for transition_id in expected_transition_ids:
                observation = observations_by_transition_id.get(transition_id)
                transition_coelution_entry = (
                    transition_coelution_by_target_sample_transition.get(
                        (target_id, sample_id, transition_id),
                        _missing_transition_coelution_entry(
                            target_id=target_id,
                            sample_id=sample_id,
                            transition_id=transition_id,
                        ),
                    )
                )
                if observation is None:
                    transition_qc_entries.append(
                        TargetedTransitionQcEntry(
                            target_id=target_id,
                            sample_id=sample_id,
                            condition=condition_by_sample.get(sample_id),
                            transition_id=transition_id,
                            detected=False,
                            coeluting=False,
                            passed=False,
                            failure_reasons=transition_coelution_entry.failure_reasons,
                        )
                    )
                    failing_transition_ids.append(transition_id)
                    continue

                if transition_coelution_entry.coeluting:
                    coeluting_transition_ids.append(transition_id)
                quality_flagged = (
                    observation.quality_flag is not None
                    and observation.quality_flag != "pass"
                )
                ratio_observation = ratio_observation_by_target_sample_transition[
                    (target_id, sample_id, transition_id)
                ]
                ratio_drift_entry = fragment_ratio_drift_by_target_transition[
                    (target_id, transition_id)
                ]
                ratio_flagged = transition_id in ratio_flags_for_sample
                reference_alignment_flagged = (
                    "transition is misaligned from the target reference window"
                    in transition_coelution_entry.failure_reasons
                )
                coelution_failure_reasons = tuple(
                    reason
                    for reason in transition_coelution_entry.failure_reasons
                    if reason
                    != "transition is misaligned from the target reference window"
                )
                coelution_flagged = not transition_coelution_entry.coeluting
                failure_reasons: list[str] = []
                failure_reasons.extend(coelution_failure_reasons)
                if quality_flagged:
                    failure_reasons.append("source quality flag is not pass")
                if ratio_observation.drift_flag:
                    failure_reasons.append(
                        "fragment-ion ratio deviates from the cross-run reference pattern"
                    )
                if ratio_observation.unstable_fragment or (
                    ratio_drift_entry.drift_flag and not ratio_observation.drift_flag
                ):
                    failure_reasons.append("fragment-ion ratio is unstable across runs")
                passed = not failure_reasons
                if passed:
                    passing_transition_ids.append(transition_id)
                    passing_total_intensity += observation.intensity
                else:
                    failing_transition_ids.append(transition_id)
                transition_qc_entries.append(
                    TargetedTransitionQcEntry(
                        target_id=target_id,
                        sample_id=sample_id,
                        condition=condition_by_sample.get(sample_id),
                        transition_id=transition_id,
                        detected=True,
                        intensity=observation.intensity,
                        quality_flag=observation.quality_flag,
                        relative_share=ratio_observation.observed_ratio,
                        reference_relative_share=ratio_observation.expected_ratio,
                        absolute_share_delta=ratio_observation.absolute_ratio_delta,
                        ratio_cv=ratio_observation.ratio_cv,
                        coeluting=transition_coelution_entry.coeluting,
                        coelution_flagged=coelution_flagged,
                        reference_alignment_flagged=reference_alignment_flagged,
                        coelution_delta_minutes=(
                            transition_coelution_entry.coelution_delta_minutes
                        ),
                        reference_delta_minutes=(
                            transition_coelution_entry.reference_delta_minutes
                        ),
                        quality_flagged=quality_flagged,
                        ratio_flagged=ratio_flagged,
                        ratio_drift_flagged=ratio_observation.drift_flag,
                        ratio_unstable_transition_flagged=ratio_drift_entry.drift_flag,
                        passed=passed,
                        failure_reasons=tuple(sorted(failure_reasons)),
                    )
                )

            retention_entry = retention_time_entries[-1]
            reliability_reasons: list[str] = []
            if len(coeluting_transition_ids) < 2:
                reliability_reasons.append(
                    "fewer than two coeluting transitions support the target"
                )
            elif len(passing_transition_ids) < 2:
                reliability_reasons.append(
                    "fewer than two coeluting transitions pass transition-quality review"
                )
            if retention_entry.flagged:
                reliability_reasons.append(
                    "retention time deviates from the target reference window"
                )
            transition_support_component = min(len(coeluting_transition_ids) / 2.0, 1.0)
            completeness_component = (
                len(passing_transition_ids) / expected_count if expected_count else 0.0
            )
            retention_component = 0.0 if retention_entry.flagged else 1.0
            reliability_score = (
                transition_support_component
                + completeness_component
                + retention_component
            ) / 3.0
            target_qc_entries.append(
                TargetedTargetQcEntry(
                    target_id=target_id,
                    sample_id=sample_id,
                    condition=condition_by_sample.get(sample_id),
                    expected_transition_count=expected_count,
                    observed_transition_count=detected_count,
                    coeluting_transition_count=len(coeluting_transition_ids),
                    coeluting_transition_ids=tuple(sorted(coeluting_transition_ids)),
                    passing_transition_count=len(passing_transition_ids),
                    passing_transition_ids=tuple(passing_transition_ids),
                    failing_transition_ids=tuple(sorted(failing_transition_ids)),
                    passing_total_intensity=(
                        passing_total_intensity if passing_transition_ids else None
                    ),
                    mean_retention_time_minutes=retention_entry.mean_retention_time_minutes,
                    reference_retention_time_minutes=(
                        retention_entry.reference_retention_time_minutes
                    ),
                    absolute_delta_minutes=retention_entry.absolute_delta_minutes,
                    quality_flag_count=len(sample_quality_flags),
                    reliability_score=reliability_score,
                    reliable=not reliability_reasons,
                    reliability_reasons=tuple(sorted(reliability_reasons)),
                )
            )

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
                sorted(
                    quality_flags_by_target_sample.get((target_id, sample_id), set())
                )
            )
            consistency_entry = next(
                entry
                for entry in consistency_entries
                if entry.target_id == target_id and entry.sample_id == sample_id
            )
            if consistency_entry.consistency_fraction < 1.0:
                reasons.append("transition detection is incomplete")
            target_qc_entry = next(
                entry
                for entry in target_qc_entries
                if entry.target_id == target_id and entry.sample_id == sample_id
            )
            if target_qc_entry.coeluting_transition_count < 2:
                reasons.append(
                    "fewer than two coeluting transitions support the target"
                )
            elif target_qc_entry.passing_transition_count < 2:
                reasons.append(
                    "fewer than two coeluting transitions pass transition-quality review"
                )
            sample_ratio_flags = ratio_flags_by_target_sample.get(
                (target_id, sample_id), set()
            )
            if sample_ratio_flags:
                sample_ratio_observations = [
                    ratio_observation_by_target_sample_transition[
                        (target_id, sample_id, transition_id)
                    ]
                    for transition_id in sample_ratio_flags
                ]
                sample_ratio_drift_entries = [
                    fragment_ratio_drift_by_target_transition[
                        (target_id, transition_id)
                    ]
                    for transition_id in sample_ratio_flags
                ]
                if any(entry.drift_flag for entry in sample_ratio_observations):
                    reasons.append(
                        "fragment-ion ratios deviate from the cross-run reference pattern"
                    )
                elif any(entry.drift_flag for entry in sample_ratio_drift_entries):
                    reasons.append("fragment-ion ratios are unstable across runs")
            retention_entry = next(
                entry
                for entry in retention_time_entries
                if entry.target_id == target_id and entry.sample_id == sample_id
            )
            if retention_entry.flagged:
                reasons.append(
                    "retention time deviates from the target reference window"
                )
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
            for entry in target_qc_entries:
                if entry.target_id == target_id and entry.condition == condition:
                    target_qc_entries[target_qc_entries.index(entry)] = (
                        entry.model_copy(
                            update={
                                "condition_replicate_cv": coefficient_of_variation,
                                "condition_replicate_cv_flagged": flagged,
                                "reliability_score": (
                                    (
                                        entry.reliability_score * 3.0
                                        + (0.0 if flagged else 1.0)
                                    )
                                    / 4.0
                                ),
                                "reliable": entry.reliable and not flagged,
                                "reliability_reasons": (
                                    entry.reliability_reasons
                                    if not flagged
                                    else tuple(
                                        sorted(
                                            set(entry.reliability_reasons).union(
                                                {
                                                    "replicate cv is above the configured threshold"
                                                }
                                            )
                                        )
                                    )
                                ),
                            }
                        )
                    )

    return TargetedAssayQcReport(
        source_name=import_report.source_name,
        transition_coelution=transition_coelution,
        fragment_ratio_stability=fragment_ratio_stability,
        target_qc=tuple(
            sorted(
                target_qc_entries,
                key=lambda entry: (
                    entry.target_id,
                    entry.sample_id,
                ),
            )
        ),
        transition_consistency=tuple(consistency_entries),
        transition_qc=tuple(
            sorted(
                transition_qc_entries,
                key=lambda entry: (
                    entry.target_id,
                    entry.sample_id,
                    entry.transition_id,
                ),
            )
        ),
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
            target_qc_entry_count=len(target_qc_entries),
            reliable_target_entry_count=sum(
                entry.reliable for entry in target_qc_entries
            ),
            transition_consistency_entry_count=len(consistency_entries),
            coelution_target_entry_count=len(transition_coelution.target_entries),
            flagged_coelution_target_entry_count=sum(
                not entry.reliable_transition_support
                for entry in transition_coelution.target_entries
            ),
            transition_coelution_entry_count=len(
                transition_coelution.transition_entries
            ),
            coeluting_transition_entry_count=sum(
                entry.coeluting for entry in transition_coelution.transition_entries
            ),
            transition_qc_entry_count=len(transition_qc_entries),
            passing_transition_qc_entry_count=sum(
                entry.passed for entry in transition_qc_entries
            ),
            fragment_ratio_entry_count=len(ratio_entries),
            fragment_ratio_stability_fragment_entry_count=len(
                fragment_ratio_stability.fragment_entries
            ),
            unstable_fragment_ratio_entry_count=(
                fragment_ratio_stability.summary.unstable_fragment_count
            ),
            drift_flagged_fragment_ratio_observation_count=(
                fragment_ratio_stability.summary.drift_flagged_observation_count
            ),
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
            "targeted assay qc keeps target-level reliability, transition-level pass-fail evidence, transition consistency, transition coelution, fragment-ion ratio stability, retention-time consistency, replicate cv, and explicit unreliable-target review visible before any sample or target is trusted"
        ),
    )


def build_skyline_targeted_assay_qc_report(path: Path) -> TargetedAssayQcReport:
    """Build targeted assay QC directly from one Skyline-style export."""

    return build_targeted_assay_qc_report(build_skyline_result_import_report(path))


def build_transition_table_targeted_assay_qc_report(
    path: Path,
) -> TargetedAssayQcReport:
    """Build targeted assay QC directly from one exported transition table."""

    return build_targeted_assay_qc_report(
        build_transition_table_result_import_report(path)
    )


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
    return float(variance**0.5 / mean_value)


def _fragment_ratio_matrix(
    import_report: TargetedResultImportReport,
) -> tuple[TargetedFragmentRatioMatrixEntry, ...]:
    return tuple(
        TargetedFragmentRatioMatrixEntry(
            target_id=observation.precursor_id,
            sample_id=observation.sample_id,
            transition_id=observation.transition_id,
            intensity=observation.intensity,
        )
        for observation in import_report.observations
    )

# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Assess targeted biomarker stability across study subgroups."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
import math
from statistics import mean, median

from bijux_proteomics.io import ExperimentalDesignEntry
from bijux_proteomics.targeted.assay_qc import (
    TargetedTargetQcEntry,
    build_targeted_assay_qc_report,
)
from bijux_proteomics.targeted.biomarker_stability.matching import (
    _ImportedTargetDescriptor,
    _build_imported_target_descriptors,
    _compute_assay_agreement_score,
    _match_assay_target_ids,
)
from bijux_proteomics.targeted.biomarker_stability.models import (
    BiomarkerStabilityDimension,
    BiomarkerStabilityEntry,
    BiomarkerStabilityPolicy,
    BiomarkerStabilityReasonCode,
    BiomarkerStabilityReport,
    BiomarkerStabilitySummary,
    BiomarkerSubgroupBehaviorEntry,
    BiomarkerSubgroupBehaviorStatus,
)
from bijux_proteomics.targeted.result_import import TargetedResultImportReport
from bijux_proteomics.targeted.result_validation import (
    TargetedValidationDiscoveryClaimInput,
    TargetedValidationPanelAssayInput,
)


@dataclass(frozen=True)
class _CandidateSignalAssessment:
    candidate_sample_values: dict[str, float]
    reliable_sample_ids: set[str]
    matched_target_ids: set[str]
    reliable_sample_count: int
    reliable_sample_fraction: float
    condition_values_with_signal: tuple[str, ...]
    condition_breadth_score: float
    assay_agreement_score: float


@dataclass(frozen=True)
class _CandidateSubgroupAssessment:
    subgroup_entries: tuple[BiomarkerSubgroupBehaviorEntry, ...]
    instability_reasons: tuple[BiomarkerStabilityReasonCode, ...]
    component_scores: tuple[float, ...]
    batch_stability_score: float | None
    timepoint_stability_score: float | None
    sample_type_stability_score: float | None


def build_biomarker_stability_report(
    biomarker_candidates: tuple[TargetedValidationDiscoveryClaimInput, ...],
    panel_assays: tuple[TargetedValidationPanelAssayInput, ...],
    import_report: TargetedResultImportReport,
    design_entries: tuple[ExperimentalDesignEntry, ...],
    *,
    policy: BiomarkerStabilityPolicy | None = None,
) -> BiomarkerStabilityReport:
    """Assess candidate stability across conditions and technical subgroups."""

    active_policy = policy or BiomarkerStabilityPolicy()
    assay_qc_report = build_targeted_assay_qc_report(import_report, design_entries)
    descriptors = _build_imported_target_descriptors(import_report)
    qc_by_target_sample = {
        (entry.target_id, entry.sample_id): entry for entry in assay_qc_report.target_qc
    }
    design_by_sample = {
        entry.sample_id: entry
        for entry in design_entries
        if entry.sample_id in {item.sample_id for item in import_report.observations}
    }
    total_sample_ids = tuple(sorted(design_by_sample))
    total_condition_values = tuple(
        sorted(
            {entry.condition for entry in design_by_sample.values() if entry.condition}
        )
    )

    assays_by_candidate: dict[str, list[TargetedValidationPanelAssayInput]] = {}
    for assay in panel_assays:
        assays_by_candidate.setdefault(assay.biomarker_candidate_id, []).append(assay)

    entries_with_aux: list[tuple[BiomarkerStabilityEntry, tuple[str, ...]]] = []
    subgroup_behavior_entries: list[BiomarkerSubgroupBehaviorEntry] = []
    for candidate in sorted(
        biomarker_candidates,
        key=lambda item: (item.priority_rank, item.candidate_id),
    ):
        candidate_assays = tuple(
            sorted(
                assays_by_candidate.get(candidate.candidate_id, ()),
                key=lambda item: (item.biomarker_priority_rank, item.assay_entry_id),
            )
        )
        candidate_entry, candidate_subgroups, rank_reason_codes = (
            _build_candidate_entry(
                candidate=candidate,
                assays=candidate_assays,
                descriptors=descriptors,
                qc_by_target_sample=qc_by_target_sample,
                design_by_sample=design_by_sample,
                total_sample_ids=total_sample_ids,
                total_condition_values=total_condition_values,
                policy=active_policy,
            )
        )
        entries_with_aux.append((candidate_entry, rank_reason_codes))
        subgroup_behavior_entries.extend(candidate_subgroups)

    ranked_entries_with_aux = sorted(
        entries_with_aux,
        key=lambda item: (
            -item[0].adjusted_final_score,
            item[0].original_priority_rank,
            item[0].candidate_id,
        ),
    )
    ranked_entries: list[BiomarkerStabilityEntry] = []
    for rank, (entry, _rank_reason_codes) in enumerate(
        ranked_entries_with_aux, start=1
    ):
        ranked_entries.append(entry.model_copy(update={"adjusted_priority_rank": rank}))

    return BiomarkerStabilityReport(
        source_name=import_report.source_name,
        policy=active_policy,
        entries=tuple(ranked_entries),
        subgroup_behavior=tuple(
            sorted(
                subgroup_behavior_entries,
                key=lambda item: (
                    item.candidate_id,
                    item.dimension.value,
                    item.subgroup_value,
                ),
            )
        ),
        summary=BiomarkerStabilitySummary(
            candidate_count=len(ranked_entries),
            downgraded_candidate_count=sum(item.downgraded for item in ranked_entries),
            low_reliable_sample_fraction_count=sum(
                BiomarkerStabilityReasonCode.LOW_RELIABLE_SAMPLE_FRACTION
                in item.instability_reasons
                for item in ranked_entries
            ),
            single_condition_signal_only_count=sum(
                BiomarkerStabilityReasonCode.SINGLE_CONDITION_SIGNAL_ONLY
                in item.instability_reasons
                for item in ranked_entries
            ),
            batch_sensitive_candidate_count=sum(
                BiomarkerStabilityReasonCode.BATCH_SENSITIVE_SIGNAL
                in item.instability_reasons
                for item in ranked_entries
            ),
            timepoint_sensitive_candidate_count=sum(
                BiomarkerStabilityReasonCode.TIMEPOINT_SENSITIVE_SIGNAL
                in item.instability_reasons
                for item in ranked_entries
            ),
            sample_type_sensitive_candidate_count=sum(
                BiomarkerStabilityReasonCode.SAMPLE_TYPE_SENSITIVE_SIGNAL
                in item.instability_reasons
                for item in ranked_entries
            ),
            assay_disagreement_candidate_count=sum(
                BiomarkerStabilityReasonCode.ASSAY_DISAGREEMENT
                in item.instability_reasons
                for item in ranked_entries
            ),
            sparse_subgroup_candidate_count=sum(
                BiomarkerStabilityReasonCode.SPARSE_SUBGROUP_COVERAGE
                in item.instability_reasons
                for item in ranked_entries
            ),
        ),
        note=(
            "biomarker stability scores candidates from targeted subgroup behavior across "
            "conditions, batches, timepoints, and sample types so one-contrast hits with "
            "unstable technical or subgroup behavior are downgraded before downstream panel selection"
        ),
    )


def _build_candidate_entry(
    *,
    candidate: TargetedValidationDiscoveryClaimInput,
    assays: tuple[TargetedValidationPanelAssayInput, ...],
    descriptors: tuple[_ImportedTargetDescriptor, ...],
    qc_by_target_sample: Mapping[tuple[str, str], TargetedTargetQcEntry],
    design_by_sample: dict[str, ExperimentalDesignEntry],
    total_sample_ids: tuple[str, ...],
    total_condition_values: tuple[str, ...],
    policy: BiomarkerStabilityPolicy,
) -> tuple[
    BiomarkerStabilityEntry, list[BiomarkerSubgroupBehaviorEntry], tuple[str, ...]
]:
    signal_assessment = _assess_candidate_signal(
        assays=assays,
        descriptors=descriptors,
        qc_by_target_sample=qc_by_target_sample,
        design_by_sample=design_by_sample,
        total_sample_ids=total_sample_ids,
        total_condition_values=total_condition_values,
        assay_disagreement_delta_threshold=policy.assay_disagreement_delta_threshold,
    )
    subgroup_assessment = _assess_candidate_subgroups(
        candidate_id=candidate.candidate_id,
        signal_assessment=signal_assessment,
        design_by_sample=design_by_sample,
        policy=policy,
    )
    deduped_reasons = tuple(
        dict.fromkeys(
            (
                *_signal_instability_reasons(
                    signal_assessment=signal_assessment,
                    total_condition_values=total_condition_values,
                    policy=policy,
                ),
                *subgroup_assessment.instability_reasons,
            )
        )
    )
    stability_score = _stability_score(
        signal_assessment=signal_assessment,
        subgroup_assessment=subgroup_assessment,
        instability_reasons=deduped_reasons,
        total_condition_values=total_condition_values,
        policy=policy,
    )
    stability_penalty = 1.0 - stability_score
    adjusted_final_score = max(0.0, min(1.0, candidate.final_score * stability_score))
    adjusted_penalty_total = candidate.penalty_total + stability_penalty
    downgraded = stability_score < policy.downgrade_below_score
    note = _build_candidate_note(
        candidate,
        stability_score=stability_score,
        reasons=deduped_reasons,
        reliable_sample_count=signal_assessment.reliable_sample_count,
        total_sample_count=len(total_sample_ids),
        condition_count_with_signal=len(signal_assessment.condition_values_with_signal),
        total_condition_count=len(total_condition_values),
    )
    rank_reason_codes = candidate.rank_reason_codes + tuple(
        reason.value for reason in deduped_reasons
    )
    return (
        BiomarkerStabilityEntry(
            candidate_id=candidate.candidate_id,
            candidate_kind=candidate.candidate_kind,
            display_label=candidate.display_label,
            target_protein_ref=candidate.target_protein_ref,
            site_key=candidate.site_key,
            original_priority_rank=candidate.priority_rank,
            adjusted_priority_rank=candidate.priority_rank,
            original_final_score=candidate.final_score,
            adjusted_final_score=adjusted_final_score,
            original_penalty_total=candidate.penalty_total,
            adjusted_penalty_total=adjusted_penalty_total,
            stability_penalty=stability_penalty,
            stability_score=stability_score,
            reliable_sample_fraction=signal_assessment.reliable_sample_fraction,
            condition_breadth_score=signal_assessment.condition_breadth_score,
            assay_agreement_score=signal_assessment.assay_agreement_score,
            batch_stability_score=subgroup_assessment.batch_stability_score,
            timepoint_stability_score=subgroup_assessment.timepoint_stability_score,
            sample_type_stability_score=subgroup_assessment.sample_type_stability_score,
            reliable_sample_count=signal_assessment.reliable_sample_count,
            total_sample_count=len(total_sample_ids),
            condition_count_with_signal=len(signal_assessment.condition_values_with_signal),
            total_condition_count=len(total_condition_values),
            assay_entry_count=len(assays),
            matched_target_count=len(signal_assessment.matched_target_ids),
            downgraded=downgraded,
            instability_reasons=deduped_reasons,
            subgroup_behavior_count=len(subgroup_assessment.subgroup_entries),
            note=note,
        ),
        list(subgroup_assessment.subgroup_entries),
        rank_reason_codes,
    )


def _assess_candidate_signal(
    *,
    assays: tuple[TargetedValidationPanelAssayInput, ...],
    descriptors: tuple[_ImportedTargetDescriptor, ...],
    qc_by_target_sample: Mapping[tuple[str, str], TargetedTargetQcEntry],
    design_by_sample: dict[str, ExperimentalDesignEntry],
    total_sample_ids: tuple[str, ...],
    total_condition_values: tuple[str, ...],
    assay_disagreement_delta_threshold: float,
) -> _CandidateSignalAssessment:
    assay_values_by_sample, reliable_sample_ids, matched_target_ids = (
        _collect_assay_values_by_sample(
            assays=assays,
            descriptors=descriptors,
            qc_by_target_sample=qc_by_target_sample,
            design_by_sample=design_by_sample,
        )
    )
    candidate_sample_values = {
        sample_id: mean(assay_values.values())
        for sample_id, assay_values in assay_values_by_sample.items()
        if assay_values
    }
    reliable_sample_count = len(
        set(candidate_sample_values).intersection(reliable_sample_ids)
    )
    total_sample_count = len(total_sample_ids)
    reliable_sample_fraction = (
        reliable_sample_count / total_sample_count if total_sample_count else 0.0
    )
    condition_values_with_signal = tuple(
        sorted(
            {
                design_by_sample[sample_id].condition
                for sample_id in candidate_sample_values
                if sample_id in design_by_sample
            }
        )
    )
    condition_breadth_score = (
        len(condition_values_with_signal) / len(total_condition_values)
        if total_condition_values
        else 0.0
    )
    assay_agreement_score = _compute_assay_agreement_score(
        assay_values_by_sample,
        disagreement_delta_threshold=assay_disagreement_delta_threshold,
    )
    return _CandidateSignalAssessment(
        candidate_sample_values=candidate_sample_values,
        reliable_sample_ids=reliable_sample_ids,
        matched_target_ids=matched_target_ids,
        reliable_sample_count=reliable_sample_count,
        reliable_sample_fraction=reliable_sample_fraction,
        condition_values_with_signal=condition_values_with_signal,
        condition_breadth_score=condition_breadth_score,
        assay_agreement_score=assay_agreement_score,
    )


def _collect_assay_values_by_sample(
    *,
    assays: tuple[TargetedValidationPanelAssayInput, ...],
    descriptors: tuple[_ImportedTargetDescriptor, ...],
    qc_by_target_sample: Mapping[tuple[str, str], TargetedTargetQcEntry],
    design_by_sample: dict[str, ExperimentalDesignEntry],
) -> tuple[dict[str, dict[str, float]], set[str], set[str]]:
    target_ids_by_assay = {
        assay.assay_entry_id: _match_assay_target_ids(assay, descriptors)
        for assay in assays
    }
    assay_values_by_sample: dict[str, dict[str, float]] = {}
    reliable_sample_ids: set[str] = set()
    matched_target_ids: set[str] = set()
    for assay in assays:
        for target_id in target_ids_by_assay[assay.assay_entry_id]:
            matched_target_ids.add(target_id)
            for sample_id in design_by_sample:
                qc_entry = qc_by_target_sample.get((target_id, sample_id))
                if qc_entry is None or not _positive_intensity(qc_entry):
                    continue
                assay_values_by_sample.setdefault(sample_id, {})[
                    assay.assay_entry_id
                ] = math.log2(qc_entry.passing_total_intensity)
                if qc_entry.reliable:
                    reliable_sample_ids.add(sample_id)
    return assay_values_by_sample, reliable_sample_ids, matched_target_ids


def _positive_intensity(qc_entry: TargetedTargetQcEntry) -> bool:
    return (
        qc_entry.passing_total_intensity is not None
        and qc_entry.passing_total_intensity > 0.0
    )


def _signal_instability_reasons(
    *,
    signal_assessment: _CandidateSignalAssessment,
    total_condition_values: tuple[str, ...],
    policy: BiomarkerStabilityPolicy,
) -> tuple[BiomarkerStabilityReasonCode, ...]:
    reasons: list[BiomarkerStabilityReasonCode] = []
    if not signal_assessment.matched_target_ids:
        reasons.append(BiomarkerStabilityReasonCode.NO_MATCHING_TARGETED_SIGNAL)
    if (
        signal_assessment.reliable_sample_fraction
        < policy.minimum_reliable_sample_fraction
    ):
        reasons.append(BiomarkerStabilityReasonCode.LOW_RELIABLE_SAMPLE_FRACTION)
    if len(signal_assessment.condition_values_with_signal) <= 1 and total_condition_values:
        reasons.append(BiomarkerStabilityReasonCode.SINGLE_CONDITION_SIGNAL_ONLY)
    if signal_assessment.assay_agreement_score < 1.0:
        reasons.append(BiomarkerStabilityReasonCode.ASSAY_DISAGREEMENT)
    return tuple(reasons)


def _assess_candidate_subgroups(
    *,
    candidate_id: str,
    signal_assessment: _CandidateSignalAssessment,
    design_by_sample: dict[str, ExperimentalDesignEntry],
    policy: BiomarkerStabilityPolicy,
) -> _CandidateSubgroupAssessment:
    subgroup_entries: list[BiomarkerSubgroupBehaviorEntry] = []
    component_scores: list[float] = []
    instability_reasons: list[BiomarkerStabilityReasonCode] = []

    condition_dimension = _build_subgroup_dimension_entries(
        candidate_id=candidate_id,
        dimension=BiomarkerStabilityDimension.CONDITION,
        group_values={
            sample_id: design_by_sample[sample_id].condition
            for sample_id in signal_assessment.candidate_sample_values
            if sample_id in design_by_sample and design_by_sample[sample_id].condition
        },
        sample_values=signal_assessment.candidate_sample_values,
        reliable_sample_ids=signal_assessment.reliable_sample_ids,
        minimum_reliable_samples_per_group=policy.minimum_reliable_samples_per_group,
    )
    subgroup_entries.extend(condition_dimension[0])

    dimension_results = {
        BiomarkerStabilityDimension.BATCH: _build_batch_entries(
            candidate_id=candidate_id,
            sample_values=signal_assessment.candidate_sample_values,
            reliable_sample_ids=signal_assessment.reliable_sample_ids,
            design_by_sample=design_by_sample,
            batch_field=policy.batch_field,
            minimum_reliable_samples_per_group=policy.minimum_reliable_samples_per_group,
            residual_delta_threshold=policy.batch_residual_delta_threshold,
        ),
        BiomarkerStabilityDimension.TIMEPOINT: _build_subgroup_dimension_entries(
            candidate_id=candidate_id,
            dimension=BiomarkerStabilityDimension.TIMEPOINT,
            group_values=_group_values_for_dimension(
                sample_ids=signal_assessment.candidate_sample_values,
                design_by_sample=design_by_sample,
                field_name=policy.timepoint_field,
            ),
            sample_values=signal_assessment.candidate_sample_values,
            reliable_sample_ids=signal_assessment.reliable_sample_ids,
            minimum_reliable_samples_per_group=policy.minimum_reliable_samples_per_group,
            median_delta_threshold=policy.subgroup_median_delta_threshold,
            instability_reason=BiomarkerStabilityReasonCode.TIMEPOINT_SENSITIVE_SIGNAL,
        ),
        BiomarkerStabilityDimension.SAMPLE_TYPE: _build_subgroup_dimension_entries(
            candidate_id=candidate_id,
            dimension=BiomarkerStabilityDimension.SAMPLE_TYPE,
            group_values=_group_values_for_dimension(
                sample_ids=signal_assessment.candidate_sample_values,
                design_by_sample=design_by_sample,
                field_name=policy.sample_type_field,
            ),
            sample_values=signal_assessment.candidate_sample_values,
            reliable_sample_ids=signal_assessment.reliable_sample_ids,
            minimum_reliable_samples_per_group=policy.minimum_reliable_samples_per_group,
            median_delta_threshold=policy.subgroup_median_delta_threshold,
            instability_reason=BiomarkerStabilityReasonCode.SAMPLE_TYPE_SENSITIVE_SIGNAL,
        ),
    }
    for entries, score, reason, sparse in dimension_results.values():
        subgroup_entries.extend(entries)
        if score is not None:
            component_scores.append(score)
        if sparse:
            instability_reasons.append(
                BiomarkerStabilityReasonCode.SPARSE_SUBGROUP_COVERAGE
            )
        if reason is not None:
            instability_reasons.append(reason)

    return _CandidateSubgroupAssessment(
        subgroup_entries=tuple(subgroup_entries),
        instability_reasons=tuple(instability_reasons),
        component_scores=tuple(component_scores),
        batch_stability_score=dimension_results[BiomarkerStabilityDimension.BATCH][1],
        timepoint_stability_score=dimension_results[
            BiomarkerStabilityDimension.TIMEPOINT
        ][1],
        sample_type_stability_score=dimension_results[
            BiomarkerStabilityDimension.SAMPLE_TYPE
        ][1],
    )


def _stability_score(
    *,
    signal_assessment: _CandidateSignalAssessment,
    subgroup_assessment: _CandidateSubgroupAssessment,
    instability_reasons: tuple[BiomarkerStabilityReasonCode, ...],
    total_condition_values: tuple[str, ...],
    policy: BiomarkerStabilityPolicy,
) -> float:
    component_scores = (
        signal_assessment.reliable_sample_fraction,
        signal_assessment.condition_breadth_score,
        signal_assessment.assay_agreement_score,
        *subgroup_assessment.component_scores,
    )
    stability_score = (
        max(0.0, min(1.0, mean(component_scores))) if component_scores else 0.0
    )
    if (
        BiomarkerStabilityReasonCode.SINGLE_CONDITION_SIGNAL_ONLY in instability_reasons
        and total_condition_values
    ):
        return min(
            stability_score,
            max(0.0, policy.downgrade_below_score - 0.05),
        )
    return stability_score


def _build_subgroup_dimension_entries(
    *,
    candidate_id: str,
    dimension: BiomarkerStabilityDimension,
    group_values: dict[str, str],
    sample_values: dict[str, float],
    reliable_sample_ids: set[str],
    minimum_reliable_samples_per_group: int,
    median_delta_threshold: float | None = None,
    instability_reason: BiomarkerStabilityReasonCode | None = None,
) -> tuple[
    list[BiomarkerSubgroupBehaviorEntry],
    float | None,
    BiomarkerStabilityReasonCode | None,
    bool,
]:
    grouped: dict[str, list[float]] = {}
    reliable_counts: dict[str, int] = {}
    totals: dict[str, int] = {}
    for sample_id, subgroup_value in group_values.items():
        totals[subgroup_value] = totals.get(subgroup_value, 0) + 1
        if sample_id in sample_values:
            grouped.setdefault(subgroup_value, []).append(sample_values[sample_id])
        if sample_id in reliable_sample_ids and sample_id in sample_values:
            reliable_counts[subgroup_value] = reliable_counts.get(subgroup_value, 0) + 1
    if not totals:
        return [], None, None, False

    entries: list[BiomarkerSubgroupBehaviorEntry] = []
    valid_medians: list[float] = []
    sparse = False
    for subgroup_value in sorted(totals):
        values = grouped.get(subgroup_value, [])
        reliable_count = reliable_counts.get(subgroup_value, 0)
        status = BiomarkerSubgroupBehaviorStatus.STABLE
        if reliable_count < minimum_reliable_samples_per_group:
            status = (
                BiomarkerSubgroupBehaviorStatus.UNSUPPORTED
                if not values
                else BiomarkerSubgroupBehaviorStatus.SPARSE
            )
            sparse = True
        if values:
            subgroup_median = median(values)
            subgroup_mean = mean(values)
            subgroup_cv = _coefficient_of_variation(values)
            valid_medians.append(subgroup_median)
            note = (
                f"{dimension.value} subgroup {subgroup_value} keeps "
                f"{len(values)} reliable targeted samples"
            )
        else:
            subgroup_median = None
            subgroup_mean = None
            subgroup_cv = None
            note = f"{dimension.value} subgroup {subgroup_value} has no reliable targeted samples"
        entries.append(
            BiomarkerSubgroupBehaviorEntry(
                candidate_id=candidate_id,
                dimension=dimension,
                subgroup_value=subgroup_value,
                reliable_sample_count=reliable_count,
                total_sample_count=totals[subgroup_value],
                mean_log2_intensity=subgroup_mean,
                median_log2_intensity=subgroup_median,
                coefficient_of_variation=subgroup_cv,
                status=status,
                note=note,
            )
        )

    score = None
    reason = None
    if (
        median_delta_threshold is not None
        and len(valid_medians) >= 2
        and all(
            len(grouped.get(entry.subgroup_value, ()))
            >= minimum_reliable_samples_per_group
            for entry in entries
            if grouped.get(entry.subgroup_value)
        )
    ):
        spread = max(valid_medians) - min(valid_medians)
        score = max(0.0, min(1.0, 1.0 - (spread / median_delta_threshold)))
        if instability_reason is not None and spread > median_delta_threshold:
            reason = instability_reason
        for index, entry in enumerate(entries):
            if entry.reliable_sample_count >= minimum_reliable_samples_per_group:
                entries[index] = entry.model_copy(
                    update={
                        "status": (
                            BiomarkerSubgroupBehaviorStatus.VARIABLE
                            if reason is not None
                            else BiomarkerSubgroupBehaviorStatus.STABLE
                        ),
                        "note": (
                            f"{entry.note}; subgroup median spread is {spread:.3f} log2"
                            if entry.median_log2_intensity is not None
                            else entry.note
                        ),
                    }
                )
    return entries, score, reason, sparse


def _build_batch_entries(
    *,
    candidate_id: str,
    sample_values: dict[str, float],
    reliable_sample_ids: set[str],
    design_by_sample: dict[str, ExperimentalDesignEntry],
    batch_field: str,
    minimum_reliable_samples_per_group: int,
    residual_delta_threshold: float,
) -> tuple[
    list[BiomarkerSubgroupBehaviorEntry],
    float | None,
    BiomarkerStabilityReasonCode | None,
    bool,
]:
    group_values = {
        sample_id: group_value
        for sample_id in sample_values
        if sample_id in design_by_sample
        for group_value in [
            _design_dimension_value(design_by_sample[sample_id], batch_field)
        ]
        if group_value is not None
    }
    if not group_values:
        return [], None, None, False

    condition_medians = {
        condition: median([sample_values[sample_id] for sample_id in sample_ids])
        for condition, sample_ids in _group_sample_ids_by_condition(
            sample_values, design_by_sample
        ).items()
    }
    residual_values = {
        sample_id: sample_values[sample_id]
        - condition_medians.get(design_by_sample[sample_id].condition, 0.0)
        for sample_id in group_values
    }

    entries, score, _reason, sparse = _build_subgroup_dimension_entries(
        candidate_id=candidate_id,
        dimension=BiomarkerStabilityDimension.BATCH,
        group_values=group_values,
        sample_values=residual_values,
        reliable_sample_ids=reliable_sample_ids,
        minimum_reliable_samples_per_group=minimum_reliable_samples_per_group,
        median_delta_threshold=residual_delta_threshold,
        instability_reason=BiomarkerStabilityReasonCode.BATCH_SENSITIVE_SIGNAL,
    )
    updated_entries = []
    for entry in entries:
        residuals = [
            residual_values[sample_id]
            for sample_id, value in group_values.items()
            if value == entry.subgroup_value and sample_id in residual_values
        ]
        updated_entries.append(
            entry.model_copy(
                update={
                    "residual_median_log2_intensity": (
                        None if not residuals else median(residuals)
                    ),
                    "note": (
                        f"{entry.note}; batch residuals are condition-normalized"
                        if entry.reliable_sample_count > 0
                        else entry.note
                    ),
                }
            )
        )
    reason = None
    if score is not None and score < 1.0:
        spread = max(
            entry.residual_median_log2_intensity or 0.0 for entry in updated_entries
        ) - min(
            entry.residual_median_log2_intensity or 0.0 for entry in updated_entries
        )
        if spread > residual_delta_threshold:
            reason = BiomarkerStabilityReasonCode.BATCH_SENSITIVE_SIGNAL
    return updated_entries, score, reason, sparse


def _group_sample_ids_by_condition(
    sample_values: dict[str, float],
    design_by_sample: dict[str, ExperimentalDesignEntry],
) -> dict[str, list[str]]:
    grouped: dict[str, list[str]] = {}
    for sample_id in sample_values:
        if sample_id not in design_by_sample:
            continue
        grouped.setdefault(design_by_sample[sample_id].condition, []).append(sample_id)
    return grouped


def _group_values_for_dimension(
    *,
    sample_ids: Iterable[str],
    design_by_sample: dict[str, ExperimentalDesignEntry],
    field_name: str,
) -> dict[str, str]:
    grouped: dict[str, str] = {}
    for sample_id in sample_ids:
        design_entry = design_by_sample.get(sample_id)
        if design_entry is None:
            continue
        group_value = _design_dimension_value(design_entry, field_name)
        if group_value is not None:
            grouped[sample_id] = group_value
    return grouped


def _design_dimension_value(
    design_entry: ExperimentalDesignEntry,
    field_name: str,
) -> str | None:
    if field_name == "condition":
        return str(design_entry.condition)
    if field_name == "batch":
        return None if design_entry.batch is None else str(design_entry.batch)
    direct = getattr(design_entry, field_name, None)
    if isinstance(direct, str) and direct.strip():
        return direct.strip()
    metadata_value = design_entry.metadata.get(field_name)
    if metadata_value is None:
        return None
    stripped = metadata_value.strip()
    return stripped or None


def _build_candidate_note(
    candidate: TargetedValidationDiscoveryClaimInput,
    *,
    stability_score: float,
    reasons: tuple[BiomarkerStabilityReasonCode, ...],
    reliable_sample_count: int,
    total_sample_count: int,
    condition_count_with_signal: int,
    total_condition_count: int,
) -> str:
    if not reasons:
        return (
            f"{candidate.display_label} stays stable with score {stability_score:.3f} "
            f"across {reliable_sample_count}/{total_sample_count} reliable targeted samples "
            f"and signal in {condition_count_with_signal}/{total_condition_count} conditions"
        )
    return (
        f"{candidate.display_label} is downgraded to stability score {stability_score:.3f} "
        f"because {', '.join(reason.value for reason in reasons)} while keeping "
        f"{reliable_sample_count}/{total_sample_count} reliable targeted samples and signal in "
        f"{condition_count_with_signal}/{total_condition_count} conditions"
    )


def _coefficient_of_variation(values: list[float]) -> float | None:
    if len(values) < 2:
        return None
    value_mean = mean(values)
    if value_mean == 0.0:
        return 0.0
    variance = sum((value - value_mean) ** 2 for value in values) / (len(values) - 1)
    return math.sqrt(variance) / abs(value_mean)

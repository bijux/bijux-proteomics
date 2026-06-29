# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Assess targeted biomarker stability across study subgroups."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
import math
from statistics import mean, median

from bijux_proteomics.io import ExperimentalDesignEntry
from bijux_proteomics.sequences import PeptideUniquenessClass
from bijux_proteomics.targeted.assay_qc import (
    TargetedTargetQcEntry,
    build_targeted_assay_qc_report,
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
class _ImportedTargetDescriptor:
    target_id: str
    peptide_sequence: str
    precursor_charge: int | None
    protein_refs: tuple[str, ...]


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
            for sample_id, _design_entry in design_by_sample.items():
                qc_entry = qc_by_target_sample.get((target_id, sample_id))
                if qc_entry is None:
                    continue
                if (
                    qc_entry.passing_total_intensity is None
                    or qc_entry.passing_total_intensity <= 0.0
                ):
                    continue
                assay_values_by_sample.setdefault(sample_id, {})[
                    assay.assay_entry_id
                ] = math.log2(qc_entry.passing_total_intensity)
                if qc_entry.reliable:
                    reliable_sample_ids.add(sample_id)

    candidate_sample_values = {
        sample_id: mean(assay_values.values())
        for sample_id, assay_values in assay_values_by_sample.items()
        if assay_values
    }
    reliable_sample_count = len(
        {
            sample_id
            for sample_id in candidate_sample_values
            if sample_id in reliable_sample_ids
        }
    )
    total_sample_count = len(total_sample_ids)
    reliable_sample_fraction = (
        reliable_sample_count / total_sample_count if total_sample_count else 0.0
    )
    condition_values_with_signal = {
        design_by_sample[sample_id].condition
        for sample_id in candidate_sample_values
        if sample_id in design_by_sample
    }
    condition_breadth_score = (
        len(condition_values_with_signal) / len(total_condition_values)
        if total_condition_values
        else 0.0
    )
    assay_agreement_score = _compute_assay_agreement_score(
        assay_values_by_sample,
        disagreement_delta_threshold=policy.assay_disagreement_delta_threshold,
    )

    subgroup_entries: list[BiomarkerSubgroupBehaviorEntry] = []
    instability_reasons: list[BiomarkerStabilityReasonCode] = []
    component_scores: list[float] = [
        reliable_sample_fraction,
        condition_breadth_score,
        assay_agreement_score,
    ]
    if not matched_target_ids:
        instability_reasons.append(
            BiomarkerStabilityReasonCode.NO_MATCHING_TARGETED_SIGNAL
        )
    if reliable_sample_fraction < policy.minimum_reliable_sample_fraction:
        instability_reasons.append(
            BiomarkerStabilityReasonCode.LOW_RELIABLE_SAMPLE_FRACTION
        )
    if len(condition_values_with_signal) <= 1 and total_condition_values:
        instability_reasons.append(
            BiomarkerStabilityReasonCode.SINGLE_CONDITION_SIGNAL_ONLY
        )
    if assay_agreement_score < 1.0:
        instability_reasons.append(BiomarkerStabilityReasonCode.ASSAY_DISAGREEMENT)

    subgroup_dimension_results = []
    condition_dimension = _build_subgroup_dimension_entries(
        candidate_id=candidate.candidate_id,
        dimension=BiomarkerStabilityDimension.CONDITION,
        group_values={
            sample_id: design_by_sample[sample_id].condition
            for sample_id in candidate_sample_values
            if sample_id in design_by_sample and design_by_sample[sample_id].condition
        },
        sample_values=candidate_sample_values,
        reliable_sample_ids=reliable_sample_ids,
        minimum_reliable_samples_per_group=policy.minimum_reliable_samples_per_group,
    )
    subgroup_entries.extend(condition_dimension[0])

    batch_dimension = _build_batch_entries(
        candidate_id=candidate.candidate_id,
        sample_values=candidate_sample_values,
        reliable_sample_ids=reliable_sample_ids,
        design_by_sample=design_by_sample,
        batch_field=policy.batch_field,
        minimum_reliable_samples_per_group=policy.minimum_reliable_samples_per_group,
        residual_delta_threshold=policy.batch_residual_delta_threshold,
    )
    subgroup_dimension_results.append(batch_dimension)
    subgroup_entries.extend(batch_dimension[0])

    timepoint_dimension = _build_subgroup_dimension_entries(
        candidate_id=candidate.candidate_id,
        dimension=BiomarkerStabilityDimension.TIMEPOINT,
        group_values=_group_values_for_dimension(
            sample_ids=candidate_sample_values,
            design_by_sample=design_by_sample,
            field_name=policy.timepoint_field,
        ),
        sample_values=candidate_sample_values,
        reliable_sample_ids=reliable_sample_ids,
        minimum_reliable_samples_per_group=policy.minimum_reliable_samples_per_group,
        median_delta_threshold=policy.subgroup_median_delta_threshold,
        instability_reason=BiomarkerStabilityReasonCode.TIMEPOINT_SENSITIVE_SIGNAL,
    )
    subgroup_dimension_results.append(timepoint_dimension)
    subgroup_entries.extend(timepoint_dimension[0])

    sample_type_dimension = _build_subgroup_dimension_entries(
        candidate_id=candidate.candidate_id,
        dimension=BiomarkerStabilityDimension.SAMPLE_TYPE,
        group_values=_group_values_for_dimension(
            sample_ids=candidate_sample_values,
            design_by_sample=design_by_sample,
            field_name=policy.sample_type_field,
        ),
        sample_values=candidate_sample_values,
        reliable_sample_ids=reliable_sample_ids,
        minimum_reliable_samples_per_group=policy.minimum_reliable_samples_per_group,
        median_delta_threshold=policy.subgroup_median_delta_threshold,
        instability_reason=BiomarkerStabilityReasonCode.SAMPLE_TYPE_SENSITIVE_SIGNAL,
    )
    subgroup_dimension_results.append(sample_type_dimension)
    subgroup_entries.extend(sample_type_dimension[0])

    batch_stability_score = None
    timepoint_stability_score = None
    sample_type_stability_score = None
    for entries, score, reason, sparse in subgroup_dimension_results:
        if score is not None:
            component_scores.append(score)
        if sparse:
            instability_reasons.append(
                BiomarkerStabilityReasonCode.SPARSE_SUBGROUP_COVERAGE
            )
        if reason is not None:
            instability_reasons.append(reason)
        if entries and entries[0].dimension is BiomarkerStabilityDimension.BATCH:
            batch_stability_score = score
        elif entries and entries[0].dimension is BiomarkerStabilityDimension.TIMEPOINT:
            timepoint_stability_score = score
        elif (
            entries and entries[0].dimension is BiomarkerStabilityDimension.SAMPLE_TYPE
        ):
            sample_type_stability_score = score

    deduped_reasons = tuple(dict.fromkeys(instability_reasons))
    stability_score = (
        max(0.0, min(1.0, mean(component_scores))) if component_scores else 0.0
    )
    if (
        BiomarkerStabilityReasonCode.SINGLE_CONDITION_SIGNAL_ONLY in deduped_reasons
        and total_condition_values
    ):
        stability_score = min(
            stability_score,
            max(0.0, policy.downgrade_below_score - 0.05),
        )
    stability_penalty = 1.0 - stability_score
    adjusted_final_score = max(0.0, min(1.0, candidate.final_score * stability_score))
    adjusted_penalty_total = candidate.penalty_total + stability_penalty
    downgraded = stability_score < policy.downgrade_below_score
    note = _build_candidate_note(
        candidate,
        stability_score=stability_score,
        reasons=deduped_reasons,
        reliable_sample_count=reliable_sample_count,
        total_sample_count=total_sample_count,
        condition_count_with_signal=len(condition_values_with_signal),
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
            reliable_sample_fraction=reliable_sample_fraction,
            condition_breadth_score=condition_breadth_score,
            assay_agreement_score=assay_agreement_score,
            batch_stability_score=batch_stability_score,
            timepoint_stability_score=timepoint_stability_score,
            sample_type_stability_score=sample_type_stability_score,
            reliable_sample_count=reliable_sample_count,
            total_sample_count=total_sample_count,
            condition_count_with_signal=len(condition_values_with_signal),
            total_condition_count=len(total_condition_values),
            assay_entry_count=len(assays),
            matched_target_count=len(matched_target_ids),
            downgraded=downgraded,
            instability_reasons=deduped_reasons,
            subgroup_behavior_count=len(subgroup_entries),
            note=note,
        ),
        subgroup_entries,
        rank_reason_codes,
    )


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


def _build_imported_target_descriptors(
    import_report: TargetedResultImportReport,
) -> tuple[_ImportedTargetDescriptor, ...]:
    grouped: dict[str, list[tuple[str, int | None, str | None]]] = {}
    for observation in import_report.observations:
        grouped.setdefault(observation.precursor_id, []).append(
            (
                observation.peptide_sequence,
                observation.precursor_charge,
                observation.protein_ref,
            )
        )
    descriptors: list[_ImportedTargetDescriptor] = []
    for target_id, rows in sorted(grouped.items()):
        peptide_sequence = rows[0][0]
        precursor_charge = rows[0][1]
        protein_refs = tuple(sorted({row[2] for row in rows if row[2]}))
        descriptors.append(
            _ImportedTargetDescriptor(
                target_id=target_id,
                peptide_sequence=peptide_sequence,
                precursor_charge=precursor_charge,
                protein_refs=protein_refs,
            )
        )
    return tuple(descriptors)


def _match_assay_target_ids(
    assay: TargetedValidationPanelAssayInput,
    descriptors: tuple[_ImportedTargetDescriptor, ...],
) -> tuple[str, ...]:
    peptide_matches = [
        descriptor
        for descriptor in descriptors
        if descriptor.peptide_sequence == assay.canonical_peptide
        and descriptor.precursor_charge == assay.precursor_charge
    ]
    if not peptide_matches:
        return ()
    protein_matches = [
        descriptor
        for descriptor in peptide_matches
        if assay.target_protein_ref in descriptor.protein_refs
    ]
    if protein_matches:
        return tuple(sorted(descriptor.target_id for descriptor in protein_matches))
    if assay.uniqueness_class is PeptideUniquenessClass.UNIQUE:
        return ()
    return tuple(sorted(descriptor.target_id for descriptor in peptide_matches))


def _compute_assay_agreement_score(
    assay_values_by_sample: dict[str, dict[str, float]],
    *,
    disagreement_delta_threshold: float,
) -> float:
    spreads = [
        max(values.values()) - min(values.values())
        for values in assay_values_by_sample.values()
        if len(values) >= 2
    ]
    if not spreads:
        return 1.0 if assay_values_by_sample else 0.0
    return max(0.0, min(1.0, 1.0 - (mean(spreads) / disagreement_delta_threshold)))


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

# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Cohort stratification over metadata-backed study subgroups."""

from __future__ import annotations

from collections import defaultdict
import csv
from enum import StrEnum
from io import StringIO
from itertools import combinations

from pydantic import ConfigDict, Field

from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics.quantification import (
    DifferentialAbundanceEntry,
    LabelFreeQuantTable,
    build_differential_abundance_report,
)
from bijux_proteomics.study import (
    ExperimentDesign,
    ExperimentDesignSample,
    coerce_experiment_design,
)
from bijux_proteomics_foundation import JsonModel


class CohortStratificationField(StrEnum):
    """Stable metadata fields supported for cohort stratification."""

    SEX = "sex"
    TISSUE_OR_CELL_TYPE = "tissue_or_cell_type"
    BATCH = "batch"
    GENOTYPE = "genotype"
    RESPONSE_CLASS = "response_class"
    TIMEPOINT = "timepoint"


class CohortStratumStatus(StrEnum):
    """Stable stratum support states."""

    SUPPORTED = "supported"
    BLOCKED_LOW_SUBGROUP_SAMPLE_COUNT = "blocked_low_subgroup_sample_count"
    BLOCKED_INFEASIBLE_SUBGROUP_DESIGN = "blocked_infeasible_subgroup_design"


class CohortInteractionCandidateKind(StrEnum):
    """Stable interaction candidate patterns across subgroup effects."""

    MAGNITUDE_DIFFERENCE = "magnitude_difference"
    DIRECTION_CONFLICT = "direction_conflict"


class CohortStratificationPolicy(JsonModel):
    """Policy controlling subgroup support and interaction filtering."""

    model_config = ConfigDict(extra="forbid")

    fields: tuple[CohortStratificationField, ...] = Field(
        default=(
            CohortStratificationField.SEX,
            CohortStratificationField.TISSUE_OR_CELL_TYPE,
            CohortStratificationField.BATCH,
            CohortStratificationField.GENOTYPE,
            CohortStratificationField.RESPONSE_CLASS,
            CohortStratificationField.TIMEPOINT,
        )
    )
    minimum_samples_per_condition: int = Field(default=2, ge=1)
    max_adjusted_p_value: float = Field(default=0.1, ge=0.0, le=1.0)
    min_absolute_log2_fold_change: float = Field(default=1.0, ge=0.0)
    min_absolute_interaction_delta: float = Field(default=1.0, ge=0.0)


class CohortStratumEntry(JsonModel):
    """One metadata stratum evaluated for subgroup differential support."""

    model_config = ConfigDict(extra="forbid")

    field_name: CohortStratificationField
    subgroup_value: str = Field(..., min_length=1)
    condition_a: str = Field(..., min_length=1)
    condition_b: str = Field(..., min_length=1)
    samples_a: tuple[str, ...] = Field(default_factory=tuple)
    samples_b: tuple[str, ...] = Field(default_factory=tuple)
    sample_count_a: int = Field(..., ge=0)
    sample_count_b: int = Field(..., ge=0)
    total_sample_count: int = Field(..., ge=0)
    status: CohortStratumStatus
    note: str = Field(..., min_length=1)


class CohortSubgroupEffectEntry(JsonModel):
    """One subgroup-supported differential effect."""

    model_config = ConfigDict(extra="forbid")

    field_name: CohortStratificationField
    subgroup_value: str = Field(..., min_length=1)
    entity_id: str = Field(..., min_length=1)
    condition_a: str = Field(..., min_length=1)
    condition_b: str = Field(..., min_length=1)
    sample_count_a: int = Field(..., ge=0)
    sample_count_b: int = Field(..., ge=0)
    log2_fold_change: float
    adjusted_p_value: float | None = Field(default=None, ge=0.0, le=1.0)
    robustness_score: float | None = Field(default=None, ge=0.0, le=1.0)
    imputation_dependent_hit: bool = False
    robustness_note: str | None = None
    uncertainty_note: str | None = None


class CohortInteractionCandidateEntry(JsonModel):
    """One cross-subgroup interaction candidate."""

    model_config = ConfigDict(extra="forbid")

    field_name: CohortStratificationField
    left_subgroup_value: str = Field(..., min_length=1)
    right_subgroup_value: str = Field(..., min_length=1)
    entity_id: str = Field(..., min_length=1)
    candidate_kind: CohortInteractionCandidateKind
    left_log2_fold_change: float
    right_log2_fold_change: float
    left_adjusted_p_value: float | None = Field(default=None, ge=0.0, le=1.0)
    right_adjusted_p_value: float | None = Field(default=None, ge=0.0, le=1.0)
    interaction_delta: float
    left_robustness_score: float | None = Field(default=None, ge=0.0, le=1.0)
    right_robustness_score: float | None = Field(default=None, ge=0.0, le=1.0)
    note: str = Field(..., min_length=1)


class CohortStratificationSummary(JsonModel):
    """Compact summary over cohort stratification."""

    model_config = ConfigDict(extra="forbid")

    field_count: int = Field(..., ge=0)
    supported_stratum_count: int = Field(..., ge=0)
    blocked_stratum_count: int = Field(..., ge=0)
    subgroup_effect_count: int = Field(..., ge=0)
    interaction_candidate_count: int = Field(..., ge=0)


class CohortStratificationReport(JsonModel):
    """Owned study subgroup exploration over metadata-backed cohorts."""

    model_config = ConfigDict(extra="forbid")

    condition_a: str = Field(..., min_length=1)
    condition_b: str = Field(..., min_length=1)
    policy: CohortStratificationPolicy
    stratum_entries: tuple[CohortStratumEntry, ...] = Field(default_factory=tuple)
    subgroup_effect_entries: tuple[CohortSubgroupEffectEntry, ...] = Field(
        default_factory=tuple
    )
    interaction_candidates: tuple[CohortInteractionCandidateEntry, ...] = Field(
        default_factory=tuple
    )
    summary: CohortStratificationSummary
    note: str = Field(..., min_length=1)


def build_cohort_stratification_report(
    table: LabelFreeQuantTable,
    design_entries: ExperimentDesign | tuple[ExperimentalDesignEntry, ...],
    *,
    condition_a: str,
    condition_b: str,
    policy: CohortStratificationPolicy | None = None,
) -> CohortStratificationReport:
    """Analyze subgroup-specific differential effects and interaction candidates."""

    experiment_design = coerce_experiment_design(design_entries)
    active_policy = policy or CohortStratificationPolicy()
    candidate_samples = tuple(
        sample
        for sample in experiment_design.samples
        if sample.condition in {condition_a, condition_b}
    )
    values_by_field = _group_samples_by_field(candidate_samples, active_policy.fields)

    stratum_entries: list[CohortStratumEntry] = []
    subgroup_effect_entries: list[CohortSubgroupEffectEntry] = []
    interaction_candidates: list[CohortInteractionCandidateEntry] = []

    for field_name in active_policy.fields:
        subgroup_samples = values_by_field.get(field_name, {})
        if len(subgroup_samples) < 2:
            continue

        supported_reports: dict[str, dict[str, DifferentialAbundanceEntry]] = {}
        for subgroup_value in sorted(subgroup_samples):
            samples = tuple(
                sorted(
                    subgroup_samples[subgroup_value], key=lambda item: item.sample_id
                )
            )
            samples_a = tuple(
                sample.sample_id
                for sample in samples
                if sample.condition == condition_a
            )
            samples_b = tuple(
                sample.sample_id
                for sample in samples
                if sample.condition == condition_b
            )
            sample_count_a = len(samples_a)
            sample_count_b = len(samples_b)
            if (
                sample_count_a < active_policy.minimum_samples_per_condition
                or sample_count_b < active_policy.minimum_samples_per_condition
            ):
                stratum_entries.append(
                    CohortStratumEntry(
                        field_name=field_name,
                        subgroup_value=subgroup_value,
                        condition_a=condition_a,
                        condition_b=condition_b,
                        samples_a=samples_a,
                        samples_b=samples_b,
                        sample_count_a=sample_count_a,
                        sample_count_b=sample_count_b,
                        total_sample_count=len(samples),
                        status=CohortStratumStatus.BLOCKED_LOW_SUBGROUP_SAMPLE_COUNT,
                        note=(
                            "subgroup was blocked because at least one condition fell below the minimum samples-per-condition threshold"
                        ),
                    )
                )
                continue
            subgroup_sample_ids = {sample.sample_id for sample in samples}
            subgroup_table = _subset_table_by_sample_ids(table, subgroup_sample_ids)
            subgroup_design_entries = tuple(
                entry
                for entry in experiment_design.entries
                if entry.sample_id in subgroup_sample_ids
            )
            try:
                subgroup_report = build_differential_abundance_report(
                    subgroup_table,
                    subgroup_design_entries,
                    condition_a=condition_a,
                    condition_b=condition_b,
                )
            except ValueError as exc:
                stratum_entries.append(
                    CohortStratumEntry(
                        field_name=field_name,
                        subgroup_value=subgroup_value,
                        condition_a=condition_a,
                        condition_b=condition_b,
                        samples_a=samples_a,
                        samples_b=samples_b,
                        sample_count_a=sample_count_a,
                        sample_count_b=sample_count_b,
                        total_sample_count=len(samples),
                        status=CohortStratumStatus.BLOCKED_INFEASIBLE_SUBGROUP_DESIGN,
                        note=(
                            "subgroup met the sample-count threshold but was blocked because "
                            f"governed differential analysis could not support the subgroup design: {exc}"
                        ),
                    )
                )
                continue
            stratum_entries.append(
                CohortStratumEntry(
                    field_name=field_name,
                    subgroup_value=subgroup_value,
                    condition_a=condition_a,
                    condition_b=condition_b,
                    samples_a=samples_a,
                    samples_b=samples_b,
                    sample_count_a=sample_count_a,
                    sample_count_b=sample_count_b,
                    total_sample_count=len(samples),
                    status=CohortStratumStatus.SUPPORTED,
                    note=(
                        "subgroup met the minimum samples-per-condition threshold for subgroup differential analysis"
                    ),
                )
            )
            entry_lookup = {entry.entity_id: entry for entry in subgroup_report.entries}
            supported_reports[subgroup_value] = entry_lookup
            subgroup_effect_entries.extend(
                _select_subgroup_effect_entries(
                    field_name=field_name,
                    subgroup_value=subgroup_value,
                    sample_count_a=sample_count_a,
                    sample_count_b=sample_count_b,
                    report_entries=subgroup_report.entries,
                    policy=active_policy,
                )
            )
        interaction_candidates.extend(
            _build_interaction_candidates(
                field_name=field_name,
                supported_reports=supported_reports,
                policy=active_policy,
            )
        )

    ordered_strata = tuple(
        sorted(
            stratum_entries,
            key=lambda entry: (entry.field_name.value, entry.subgroup_value),
        )
    )
    ordered_effects = tuple(
        sorted(
            subgroup_effect_entries,
            key=lambda entry: (
                entry.field_name.value,
                entry.subgroup_value,
                entry.adjusted_p_value if entry.adjusted_p_value is not None else 1.0,
                -abs(entry.log2_fold_change),
                entry.entity_id,
            ),
        )
    )
    ordered_interactions = tuple(
        sorted(
            interaction_candidates,
            key=lambda entry: (
                entry.field_name.value,
                entry.candidate_kind.value,
                -(abs(entry.interaction_delta)),
                entry.entity_id,
                entry.left_subgroup_value,
                entry.right_subgroup_value,
            ),
        )
    )
    return CohortStratificationReport(
        condition_a=condition_a,
        condition_b=condition_b,
        policy=active_policy,
        stratum_entries=ordered_strata,
        subgroup_effect_entries=ordered_effects,
        interaction_candidates=ordered_interactions,
        summary=CohortStratificationSummary(
            field_count=len({entry.field_name for entry in ordered_strata}),
            supported_stratum_count=sum(
                entry.status is CohortStratumStatus.SUPPORTED
                for entry in ordered_strata
            ),
            blocked_stratum_count=sum(
                entry.status is not CohortStratumStatus.SUPPORTED
                for entry in ordered_strata
            ),
            subgroup_effect_count=len(ordered_effects),
            interaction_candidate_count=len(ordered_interactions),
        ),
        note=(
            "cohort stratification repeats governed differential analysis within metadata-defined "
            "subgroups, emits subgroup-specific effects and interaction candidates, and blocks "
            "small strata before they can be overinterpreted as subgroup biology"
        ),
    )


def render_cohort_stratification_summary_tsv(report: CohortStratificationReport) -> str:
    """Render the compact cohort stratification summary as TSV."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(("field", "value"))
    writer.writerow(("condition_a", report.condition_a))
    writer.writerow(("condition_b", report.condition_b))
    writer.writerow(("field_count", report.summary.field_count))
    writer.writerow(("supported_stratum_count", report.summary.supported_stratum_count))
    writer.writerow(("blocked_stratum_count", report.summary.blocked_stratum_count))
    writer.writerow(("subgroup_effect_count", report.summary.subgroup_effect_count))
    writer.writerow(
        ("interaction_candidate_count", report.summary.interaction_candidate_count)
    )
    writer.writerow(("note", report.note))
    return handle.getvalue()


def render_cohort_stratum_tsv(report: CohortStratificationReport) -> str:
    """Render cohort strata and support status as TSV."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "field_name",
            "subgroup_value",
            "condition_a",
            "condition_b",
            "samples_a",
            "samples_b",
            "sample_count_a",
            "sample_count_b",
            "total_sample_count",
            "status",
            "note",
        )
    )
    for entry in report.stratum_entries:
        writer.writerow(
            (
                entry.field_name.value,
                entry.subgroup_value,
                entry.condition_a,
                entry.condition_b,
                ";".join(entry.samples_a),
                ";".join(entry.samples_b),
                entry.sample_count_a,
                entry.sample_count_b,
                entry.total_sample_count,
                entry.status.value,
                entry.note,
            )
        )
    return handle.getvalue()


def render_cohort_subgroup_effect_tsv(report: CohortStratificationReport) -> str:
    """Render subgroup-supported differential effects as TSV."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "field_name",
            "subgroup_value",
            "entity_id",
            "condition_a",
            "condition_b",
            "sample_count_a",
            "sample_count_b",
            "log2_fold_change",
            "adjusted_p_value",
            "robustness_score",
            "imputation_dependent_hit",
            "robustness_note",
            "uncertainty_note",
        )
    )
    for entry in report.subgroup_effect_entries:
        writer.writerow(
            (
                entry.field_name.value,
                entry.subgroup_value,
                entry.entity_id,
                entry.condition_a,
                entry.condition_b,
                entry.sample_count_a,
                entry.sample_count_b,
                f"{entry.log2_fold_change:g}",
                "" if entry.adjusted_p_value is None else f"{entry.adjusted_p_value:g}",
                "" if entry.robustness_score is None else f"{entry.robustness_score:g}",
                str(entry.imputation_dependent_hit).lower(),
                entry.robustness_note or "",
                entry.uncertainty_note or "",
            )
        )
    return handle.getvalue()


def render_cohort_interaction_candidate_tsv(report: CohortStratificationReport) -> str:
    """Render subgroup interaction candidates as TSV."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "field_name",
            "left_subgroup_value",
            "right_subgroup_value",
            "entity_id",
            "candidate_kind",
            "left_log2_fold_change",
            "right_log2_fold_change",
            "left_adjusted_p_value",
            "right_adjusted_p_value",
            "interaction_delta",
            "left_robustness_score",
            "right_robustness_score",
            "note",
        )
    )
    for entry in report.interaction_candidates:
        writer.writerow(
            (
                entry.field_name.value,
                entry.left_subgroup_value,
                entry.right_subgroup_value,
                entry.entity_id,
                entry.candidate_kind.value,
                f"{entry.left_log2_fold_change:g}",
                f"{entry.right_log2_fold_change:g}",
                ""
                if entry.left_adjusted_p_value is None
                else f"{entry.left_adjusted_p_value:g}",
                ""
                if entry.right_adjusted_p_value is None
                else f"{entry.right_adjusted_p_value:g}",
                f"{entry.interaction_delta:g}",
                ""
                if entry.left_robustness_score is None
                else f"{entry.left_robustness_score:g}",
                ""
                if entry.right_robustness_score is None
                else f"{entry.right_robustness_score:g}",
                entry.note,
            )
        )
    return handle.getvalue()


def _group_samples_by_field(
    samples: tuple[ExperimentDesignSample, ...],
    fields: tuple[CohortStratificationField, ...],
) -> dict[CohortStratificationField, dict[str, list[ExperimentDesignSample]]]:
    grouped: dict[
        CohortStratificationField, dict[str, list[ExperimentDesignSample]]
    ] = {}
    for field_name in fields:
        values: dict[str, list[ExperimentDesignSample]] = defaultdict(list)
        for sample in samples:
            field_value = _sample_field_value(sample, field_name)
            if field_value:
                values[field_value].append(sample)
        if len(values) >= 2:
            grouped[field_name] = values
    return grouped


def _sample_field_value(
    sample: ExperimentDesignSample,
    field_name: CohortStratificationField,
) -> str | None:
    if field_name is CohortStratificationField.TISSUE_OR_CELL_TYPE:
        value = sample.tissue_or_cell_type
        return value if isinstance(value, str) else None
    if field_name is CohortStratificationField.TIMEPOINT:
        value = sample.timepoint
        return value if isinstance(value, str) else None
    if field_name is CohortStratificationField.BATCH:
        return sample.batch_ids[0] if len(sample.batch_ids) == 1 else None
    value = sample.metadata.get(field_name.value)
    return value if isinstance(value, str) else None


def _subset_table_by_sample_ids(
    table: LabelFreeQuantTable,
    sample_ids: set[str],
) -> LabelFreeQuantTable:
    ordered_sample_ids = tuple(
        sample_id for sample_id in table.sample_ids if sample_id in sample_ids
    )
    return table.model_copy(
        update={
            "sample_ids": ordered_sample_ids,
            "values": tuple(
                value for value in table.values if value.sample_id in sample_ids
            ),
            "quant_matrix": None,
            "normalization_factors": {
                sample_id: factor
                for sample_id, factor in table.normalization_factors.items()
                if sample_id in sample_ids
            },
        }
    )


def _select_subgroup_effect_entries(
    *,
    field_name: CohortStratificationField,
    subgroup_value: str,
    sample_count_a: int,
    sample_count_b: int,
    report_entries: tuple[DifferentialAbundanceEntry, ...],
    policy: CohortStratificationPolicy,
) -> list[CohortSubgroupEffectEntry]:
    selected: list[CohortSubgroupEffectEntry] = []
    for entry in report_entries:
        if not _effect_passes_policy(entry, policy=policy):
            continue
        selected.append(
            CohortSubgroupEffectEntry(
                field_name=field_name,
                subgroup_value=subgroup_value,
                entity_id=entry.entity_id,
                condition_a=entry.condition_a,
                condition_b=entry.condition_b,
                sample_count_a=sample_count_a,
                sample_count_b=sample_count_b,
                log2_fold_change=entry.log2_fold_change,
                adjusted_p_value=entry.adjusted_p_value,
                robustness_score=entry.robustness_score,
                imputation_dependent_hit=entry.imputation_dependent_hit,
                robustness_note=entry.robustness_note,
                uncertainty_note=entry.uncertainty_note,
            )
        )
    return selected


def _build_interaction_candidates(
    *,
    field_name: CohortStratificationField,
    supported_reports: dict[str, dict[str, DifferentialAbundanceEntry]],
    policy: CohortStratificationPolicy,
) -> list[CohortInteractionCandidateEntry]:
    candidates: list[CohortInteractionCandidateEntry] = []
    for left_value, right_value in combinations(sorted(supported_reports), 2):
        left_entries = supported_reports[left_value]
        right_entries = supported_reports[right_value]
        for entity_id in sorted(set(left_entries) & set(right_entries)):
            left_entry = left_entries[entity_id]
            right_entry = right_entries[entity_id]
            delta = left_entry.log2_fold_change - right_entry.log2_fold_change
            passes_delta = abs(delta) >= policy.min_absolute_interaction_delta
            left_pass = _effect_passes_policy(left_entry, policy=policy)
            right_pass = _effect_passes_policy(right_entry, policy=policy)
            direction_conflict = (
                left_entry.log2_fold_change * right_entry.log2_fold_change < 0
                and min(
                    abs(left_entry.log2_fold_change),
                    abs(right_entry.log2_fold_change),
                )
                >= (policy.min_absolute_log2_fold_change / 2.0)
            )
            if not ((passes_delta and (left_pass or right_pass)) or direction_conflict):
                continue
            candidate_kind = (
                CohortInteractionCandidateKind.DIRECTION_CONFLICT
                if direction_conflict
                else CohortInteractionCandidateKind.MAGNITUDE_DIFFERENCE
            )
            candidates.append(
                CohortInteractionCandidateEntry(
                    field_name=field_name,
                    left_subgroup_value=left_value,
                    right_subgroup_value=right_value,
                    entity_id=entity_id,
                    candidate_kind=candidate_kind,
                    left_log2_fold_change=left_entry.log2_fold_change,
                    right_log2_fold_change=right_entry.log2_fold_change,
                    left_adjusted_p_value=left_entry.adjusted_p_value,
                    right_adjusted_p_value=right_entry.adjusted_p_value,
                    interaction_delta=delta,
                    left_robustness_score=left_entry.robustness_score,
                    right_robustness_score=right_entry.robustness_score,
                    note=(
                        "subgroup effects diverged beyond the interaction-delta threshold"
                        if candidate_kind
                        is CohortInteractionCandidateKind.MAGNITUDE_DIFFERENCE
                        else "subgroup effects reversed direction across supported strata"
                    ),
                )
            )
    return candidates


def _effect_passes_policy(
    entry: DifferentialAbundanceEntry,
    *,
    policy: CohortStratificationPolicy,
) -> bool:
    return (
        entry.adjusted_p_value is not None
        and entry.adjusted_p_value <= policy.max_adjusted_p_value
        and abs(entry.log2_fold_change) >= policy.min_absolute_log2_fold_change
    )


__all__ = [
    "CohortInteractionCandidateEntry",
    "CohortInteractionCandidateKind",
    "CohortStratificationField",
    "CohortStratificationPolicy",
    "CohortStratificationReport",
    "CohortStratificationSummary",
    "CohortStratumEntry",
    "CohortStratumStatus",
    "CohortSubgroupEffectEntry",
    "build_cohort_stratification_report",
    "render_cohort_interaction_candidate_tsv",
    "render_cohort_stratification_summary_tsv",
    "render_cohort_stratum_tsv",
    "render_cohort_subgroup_effect_tsv",
]

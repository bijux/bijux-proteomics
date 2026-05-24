# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owned imputation-dependence labeling for differential-result rows."""

from __future__ import annotations

from pydantic import ConfigDict, Field

from bijux_proteomics.quantification.contracts import (
    DifferentialAbundanceEntry,
    DifferentialAbundanceReport,
    DifferentialImputationSignificanceChangeReason,
    ImputationMethod,
    LabelFreeQuantTable,
    QuantValueOrigin,
)
from bijux_proteomics_foundation import JsonModel


class DifferentialImputationDependenceEntry(JsonModel):
    """One entity-level comparison between no-impute and imputed differential calls."""

    model_config = ConfigDict(extra="forbid")

    entity_id: str = Field(..., min_length=1)
    baseline_method: ImputationMethod
    imputation_method: ImputationMethod
    no_impute_adjusted_p_value: float | None = Field(default=None, ge=0.0, le=1.0)
    no_impute_log2_fold_change: float | None = None
    imputed_adjusted_p_value: float | None = Field(default=None, ge=0.0, le=1.0)
    imputed_log2_fold_change: float | None = None
    no_impute_significant: bool
    imputed_significant: bool
    significance_change_reason: DifferentialImputationSignificanceChangeReason
    imputation_dependent_hit: bool = False
    note: str = Field(..., min_length=1)


class DifferentialImputationDependenceReport(JsonModel):
    """Stable report comparing no-impute and imputed differential results."""

    model_config = ConfigDict(extra="forbid")

    baseline_method: ImputationMethod = ImputationMethod.NONE
    imputation_method: ImputationMethod
    significance_threshold: float = Field(default=0.05, ge=0.0, le=1.0)
    entries: tuple[DifferentialImputationDependenceEntry, ...] = Field(
        default_factory=tuple
    )
    imputation_dependent_hit_count: int = Field(..., ge=0)
    note: str = Field(..., min_length=1)


def build_differential_imputation_dependence_report(
    no_impute_report: DifferentialAbundanceReport,
    imputed_report: DifferentialAbundanceReport,
    *,
    significance_threshold: float = 0.05,
) -> DifferentialImputationDependenceReport:
    """Compare baseline and imputed pairwise differential reports entity by entity."""

    _require_matching_differential_reports(no_impute_report, imputed_report)
    baseline_lookup = {entry.entity_id: entry for entry in no_impute_report.entries}
    imputed_lookup = {entry.entity_id: entry for entry in imputed_report.entries}
    entity_ids = tuple(sorted(set(baseline_lookup) | set(imputed_lookup)))
    entries = tuple(
        _build_dependence_entry(
            entity_id=entity_id,
            baseline_entry=baseline_lookup.get(entity_id),
            imputed_entry=imputed_lookup.get(entity_id),
            significance_threshold=significance_threshold,
            imputation_method=imputed_report.imputation_method,
        )
        for entity_id in entity_ids
    )
    return DifferentialImputationDependenceReport(
        imputation_method=imputed_report.imputation_method,
        significance_threshold=significance_threshold,
        entries=entries,
        imputation_dependent_hit_count=sum(
            entry.imputation_dependent_hit for entry in entries
        ),
        note=(
            "differential imputation dependence preserves no-impute and imputed significance side by side"
        ),
    )


def annotate_differential_abundance_report_imputation_dependence(
    report: DifferentialAbundanceReport,
    *,
    no_impute_report: DifferentialAbundanceReport | None = None,
    significance_threshold: float = 0.05,
) -> DifferentialAbundanceReport:
    """Attach imputation-dependence fields to pairwise differential rows."""

    if no_impute_report is None:
        entries = tuple(
            entry.model_copy(
                update={
                    "no_impute_adjusted_p_value": entry.adjusted_p_value,
                    "no_impute_log2_fold_change": entry.log2_fold_change,
                    "imputed_adjusted_p_value": None,
                    "imputed_log2_fold_change": None,
                    "imputation_significance_change_reason": (
                        DifferentialImputationSignificanceChangeReason.NOT_IMPUTED
                    ),
                    "imputation_dependent_hit": False,
                }
            )
            for entry in report.entries
        )
        return report.model_copy(update={"entries": entries})

    dependence_report = build_differential_imputation_dependence_report(
        no_impute_report,
        report,
        significance_threshold=significance_threshold,
    )
    dependence_by_entity = {entry.entity_id: entry for entry in dependence_report.entries}
    entries = tuple(
        result_entry.model_copy(
            update={
                "no_impute_adjusted_p_value": dependence_entry.no_impute_adjusted_p_value,
                "no_impute_log2_fold_change": dependence_entry.no_impute_log2_fold_change,
                "imputed_adjusted_p_value": dependence_entry.imputed_adjusted_p_value,
                "imputed_log2_fold_change": dependence_entry.imputed_log2_fold_change,
                "imputation_significance_change_reason": (
                    dependence_entry.significance_change_reason
                ),
                "imputation_dependent_hit": dependence_entry.imputation_dependent_hit,
            }
        )
        for result_entry in report.entries
        if (dependence_entry := dependence_by_entity[result_entry.entity_id])
    )
    return report.model_copy(update={"entries": entries})


def build_no_impute_reference_table(
    table: LabelFreeQuantTable,
) -> LabelFreeQuantTable:
    """Rebuild a no-impute baseline table from explicit per-cell imputation provenance."""

    if table.imputation_method is ImputationMethod.NONE:
        return table
    values = []
    for value in table.values:
        if value.imputation_provenance is None:
            values.append(
                value.model_copy(
                    update={
                        "value_provenance": (
                            None
                            if value.value_provenance is None
                            else value.value_provenance.model_copy(
                                update={"value_origin": QuantValueOrigin.OBSERVED}
                            )
                        )
                    }
                )
            )
            continue
        values.append(
            value.model_copy(
                update={
                    "abundance": None,
                    "missing_value_kind": (
                        value.imputation_provenance.original_missing_value_kind
                    ),
                    "imputation_provenance": None,
                    "value_provenance": (
                        None
                        if value.value_provenance is None
                        else value.value_provenance.model_copy(
                            update={"value_origin": QuantValueOrigin.MISSING}
                        )
                    ),
                }
            )
        )
    return table.model_copy(
        update={
            "imputation_method": ImputationMethod.NONE,
            "values": tuple(values),
            "quant_matrix": None,
        }
    )


def _build_dependence_entry(
    *,
    entity_id: str,
    baseline_entry: DifferentialAbundanceEntry | None,
    imputed_entry: DifferentialAbundanceEntry | None,
    significance_threshold: float,
    imputation_method: ImputationMethod,
) -> DifferentialImputationDependenceEntry:
    no_impute_significant = _is_significant(
        None if baseline_entry is None else baseline_entry.adjusted_p_value,
        significance_threshold,
    )
    imputed_significant = _is_significant(
        None if imputed_entry is None else imputed_entry.adjusted_p_value,
        significance_threshold,
    )
    if imputed_significant and not no_impute_significant:
        reason = (
            DifferentialImputationSignificanceChangeReason.SIGNIFICANT_ONLY_AFTER_IMPUTATION
        )
    elif no_impute_significant and not imputed_significant:
        reason = (
            DifferentialImputationSignificanceChangeReason.SIGNIFICANCE_LOST_AFTER_IMPUTATION
        )
    elif imputed_significant:
        reason = DifferentialImputationSignificanceChangeReason.STABLE_SIGNIFICANT
    else:
        reason = DifferentialImputationSignificanceChangeReason.STABLE_NON_SIGNIFICANT
    return DifferentialImputationDependenceEntry(
        entity_id=entity_id,
        baseline_method=ImputationMethod.NONE,
        imputation_method=imputation_method,
        no_impute_adjusted_p_value=(
            None if baseline_entry is None else baseline_entry.adjusted_p_value
        ),
        no_impute_log2_fold_change=(
            None if baseline_entry is None else baseline_entry.log2_fold_change
        ),
        imputed_adjusted_p_value=(
            None if imputed_entry is None else imputed_entry.adjusted_p_value
        ),
        imputed_log2_fold_change=(
            None if imputed_entry is None else imputed_entry.log2_fold_change
        ),
        no_impute_significant=no_impute_significant,
        imputed_significant=imputed_significant,
        significance_change_reason=reason,
        imputation_dependent_hit=(
            reason
            is DifferentialImputationSignificanceChangeReason.SIGNIFICANT_ONLY_AFTER_IMPUTATION
        ),
        note=_note_for_reason(reason),
    )


def _is_significant(adjusted_p_value: float | None, threshold: float) -> bool:
    return adjusted_p_value is not None and adjusted_p_value <= threshold


def _note_for_reason(
    reason: DifferentialImputationSignificanceChangeReason,
) -> str:
    messages = {
        DifferentialImputationSignificanceChangeReason.NOT_IMPUTED: (
            "result was not evaluated under an imputed quantification table"
        ),
        DifferentialImputationSignificanceChangeReason.STABLE_SIGNIFICANT: (
            "result remains significant without imputation"
        ),
        DifferentialImputationSignificanceChangeReason.STABLE_NON_SIGNIFICANT: (
            "result remains non-significant with or without imputation"
        ),
        DifferentialImputationSignificanceChangeReason.SIGNIFICANT_ONLY_AFTER_IMPUTATION: (
            "result becomes significant only after imputation"
        ),
        DifferentialImputationSignificanceChangeReason.SIGNIFICANCE_LOST_AFTER_IMPUTATION: (
            "result loses significance after imputation"
        ),
    }
    return messages[reason]


def _require_matching_differential_reports(
    no_impute_report: DifferentialAbundanceReport,
    imputed_report: DifferentialAbundanceReport,
) -> None:
    if (
        no_impute_report.condition_a != imputed_report.condition_a
        or no_impute_report.condition_b != imputed_report.condition_b
    ):
        raise ValueError(
            "imputation dependence requires matching differential contrast conditions"
        )


__all__ = [
    "DifferentialImputationDependenceEntry",
    "DifferentialImputationDependenceReport",
    "annotate_differential_abundance_report_imputation_dependence",
    "build_differential_imputation_dependence_report",
    "build_no_impute_reference_table",
]

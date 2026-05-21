# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owned missingness analysis for quantitative proteomics tables."""

from __future__ import annotations

from bijux_proteomics.io.formats import ExperimentalDesignEntry
from bijux_proteomics.quantification.contracts import (
    LabelFreeQuantTable,
    MissingDataMechanism,
    MissingDataMechanismEntry,
    MissingDataMechanismReport,
    MissingValueCorrectionPolicy,
    MissingValueKind,
    MissingValueSummaryEntry,
    MissingValueSummaryPolicy,
    MissingValueSummaryReport,
    _condition_lookup,
    _matrix_value_index,
)


def summarize_missing_values(
    table: LabelFreeQuantTable,
    *,
    policy: MissingValueSummaryPolicy | None = None,
) -> MissingValueSummaryReport:
    """Summarize missing values with explicit correction and sparse-entity filters."""
    active_policy = policy or MissingValueSummaryPolicy()
    lookup = _matrix_value_index(table)
    included_entity_ids: list[str] = []
    excluded_entity_ids: list[str] = []
    for entity_id in table.entity_ids:
        observed_samples = sum(
            1
            for sample_id in table.sample_ids
            if lookup[(entity_id, sample_id)].missing_value_kind
            in (MissingValueKind.OBSERVED, MissingValueKind.ZERO)
        )
        if observed_samples < active_policy.min_observed_samples_per_entity:
            excluded_entity_ids.append(entity_id)
            continue
        included_entity_ids.append(entity_id)

    entries: list[MissingValueSummaryEntry] = []
    for sample_id in table.sample_ids:
        counts = {
            MissingValueKind.OBSERVED: 0,
            MissingValueKind.ZERO: 0,
            MissingValueKind.NOT_OBSERVED: 0,
            MissingValueKind.FILTERED: 0,
        }
        for entity_id in included_entity_ids:
            kind = _apply_missing_value_summary_policy(
                lookup[(entity_id, sample_id)].missing_value_kind,
                policy=active_policy,
            )
            counts[kind] += 1
        entries.append(
            MissingValueSummaryEntry(
                sample_id=sample_id,
                observed_count=counts[MissingValueKind.OBSERVED],
                zero_count=counts[MissingValueKind.ZERO],
                not_observed_count=counts[MissingValueKind.NOT_OBSERVED],
                filtered_count=counts[MissingValueKind.FILTERED],
            )
        )
    return MissingValueSummaryReport(
        entity_level=table.entity_level,
        policy=active_policy,
        entries=tuple(entries),
        included_entity_ids=tuple(included_entity_ids),
        excluded_entity_ids=tuple(excluded_entity_ids),
    )


def build_missing_data_mechanism_report(
    table: LabelFreeQuantTable,
    design_entries: tuple[ExperimentalDesignEntry, ...],
) -> MissingDataMechanismReport:
    """Classify missingness patterns as likely biology, likely failure, or unresolved."""
    lookup = _matrix_value_index(table)
    condition_by_sample = _condition_lookup(design_entries)
    conditions = tuple(
        sorted({condition for condition in condition_by_sample.values() if condition})
    )
    entries: list[MissingDataMechanismEntry] = []
    summary_counts = dict.fromkeys(MissingDataMechanism, 0)
    for entity_id in table.entity_ids:
        observed_conditions: set[str] = set()
        missing_samples: list[str] = []
        observed_samples: list[str] = []
        missing_conditions: set[str] = set()
        for sample_id in table.sample_ids:
            cell = lookup[(entity_id, sample_id)]
            condition = condition_by_sample.get(sample_id, "unknown")
            if cell.missing_value_kind in (
                MissingValueKind.OBSERVED,
                MissingValueKind.ZERO,
            ):
                observed_conditions.add(condition)
                observed_samples.append(sample_id)
                continue
            missing_samples.append(sample_id)
            missing_conditions.add(condition)

        mechanism = MissingDataMechanism.MIXED_OR_UNRESOLVED
        note = "missingness mixes biological and technical explanations or lacks enough support"
        if (
            len(observed_conditions) == 1
            and len(missing_conditions) >= 1
            and any(condition not in observed_conditions for condition in conditions)
        ):
            mechanism = MissingDataMechanism.LIKELY_BIOLOGICAL_SPARSE
            note = "signal is confined to one condition while another condition remains consistently missing"
        elif len(missing_samples) == 1 and len(observed_samples) >= 2:
            mechanism = MissingDataMechanism.LIKELY_TECHNICAL_FAILURE
            note = "one isolated missing sample breaks an otherwise observed pattern"

        summary_counts[mechanism] += 1
        entries.append(
            MissingDataMechanismEntry(
                entity_id=entity_id,
                mechanism=mechanism,
                observed_conditions=tuple(sorted(observed_conditions)),
                missing_samples=tuple(sorted(missing_samples)),
                note=note,
            )
        )
    return MissingDataMechanismReport(
        entity_level=table.entity_level,
        entries=tuple(entries),
        summary_counts=summary_counts,
    )


def _apply_missing_value_summary_policy(
    kind: MissingValueKind,
    *,
    policy: MissingValueSummaryPolicy,
) -> MissingValueKind:
    if (
        kind is MissingValueKind.ZERO
        and policy.zero_policy is MissingValueCorrectionPolicy.TREAT_AS_NOT_OBSERVED
    ):
        return MissingValueKind.NOT_OBSERVED
    if (
        kind is MissingValueKind.FILTERED
        and policy.filtered_policy is MissingValueCorrectionPolicy.TREAT_AS_NOT_OBSERVED
    ):
        return MissingValueKind.NOT_OBSERVED
    return kind


__all__ = [
    "build_missing_data_mechanism_report",
    "summarize_missing_values",
]

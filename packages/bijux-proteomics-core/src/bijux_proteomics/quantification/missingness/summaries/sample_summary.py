# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Sample-level missing value summaries."""

from __future__ import annotations

import numpy as np

from bijux_proteomics.quantification.contracts.input_models import MissingValueKind
from bijux_proteomics.quantification.contracts.matrix_building import (
    _matrix_value_index,
)
from bijux_proteomics.quantification.contracts.matrix_models import LabelFreeQuantTable
from bijux_proteomics.quantification.contracts.missingness import (
    MissingValueSummaryEntry,
    MissingValueSummaryPolicy,
    MissingValueSummaryReport,
)
from bijux_proteomics.quantification.matrix import (
    build_dense_label_free_quant_table_view,
    missing_value_kind_to_code,
)
from bijux_proteomics.quantification.missingness.policy import (
    _MISSING_VALUE_KINDS,
    _OBSERVED_VALUE_CODES,
    apply_missing_value_summary_policy,
    apply_missing_value_summary_policy_codes,
)


def summarize_missing_values(
    table: LabelFreeQuantTable,
    *,
    policy: MissingValueSummaryPolicy | None = None,
) -> MissingValueSummaryReport:
    return _summarize_missing_values_vectorized(table, policy=policy)


def _summarize_missing_values_pure(
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
            in (
                MissingValueKind.OBSERVED,
                MissingValueKind.ZERO,
                MissingValueKind.IMPUTED,
            )
        )
        if observed_samples < active_policy.min_observed_samples_per_entity:
            excluded_entity_ids.append(entity_id)
            continue
        included_entity_ids.append(entity_id)

    entries: list[MissingValueSummaryEntry] = []
    for sample_id in table.sample_ids:
        counts = dict.fromkeys(MissingValueKind, 0)
        for entity_id in included_entity_ids:
            kind = apply_missing_value_summary_policy(
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
                imputed_count=counts[MissingValueKind.IMPUTED],
                censored_count=counts[MissingValueKind.CENSORED],
                excluded_count=counts[MissingValueKind.EXCLUDED],
                not_applicable_count=counts[MissingValueKind.NOT_APPLICABLE],
            )
        )
    return MissingValueSummaryReport(
        entity_level=table.entity_level,
        policy=active_policy,
        entries=tuple(entries),
        included_entity_ids=tuple(included_entity_ids),
        excluded_entity_ids=tuple(excluded_entity_ids),
    )


def _summarize_missing_values_vectorized(
    table: LabelFreeQuantTable,
    *,
    policy: MissingValueSummaryPolicy | None = None,
) -> MissingValueSummaryReport:
    active_policy = policy or MissingValueSummaryPolicy()
    dense_view = build_dense_label_free_quant_table_view(table)
    missing_kind_codes = apply_missing_value_summary_policy_codes(
        dense_view.missing_kind_codes,
        policy=active_policy,
    )
    observed_like_mask = np.isin(missing_kind_codes, _OBSERVED_VALUE_CODES)
    observed_sample_counts = np.sum(observed_like_mask, axis=1)
    included_mask = (
        observed_sample_counts >= active_policy.min_observed_samples_per_entity
    )
    included_entity_ids = tuple(
        entity_id
        for row_index, entity_id in enumerate(table.entity_ids)
        if included_mask[row_index]
    )
    excluded_entity_ids = tuple(
        entity_id
        for row_index, entity_id in enumerate(table.entity_ids)
        if not included_mask[row_index]
    )
    included_codes = missing_kind_codes[included_mask, :]
    counts_by_kind = {
        kind: np.sum(
            included_codes == missing_value_kind_to_code(kind),
            axis=0,
        )
        for kind in _MISSING_VALUE_KINDS
    }
    entries = tuple(
        MissingValueSummaryEntry(
            sample_id=sample_id,
            observed_count=int(counts_by_kind[MissingValueKind.OBSERVED][column_index]),
            zero_count=int(counts_by_kind[MissingValueKind.ZERO][column_index]),
            not_observed_count=int(
                counts_by_kind[MissingValueKind.NOT_OBSERVED][column_index]
            ),
            filtered_count=int(counts_by_kind[MissingValueKind.FILTERED][column_index]),
            imputed_count=int(counts_by_kind[MissingValueKind.IMPUTED][column_index]),
            censored_count=int(counts_by_kind[MissingValueKind.CENSORED][column_index]),
            excluded_count=int(counts_by_kind[MissingValueKind.EXCLUDED][column_index]),
            not_applicable_count=int(
                counts_by_kind[MissingValueKind.NOT_APPLICABLE][column_index]
            ),
        )
        for column_index, sample_id in enumerate(table.sample_ids)
    )
    return MissingValueSummaryReport(
        entity_level=table.entity_level,
        policy=active_policy,
        entries=entries,
        included_entity_ids=included_entity_ids,
        excluded_entity_ids=excluded_entity_ids,
    )


__all__ = [
    "_summarize_missing_values_pure",
    "_summarize_missing_values_vectorized",
    "summarize_missing_values",
]

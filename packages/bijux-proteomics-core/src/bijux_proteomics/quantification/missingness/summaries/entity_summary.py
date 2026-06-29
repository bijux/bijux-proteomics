# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Entity-level missingness summaries."""

from __future__ import annotations

import numpy as np

from bijux_proteomics.quantification.contracts.input_models import MissingValueKind
from bijux_proteomics.quantification.contracts.matrix_building import (
    _matrix_value_index,
)
from bijux_proteomics.quantification.contracts.matrix_models import LabelFreeQuantTable
from bijux_proteomics.quantification.contracts.missingness import (
    MissingValueSummaryPolicy,
    MissingnessEntitySummaryEntry,
    MissingnessEntitySummaryReport,
)
from bijux_proteomics.quantification.matrix import (
    build_dense_label_free_quant_table_view,
    missing_value_kind_to_code,
)
from bijux_proteomics.quantification.missingness.policy import (
    _MISSING_BURDEN_CODES,
    _MISSING_VALUE_KINDS,
    apply_missing_value_summary_policy,
    apply_missing_value_summary_policy_codes,
    empty_missing_value_counts,
    is_missing_burden,
)


def build_missingness_entity_summary_report(
    table: LabelFreeQuantTable,
    *,
    policy: MissingValueSummaryPolicy | None = None,
) -> MissingnessEntitySummaryReport:
    return _build_missingness_entity_summary_report_vectorized(table, policy=policy)


def _build_missingness_entity_summary_report_pure(
    table: LabelFreeQuantTable,
    *,
    policy: MissingValueSummaryPolicy | None = None,
) -> MissingnessEntitySummaryReport:
    """Summarize missingness per quantified entity across all samples."""
    active_policy = policy or MissingValueSummaryPolicy()
    lookup = _matrix_value_index(table)
    entries: list[MissingnessEntitySummaryEntry] = []
    for entity_id in table.entity_ids:
        counts = empty_missing_value_counts()
        for sample_id in table.sample_ids:
            kind = apply_missing_value_summary_policy(
                lookup[(entity_id, sample_id)].missing_value_kind,
                policy=active_policy,
            )
            counts[kind] += 1
        missing_count = sum(
            count for kind, count in counts.items() if is_missing_burden(kind)
        )
        entries.append(
            MissingnessEntitySummaryEntry(
                entity_id=entity_id,
                observed_sample_count=counts[MissingValueKind.OBSERVED],
                zero_sample_count=counts[MissingValueKind.ZERO],
                not_observed_sample_count=counts[MissingValueKind.NOT_OBSERVED],
                filtered_sample_count=counts[MissingValueKind.FILTERED],
                imputed_sample_count=counts[MissingValueKind.IMPUTED],
                censored_sample_count=counts[MissingValueKind.CENSORED],
                excluded_sample_count=counts[MissingValueKind.EXCLUDED],
                not_applicable_sample_count=counts[MissingValueKind.NOT_APPLICABLE],
                missing_fraction=(
                    float(missing_count / len(table.sample_ids))
                    if table.sample_ids
                    else 0.0
                ),
            )
        )
    return MissingnessEntitySummaryReport(
        entity_level=table.entity_level,
        entries=tuple(entries),
    )


def _build_missingness_entity_summary_report_vectorized(
    table: LabelFreeQuantTable,
    *,
    policy: MissingValueSummaryPolicy | None = None,
) -> MissingnessEntitySummaryReport:
    active_policy = policy or MissingValueSummaryPolicy()
    dense_view = build_dense_label_free_quant_table_view(table)
    missing_kind_codes = apply_missing_value_summary_policy_codes(
        dense_view.missing_kind_codes,
        policy=active_policy,
    )
    counts_by_kind = {
        kind: np.sum(
            missing_kind_codes == missing_value_kind_to_code(kind),
            axis=1,
        )
        for kind in _MISSING_VALUE_KINDS
    }
    missing_counts = np.sum(
        np.isin(missing_kind_codes, _MISSING_BURDEN_CODES),
        axis=1,
    )
    sample_count = len(table.sample_ids)
    entries = tuple(
        MissingnessEntitySummaryEntry(
            entity_id=entity_id,
            observed_sample_count=int(
                counts_by_kind[MissingValueKind.OBSERVED][row_index]
            ),
            zero_sample_count=int(counts_by_kind[MissingValueKind.ZERO][row_index]),
            not_observed_sample_count=int(
                counts_by_kind[MissingValueKind.NOT_OBSERVED][row_index]
            ),
            filtered_sample_count=int(
                counts_by_kind[MissingValueKind.FILTERED][row_index]
            ),
            imputed_sample_count=int(
                counts_by_kind[MissingValueKind.IMPUTED][row_index]
            ),
            censored_sample_count=int(
                counts_by_kind[MissingValueKind.CENSORED][row_index]
            ),
            excluded_sample_count=int(
                counts_by_kind[MissingValueKind.EXCLUDED][row_index]
            ),
            not_applicable_sample_count=int(
                counts_by_kind[MissingValueKind.NOT_APPLICABLE][row_index]
            ),
            missing_fraction=float(missing_counts[row_index] / sample_count)
            if sample_count
            else 0.0,
        )
        for row_index, entity_id in enumerate(table.entity_ids)
    )
    return MissingnessEntitySummaryReport(
        entity_level=table.entity_level,
        entries=entries,
    )


__all__ = [
    "_build_missingness_entity_summary_report_pure",
    "_build_missingness_entity_summary_report_vectorized",
    "build_missingness_entity_summary_report",
]

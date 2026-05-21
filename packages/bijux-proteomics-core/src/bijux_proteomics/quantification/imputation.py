# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owned missing-value imputation for quantitative proteomics tables."""

from __future__ import annotations

from bijux_proteomics.quantification.contracts import (
    ImputationMethod,
    ImputationReport,
    LabelFreeQuantTable,
)


def build_imputation_report(
    before: LabelFreeQuantTable,
    after: LabelFreeQuantTable,
) -> ImputationReport:
    """Build a stable ledger of values introduced by imputation."""
    _validate_imputation_pair(before, after)
    return ImputationReport(
        entity_level=after.entity_level,
        method=after.imputation_method,
        entries=(),
        imputed_value_count=0,
        note="no values were imputed under the current table pair",
    )


def impute_label_free_table(
    table: LabelFreeQuantTable,
    *,
    method: ImputationMethod = ImputationMethod.NONE,
) -> LabelFreeQuantTable:
    """Impute a label-free quant table under one explicit imputation policy."""
    if method is not ImputationMethod.NONE:
        raise ValueError(f"unsupported imputation method: {method.value}")
    return table.model_copy(update={"imputation_method": method})


def _validate_imputation_pair(
    before: LabelFreeQuantTable,
    after: LabelFreeQuantTable,
) -> None:
    if before.sample_ids != after.sample_ids or before.entity_ids != after.entity_ids:
        raise ValueError("before and after tables must cover the same sample/entity grid")


__all__ = [
    "build_imputation_report",
    "impute_label_free_table",
]

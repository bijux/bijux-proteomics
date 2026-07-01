# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Claim and trust policy for biological result graph protein claims."""

from __future__ import annotations

from bijux_proteomics.quantification.contracts import (
    DifferentialAbundanceEntry,
    LabelFreeQuantTable,
    MissingValueKind,
)


def _protein_label(entity_id: str, quant_table: LabelFreeQuantTable) -> str:
    protein_refs = quant_table.entity_protein_refs.get(entity_id, ())
    return protein_refs[0] if protein_refs else entity_id


def _protein_trust_class(entry: DifferentialAbundanceEntry) -> str:
    if min(entry.observations_a, entry.observations_b) <= 1:
        return "single_run_only"
    return "high"


def _quant_trust_class(missing_value_kind: MissingValueKind) -> str:
    if missing_value_kind is MissingValueKind.OBSERVED:
        return "high"
    return "imputed"


def _claim_state(
    entry: DifferentialAbundanceEntry,
    *,
    max_adjusted_p_value: float,
    min_absolute_log2_fold_change: float,
) -> str:
    adjusted = entry.adjusted_p_value
    if adjusted is None:
        return "unchanged"
    if adjusted > max_adjusted_p_value:
        return "unchanged"
    if abs(entry.log2_fold_change) < min_absolute_log2_fold_change:
        return "unchanged"
    return "upregulated" if entry.log2_fold_change >= 0.0 else "downregulated"


def _claim_confidence(entry: DifferentialAbundanceEntry) -> float:
    adjusted = 1.0 if entry.adjusted_p_value is None else entry.adjusted_p_value
    return max(0.05, min(0.99, 1.0 - adjusted))

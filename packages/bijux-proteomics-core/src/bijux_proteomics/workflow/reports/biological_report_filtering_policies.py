# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Owned biological filtering policies for enrichment foreground selection."""

from __future__ import annotations

from bijux_proteomics.interpretation import BiologicalSetFilteringPolicy
from bijux_proteomics.workflow.reports.biological_report_selection_policy import (
    BiologicalResultSelectionPolicy,
)


def _build_biological_foreground_filtering_policy(
    selection_policy: BiologicalResultSelectionPolicy,
) -> BiologicalSetFilteringPolicy:
    return BiologicalSetFilteringPolicy(
        policy_name="biological_result_selection",
        max_adjusted_p_value=selection_policy.max_adjusted_p_value,
        min_absolute_log2_fold_change=selection_policy.min_absolute_log2_fold_change,
        measured_entities_only=True,
        deduplicate_protein_refs=True,
        note=(
            "foreground keeps statistically selected proteins from the governed "
            "contrast using the biological result selection thresholds"
        ),
    )


def _build_biological_background_filtering_policy() -> BiologicalSetFilteringPolicy:
    return BiologicalSetFilteringPolicy(
        policy_name="measured_protein_quantification_universe",
        measured_entities_only=True,
        deduplicate_protein_refs=True,
        note=(
            "background keeps every measured protein in the normalized quantification "
            "table instead of silently broadening to the annotation universe"
        ),
    )

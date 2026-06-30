# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi
"""Selection policy contracts and protocol-derived defaults for biological reports."""

from __future__ import annotations

from pathlib import Path

from pydantic import ConfigDict, Field

from bijux_proteomics.lab.protocol_context import (
    build_lab_protocol_interpretation_profile,
    parse_lab_protocol_context_table,
    require_single_lab_protocol_context,
)
from bijux_proteomics_foundation import JsonModel


class BiologicalResultSelectionPolicy(JsonModel):
    """Selection policy for interpretation-focused biological result bundles."""

    model_config = ConfigDict(extra="forbid")

    max_adjusted_p_value: float = Field(default=0.1, ge=0.0, le=1.0)
    min_absolute_log2_fold_change: float = Field(default=1.0, ge=0.0)
    heatmap_max_entity_count: int = Field(default=50, ge=1)
    heatmap_min_observed_fraction: float = Field(default=0.5, ge=0.0, le=1.0)


def _resolve_biological_result_selection_policy(
    selection_policy: BiologicalResultSelectionPolicy | None,
    *,
    protocol_context_tsv_path: Path | None,
) -> BiologicalResultSelectionPolicy:
    if selection_policy is not None:
        return selection_policy
    if protocol_context_tsv_path is None:
        return BiologicalResultSelectionPolicy()
    protocol_context = require_single_lab_protocol_context(
        parse_lab_protocol_context_table(protocol_context_tsv_path)
    )
    profile = build_lab_protocol_interpretation_profile(protocol_context)
    return BiologicalResultSelectionPolicy(
        max_adjusted_p_value=profile.max_adjusted_p_value,
        min_absolute_log2_fold_change=profile.min_absolute_log2_fold_change,
        heatmap_max_entity_count=profile.heatmap_max_entity_count,
        heatmap_min_observed_fraction=(
            BiologicalResultSelectionPolicy().heatmap_min_observed_fraction
        ),
    )

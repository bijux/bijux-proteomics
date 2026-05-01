# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Intelligence and review production surfaces for iteration 15."""

from __future__ import annotations

from enum import StrEnum
from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel


class EnrichmentCorrectionMethod(StrEnum):
    """Multiple-testing correction method for enrichment analyses."""

    BENJAMINI_HOCHBERG = "benjamini_hochberg"
    BONFERRONI = "bonferroni"
    NONE = "none"


class EnrichmentBackgroundProvenance(JsonModel):
    """Background and statistical provenance for one enrichment output."""

    model_config = ConfigDict(extra="forbid")

    analysis_id: str = Field(..., min_length=1)
    universe_id: str = Field(..., min_length=1)
    filter_expression: str = Field(..., min_length=1)
    statistical_test: str = Field(..., min_length=1)
    correction_method: EnrichmentCorrectionMethod
    input_evidence_ids: tuple[str, ...] = Field(default_factory=tuple)
    notes: tuple[str, ...] = Field(default_factory=tuple)


def build_enrichment_background_provenance(
    *,
    analysis_id: str,
    universe_id: str,
    filter_expression: str,
    statistical_test: str,
    correction_method: EnrichmentCorrectionMethod,
    input_evidence_ids: tuple[str, ...],
    notes: tuple[str, ...] = (),
) -> EnrichmentBackgroundProvenance:
    """Record universe, filter, test, correction, and evidence provenance."""

    if not input_evidence_ids:
        raise ValueError("enrichment provenance requires input evidence pointers")

    return EnrichmentBackgroundProvenance(
        analysis_id=analysis_id,
        universe_id=universe_id,
        filter_expression=filter_expression,
        statistical_test=statistical_test,
        correction_method=correction_method,
        input_evidence_ids=tuple(sorted(set(input_evidence_ids))),
        notes=tuple(sorted(set(notes))),
    )

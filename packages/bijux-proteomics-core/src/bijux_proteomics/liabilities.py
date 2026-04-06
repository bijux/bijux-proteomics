# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Liability models for protein programs."""

from __future__ import annotations

from enum import StrEnum

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import EvidenceId, JsonModel


class LiabilityCategory(StrEnum):
    """Major liability families tracked at the program layer."""

    SAFETY = "safety"
    DEVELOPABILITY = "developability"
    SPECIFICITY = "specificity"
    ASSAY = "assay"


class ProgramLiability(JsonModel):
    """Known liability that should shape program and candidate decisions."""

    model_config = ConfigDict(extra="forbid")

    liability_id: EvidenceId = Field(..., description="Stable liability identifier.")
    category: LiabilityCategory = Field(..., description="Liability family.")
    summary: str = Field(..., min_length=1, description="Human-readable liability summary.")
    impact: str = Field(..., min_length=1, description="Expected program impact.")
    mitigation: str = Field(..., min_length=1, description="Planned mitigation path.")
    severity: int = Field(
        default=3,
        ge=1,
        le=5,
        description="Liability severity from low to critical.",
    )
    blocker: bool = Field(
        default=False,
        description="Whether this liability should block progression until mitigated.",
    )
    owner_role: str | None = Field(
        default=None,
        description="Decision owner role accountable for this liability.",
    )
    evidence_ids: list[str] = Field(
        default_factory=list,
        description="Evidence references supporting this liability assessment.",
    )

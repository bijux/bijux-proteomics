# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Policy models for candidate ranking."""

from __future__ import annotations

from enum import StrEnum

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import DocumentSchema, JsonModel


class TieBreakRule(StrEnum):
    """Tie-break rules used after primary scoring."""

    EVIDENCE_SUPPORT = "evidence_support"
    MANUFACTURABILITY = "manufacturability"
    LOWER_UNCERTAINTY = "lower_uncertainty"
    FEWER_LIABILITIES = "fewer_liabilities"


class RankingPolicy(JsonModel):
    """Serializable ranking policy for candidate evaluation."""

    model_config = ConfigDict(extra="forbid")

    policy_id: str = Field(..., min_length=1, description="Stable policy identifier.")
    document_schema: DocumentSchema = Field(
        default_factory=lambda: DocumentSchema(created_by="bijux-proteomics-intelligence"),
        description="Schema and provenance metadata.",
    )
    minimum_metric_fraction: float = Field(
        default=0.5,
        ge=0.0,
        description="Minimum fraction of criterion thresholds required to stay in ranking.",
    )
    minimum_evidence_support: float = Field(
        default=0.2,
        ge=0.0,
        le=1.0,
        description="Minimum evidence support required to stay in ranking.",
    )
    require_manufacturability_floor: bool = Field(
        default=False,
        description="Whether low manufacturability is a hard rejection.",
    )
    manufacturability_floor: float = Field(
        default=0.3,
        ge=0.0,
        le=1.0,
        description="Minimum acceptable manufacturability score.",
    )
    uncertainty_penalty_weight: float = Field(
        default=0.4,
        ge=0.0,
        description="Penalty weight applied to uncertainty.",
    )
    diversity_bonus_weight: float = Field(
        default=0.1,
        ge=0.0,
        description="Bonus weight for candidates with fewer liabilities.",
    )
    tie_break_rules: list[TieBreakRule] = Field(
        default_factory=lambda: [
            TieBreakRule.EVIDENCE_SUPPORT,
            TieBreakRule.MANUFACTURABILITY,
            TieBreakRule.LOWER_UNCERTAINTY,
        ],
        description="Ordered tie-break rules for near-equal scores.",
    )

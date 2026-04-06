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


class RankingFactor(StrEnum):
    """Named factors used in normalized ranking."""

    CRITERIA = "criteria"
    EVIDENCE = "evidence"
    MANUFACTURABILITY = "manufacturability"
    LIABILITY = "liability"
    UNCERTAINTY = "uncertainty"


class ScientificMetricClass(StrEnum):
    """Typed scientific metric classes used across ranking logic."""

    ACTIVITY = "activity"
    AFFINITY = "affinity"
    STABILITY = "stability"
    SPECIFICITY = "specificity"
    SAFETY = "safety"
    DEVELOPABILITY = "developability"


class MetricDirection(StrEnum):
    """Direction semantics for scientific metrics."""

    HIGHER_IS_BETTER = "higher_is_better"
    LOWER_IS_BETTER = "lower_is_better"
    RANGE_IS_BETTER = "range_is_better"


class MetricDefinition(JsonModel):
    """Typed scientific metric definition used by ranking and validation."""

    model_config = ConfigDict(extra="forbid")

    metric_key: str = Field(..., min_length=1, description="Stable metric key.")
    metric_class: ScientificMetricClass = Field(..., description="Scientific metric family.")
    unit: str | None = Field(default=None, description="Expected measurement unit.")
    direction: MetricDirection = Field(..., description="Direction semantics for optimization.")
    normalization: str | None = Field(
        default=None,
        description="Optional normalization method such as zscore or minmax.",
    )


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
    factor_weights: dict[RankingFactor, float] = Field(
        default_factory=lambda: {
            RankingFactor.CRITERIA: 0.45,
            RankingFactor.EVIDENCE: 0.2,
            RankingFactor.MANUFACTURABILITY: 0.15,
            RankingFactor.LIABILITY: 0.1,
            RankingFactor.UNCERTAINTY: 0.1,
        },
        description="Weights used for normalized factor scoring.",
    )
    tie_break_rules: list[TieBreakRule] = Field(
        default_factory=lambda: [
            TieBreakRule.EVIDENCE_SUPPORT,
            TieBreakRule.MANUFACTURABILITY,
            TieBreakRule.LOWER_UNCERTAINTY,
        ],
        description="Ordered tie-break rules for near-equal scores.",
    )


class ProgressionPolicyConfig(JsonModel):
    """Policy settings for progression decisions."""

    model_config = ConfigDict(extra="forbid")

    policy_id: str = Field(..., min_length=1, description="Stable progression policy identifier.")
    minimum_evidence_support: float = Field(
        default=0.6,
        ge=0.0,
        le=1.0,
        description="Minimum evidence support required for progression recommendations.",
    )


class HoldPolicyConfig(JsonModel):
    """Policy settings for hold decisions."""

    model_config = ConfigDict(extra="forbid")

    policy_id: str = Field(..., min_length=1, description="Stable hold policy identifier.")
    minimum_confidence_for_release: float = Field(
        default=0.65,
        ge=0.0,
        le=1.0,
        description="Minimum confidence required to release a hold.",
    )


class RedesignPolicyConfig(JsonModel):
    """Policy settings for redesign decisions."""

    model_config = ConfigDict(extra="forbid")

    policy_id: str = Field(..., min_length=1, description="Stable redesign policy identifier.")
    residual_risk_trigger: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Residual risk threshold that should trigger redesign.",
    )


def classify_metric_name(metric: str) -> ScientificMetricClass:
    """Classify a metric name into a typed scientific metric class."""
    lowered = metric.lower()
    if any(token in lowered for token in ("affin", "bind", "kd", "ic50", "ec50")):
        return ScientificMetricClass.AFFINITY
    if any(token in lowered for token in ("stabil", "tm", "fold")):
        return ScientificMetricClass.STABILITY
    if any(token in lowered for token in ("specif", "off_target", "selectiv")):
        return ScientificMetricClass.SPECIFICITY
    if any(token in lowered for token in ("tox", "immun", "safety")):
        return ScientificMetricClass.SAFETY
    if any(token in lowered for token in ("yield", "express", "aggregation", "develop")):
        return ScientificMetricClass.DEVELOPABILITY
    return ScientificMetricClass.ACTIVITY

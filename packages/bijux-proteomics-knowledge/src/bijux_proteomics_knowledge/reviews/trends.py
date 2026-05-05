# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Packet comparison and trend summaries for reviewer-facing knowledge output."""

from __future__ import annotations

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel
from bijux_proteomics_knowledge.reviews.packets import KnowledgeReviewPacket


class KnowledgeReviewDelta(JsonModel):
    """Difference report between two review packets."""

    model_config = ConfigDict(extra="forbid")

    decision_tag: str = Field(..., min_length=1, description="Decision tag compared.")
    intelligence_index_delta: float = Field(
        ..., description="Change in decision intelligence index."
    )
    trust_delta: float = Field(..., description="Change in trust score.")
    triangulation_delta: float = Field(
        ..., description="Change in triangulation score."
    )
    gap_delta: int = Field(..., description="Change in unresolved knowledge gap count.")
    recommendation_changed: bool = Field(
        ..., description="Whether gate recommendation changed."
    )


class KnowledgeReviewTrend(JsonModel):
    """Trend summary across a sequence of review deltas."""

    model_config = ConfigDict(extra="forbid")

    decision_tag: str = Field(
        ..., min_length=1, description="Decision tag under trend analysis."
    )
    net_intelligence_delta: float = Field(
        ..., description="Net intelligence-index change across deltas."
    )
    improving_steps: int = Field(
        default=0, ge=0, description="Count of positive intelligence steps."
    )
    regressing_steps: int = Field(
        default=0, ge=0, description="Count of negative intelligence steps."
    )
    recommendation_change_count: int = Field(
        default=0, ge=0, description="Count of recommendation transitions."
    )


def compare_review_packets(
    previous: KnowledgeReviewPacket,
    current: KnowledgeReviewPacket,
) -> KnowledgeReviewDelta:
    """Compare two review packets for the same decision tag."""
    if previous.decision_tag != current.decision_tag:
        raise ValueError("review packets must share the same decision_tag")
    return KnowledgeReviewDelta(
        decision_tag=current.decision_tag,
        intelligence_index_delta=round(
            current.decision_intelligence_index - previous.decision_intelligence_index,
            4,
        ),
        trust_delta=round(
            current.quality_audit.trust_score - previous.quality_audit.trust_score, 4
        ),
        triangulation_delta=round(
            current.quality_audit.triangulation_score
            - previous.quality_audit.triangulation_score,
            4,
        ),
        gap_delta=len(current.knowledge_gaps) - len(previous.knowledge_gaps),
        recommendation_changed=current.gate_recommendation
        != previous.gate_recommendation,
    )


def summarize_review_trend(deltas: list[KnowledgeReviewDelta]) -> KnowledgeReviewTrend:
    """Summarize progression trend across ordered review deltas."""
    if not deltas:
        return KnowledgeReviewTrend(
            decision_tag="unknown",
            net_intelligence_delta=0.0,
            improving_steps=0,
            regressing_steps=0,
            recommendation_change_count=0,
        )
    return KnowledgeReviewTrend(
        decision_tag=deltas[-1].decision_tag,
        net_intelligence_delta=round(
            sum(delta.intelligence_index_delta for delta in deltas), 4
        ),
        improving_steps=sum(
            1 for delta in deltas if delta.intelligence_index_delta > 0
        ),
        regressing_steps=sum(
            1 for delta in deltas if delta.intelligence_index_delta < 0
        ),
        recommendation_change_count=sum(
            1 for delta in deltas if delta.recommendation_changed
        ),
    )

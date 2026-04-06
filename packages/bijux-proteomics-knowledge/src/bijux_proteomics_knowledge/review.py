# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Integrated review packet builders for scientific decision readiness."""

from __future__ import annotations

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel
from bijux_proteomics_knowledge.claims import (
    EvidenceClaim,
    HypothesisDossier,
    KnowledgeGap,
    build_hypothesis_dossier,
    identify_knowledge_gaps,
)
from bijux_proteomics_knowledge.evidence import (
    EvidenceBundle,
    EvidenceRelevanceScore,
    KnowledgeQualityAudit,
    audit_knowledge_quality,
    rank_evidence_for_decision,
)
from bijux_proteomics_knowledge.resolution import ConflictCluster, cluster_conflicts, resolve_conflicts


class KnowledgeReviewPacket(JsonModel):
    """Unified review packet for one target and decision dimension."""

    model_config = ConfigDict(extra="forbid")

    target_id: str = Field(..., min_length=1, description="Target identifier.")
    decision_tag: str = Field(..., min_length=1, description="Decision tag under review.")
    evidence_ranking: list[EvidenceRelevanceScore] = Field(
        default_factory=list,
        description="Evidence ranked for decision relevance.",
    )
    quality_audit: KnowledgeQualityAudit = Field(..., description="Bundle-level quality audit.")
    hypothesis_dossier: HypothesisDossier = Field(..., description="Claim-level hypothesis dossier.")
    knowledge_gaps: list[KnowledgeGap] = Field(default_factory=list, description="Structured unresolved gaps.")
    conflict_clusters: list[ConflictCluster] = Field(default_factory=list, description="Grouped conflicts for review.")
    gate_recommendation: str = Field(..., min_length=1, description="Recommended gate action for the decision tag.")
    executive_summary: list[str] = Field(default_factory=list, description="High-level review summary points.")
    decision_intelligence_index: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Composite index for decision intelligence readiness.",
    )


class MultiDecisionReadiness(JsonModel):
    """Decision readiness summary across multiple decision tags."""

    model_config = ConfigDict(extra="forbid")

    target_id: str = Field(..., min_length=1, description="Target identifier.")
    decision_scores: dict[str, float] = Field(default_factory=dict, description="Decision-tag intelligence indices.")
    weakest_decision_tag: str | None = Field(default=None, description="Lowest-scoring decision tag.")
    portfolio_score: float = Field(..., ge=0.0, le=1.0, description="Mean readiness score across decision tags.")


def build_knowledge_review_packet(
    bundle: EvidenceBundle,
    claims: list[EvidenceClaim],
    *,
    decision_tag: str,
    required_modalities: list[str] | None = None,
    expected_species: str | None = None,
    expected_system: str | None = None,
    expected_sample_type: str | None = None,
) -> KnowledgeReviewPacket:
    """Build an integrated review packet for decision workflows."""
    ranking = rank_evidence_for_decision(
        bundle,
        decision_tag=decision_tag,
        expected_species=expected_species,
        expected_system=expected_system,
        expected_sample_type=expected_sample_type,
    )
    audit = audit_knowledge_quality(
        bundle,
        decision_tag=decision_tag,
        required_modalities=required_modalities,
    )
    dossier = build_hypothesis_dossier(bundle, claims, decision_tag=decision_tag)
    gaps = identify_knowledge_gaps(bundle, claims, decision_tag=decision_tag)
    trust, _ = resolve_conflicts(bundle)
    clusters = cluster_conflicts(bundle, trust)
    gate_recommendation = _recommend_gate_action(
        quality_audit=audit,
        knowledge_gaps=gaps,
        conflict_clusters=clusters,
    )
    summary = _build_executive_summary(
        quality_audit=audit,
        dossier=dossier,
        knowledge_gaps=gaps,
        gate_recommendation=gate_recommendation,
    )
    intelligence_index = compute_decision_intelligence_index(
        quality_audit=audit,
        knowledge_gaps=gaps,
        conflict_clusters=clusters,
    )
    return KnowledgeReviewPacket(
        target_id=bundle.target_id,
        decision_tag=decision_tag,
        evidence_ranking=ranking,
        quality_audit=audit,
        hypothesis_dossier=dossier,
        knowledge_gaps=gaps,
        conflict_clusters=clusters,
        gate_recommendation=gate_recommendation,
        executive_summary=summary,
        decision_intelligence_index=intelligence_index,
    )


def _recommend_gate_action(
    *,
    quality_audit: KnowledgeQualityAudit,
    knowledge_gaps: list[KnowledgeGap],
    conflict_clusters: list[ConflictCluster],
) -> str:
    if any(cluster.recommended_hold for cluster in conflict_clusters):
        return "hold-for-conflict-resolution"
    if knowledge_gaps:
        return "advance-with-targeted-gap-closure"
    if quality_audit.trust_score < 0.7:
        return "advance-with-evidence-hardening"
    return "advance"


def _build_executive_summary(
    *,
    quality_audit: KnowledgeQualityAudit,
    dossier: HypothesisDossier,
    knowledge_gaps: list[KnowledgeGap],
    gate_recommendation: str,
) -> list[str]:
    summary = [
        f"trust score {quality_audit.trust_score:.2f} with triangulation {quality_audit.triangulation_score:.2f}",
        f"{len(dossier.supporting_claim_ids)} supporting and {len(dossier.contradicting_claim_ids)} contradicting claims",
        f"gate recommendation: {gate_recommendation}",
    ]
    if knowledge_gaps:
        summary.append(f"{len(knowledge_gaps)} unresolved knowledge gaps remain")
    return summary


def compute_decision_intelligence_index(
    *,
    quality_audit: KnowledgeQualityAudit,
    knowledge_gaps: list[KnowledgeGap],
    conflict_clusters: list[ConflictCluster],
) -> float:
    """Compute a composite readiness index from quality, gaps, and conflicts."""
    score = quality_audit.trust_score * 0.45 + quality_audit.triangulation_score * 0.35
    gap_penalty = min(0.25, 0.05 * len(knowledge_gaps))
    high_conflict_penalty = min(
        0.25,
        0.08 * sum(1 for cluster in conflict_clusters if cluster.recommended_hold),
    )
    return max(0.0, min(round(score - gap_penalty - high_conflict_penalty, 4), 1.0))


def summarize_multi_decision_readiness(
    bundle: EvidenceBundle,
    claims: list[EvidenceClaim],
    *,
    decision_tags: list[str],
    required_modalities: list[str] | None = None,
) -> MultiDecisionReadiness:
    """Build a cross-decision readiness summary from review packets."""
    scores: dict[str, float] = {}
    for decision_tag in decision_tags:
        packet = build_knowledge_review_packet(
            bundle,
            claims,
            decision_tag=decision_tag,
            required_modalities=required_modalities,
        )
        scores[decision_tag] = packet.decision_intelligence_index
    if not scores:
        return MultiDecisionReadiness(
            target_id=bundle.target_id,
            decision_scores={},
            weakest_decision_tag=None,
            portfolio_score=0.0,
        )
    weakest = min(scores, key=scores.get)
    portfolio_score = round(sum(scores.values()) / len(scores), 4)
    return MultiDecisionReadiness(
        target_id=bundle.target_id,
        decision_scores=scores,
        weakest_decision_tag=weakest,
        portfolio_score=portfolio_score,
    )

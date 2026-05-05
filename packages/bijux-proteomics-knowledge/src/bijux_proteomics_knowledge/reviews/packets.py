# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Integrated review packet builders for scientific decision readiness."""

from __future__ import annotations

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel
from bijux_proteomics_knowledge.memory.claims import (
    EvidenceClaim,
    HypothesisDossier,
    KnowledgeGap,
    build_hypothesis_dossier,
    identify_knowledge_gaps,
)
from bijux_proteomics_knowledge.memory.evidence import (
    EvidenceBundle,
    EvidenceConflict,
    EvidenceRelevanceScore,
    KnowledgeQualityAudit,
    audit_knowledge_quality,
    rank_evidence_for_decision,
)
from bijux_proteomics_knowledge.memory.resolution import (
    ConflictCluster,
    cluster_conflicts,
    resolve_conflicts,
)


class KnowledgeReviewPacket(JsonModel):
    """Unified review packet for one target and decision dimension."""

    model_config = ConfigDict(extra="forbid")

    target_id: str = Field(..., min_length=1, description="Target identifier.")
    decision_tag: str = Field(
        ..., min_length=1, description="Decision tag under review."
    )
    evidence_ranking: list[EvidenceRelevanceScore] = Field(
        default_factory=list,
        description="Evidence ranked for decision relevance.",
    )
    quality_audit: KnowledgeQualityAudit = Field(
        ..., description="Bundle-level quality audit."
    )
    hypothesis_dossier: HypothesisDossier = Field(
        ..., description="Claim-level hypothesis dossier."
    )
    knowledge_gaps: list[KnowledgeGap] = Field(
        default_factory=list, description="Structured unresolved gaps."
    )
    conflict_clusters: list[ConflictCluster] = Field(
        default_factory=list, description="Grouped conflicts for review."
    )
    gate_recommendation: str = Field(
        ..., min_length=1, description="Recommended gate action for the decision tag."
    )
    executive_summary: list[str] = Field(
        default_factory=list, description="High-level review summary points."
    )
    blocker_highlights: list[str] = Field(
        default_factory=list, description="Top blocker highlights for decision review."
    )
    scientific_conclusions: list[ScientificConclusion] = Field(
        default_factory=list,
        description="Scientific conclusions kept separate from operational labels.",
    )
    operational_labels: list[OperationalDecisionLabel] = Field(
        default_factory=list,
        description="Operational labels derived from scientific conclusions.",
    )
    decision_intelligence_index: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Composite index for decision intelligence readiness.",
    )


class ScientificConclusion(JsonModel):
    """A scientific conclusion supported or challenged by reviewed evidence."""

    model_config = ConfigDict(extra="forbid")

    claim_id: str = Field(..., min_length=1)
    statement: str = Field(..., min_length=1)
    evidence_state: str = Field(..., min_length=1)
    confidence: float = Field(..., ge=0.0, le=1.0)
    evidence_ids: list[str] = Field(default_factory=list)


class OperationalDecisionLabel(JsonModel):
    """Operational label layered on top of scientific conclusions."""

    model_config = ConfigDict(extra="forbid")

    label: str = Field(..., min_length=1)
    rationale: str = Field(..., min_length=1)
    conclusion_claim_ids: list[str] = Field(default_factory=list)


class MultiDecisionReadiness(JsonModel):
    """Decision readiness summary across multiple decision tags."""

    model_config = ConfigDict(extra="forbid")

    target_id: str = Field(..., min_length=1, description="Target identifier.")
    decision_scores: dict[str, float] = Field(
        default_factory=dict, description="Decision-tag intelligence indices."
    )
    weakest_decision_tag: str | None = Field(
        default=None, description="Lowest-scoring decision tag."
    )
    portfolio_score: float = Field(
        ..., ge=0.0, le=1.0, description="Mean readiness score across decision tags."
    )


class DecisionGateProfile(JsonModel):
    """Policy thresholds for decision recommendation in review packets."""

    model_config = ConfigDict(extra="forbid")

    profile_id: str = Field(
        ..., min_length=1, description="Stable gate profile identifier."
    )
    minimum_trust_score: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Minimum trust score for direct advance.",
    )
    minimum_triangulation_score: float = Field(
        default=0.6,
        ge=0.0,
        le=1.0,
        description="Minimum triangulation score for direct advance.",
    )


def build_knowledge_review_packet(
    bundle: EvidenceBundle,
    claims: list[EvidenceClaim],
    *,
    decision_tag: str,
    required_modalities: list[str] | None = None,
    expected_species: str | None = None,
    expected_system: str | None = None,
    expected_sample_type: str | None = None,
    gate_profile: DecisionGateProfile | None = None,
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
    gate_profile = gate_profile or DecisionGateProfile(
        profile_id="default-gate-profile"
    )
    gate_recommendation = _recommend_gate_action(
        quality_audit=audit,
        knowledge_gaps=gaps,
        conflict_clusters=clusters,
        gate_profile=gate_profile,
    )
    summary = _build_executive_summary(
        quality_audit=audit,
        dossier=dossier,
        knowledge_gaps=gaps,
        gate_recommendation=gate_recommendation,
    )
    blocker_highlights = extract_blocker_highlights(
        quality_audit=audit,
        knowledge_gaps=gaps,
        conflict_clusters=clusters,
    )
    scientific_conclusions = _build_scientific_conclusions(
        claims=claims,
        decision_tag=decision_tag,
        bundle=bundle,
    )
    operational_labels = _build_operational_labels(
        gate_recommendation=gate_recommendation,
        scientific_conclusions=scientific_conclusions,
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
        blocker_highlights=blocker_highlights,
        scientific_conclusions=scientific_conclusions,
        operational_labels=operational_labels,
        decision_intelligence_index=intelligence_index,
    )


def _build_scientific_conclusions(
    *,
    claims: list[EvidenceClaim],
    decision_tag: str,
    bundle: EvidenceBundle,
) -> list[ScientificConclusion]:
    tagged_evidence_ids = {
        record.evidence_id
        for record in bundle.records
        if decision_tag in record.decision_tags
    }
    conclusions = [
        ScientificConclusion(
            claim_id=claim.claim_id,
            statement=claim.statement,
            evidence_state=claim.evidence_state.value,
            confidence=round(claim.confidence, 4),
            evidence_ids=[
                evidence_id
                for evidence_id in claim.evidence_ids
                if evidence_id in tagged_evidence_ids
            ],
        )
        for claim in claims
        if tagged_evidence_ids.intersection(claim.evidence_ids)
    ]
    return sorted(conclusions, key=lambda conclusion: conclusion.claim_id)


def _build_operational_labels(
    *,
    gate_recommendation: str,
    scientific_conclusions: list[ScientificConclusion],
) -> list[OperationalDecisionLabel]:
    return [
        OperationalDecisionLabel(
            label=gate_recommendation,
            rationale="operational recommendation derived from current scientific conclusions and review policy",
            conclusion_claim_ids=[
                conclusion.claim_id for conclusion in scientific_conclusions
            ],
        )
    ]


def _recommend_gate_action(
    *,
    quality_audit: KnowledgeQualityAudit,
    knowledge_gaps: list[KnowledgeGap],
    conflict_clusters: list[ConflictCluster],
    gate_profile: DecisionGateProfile,
) -> str:
    if any(cluster.recommended_hold for cluster in conflict_clusters):
        return "hold-for-conflict-resolution"
    if knowledge_gaps:
        return "advance-with-targeted-gap-closure"
    if quality_audit.trust_score < gate_profile.minimum_trust_score:
        return "advance-with-evidence-hardening"
    if quality_audit.triangulation_score < gate_profile.minimum_triangulation_score:
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
    weakest = min(scores, key=lambda tag: scores[tag])
    portfolio_score = round(sum(scores.values()) / len(scores), 4)
    return MultiDecisionReadiness(
        target_id=bundle.target_id,
        decision_scores=scores,
        weakest_decision_tag=weakest,
        portfolio_score=portfolio_score,
    )


def extract_blocker_highlights(
    *,
    quality_audit: KnowledgeQualityAudit,
    knowledge_gaps: list[KnowledgeGap],
    conflict_clusters: list[ConflictCluster],
    limit: int = 5,
) -> list[str]:
    """Extract concise blocker highlights sorted by decision risk."""
    highlights: list[tuple[int, str]] = [
        (3, f"high-severity conflict cluster in '{cluster.decision_tag}'")
        for cluster in conflict_clusters
        if cluster.recommended_hold
    ]
    highlights.extend((2, f"knowledge gap: {gap.gap_code}") for gap in knowledge_gaps)
    highlights.extend(
        (1, f"quality action: {recommendation}")
        for recommendation in quality_audit.recommendations
    )
    highlights.sort(key=lambda item: item[0], reverse=True)
    return [text for _, text in highlights[:limit]]

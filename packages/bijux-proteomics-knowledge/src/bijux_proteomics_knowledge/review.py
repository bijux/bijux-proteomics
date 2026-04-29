# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Integrated review packet builders for scientific decision readiness."""

from __future__ import annotations

from enum import StrEnum

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
    EvidenceConflict,
    EvidenceRelevanceScore,
    KnowledgeQualityAudit,
    audit_knowledge_quality,
    rank_evidence_for_decision,
)
from bijux_proteomics_knowledge.graph import (
    DecisionTracePath,
    EvidenceGraph,
    UnresolvedQuestion,
    build_evidence_graph,
    extract_decision_subgraph,
    trace_decision_paths,
)
from bijux_proteomics_knowledge.resolution import (
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


class CandidateDecisionDisposition(StrEnum):
    """Disposition under explanation for one candidate review query."""

    ACCEPTED = "accepted"
    REJECTED = "rejected"
    DEFERRED = "deferred"


class CandidateDecisionGraphQuery(JsonModel):
    """Decision-scoped graph query for one candidate outcome explanation."""

    model_config = ConfigDict(extra="forbid")

    candidate_id: str = Field(..., min_length=1)
    decision_tag: str = Field(..., min_length=1)
    disposition: CandidateDecisionDisposition


class CandidateDecisionGraphExplanation(JsonModel):
    """Evidence-graph-backed explanation for one candidate outcome."""

    model_config = ConfigDict(extra="forbid")

    candidate_id: str = Field(..., min_length=1)
    decision_tag: str = Field(..., min_length=1)
    disposition: CandidateDecisionDisposition
    gate_recommendation: str = Field(..., min_length=1)
    decision_subgraph: EvidenceGraph = Field(
        ..., description="Decision-scoped evidence subgraph."
    )
    decision_paths: list[DecisionTracePath] = Field(
        default_factory=list,
        description="Decision traces ending in evidence, claim, or blocker nodes.",
    )
    supporting_evidence_ids: list[str] = Field(default_factory=list)
    contradicting_evidence_ids: list[str] = Field(default_factory=list)
    unresolved_question_ids: list[str] = Field(default_factory=list)
    blocker_highlights: list[str] = Field(default_factory=list)
    conflict_pairs: list[str] = Field(default_factory=list)
    explanation_lines: list[str] = Field(default_factory=list)


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


def explain_candidate_decision_with_graph(
    bundle: EvidenceBundle,
    claims: list[EvidenceClaim],
    *,
    query: CandidateDecisionGraphQuery,
    required_modalities: list[str] | None = None,
    expected_species: str | None = None,
    expected_system: str | None = None,
    expected_sample_type: str | None = None,
    gate_profile: DecisionGateProfile | None = None,
) -> CandidateDecisionGraphExplanation:
    """Explain one candidate outcome with decision-scoped graph evidence."""
    packet = build_knowledge_review_packet(
        bundle,
        claims,
        decision_tag=query.decision_tag,
        required_modalities=required_modalities,
        expected_species=expected_species,
        expected_system=expected_system,
        expected_sample_type=expected_sample_type,
        gate_profile=gate_profile,
    )
    unresolved_questions = [
        UnresolvedQuestion(
            question_id=f"{query.decision_tag}:{gap.gap_code}",
            text=gap.message,
            related_decision_tags=[query.decision_tag],
        )
        for gap in packet.knowledge_gaps
    ]
    graph = build_evidence_graph(
        bundle,
        claims=claims,
        unresolved_questions=unresolved_questions,
    )
    decision_subgraph = extract_decision_subgraph(
        graph, decision_tag=query.decision_tag
    )
    decision_paths = trace_decision_paths(graph, decision_tag=query.decision_tag)
    supporting_evidence_ids = _collect_supporting_evidence_ids(
        claims=claims,
        disposition=query.disposition,
        decision_tag=query.decision_tag,
        bundle=bundle,
    )
    contradicting_evidence_ids = _collect_contradicting_evidence_ids(
        claims=claims,
        disposition=query.disposition,
        decision_tag=query.decision_tag,
        bundle=bundle,
    )
    conflict_pairs = _collect_decision_conflict_pairs(
        bundle=bundle,
        decision_tag=query.decision_tag,
    )
    explanation_lines = _build_candidate_decision_explanation_lines(
        query=query,
        packet=packet,
        supporting_evidence_ids=supporting_evidence_ids,
        contradicting_evidence_ids=contradicting_evidence_ids,
        unresolved_question_ids=[
            question.question_id for question in unresolved_questions
        ],
        conflict_pairs=conflict_pairs,
    )
    return CandidateDecisionGraphExplanation(
        candidate_id=query.candidate_id,
        decision_tag=query.decision_tag,
        disposition=query.disposition,
        gate_recommendation=packet.gate_recommendation,
        decision_subgraph=decision_subgraph,
        decision_paths=decision_paths,
        supporting_evidence_ids=supporting_evidence_ids,
        contradicting_evidence_ids=contradicting_evidence_ids,
        unresolved_question_ids=[
            question.question_id for question in unresolved_questions
        ],
        blocker_highlights=packet.blocker_highlights,
        conflict_pairs=conflict_pairs,
        explanation_lines=explanation_lines,
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


def _collect_supporting_evidence_ids(
    *,
    claims: list[EvidenceClaim],
    disposition: CandidateDecisionDisposition,
    decision_tag: str,
    bundle: EvidenceBundle,
) -> list[str]:
    tagged_ids = {
        record.evidence_id
        for record in bundle.records
        if decision_tag in record.decision_tags
    }
    if disposition is CandidateDecisionDisposition.REJECTED:
        evidence_ids = {
            evidence_id
            for claim in claims
            for evidence_id in claim.contradicting_evidence_ids
            if evidence_id in tagged_ids
        }
    else:
        evidence_ids = {
            evidence_id
            for claim in claims
            for evidence_id in claim.evidence_ids
            if evidence_id in tagged_ids
        }
    return sorted(evidence_ids)


def _collect_contradicting_evidence_ids(
    *,
    claims: list[EvidenceClaim],
    disposition: CandidateDecisionDisposition,
    decision_tag: str,
    bundle: EvidenceBundle,
) -> list[str]:
    tagged_ids = {
        record.evidence_id
        for record in bundle.records
        if decision_tag in record.decision_tags
    }
    if disposition is CandidateDecisionDisposition.ACCEPTED:
        evidence_ids = {
            evidence_id
            for claim in claims
            for evidence_id in claim.contradicting_evidence_ids
            if evidence_id in tagged_ids
        }
    else:
        evidence_ids = {
            evidence_id
            for claim in claims
            for evidence_id in claim.evidence_ids
            if evidence_id in tagged_ids
        }
    return sorted(evidence_ids)


def _collect_decision_conflict_pairs(
    *,
    bundle: EvidenceBundle,
    decision_tag: str,
) -> list[str]:
    trust, _ = resolve_conflicts(bundle)
    return sorted(
        f"{conflict.left_evidence_id}<>{conflict.right_evidence_id}"
        for conflict in trust.conflicts
        if _conflict_matches_decision(
            bundle, conflict=conflict, decision_tag=decision_tag
        )
    )


def _conflict_matches_decision(
    bundle: EvidenceBundle,
    *,
    conflict: EvidenceConflict,
    decision_tag: str,
) -> bool:
    records = {
        record.evidence_id: record
        for record in bundle.records
        if record.evidence_id
        in {
            conflict.left_evidence_id,
            conflict.right_evidence_id,
        }
    }
    return any(decision_tag in record.decision_tags for record in records.values())


def _build_candidate_decision_explanation_lines(
    *,
    query: CandidateDecisionGraphQuery,
    packet: KnowledgeReviewPacket,
    supporting_evidence_ids: list[str],
    contradicting_evidence_ids: list[str],
    unresolved_question_ids: list[str],
    conflict_pairs: list[str],
) -> list[str]:
    lines = [
        f"{query.candidate_id} is {query.disposition.value} for '{query.decision_tag}' under gate recommendation '{packet.gate_recommendation}'.",
        f"decision intelligence index is {packet.decision_intelligence_index:.2f} with trust {packet.quality_audit.trust_score:.2f} and triangulation {packet.quality_audit.triangulation_score:.2f}.",
    ]
    if supporting_evidence_ids:
        lines.append("supporting evidence: " + ", ".join(supporting_evidence_ids[:5]))
    if contradicting_evidence_ids:
        lines.append(
            "contradicting evidence: " + ", ".join(contradicting_evidence_ids[:5])
        )
    if unresolved_question_ids:
        lines.append("unresolved questions: " + ", ".join(unresolved_question_ids[:5]))
    if conflict_pairs:
        lines.append("conflict pairs: " + ", ".join(conflict_pairs[:5]))
    return lines


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

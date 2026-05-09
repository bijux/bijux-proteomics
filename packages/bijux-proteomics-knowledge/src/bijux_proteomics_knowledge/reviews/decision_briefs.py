# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Decision-brief builders for scientific decision readiness."""

from __future__ import annotations

from enum import StrEnum

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel
from bijux_proteomics_knowledge.memory.models.claims import (
    EvidenceClaim,
    HypothesisDossier,
    KnowledgeGap,
    build_hypothesis_dossier,
    identify_knowledge_gaps,
)
from bijux_proteomics_knowledge.memory.models.evidence import (
    EvidenceBundle,
    EvidenceRelevanceScore,
    EvidenceStateIndex,
    KnowledgeQualityAudit,
    audit_knowledge_quality,
    build_evidence_state_index,
    rank_evidence_for_decision,
)
from bijux_proteomics_knowledge.memory.reconciliation.resolution import (
    ConflictCluster,
    cluster_conflicts,
    resolve_conflicts,
)
from bijux_proteomics_knowledge.references.workflows.benchmarks import (
    KnowledgeWorkflowFamily,
)
from bijux_proteomics_knowledge.references.workflows.briefings import (
    build_workflow_reference_briefing,
)
from bijux_proteomics_knowledge.reviews.provenance import (
    CriticalClaimProvenanceLine,
    ReferenceDisagreementReport,
    build_critical_claim_provenance_lines,
    build_reference_disagreement_report,
)


class KnowledgeDecisionBrief(JsonModel):
    """Unified decision brief for one target and decision dimension."""

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
    evidence_state_index: EvidenceStateIndex = Field(
        ...,
        description="Machine-readable trust, freshness, contradiction, and caveat index.",
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
    critical_claim_provenance: tuple[CriticalClaimProvenanceLine, ...] = Field(
        default_factory=tuple,
        description="Recommendation-critical claims traced to benchmark, citation, corpus, and evidence links.",
    )
    reference_disagreement_report: ReferenceDisagreementReport | None = Field(
        default=None,
        description="Benchmark-versus-literature disagreement artifact for this workflow family.",
    )
    biological_takeaway: BiologicalTakeaway | None = Field(
        default=None,
        description="Bounded biological takeaway that keeps benchmark, literature, and unknowns separate.",
    )


class BiologicalGroundingState(StrEnum):
    """How strong the current biological takeaway is after contradiction pressure."""

    LITERATURE_GROUNDED_REVIEW_GRADE = "literature_grounded_review_grade"
    BOUNDED_BY_CONTRADICTION = "bounded_by_contradiction"
    THINLY_GROUNDED = "thinly_grounded"


class BiologicalTakeaway(JsonModel):
    """Structured biological takeaway that refuses to hide thin grounding."""

    model_config = ConfigDict(extra="forbid")

    grounding_state: BiologicalGroundingState
    data_says: tuple[str, ...] = Field(default_factory=tuple)
    benchmark_allows: tuple[str, ...] = Field(default_factory=tuple)
    literature_suggests: tuple[str, ...] = Field(default_factory=tuple)
    unknowns: tuple[str, ...] = Field(default_factory=tuple)
    bounded_takeaway: str = Field(..., min_length=1)
    downgrade_reasons: tuple[str, ...] = Field(default_factory=tuple)


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
    """Policy thresholds for decision recommendation in decision briefs."""

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


def build_knowledge_decision_brief(
    bundle: EvidenceBundle,
    claims: list[EvidenceClaim],
    *,
    decision_tag: str,
    workflow_family: KnowledgeWorkflowFamily | None = None,
    required_modalities: list[str] | None = None,
    expected_species: str | None = None,
    expected_system: str | None = None,
    expected_sample_type: str | None = None,
    gate_profile: DecisionGateProfile | None = None,
) -> KnowledgeDecisionBrief:
    """Build an integrated decision brief for decision workflows."""
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
    state_index = build_evidence_state_index(bundle, decision_tag=decision_tag)
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
    critical_claim_provenance: tuple[CriticalClaimProvenanceLine, ...] = ()
    reference_disagreement_report: ReferenceDisagreementReport | None = None
    if workflow_family is not None:
        critical_claim_provenance = build_critical_claim_provenance_lines(
            bundle,
            claims,
            decision_tag=decision_tag,
            workflow_family=workflow_family,
        )
        reference_disagreement_report = build_reference_disagreement_report(
            workflow_family
        )
    biological_takeaway = _build_biological_takeaway(
        scientific_conclusions=scientific_conclusions,
        knowledge_gaps=gaps,
        conflict_clusters=clusters,
        quality_audit=audit,
        workflow_family=workflow_family,
        reference_disagreement_report=reference_disagreement_report,
    )
    summary = _build_executive_summary(
        quality_audit=audit,
        dossier=dossier,
        knowledge_gaps=gaps,
        gate_recommendation=gate_recommendation,
        biological_takeaway=biological_takeaway,
    )
    return KnowledgeDecisionBrief(
        target_id=bundle.target_id,
        decision_tag=decision_tag,
        evidence_ranking=ranking,
        quality_audit=audit,
        evidence_state_index=state_index,
        hypothesis_dossier=dossier,
        knowledge_gaps=gaps,
        conflict_clusters=clusters,
        gate_recommendation=gate_recommendation,
        executive_summary=summary,
        blocker_highlights=blocker_highlights,
        scientific_conclusions=scientific_conclusions,
        operational_labels=operational_labels,
        decision_intelligence_index=intelligence_index,
        critical_claim_provenance=critical_claim_provenance,
        reference_disagreement_report=reference_disagreement_report,
        biological_takeaway=biological_takeaway,
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
    biological_takeaway: BiologicalTakeaway | None,
) -> list[str]:
    summary = [
        f"trust score {quality_audit.trust_score:.2f} with triangulation {quality_audit.triangulation_score:.2f}",
        f"{len(dossier.supporting_claim_ids)} supporting and {len(dossier.contradicting_claim_ids)} contradicting claims",
        f"gate recommendation: {gate_recommendation}",
    ]
    if knowledge_gaps:
        summary.append(f"{len(knowledge_gaps)} unresolved knowledge gaps remain")
    if biological_takeaway is not None and biological_takeaway.downgrade_reasons:
        summary.append(
            f"grounding limits: {biological_takeaway.downgrade_reasons[0]}"
        )
    if biological_takeaway is not None:
        summary.append(
            f"biological grounding: {biological_takeaway.grounding_state.value}"
        )
    return summary


def _build_biological_takeaway(
    *,
    scientific_conclusions: list[ScientificConclusion],
    knowledge_gaps: list[KnowledgeGap],
    conflict_clusters: list[ConflictCluster],
    quality_audit: KnowledgeQualityAudit,
    workflow_family: KnowledgeWorkflowFamily | None,
    reference_disagreement_report: ReferenceDisagreementReport | None,
) -> BiologicalTakeaway | None:
    if workflow_family is None:
        return None

    briefing = build_workflow_reference_briefing(workflow_family)
    data_says = tuple(
        conclusion.statement for conclusion in scientific_conclusions[:3]
    ) or ("current benchmark-backed packet has no claim-level biological statement",)
    benchmark_allows = briefing.benchmark_manifest.supported_repo_claims[:2]
    literature_suggests = tuple(
        group.curation_note for group in briefing.literature_groups[:2]
    )
    unknowns = tuple(
        dict.fromkeys(
            [gap.gap_code for gap in knowledge_gaps[:2]]
            + list(briefing.scope_limit_notes[:2])
        )
    )
    downgrade_reasons: list[str] = []
    contradiction_present = any(cluster.recommended_hold for cluster in conflict_clusters)
    if contradiction_present:
        downgrade_reasons.append(
            "direct evidence conflict still forces a bounded biological reading"
        )
    if reference_disagreement_report is not None and reference_disagreement_report.entries:
        downgrade_reasons.append(
            "benchmark and literature still disagree on at least one workflow-facing claim"
        )
    if quality_audit.trust_score < 0.75:
        downgrade_reasons.append(
            "trust score remains below the threshold needed for a strong biological takeaway"
        )
    if quality_audit.triangulation_score < 0.6:
        downgrade_reasons.append(
            "triangulation remains too thin for a robust biological takeaway"
        )

    if contradiction_present or (
        reference_disagreement_report is not None
        and reference_disagreement_report.entries
    ):
        grounding_state = BiologicalGroundingState.BOUNDED_BY_CONTRADICTION
        bounded_takeaway = (
            "Biological takeaway remains downgraded because benchmark, literature, "
            "or direct evidence still disagree inside the current workflow scope."
        )
    elif downgrade_reasons:
        grounding_state = BiologicalGroundingState.THINLY_GROUNDED
        bounded_takeaway = (
            "Biological takeaway remains review-grade only because the evidence base "
            "is still too thin to defend a stronger interpretation."
        )
    else:
        grounding_state = BiologicalGroundingState.LITERATURE_GROUNDED_REVIEW_GRADE
        bounded_takeaway = (
            "Biological takeaway is literature-grounded and benchmark-bounded, but still "
            "remains explicitly review-grade rather than broad decision-grade authority."
        )
    return BiologicalTakeaway(
        grounding_state=grounding_state,
        data_says=data_says,
        benchmark_allows=benchmark_allows,
        literature_suggests=literature_suggests,
        unknowns=unknowns,
        bounded_takeaway=bounded_takeaway,
        downgrade_reasons=tuple(dict.fromkeys(downgrade_reasons)),
    )


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
    """Build a cross-decision readiness summary from decision briefs."""
    scores: dict[str, float] = {}
    for decision_tag in decision_tags:
        packet = build_knowledge_decision_brief(
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

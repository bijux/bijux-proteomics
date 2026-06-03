# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Evidence review and trust-analysis surfaces."""

from __future__ import annotations

from pydantic import ConfigDict, Field

from bijux_proteomics.review.evidence_graph import (
    ProteomicsEvidenceEdge as EvidenceGraphEdge,
)
from bijux_proteomics.review.evidence_graph import (
    ProteomicsEvidenceNode as EvidenceGraphNode,
)
from bijux_proteomics.review.cards.inference_packets import (
    InferenceDisagreementReviewEntry as InferenceDisagreementReviewEntry,
)
from bijux_proteomics.review.cards.inference_packets import (
    InferenceDisagreementReviewPacket as InferenceDisagreementReviewPacket,
)
from bijux_proteomics.review.cards.inference_packets import (
    InferenceDisagreementSeverity as InferenceDisagreementSeverity,
)
from bijux_proteomics.review.cards.inference_packets import (
    build_inference_disagreement_review_packet as build_inference_disagreement_review_packet,
)
from bijux_proteomics_foundation import JsonModel


class EvidenceGraphQuery(JsonModel):
    """Filter query for evidence graph traversal."""

    model_config = ConfigDict(extra="forbid")

    candidate_id: str | None = None
    protein_id: str | None = None
    peptide_id: str | None = None
    ptm_id: str | None = None
    sample_id: str | None = None
    run_id: str | None = None
    claim_state: str | None = None
    contradiction_only: bool = False
    trust_class: str | None = None


class EvidenceGraphQueryResult(JsonModel):
    """Query result over filtered evidence graph nodes and connecting edges."""

    model_config = ConfigDict(extra="forbid")

    query: EvidenceGraphQuery
    matched_nodes: tuple[EvidenceGraphNode, ...] = Field(default_factory=tuple)
    connecting_edges: tuple[EvidenceGraphEdge, ...] = Field(default_factory=tuple)
    node_count: int = Field(..., ge=0)
    edge_count: int = Field(..., ge=0)


def query_evidence_graph(
    nodes: tuple[EvidenceGraphNode, ...],
    edges: tuple[EvidenceGraphEdge, ...],
    query: EvidenceGraphQuery,
) -> EvidenceGraphQueryResult:
    """Query evidence graph nodes by scientific entity and review constraints."""

    entity_filters = {
        "candidate": query.candidate_id,
        "protein": query.protein_id,
        "peptide": query.peptide_id,
        "ptm": query.ptm_id,
        "sample": query.sample_id,
        "run": query.run_id,
    }

    def _matches_entity(node: EvidenceGraphNode) -> bool:
        requested = entity_filters.get(node.entity_type)
        if requested is None:
            return not any(entity_filters.values())
        return bool(node.entity_ref == requested)

    matched = [node for node in nodes if _matches_entity(node)]
    if query.claim_state is not None:
        matched = [node for node in matched if node.claim_state == query.claim_state]
    if query.trust_class is not None:
        matched = [node for node in matched if node.trust_class == query.trust_class]
    if query.contradiction_only:
        matched = [node for node in matched if node.contradiction_ids]

    matched_ids = {node.node_id for node in matched}
    connecting = [
        edge
        for edge in edges
        if edge.source_node_id in matched_ids and edge.target_node_id in matched_ids
    ]

    return EvidenceGraphQueryResult(
        query=query,
        matched_nodes=tuple(sorted(matched, key=lambda node: node.node_id)),
        connecting_edges=tuple(
            sorted(
                connecting,
                key=lambda edge: (
                    edge.source_node_id,
                    edge.target_node_id,
                    edge.relation,
                ),
            )
        ),
        node_count=len(matched),
        edge_count=len(connecting),
    )


class ContradictionObservation(JsonModel):
    """One observed contradiction between two evidence records."""

    model_config = ConfigDict(extra="forbid")

    contradiction_id: str = Field(..., min_length=1)
    left_evidence_id: str = Field(..., min_length=1)
    right_evidence_id: str = Field(..., min_length=1)
    left_source: str = Field(..., min_length=1)
    right_source: str = Field(..., min_length=1)
    left_method: str = Field(..., min_length=1)
    right_method: str = Field(..., min_length=1)
    left_score: float = Field(..., ge=0.0, le=1.0)
    right_score: float = Field(..., ge=0.0, le=1.0)
    left_quant_state: str = Field(..., min_length=1)
    right_quant_state: str = Field(..., min_length=1)
    left_ptm_state: str = Field(..., min_length=1)
    right_ptm_state: str = Field(..., min_length=1)
    left_qc_state: str = Field(..., min_length=1)
    right_qc_state: str = Field(..., min_length=1)
    left_lab_outcome: str = Field(..., min_length=1)
    right_lab_outcome: str = Field(..., min_length=1)


class ContradictionTaxonomyEntry(JsonModel):
    """One taxonomy classification for an observed contradiction."""

    model_config = ConfigDict(extra="forbid")

    contradiction_id: str = Field(..., min_length=1)
    category: str = Field(..., min_length=1)
    rationale: str = Field(..., min_length=1)
    evidence_ids: tuple[str, ...] = Field(default_factory=tuple)


class ContradictionTaxonomyReport(JsonModel):
    """Deterministic contradiction taxonomy report."""

    model_config = ConfigDict(extra="forbid")

    entries: tuple[ContradictionTaxonomyEntry, ...] = Field(default_factory=tuple)
    category_counts: dict[str, int] = Field(default_factory=dict)


def classify_contradictions(
    observations: tuple[ContradictionObservation, ...],
) -> ContradictionTaxonomyReport:
    """Classify contradictions by source/method/score/quant/PTM/QC/lab disagreement."""

    entries: list[ContradictionTaxonomyEntry] = []
    counts: dict[str, int] = {}
    for observation in observations:
        if observation.left_source != observation.right_source:
            category = "source_disagreement"
            rationale = "evidence sources disagree"
        elif observation.left_method != observation.right_method:
            category = "method_disagreement"
            rationale = "methods differ across contradicting evidence"
        elif abs(observation.left_score - observation.right_score) >= 0.2:
            category = "score_disagreement"
            rationale = "confidence scores diverge materially"
        elif observation.left_quant_state != observation.right_quant_state:
            category = "quant_disagreement"
            rationale = "quantification state conflicts"
        elif observation.left_ptm_state != observation.right_ptm_state:
            category = "ptm_disagreement"
            rationale = "PTM state conflicts"
        elif observation.left_qc_state != observation.right_qc_state:
            category = "qc_disagreement"
            rationale = "QC states disagree"
        else:
            category = "lab_outcome_disagreement"
            rationale = "lab outcomes disagree while upstream context matches"

        counts[category] = counts.get(category, 0) + 1
        entries.append(
            ContradictionTaxonomyEntry(
                contradiction_id=observation.contradiction_id,
                category=category,
                rationale=rationale,
                evidence_ids=(
                    observation.left_evidence_id,
                    observation.right_evidence_id,
                ),
            )
        )

    return ContradictionTaxonomyReport(
        entries=tuple(sorted(entries, key=lambda entry: entry.contradiction_id)),
        category_counts=dict(sorted(counts.items())),
    )


class ReviewTrustScoreInput(JsonModel):
    """Structured review trust-score inputs for one candidate."""

    model_config = ConfigDict(extra="forbid")

    candidate_id: str = Field(..., min_length=1)
    evidence_inputs: dict[str, float] = Field(default_factory=dict)
    weights: dict[str, float] = Field(default_factory=dict)
    penalties: dict[str, float] = Field(default_factory=dict)
    contradiction_penalty: float = Field(0.0, ge=0.0, le=1.0)
    uncertainty: float = Field(0.0, ge=0.0, le=1.0)


class TrustScoreComponent(JsonModel):
    """One decomposed component of a trust score."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., min_length=1)
    raw_value: float = Field(..., ge=0.0, le=1.0)
    weight: float = Field(..., ge=0.0)
    contribution: float = Field(..., ge=0.0)


class TrustScoreDecomposition(JsonModel):
    """Trust-score decomposition preserving evidence and penalty contributions."""

    model_config = ConfigDict(extra="forbid")

    candidate_id: str = Field(..., min_length=1)
    components: tuple[TrustScoreComponent, ...] = Field(default_factory=tuple)
    weighted_evidence_total: float = Field(..., ge=0.0)
    penalty_total: float = Field(..., ge=0.0)
    contradiction_penalty: float = Field(..., ge=0.0, le=1.0)
    uncertainty: float = Field(..., ge=0.0, le=1.0)
    final_score: float = Field(..., ge=0.0, le=1.0)


def decompose_trust_score(payload: ReviewTrustScoreInput) -> TrustScoreDecomposition:
    """Expose weighted evidence, penalties, contradictions, and uncertainty."""

    components: list[TrustScoreComponent] = []
    weighted_total = 0.0
    for name, raw_value in sorted(payload.evidence_inputs.items()):
        weight = payload.weights.get(name, 1.0)
        contribution = raw_value * weight
        weighted_total += contribution
        components.append(
            TrustScoreComponent(
                name=name,
                raw_value=raw_value,
                weight=weight,
                contribution=contribution,
            )
        )

    penalty_total = sum(max(0.0, value) for value in payload.penalties.values())
    raw_final = weighted_total - penalty_total - payload.contradiction_penalty
    uncertainty_discount = max(0.0, 1.0 - payload.uncertainty)
    final_score = min(1.0, max(0.0, raw_final * uncertainty_discount))

    return TrustScoreDecomposition(
        candidate_id=payload.candidate_id,
        components=tuple(components),
        weighted_evidence_total=weighted_total,
        penalty_total=penalty_total,
        contradiction_penalty=payload.contradiction_penalty,
        uncertainty=payload.uncertainty,
        final_score=final_score,
    )


class RankingPerturbationScenario(JsonModel):
    """One scoring perturbation scenario for ranking sensitivity analysis."""

    model_config = ConfigDict(extra="forbid")

    scenario_id: str = Field(..., min_length=1)
    weight_multiplier: float = Field(..., ge=0.0)
    extra_penalty: float = Field(0.0, ge=0.0, le=1.0)
    candidate_score_offsets: dict[str, float] = Field(default_factory=dict)


class RankingSensitivityEntry(JsonModel):
    """Sensitivity envelope for one candidate ranking."""

    model_config = ConfigDict(extra="forbid")

    candidate_id: str = Field(..., min_length=1)
    base_rank: int = Field(..., ge=1)
    min_rank: int = Field(..., ge=1)
    max_rank: int = Field(..., ge=1)
    stable: bool


class ReviewRankingSensitivityReport(JsonModel):
    """Report over review-ranking stability under perturbed scoring assumptions."""

    model_config = ConfigDict(extra="forbid")

    entries: tuple[RankingSensitivityEntry, ...] = Field(default_factory=tuple)
    scenario_count: int = Field(..., ge=0)
    stable_candidate_count: int = Field(..., ge=0)
    unstable_candidate_count: int = Field(..., ge=0)


def build_ranking_sensitivity_report(
    decompositions: tuple[TrustScoreDecomposition, ...],
    scenarios: tuple[RankingPerturbationScenario, ...],
) -> ReviewRankingSensitivityReport:
    """Perturb scoring assumptions and classify stable vs unstable candidate ranks."""

    base_sorted = sorted(
        decompositions,
        key=lambda entry: (-entry.final_score, entry.candidate_id),
    )
    base_ranks = {
        entry.candidate_id: rank for rank, entry in enumerate(base_sorted, start=1)
    }

    rank_history: dict[str, list[int]] = {
        entry.candidate_id: [base_ranks[entry.candidate_id]] for entry in decompositions
    }

    for scenario in scenarios:
        scenario_scores = []
        for entry in decompositions:
            perturbed = (
                entry.weighted_evidence_total * scenario.weight_multiplier
                - entry.penalty_total
                - entry.contradiction_penalty
                - scenario.extra_penalty
                + scenario.candidate_score_offsets.get(entry.candidate_id, 0.0)
            )
            score = min(1.0, max(0.0, perturbed * (1.0 - entry.uncertainty)))
            scenario_scores.append((entry.candidate_id, score))
        scenario_sorted = sorted(scenario_scores, key=lambda item: (-item[1], item[0]))
        for rank, (candidate_id, _) in enumerate(scenario_sorted, start=1):
            rank_history[candidate_id].append(rank)

    entries = []
    for candidate_id, ranks in sorted(rank_history.items()):
        min_rank = min(ranks)
        max_rank = max(ranks)
        entries.append(
            RankingSensitivityEntry(
                candidate_id=candidate_id,
                base_rank=base_ranks[candidate_id],
                min_rank=min_rank,
                max_rank=max_rank,
                stable=min_rank == max_rank,
            )
        )

    return ReviewRankingSensitivityReport(
        entries=tuple(entries),
        scenario_count=len(scenarios),
        stable_candidate_count=sum(1 for entry in entries if entry.stable),
        unstable_candidate_count=sum(1 for entry in entries if not entry.stable),
    )


class CandidateLifecycleEvent(JsonModel):
    """One candidate-state transition event for lifecycle replay."""

    model_config = ConfigDict(extra="forbid")

    candidate_id: str = Field(..., min_length=1)
    from_state: str = Field(..., min_length=1)
    to_state: str = Field(..., min_length=1)
    reason: str = Field(..., min_length=1)
    evidence_pointers: tuple[str, ...] = Field(default_factory=tuple)
    sequence_index: int = Field(..., ge=0)


class CandidateLifecycleReplayEntry(JsonModel):
    """Replayed lifecycle movement summary for one candidate."""

    model_config = ConfigDict(extra="forbid")

    candidate_id: str = Field(..., min_length=1)
    state_path: tuple[str, ...] = Field(default_factory=tuple)
    transition_count: int = Field(..., ge=0)
    current_state: str = Field(..., min_length=1)
    movement_explanation: str = Field(..., min_length=1)


class CandidateLifecycleReplayReport(JsonModel):
    """Lifecycle replay report across candidates."""

    model_config = ConfigDict(extra="forbid")

    entries: tuple[CandidateLifecycleReplayEntry, ...] = Field(default_factory=tuple)
    candidate_count: int = Field(..., ge=0)


def replay_candidate_lifecycle(
    events: tuple[CandidateLifecycleEvent, ...],
) -> CandidateLifecycleReplayReport:
    """Explain movement between accepted/rejected/deferred/promoted/lab-requested states."""

    per_candidate: dict[str, list[CandidateLifecycleEvent]] = {}
    for event in sorted(
        events, key=lambda item: (item.candidate_id, item.sequence_index)
    ):
        per_candidate.setdefault(event.candidate_id, []).append(event)

    entries: list[CandidateLifecycleReplayEntry] = []
    for candidate_id, candidate_events in sorted(per_candidate.items()):
        state_path = [candidate_events[0].from_state]
        for event in candidate_events:
            state_path.append(event.to_state)
        explanation = "; ".join(
            f"{event.from_state}->{event.to_state}: {event.reason}"
            for event in candidate_events
        )
        entries.append(
            CandidateLifecycleReplayEntry(
                candidate_id=candidate_id,
                state_path=tuple(state_path),
                transition_count=len(candidate_events),
                current_state=state_path[-1],
                movement_explanation=explanation,
            )
        )

    return CandidateLifecycleReplayReport(
        entries=tuple(entries),
        candidate_count=len(entries),
    )


class EvidenceGapItem(JsonModel):
    """One missing-evidence item relevant to candidate and lab decisions."""

    model_config = ConfigDict(extra="forbid")

    gap_id: str = Field(..., min_length=1)
    candidate_id: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    decision_surfaces: tuple[str, ...] = Field(default_factory=tuple)
    decision_impact: float = Field(..., ge=0.0, le=1.0)
    uncertainty: float = Field(..., ge=0.0, le=1.0)
    collection_effort: float = Field(..., ge=0.0)


class EvidenceGapPriorityEntry(JsonModel):
    """Prioritized evidence gap with impact-oriented rationale."""

    model_config = ConfigDict(extra="forbid")

    gap_id: str = Field(..., min_length=1)
    candidate_id: str = Field(..., min_length=1)
    priority_rank: int = Field(..., ge=1)
    priority_score: float = Field(..., ge=0.0)
    rationale: str = Field(..., min_length=1)


class EvidenceGapPrioritizationReport(JsonModel):
    """Deterministic ranking of evidence gaps by decision impact."""

    model_config = ConfigDict(extra="forbid")

    entries: tuple[EvidenceGapPriorityEntry, ...] = Field(default_factory=tuple)


def prioritize_evidence_gaps(
    gaps: tuple[EvidenceGapItem, ...],
) -> EvidenceGapPrioritizationReport:
    """Rank missing evidence by expected impact on candidate/lab decisions."""

    scored: list[tuple[EvidenceGapItem, float]] = []
    for gap in gaps:
        surface_weight = 1.0 + (0.1 * len(set(gap.decision_surfaces)))
        uncertainty_weight = 1.0 + (0.5 * gap.uncertainty)
        effort_divisor = 1.0 + gap.collection_effort
        score = (
            gap.decision_impact * surface_weight * uncertainty_weight
        ) / effort_divisor
        scored.append((gap, score))

    scored.sort(key=lambda item: (-item[1], item[0].gap_id))

    entries = []
    for rank, (gap, score) in enumerate(scored, start=1):
        entries.append(
            EvidenceGapPriorityEntry(
                gap_id=gap.gap_id,
                candidate_id=gap.candidate_id,
                priority_rank=rank,
                priority_score=score,
                rationale=(
                    "prioritized by decision impact, surface coverage, uncertainty, and effort"
                ),
            )
        )

    return EvidenceGapPrioritizationReport(entries=tuple(entries))


class ReviewPacketEvidenceEntry(JsonModel):
    """Evidence record bundled into a decision brief."""

    model_config = ConfigDict(extra="forbid")

    evidence_id: str = Field(..., min_length=1)
    claim: str = Field(..., min_length=1)
    source: str = Field(..., min_length=1)
    trust_score: float = Field(..., ge=0.0, le=1.0)


class ReviewPacketContradictionEntry(JsonModel):
    """Contradiction row included in the decision brief."""

    model_config = ConfigDict(extra="forbid")

    contradiction_id: str = Field(..., min_length=1)
    category: str = Field(..., min_length=1)
    evidence_ids: tuple[str, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


class ReviewPacketQcCaveatEntry(JsonModel):
    """QC caveat associated with review interpretation."""

    model_config = ConfigDict(extra="forbid")

    caveat_id: str = Field(..., min_length=1)
    severity: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)
    evidence_ids: tuple[str, ...] = Field(default_factory=tuple)


class ReviewPacketAssayPlanEntry(JsonModel):
    """Assay planning entry included for lab follow-up."""

    model_config = ConfigDict(extra="forbid")

    plan_id: str = Field(..., min_length=1)
    method: str = Field(..., min_length=1)
    target_ids: tuple[str, ...] = Field(default_factory=tuple)
    sample_ids: tuple[str, ...] = Field(default_factory=tuple)


class ReviewPacketRiskEntry(JsonModel):
    """Risk and mitigation row in decision brief."""

    model_config = ConfigDict(extra="forbid")

    risk_id: str = Field(..., min_length=1)
    severity: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)
    mitigation: str = Field(..., min_length=1)


class ReviewPacketDecisionEntry(JsonModel):
    """Decision row in decision brief."""

    model_config = ConfigDict(extra="forbid")

    decision_id: str = Field(..., min_length=1)
    candidate_id: str = Field(..., min_length=1)
    decision_state: str = Field(..., min_length=1)
    rationale: str = Field(..., min_length=1)
    evidence_ids: tuple[str, ...] = Field(default_factory=tuple)


class ReviewPacketSchema(JsonModel):
    """Review packet schema bundling evidence, caveats, plans, risks, and decisions."""

    model_config = ConfigDict(extra="forbid")

    packet_id: str = Field(..., min_length=1)
    run_id: str = Field(..., min_length=1)
    evidence: tuple[ReviewPacketEvidenceEntry, ...] = Field(default_factory=tuple)
    trust_scores: dict[str, float] = Field(default_factory=dict)
    contradictions: tuple[ReviewPacketContradictionEntry, ...] = Field(
        default_factory=tuple
    )
    qc_caveats: tuple[ReviewPacketQcCaveatEntry, ...] = Field(default_factory=tuple)
    assay_plans: tuple[ReviewPacketAssayPlanEntry, ...] = Field(default_factory=tuple)
    risks: tuple[ReviewPacketRiskEntry, ...] = Field(default_factory=tuple)
    decisions: tuple[ReviewPacketDecisionEntry, ...] = Field(default_factory=tuple)


def build_review_packet_schema(
    *,
    packet_id: str,
    run_id: str,
    evidence: tuple[ReviewPacketEvidenceEntry, ...],
    trust_scores: dict[str, float],
    contradictions: tuple[ReviewPacketContradictionEntry, ...],
    qc_caveats: tuple[ReviewPacketQcCaveatEntry, ...],
    assay_plans: tuple[ReviewPacketAssayPlanEntry, ...],
    risks: tuple[ReviewPacketRiskEntry, ...],
    decisions: tuple[ReviewPacketDecisionEntry, ...],
) -> ReviewPacketSchema:
    """Build one deterministic decision brief bundle from structured facts."""

    return ReviewPacketSchema(
        packet_id=packet_id,
        run_id=run_id,
        evidence=tuple(sorted(evidence, key=lambda entry: entry.evidence_id)),
        trust_scores=dict(sorted(trust_scores.items())),
        contradictions=tuple(
            sorted(contradictions, key=lambda entry: entry.contradiction_id)
        ),
        qc_caveats=tuple(sorted(qc_caveats, key=lambda entry: entry.caveat_id)),
        assay_plans=tuple(sorted(assay_plans, key=lambda entry: entry.plan_id)),
        risks=tuple(sorted(risks, key=lambda entry: entry.risk_id)),
        decisions=tuple(sorted(decisions, key=lambda entry: entry.decision_id)),
    )


class ReviewerChallengeEntry(JsonModel):
    """One reviewer challenge against trust, ranking, or claim interpretation."""

    model_config = ConfigDict(extra="forbid")

    challenge_id: str = Field(..., min_length=1)
    reviewer_id: str = Field(..., min_length=1)
    candidate_id: str = Field(..., min_length=1)
    challenge_surface: str = Field(..., min_length=1)
    reason: str = Field(..., min_length=1)
    evidence_ids: tuple[str, ...] = Field(default_factory=tuple)


class ReviewerChallengeResolutionEntry(JsonModel):
    """Resolution outcome for one reviewer challenge."""

    model_config = ConfigDict(extra="forbid")

    challenge_id: str = Field(..., min_length=1)
    status: str = Field(..., min_length=1)
    rationale: str = Field(..., min_length=1)
    impacted_decision_ids: tuple[str, ...] = Field(default_factory=tuple)


class ReviewerChallengeWorkflowReport(JsonModel):
    """Challenge workflow summary preserving challengeability with evidence pointers."""

    model_config = ConfigDict(extra="forbid")

    resolutions: tuple[ReviewerChallengeResolutionEntry, ...] = Field(
        default_factory=tuple
    )
    open_count: int = Field(..., ge=0)
    resolved_count: int = Field(..., ge=0)


def run_reviewer_challenge_workflow(
    packet: ReviewPacketSchema,
    challenges: tuple[ReviewerChallengeEntry, ...],
) -> ReviewerChallengeWorkflowReport:
    """Resolve reviewer challenges using packet evidence and decision references."""

    packet_evidence_ids = {entry.evidence_id for entry in packet.evidence}
    decisions_by_candidate: dict[str, list[str]] = {}
    for decision in packet.decisions:
        decisions_by_candidate.setdefault(decision.candidate_id, []).append(
            decision.decision_id
        )

    resolutions: list[ReviewerChallengeResolutionEntry] = []
    for challenge in sorted(challenges, key=lambda entry: entry.challenge_id):
        missing_evidence = [
            evidence_id
            for evidence_id in challenge.evidence_ids
            if evidence_id not in packet_evidence_ids
        ]
        if missing_evidence:
            resolutions.append(
                ReviewerChallengeResolutionEntry(
                    challenge_id=challenge.challenge_id,
                    status="needs_follow_up",
                    rationale="challenge references evidence ids not present in packet",
                    impacted_decision_ids=tuple(
                        decisions_by_candidate.get(challenge.candidate_id, [])
                    ),
                )
            )
            continue

        resolutions.append(
            ReviewerChallengeResolutionEntry(
                challenge_id=challenge.challenge_id,
                status="resolved",
                rationale="challenge evidence was found and linked for board review",
                impacted_decision_ids=tuple(
                    decisions_by_candidate.get(challenge.candidate_id, [])
                ),
            )
        )

    return ReviewerChallengeWorkflowReport(
        resolutions=tuple(resolutions),
        open_count=sum(1 for entry in resolutions if entry.status != "resolved"),
        resolved_count=sum(1 for entry in resolutions if entry.status == "resolved"),
    )


class ReviewNarrativeLine(JsonModel):
    """One narrative sentence grounded in structured evidence facts."""

    model_config = ConfigDict(extra="forbid")

    section: str = Field(..., min_length=1)
    text: str = Field(..., min_length=1)
    evidence_ids: tuple[str, ...] = Field(default_factory=tuple)


class ReviewNarrativeReport(JsonModel):
    """Generated narrative constrained to evidence graph facts."""

    model_config = ConfigDict(extra="forbid")

    lines: tuple[ReviewNarrativeLine, ...] = Field(default_factory=tuple)
    claim_count: int = Field(..., ge=0)


def generate_review_narrative_from_structured_facts(
    packet: ReviewPacketSchema,
) -> ReviewNarrativeReport:
    """Generate narrative summaries from packet facts with claim-to-evidence links."""

    evidence_index = {entry.evidence_id: entry for entry in packet.evidence}
    lines: list[ReviewNarrativeLine] = []

    for decision in packet.decisions:
        linked_evidence = tuple(
            evidence_id
            for evidence_id in decision.evidence_ids
            if evidence_id in evidence_index
        )
        claims = []
        for evidence_id in linked_evidence:
            evidence = evidence_index[evidence_id]
            claims.append(f"{evidence.claim} ({evidence.source})")

        if claims:
            text = (
                f"candidate {decision.candidate_id} is {decision.decision_state} because "
                + "; ".join(claims)
            )
        else:
            text = (
                f"candidate {decision.candidate_id} is {decision.decision_state} with "
                "no linked evidence in this packet"
            )

        lines.append(
            ReviewNarrativeLine(
                section="decision",
                text=text,
                evidence_ids=linked_evidence,
            )
        )

    return ReviewNarrativeReport(lines=tuple(lines), claim_count=len(lines))


class ReviewPacketDiffEntry(JsonModel):
    """One review-packet difference entry across runs or evidence updates."""

    model_config = ConfigDict(extra="forbid")

    surface: str = Field(..., min_length=1)
    key: str = Field(..., min_length=1)
    change_type: str = Field(..., min_length=1)
    before: str | None = None
    after: str | None = None


class ReviewPacketDiffReport(JsonModel):
    """Diff report between two decision briefs."""

    model_config = ConfigDict(extra="forbid")

    entries: tuple[ReviewPacketDiffEntry, ...] = Field(default_factory=tuple)
    added_count: int = Field(..., ge=0)
    removed_count: int = Field(..., ge=0)
    changed_count: int = Field(..., ge=0)


def diff_review_packets(
    before: ReviewPacketSchema,
    after: ReviewPacketSchema,
) -> ReviewPacketDiffReport:
    """Compare decision briefs across runs, releases, or evidence updates."""

    entries: list[ReviewPacketDiffEntry] = []

    before_evidence = {entry.evidence_id: entry.claim for entry in before.evidence}
    after_evidence = {entry.evidence_id: entry.claim for entry in after.evidence}
    for evidence_id in sorted(before_evidence.keys() | after_evidence.keys()):
        if evidence_id not in before_evidence:
            entries.append(
                ReviewPacketDiffEntry(
                    surface="evidence",
                    key=evidence_id,
                    change_type="added",
                    after=after_evidence[evidence_id],
                )
            )
        elif evidence_id not in after_evidence:
            entries.append(
                ReviewPacketDiffEntry(
                    surface="evidence",
                    key=evidence_id,
                    change_type="removed",
                    before=before_evidence[evidence_id],
                )
            )
        elif before_evidence[evidence_id] != after_evidence[evidence_id]:
            entries.append(
                ReviewPacketDiffEntry(
                    surface="evidence",
                    key=evidence_id,
                    change_type="changed",
                    before=before_evidence[evidence_id],
                    after=after_evidence[evidence_id],
                )
            )

    before_decisions = {
        entry.decision_id: entry.decision_state for entry in before.decisions
    }
    after_decisions = {
        entry.decision_id: entry.decision_state for entry in after.decisions
    }
    for decision_id in sorted(before_decisions.keys() & after_decisions.keys()):
        if before_decisions[decision_id] != after_decisions[decision_id]:
            entries.append(
                ReviewPacketDiffEntry(
                    surface="decision",
                    key=decision_id,
                    change_type="changed",
                    before=before_decisions[decision_id],
                    after=after_decisions[decision_id],
                )
            )

    return ReviewPacketDiffReport(
        entries=tuple(entries),
        added_count=sum(1 for entry in entries if entry.change_type == "added"),
        removed_count=sum(1 for entry in entries if entry.change_type == "removed"),
        changed_count=sum(1 for entry in entries if entry.change_type == "changed"),
    )

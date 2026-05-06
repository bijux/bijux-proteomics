# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Decision-scoped graph explanations built from knowledge review packets."""

from __future__ import annotations

from enum import StrEnum

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel
from bijux_proteomics_knowledge.memory.models.claims import EvidenceClaim
from bijux_proteomics_knowledge.memory.models.evidence import (
    EvidenceBundle,
    EvidenceConflict,
)
from bijux_proteomics_knowledge.memory.integrity.graph import (
    DecisionTracePath,
    EvidenceGraph,
    UnresolvedQuestion,
    build_evidence_graph,
    extract_decision_subgraph,
    trace_decision_paths,
)
from bijux_proteomics_knowledge.memory.reconciliation.resolution import (
    resolve_conflicts,
)
from bijux_proteomics_knowledge.reviews.packets import (
    DecisionGateProfile,
    KnowledgeReviewPacket,
    build_knowledge_review_packet,
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

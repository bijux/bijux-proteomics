# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Knowledge review capability surfaces for iteration 09."""

from __future__ import annotations

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel


class EvidenceGraphNode(JsonModel):
    """One node in the evidence graph query surface."""

    model_config = ConfigDict(extra="forbid")

    node_id: str = Field(..., min_length=1)
    entity_type: str = Field(..., min_length=1)
    entity_ref: str = Field(..., min_length=1)
    claim_state: str = Field(..., min_length=1)
    trust_class: str = Field(..., min_length=1)
    contradiction_ids: tuple[str, ...] = Field(default_factory=tuple)


class EvidenceGraphEdge(JsonModel):
    """One directed edge in the evidence graph."""

    model_config = ConfigDict(extra="forbid")

    source_node_id: str = Field(..., min_length=1)
    target_node_id: str = Field(..., min_length=1)
    relation: str = Field(..., min_length=1)


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
        return node.entity_ref == requested

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
                key=lambda edge: (edge.source_node_id, edge.target_node_id, edge.relation),
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


class TrustScoreInput(JsonModel):
    """Structured trust-score inputs for one candidate."""

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


def decompose_trust_score(payload: TrustScoreInput) -> TrustScoreDecomposition:
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

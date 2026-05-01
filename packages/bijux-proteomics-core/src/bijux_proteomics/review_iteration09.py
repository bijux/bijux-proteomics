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

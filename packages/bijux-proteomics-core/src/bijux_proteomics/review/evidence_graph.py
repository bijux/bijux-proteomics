# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Canonical proteomics evidence graph owner for review and trust surfaces."""

from __future__ import annotations

from enum import StrEnum

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel


class ProteomicsEvidenceNodeKind(StrEnum):
    """Stable node kinds admitted into the canonical proteomics evidence graph."""

    CANDIDATE = "candidate"
    SAMPLE = "sample"
    RUN = "run"
    SPECTRUM = "spectrum"
    PRECURSOR = "precursor"
    PEPTIDE = "peptide"
    MODIFIED_PEPTIDE = "modified_peptide"
    PSM = "psm"
    PROTEIN = "protein"
    PROTEIN_GROUP = "protein_group"
    PTM_SITE = "ptm_site"
    TRANSITION = "transition"
    QUANT_VALUE = "quant_value"
    PATHWAY = "pathway"
    QC_DECISION = "qc_decision"


class ProteomicsEvidenceContextRef(JsonModel):
    """One stable context reference attached to a graph node."""

    model_config = ConfigDict(extra="forbid")

    entity_type: ProteomicsEvidenceNodeKind
    entity_ref: str = Field(..., min_length=1)


class ProteomicsEvidenceNode(JsonModel):
    """One canonical node in the proteomics evidence graph."""

    model_config = ConfigDict(extra="forbid")

    node_id: str = Field(..., min_length=1)
    entity_type: ProteomicsEvidenceNodeKind
    entity_ref: str = Field(..., min_length=1)
    label: str = Field(..., min_length=1)
    claim_state: str = Field(default="observed", min_length=1)
    trust_class: str = Field(default="unreviewed", min_length=1)
    contradiction_ids: tuple[str, ...] = Field(default_factory=tuple)
    context_refs: tuple[ProteomicsEvidenceContextRef, ...] = Field(default_factory=tuple)


class ProteomicsEvidenceEdge(JsonModel):
    """One directed relation between canonical evidence-graph nodes."""

    model_config = ConfigDict(extra="forbid")

    source_node_id: str = Field(..., min_length=1)
    target_node_id: str = Field(..., min_length=1)
    relation: str = Field(..., min_length=1)
    support_count: int = Field(default=1, ge=1)


class ProteomicsEvidenceGraphSummary(JsonModel):
    """Deterministic summary of one proteomics evidence graph."""

    model_config = ConfigDict(extra="forbid")

    node_count: int = Field(..., ge=0)
    edge_count: int = Field(..., ge=0)
    contradiction_node_count: int = Field(..., ge=0)
    node_kind_counts: dict[str, int] = Field(default_factory=dict)


class ProteomicsEvidenceGraph(JsonModel):
    """Canonical proteomics evidence graph over review-grade scientific entities."""

    model_config = ConfigDict(extra="forbid")

    nodes: tuple[ProteomicsEvidenceNode, ...] = Field(default_factory=tuple)
    edges: tuple[ProteomicsEvidenceEdge, ...] = Field(default_factory=tuple)
    summary: ProteomicsEvidenceGraphSummary


def build_proteomics_evidence_graph(
    nodes: tuple[ProteomicsEvidenceNode, ...],
    edges: tuple[ProteomicsEvidenceEdge, ...],
) -> ProteomicsEvidenceGraph:
    """Build one canonical proteomics evidence graph with endpoint validation."""

    node_ids = {node.node_id for node in nodes}
    for edge in edges:
        if edge.source_node_id not in node_ids:
            raise ValueError(
                f"edge source node is missing from graph: {edge.source_node_id}"
            )
        if edge.target_node_id not in node_ids:
            raise ValueError(
                f"edge target node is missing from graph: {edge.target_node_id}"
            )

    sorted_nodes = tuple(sorted(nodes, key=lambda node: node.node_id))
    sorted_edges = tuple(
        sorted(
            edges,
            key=lambda edge: (
                edge.source_node_id,
                edge.target_node_id,
                edge.relation,
            ),
        )
    )
    kind_counts: dict[str, int] = {}
    for node in sorted_nodes:
        kind_counts[node.entity_type.value] = kind_counts.get(node.entity_type.value, 0) + 1

    summary = ProteomicsEvidenceGraphSummary(
        node_count=len(sorted_nodes),
        edge_count=len(sorted_edges),
        contradiction_node_count=sum(bool(node.contradiction_ids) for node in sorted_nodes),
        node_kind_counts=dict(sorted(kind_counts.items())),
    )
    return ProteomicsEvidenceGraph(
        nodes=sorted_nodes,
        edges=sorted_edges,
        summary=summary,
    )


class ProteomicsEvidenceGraphBuilder:
    """Builder that canonicalizes nodes and aggregates repeated evidence edges."""

    def __init__(self) -> None:
        self._nodes_by_id: dict[str, ProteomicsEvidenceNode] = {}
        self._edge_support_by_key: dict[tuple[str, str, str], int] = {}

    def add_node(
        self,
        node: ProteomicsEvidenceNode,
    ) -> ProteomicsEvidenceNode:
        """Add one canonical node or reject conflicting duplicate definitions."""

        existing = self._nodes_by_id.get(node.node_id)
        if existing is None:
            self._nodes_by_id[node.node_id] = node
            return node
        if existing != node:
            raise ValueError(f"conflicting node definition for {node.node_id}")
        return existing

    def ensure_node(
        self,
        entity_type: ProteomicsEvidenceNodeKind,
        entity_ref: str,
        *,
        label: str | None = None,
        claim_state: str = "observed",
        trust_class: str = "unreviewed",
        contradiction_ids: tuple[str, ...] = (),
        context_refs: tuple[ProteomicsEvidenceContextRef, ...] = (),
    ) -> ProteomicsEvidenceNode:
        """Add or return one canonical node with a stable graph-local identifier."""

        return self.add_node(
            ProteomicsEvidenceNode(
                node_id=f"{entity_type.value}:{entity_ref}",
                entity_type=entity_type,
                entity_ref=entity_ref,
                label=label or entity_ref,
                claim_state=claim_state,
                trust_class=trust_class,
                contradiction_ids=contradiction_ids,
                context_refs=context_refs,
            )
        )

    def add_edge(
        self,
        source_node_id: str,
        target_node_id: str,
        relation: str,
        *,
        support_count: int = 1,
    ) -> None:
        """Add or aggregate one directed relation between existing nodes."""

        if source_node_id not in self._nodes_by_id:
            raise ValueError(f"source node is missing from builder: {source_node_id}")
        if target_node_id not in self._nodes_by_id:
            raise ValueError(f"target node is missing from builder: {target_node_id}")
        key = (source_node_id, target_node_id, relation)
        self._edge_support_by_key[key] = self._edge_support_by_key.get(key, 0) + support_count

    def add_candidate(self, candidate_id: str, **kwargs: object) -> ProteomicsEvidenceNode:
        return self.ensure_node(ProteomicsEvidenceNodeKind.CANDIDATE, candidate_id, **kwargs)

    def add_sample(self, sample_id: str, **kwargs: object) -> ProteomicsEvidenceNode:
        return self.ensure_node(ProteomicsEvidenceNodeKind.SAMPLE, sample_id, **kwargs)

    def add_run(self, run_id: str, **kwargs: object) -> ProteomicsEvidenceNode:
        return self.ensure_node(ProteomicsEvidenceNodeKind.RUN, run_id, **kwargs)

    def add_spectrum(self, spectrum_id: str, **kwargs: object) -> ProteomicsEvidenceNode:
        return self.ensure_node(ProteomicsEvidenceNodeKind.SPECTRUM, spectrum_id, **kwargs)

    def add_precursor(self, precursor_id: str, **kwargs: object) -> ProteomicsEvidenceNode:
        return self.ensure_node(ProteomicsEvidenceNodeKind.PRECURSOR, precursor_id, **kwargs)

    def add_peptide(self, peptide_id: str, **kwargs: object) -> ProteomicsEvidenceNode:
        return self.ensure_node(ProteomicsEvidenceNodeKind.PEPTIDE, peptide_id, **kwargs)

    def add_modified_peptide(
        self, modified_peptide_id: str, **kwargs: object
    ) -> ProteomicsEvidenceNode:
        return self.ensure_node(
            ProteomicsEvidenceNodeKind.MODIFIED_PEPTIDE,
            modified_peptide_id,
            **kwargs,
        )

    def add_psm(self, psm_id: str, **kwargs: object) -> ProteomicsEvidenceNode:
        return self.ensure_node(ProteomicsEvidenceNodeKind.PSM, psm_id, **kwargs)

    def add_protein(self, protein_id: str, **kwargs: object) -> ProteomicsEvidenceNode:
        return self.ensure_node(ProteomicsEvidenceNodeKind.PROTEIN, protein_id, **kwargs)

    def add_protein_group(
        self, protein_group_id: str, **kwargs: object
    ) -> ProteomicsEvidenceNode:
        return self.ensure_node(
            ProteomicsEvidenceNodeKind.PROTEIN_GROUP,
            protein_group_id,
            **kwargs,
        )

    def add_ptm_site(self, ptm_site_id: str, **kwargs: object) -> ProteomicsEvidenceNode:
        return self.ensure_node(ProteomicsEvidenceNodeKind.PTM_SITE, ptm_site_id, **kwargs)

    def add_transition(
        self, transition_id: str, **kwargs: object
    ) -> ProteomicsEvidenceNode:
        return self.ensure_node(ProteomicsEvidenceNodeKind.TRANSITION, transition_id, **kwargs)

    def add_quant_value(
        self, quant_value_id: str, **kwargs: object
    ) -> ProteomicsEvidenceNode:
        return self.ensure_node(
            ProteomicsEvidenceNodeKind.QUANT_VALUE,
            quant_value_id,
            **kwargs,
        )

    def add_pathway(self, pathway_id: str, **kwargs: object) -> ProteomicsEvidenceNode:
        return self.ensure_node(ProteomicsEvidenceNodeKind.PATHWAY, pathway_id, **kwargs)

    def add_qc_decision(
        self, qc_decision_id: str, **kwargs: object
    ) -> ProteomicsEvidenceNode:
        return self.ensure_node(
            ProteomicsEvidenceNodeKind.QC_DECISION,
            qc_decision_id,
            **kwargs,
        )

    def build(self) -> ProteomicsEvidenceGraph:
        """Build one validated canonical graph from the accumulated nodes and edges."""

        edges = tuple(
            ProteomicsEvidenceEdge(
                source_node_id=source_node_id,
                target_node_id=target_node_id,
                relation=relation,
                support_count=support_count,
            )
            for (source_node_id, target_node_id, relation), support_count in sorted(
                self._edge_support_by_key.items()
            )
        )
        return build_proteomics_evidence_graph(
            tuple(self._nodes_by_id.values()),
            edges,
        )

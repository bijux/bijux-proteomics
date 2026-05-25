# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""External-inspection exports over the canonical proteomics evidence graph."""

from __future__ import annotations

import csv
from io import StringIO

from pydantic import ConfigDict, Field

from bijux_proteomics.review.evidence_graph import ProteomicsEvidenceGraph
from bijux_proteomics_foundation import JsonModel


class EvidenceGraphExportContextRef(JsonModel):
    """Compact context reference exported for one graph node."""

    model_config = ConfigDict(extra="forbid")

    kind: str = Field(..., min_length=1)
    ref: str = Field(..., min_length=1)


class EvidenceGraphExportNode(JsonModel):
    """One compact exported node for external graph inspection."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., min_length=1)
    kind: str = Field(..., min_length=1)
    ref: str = Field(..., min_length=1)
    label: str = Field(..., min_length=1)
    state: str = Field(..., min_length=1)
    trust: str = Field(..., min_length=1)
    contradictions: tuple[str, ...] = Field(default_factory=tuple)
    context: tuple[EvidenceGraphExportContextRef, ...] = Field(default_factory=tuple)


class EvidenceGraphExportEdge(JsonModel):
    """One compact exported edge for external graph inspection."""

    model_config = ConfigDict(extra="forbid")

    source: str = Field(..., min_length=1)
    target: str = Field(..., min_length=1)
    relation: str = Field(..., min_length=1)
    row_ref: str = Field(..., min_length=1)
    confidence: float = Field(..., ge=0.0, le=1.0)
    evidence_type: str = Field(..., min_length=1)
    reason: str = Field(..., min_length=1)
    support_count: int = Field(..., ge=1)


class EvidenceGraphExportBundle(JsonModel):
    """Deterministic node and edge export bundle for one evidence graph."""

    model_config = ConfigDict(extra="forbid")

    nodes: tuple[EvidenceGraphExportNode, ...] = Field(default_factory=tuple)
    edges: tuple[EvidenceGraphExportEdge, ...] = Field(default_factory=tuple)
    node_count: int = Field(..., ge=0)
    edge_count: int = Field(..., ge=0)
    contradiction_node_count: int = Field(..., ge=0)


def export_proteomics_evidence_graph(
    graph: ProteomicsEvidenceGraph,
) -> EvidenceGraphExportBundle:
    """Project the canonical graph into deterministic external-inspection records."""

    nodes = tuple(
        EvidenceGraphExportNode(
            id=node.node_id,
            kind=node.entity_type.value,
            ref=node.entity_ref,
            label=node.label,
            state=node.claim_state,
            trust=node.trust_class,
            contradictions=node.contradiction_ids,
            context=tuple(
                EvidenceGraphExportContextRef(
                    kind=context.entity_type.value,
                    ref=context.entity_ref,
                )
                for context in node.context_refs
            ),
        )
        for node in graph.nodes
    )
    edges = tuple(
        EvidenceGraphExportEdge(
            source=edge.source_node_id,
            target=edge.target_node_id,
            relation=edge.relation.value,
            row_ref=edge.source_row_ref,
            confidence=edge.confidence,
            evidence_type=edge.evidence_type.value,
            reason=edge.reason,
            support_count=edge.support_count,
        )
        for edge in graph.edges
    )
    return EvidenceGraphExportBundle(
        nodes=nodes,
        edges=edges,
        node_count=len(nodes),
        edge_count=len(edges),
        contradiction_node_count=sum(1 for node in nodes if node.contradictions),
    )


def render_proteomics_evidence_graph_nodes_tsv(bundle: EvidenceGraphExportBundle) -> str:
    """Render exported graph nodes as Cytoscape-friendly TSV."""

    return _dict_rows_to_tsv(
        [
            {
                "node_id": node.id,
                "entity_type": node.kind,
                "entity_ref": node.ref,
                "label": node.label,
                "claim_state": node.state,
                "trust_class": node.trust,
                "contradiction_ids": "|".join(node.contradictions),
                "context_refs": "|".join(
                    f"{context.kind}:{context.ref}" for context in node.context
                ),
            }
            for node in bundle.nodes
        ]
    )


def render_proteomics_evidence_graph_edges_tsv(bundle: EvidenceGraphExportBundle) -> str:
    """Render exported graph edges as Cytoscape-friendly TSV."""

    return _dict_rows_to_tsv(
        [
            {
                "source_node_id": edge.source,
                "target_node_id": edge.target,
                "relation": edge.relation,
                "source_row_ref": edge.row_ref,
                "confidence": edge.confidence,
                "evidence_type": edge.evidence_type,
                "reason": edge.reason,
                "support_count": edge.support_count,
            }
            for edge in bundle.edges
        ]
    )


def render_proteomics_evidence_graph_compact_json(bundle: EvidenceGraphExportBundle) -> str:
    """Render one compact deterministic JSON export for external graph tools."""

    return bundle.to_stable_json()


def _dict_rows_to_tsv(rows: list[dict[str, object]]) -> str:
    if not rows:
        return ""
    buffer = StringIO()
    writer = csv.DictWriter(buffer, fieldnames=list(rows[0].keys()), delimiter="\t")
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue()

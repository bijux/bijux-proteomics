# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.review import (
    EvidenceGraphEdge,
    EvidenceGraphNode,
    EvidenceGraphQuery,
    ProteomicsEvidenceEdgeKind,
    ProteomicsEvidenceNodeKind,
    ProteomicsEvidenceType,
    query_evidence_graph,
)


def test_query_evidence_graph_filters_nodes_and_connecting_edges() -> None:
    nodes = (
        EvidenceGraphNode(
            node_id="n1",
            entity_type=ProteomicsEvidenceNodeKind.CANDIDATE,
            entity_ref="cand-1",
            label="candidate cand-1",
            claim_state="accepted",
            trust_class="high",
            contradiction_ids=("cx-1",),
        ),
        EvidenceGraphNode(
            node_id="n2",
            entity_type=ProteomicsEvidenceNodeKind.PROTEIN,
            entity_ref="P12345",
            label="protein P12345",
            claim_state="accepted",
            trust_class="high",
            contradiction_ids=("cx-1",),
        ),
        EvidenceGraphNode(
            node_id="n3",
            entity_type=ProteomicsEvidenceNodeKind.CANDIDATE,
            entity_ref="cand-2",
            label="candidate cand-2",
            claim_state="deferred",
            trust_class="medium",
        ),
    )
    edges = (
        EvidenceGraphEdge(
            source_node_id="n1",
            target_node_id="n2",
            relation=ProteomicsEvidenceEdgeKind.CANDIDATE_SUPPORTS_PROTEIN,
            source_row_ref="review.tsv:2",
            confidence=0.9,
            evidence_type=ProteomicsEvidenceType.INFERENCE,
            reason="candidate cand-1 supports protein P12345",
        ),
        EvidenceGraphEdge(
            source_node_id="n1",
            target_node_id="n3",
            relation=ProteomicsEvidenceEdgeKind.PSM_SUPPORTS_PEPTIDE,
            source_row_ref="psm.tsv:8",
            confidence=0.7,
            evidence_type=ProteomicsEvidenceType.SPECTRUM_ASSIGNMENT,
            reason="candidate-linked psm also supports peptide cand-2",
        ),
    )

    result = query_evidence_graph(
        nodes,
        edges,
        EvidenceGraphQuery(
            candidate_id="cand-1",
            claim_state="accepted",
            contradiction_only=True,
            trust_class="high",
        ),
    )

    assert result.node_count == 1
    assert result.edge_count == 0
    assert result.matched_nodes[0].node_id == "n1"

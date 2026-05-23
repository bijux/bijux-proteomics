# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.review import (
    EvidenceGraphEdge,
    EvidenceGraphNode,
    EvidenceGraphQuery,
    ProteomicsEvidenceNodeKind,
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
            source_node_id="n1", target_node_id="n2", relation="supports"
        ),
        EvidenceGraphEdge(
            source_node_id="n1", target_node_id="n3", relation="competes"
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

# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import pytest

from bijux_proteomics.review import (
    export_proteomics_evidence_graph,
    render_proteomics_evidence_graph_edges_tsv,
    render_proteomics_evidence_graph_nodes_tsv,
)
from bijux_proteomics.review.evidence_graph.lazy_evidence_graph import (
    load_lazy_proteomics_evidence_graph,
)

from .test_evidence_graph_query_engine_surface import build_review_query_fixture_graph


def test_load_lazy_proteomics_evidence_graph_preserves_summary_and_node_lookup(
    tmp_path,
) -> None:
    graph = build_review_query_fixture_graph()
    bundle = export_proteomics_evidence_graph(graph)
    nodes_path = tmp_path / "evidence_graph_nodes.tsv"
    edges_path = tmp_path / "evidence_graph_edges.tsv"
    nodes_path.write_text(
        render_proteomics_evidence_graph_nodes_tsv(bundle),
        encoding="utf-8",
    )
    edges_path.write_text(
        render_proteomics_evidence_graph_edges_tsv(bundle),
        encoding="utf-8",
    )

    lazy_graph = load_lazy_proteomics_evidence_graph(nodes_path, edges_path)

    assert lazy_graph.summary == graph.summary
    assert lazy_graph.require_node_by_id("protein:P11111").entity_ref == "P11111"
    assert lazy_graph.require_node_by_id("psm:psm:1002").claim_state == "rejected"


def test_load_lazy_proteomics_evidence_graph_rejects_missing_edge_endpoints(
    tmp_path,
) -> None:
    graph = build_review_query_fixture_graph()
    bundle = export_proteomics_evidence_graph(graph)
    nodes_path = tmp_path / "evidence_graph_nodes.tsv"
    edges_path = tmp_path / "evidence_graph_edges.tsv"
    node_lines = render_proteomics_evidence_graph_nodes_tsv(bundle).splitlines()
    nodes_path.write_text(
        "\n".join(
            line for line in node_lines if not line.startswith("protein:P11111\t")
        )
        + "\n",
        encoding="utf-8",
    )
    edges_path.write_text(
        render_proteomics_evidence_graph_edges_tsv(bundle),
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="edge target node is missing from lazy graph artifacts: protein:P11111",
    ):
        load_lazy_proteomics_evidence_graph(nodes_path, edges_path)

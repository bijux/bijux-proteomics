# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import bijux_proteomics.review as review


def test_review_package_exports_proteomics_evidence_graph_owner_surface() -> None:
    builder = review.ProteomicsEvidenceGraphBuilder()
    sample = builder.add_sample("S1", label="sample S1")
    run = builder.add_run("R1", label="run R1")
    builder.add_sample_contains_run(
        sample.node_id,
        run.node_id,
        source_row_ref="design.tsv:2",
        confidence=1.0,
        reason="sample table assigns run R1 to sample S1",
    )
    graph = builder.build()

    assert hasattr(review, "build_proteomics_evidence_graph")
    assert hasattr(review, "ProteomicsEvidenceNodeKind")
    assert hasattr(review, "ProteomicsEvidenceEdgeKind")
    assert hasattr(review, "ProteomicsEvidenceType")
    assert graph.summary.node_kind_counts == {"run": 1, "sample": 1}
    assert graph.summary.edge_kind_counts == {"sample_contains_run": 1}

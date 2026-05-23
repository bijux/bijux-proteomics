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


def test_review_package_exports_evidence_graph_query_engine_surface() -> None:
    builder = review.ProteomicsEvidenceGraphBuilder()
    protein = builder.add_protein("P11111", label="P11111")
    peptide = builder.add_peptide("PEPTIDE", label="PEPTIDE")
    builder.add_peptide_maps_to_protein(
        peptide.node_id,
        protein.node_id,
        source_row_ref="digest.tsv:4",
        confidence=1.0,
        reason="peptide maps uniquely to protein P11111",
    )
    report = review.query_protein_evidence_summary(builder.build(), protein_id="P11111")

    assert hasattr(review, "query_protein_evidence_summary")
    assert hasattr(review, "render_protein_evidence_summary_tsv")
    assert report.support_edge_count == 1
    assert "protein_id\tprotein_label\trelation" in review.render_protein_evidence_summary_tsv(
        report
    )

# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

import pytest

from bijux_proteomics.review import (
    export_proteomics_evidence_graph,
    query_pathway_support_proteins,
    query_peptide_support_chain,
    query_protein_evidence_summary,
    query_ptm_site_evidence,
    query_rejected_evidence_path,
    query_sample_qc_reasons,
    render_proteomics_evidence_graph_edges_tsv,
    render_proteomics_evidence_graph_nodes_tsv,
)
from bijux_proteomics.review.evidence_graph.evidence_graph import (
    ProteomicsEvidenceGraph,
)
from bijux_proteomics.review.evidence_graph.lazy_evidence_graph import (
    LazyProteomicsEvidenceGraph,
    load_lazy_proteomics_evidence_graph,
)

from .test_evidence_graph_query_engine_surface import build_review_query_fixture_graph


def _write_lazy_graph_artifacts(
    tmp_path: Path,
) -> tuple[ProteomicsEvidenceGraph, LazyProteomicsEvidenceGraph]:
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
    return graph, load_lazy_proteomics_evidence_graph(nodes_path, edges_path)


def test_load_lazy_proteomics_evidence_graph_preserves_summary_and_node_lookup(
    tmp_path: Path,
) -> None:
    graph, lazy_graph = _write_lazy_graph_artifacts(tmp_path)

    assert lazy_graph.summary == graph.summary
    assert lazy_graph.require_node_by_id("protein:P11111").entity_ref == "P11111"
    assert lazy_graph.require_node_by_id("psm:psm:1002").claim_state == "rejected"


def test_load_lazy_proteomics_evidence_graph_rejects_missing_edge_endpoints(
    tmp_path: Path,
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


def test_lazy_graph_matches_eager_protein_peptide_and_ptm_queries(
    tmp_path: Path,
) -> None:
    graph, lazy_graph = _write_lazy_graph_artifacts(tmp_path)

    eager_protein = query_protein_evidence_summary(graph, protein_id="P11111")
    lazy_protein = query_protein_evidence_summary(lazy_graph, protein_id="P11111")
    eager_peptide = query_peptide_support_chain(graph, peptide_id="PEPTIDE")
    lazy_peptide = query_peptide_support_chain(lazy_graph, peptide_id="PEPTIDE")
    eager_ptm = query_ptm_site_evidence(graph, ptm_site_id="P11111:S3:Phospho")
    lazy_ptm = query_ptm_site_evidence(lazy_graph, ptm_site_id="P11111:S3:Phospho")

    assert lazy_protein == eager_protein
    assert lazy_peptide == eager_peptide
    assert lazy_ptm == eager_ptm


def test_lazy_graph_matches_eager_pathway_and_qc_queries(tmp_path: Path) -> None:
    graph, lazy_graph = _write_lazy_graph_artifacts(tmp_path)

    eager_pathway = query_pathway_support_proteins(graph, pathway_id="R-HSA-199420")
    lazy_pathway = query_pathway_support_proteins(lazy_graph, pathway_id="R-HSA-199420")
    eager_qc = query_sample_qc_reasons(graph, sample_id="S1")
    lazy_qc = query_sample_qc_reasons(lazy_graph, sample_id="S1")

    assert lazy_pathway == eager_pathway
    assert lazy_qc == eager_qc


def test_lazy_graph_matches_eager_rejected_evidence_paths(tmp_path: Path) -> None:
    graph, lazy_graph = _write_lazy_graph_artifacts(tmp_path)

    eager_path = query_rejected_evidence_path(graph, node_id="psm:psm:1002")
    lazy_path = query_rejected_evidence_path(lazy_graph, node_id="psm:psm:1002")

    assert lazy_path == eager_path

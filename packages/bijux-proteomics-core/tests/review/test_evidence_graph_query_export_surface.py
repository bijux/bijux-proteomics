# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.review import (
    query_pathway_support_proteins,
    query_peptide_support_chain,
    query_protein_evidence_summary,
    query_ptm_site_evidence,
    query_rejected_evidence_path,
    query_sample_qc_reasons,
    render_pathway_support_proteins_tsv,
    render_peptide_support_chain_tsv,
    render_protein_evidence_summary_tsv,
    render_ptm_site_evidence_tsv,
    render_rejected_evidence_path_tsv,
    render_sample_qc_reasons_tsv,
)

from .test_evidence_graph_query_engine_surface import build_review_query_fixture_graph


def test_evidence_graph_query_reports_render_tsv_and_json() -> None:
    graph = build_review_query_fixture_graph()

    protein = query_protein_evidence_summary(graph, protein_id="P11111")
    peptide = query_peptide_support_chain(graph, peptide_id="PEPTIDE")
    ptm_site = query_ptm_site_evidence(graph, ptm_site_id="P11111:S3:Phospho")
    rejected = query_rejected_evidence_path(graph, node_id="psm:psm:1002")
    pathway = query_pathway_support_proteins(graph, pathway_id="R-HSA-199420")
    sample_qc = query_sample_qc_reasons(graph, sample_id="S1")

    assert "protein_id\tprotein_label\trelation" in render_protein_evidence_summary_tsv(protein)
    assert "peptide_id\tdepth\tnode_id" in render_peptide_support_chain_tsv(peptide)
    assert "ptm_site_id\trelation\tsource_node_id" in render_ptm_site_evidence_tsv(ptm_site)
    assert "rejected_node_id\tdepth\tnode_id" in render_rejected_evidence_path_tsv(rejected)
    assert "pathway_id\tprotein_id\tprotein_label" in render_pathway_support_proteins_tsv(pathway)
    assert "sample_id\trun_id\tqc_decision_id" in render_sample_qc_reasons_tsv(sample_qc)
    assert "\"support_edge_count\": 4" in protein.to_stable_json()
    assert "\"edge_count\"" in peptide.to_stable_json()
    assert "\"support_edge_count\"" in ptm_site.to_stable_json()
    assert "\"step_count\"" in rejected.to_stable_json()
    assert "\"support_edge_count\": 1" in pathway.to_stable_json()
    assert "\"qc_edge_count\": 1" in sample_qc.to_stable_json()

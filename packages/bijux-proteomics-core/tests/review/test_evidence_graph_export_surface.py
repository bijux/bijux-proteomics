# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.review import (
    ProteomicsEvidenceContextRef,
    ProteomicsEvidenceGraph,
    ProteomicsEvidenceGraphBuilder,
    ProteomicsEvidenceNodeKind,
    export_proteomics_evidence_graph,
)


def build_graph_export_fixture() -> ProteomicsEvidenceGraph:
    builder = ProteomicsEvidenceGraphBuilder()

    sample = builder.add_sample("S1", label="sample S1")
    run = builder.add_run(
        "R1",
        label="run R1",
        context_refs=(
            ProteomicsEvidenceContextRef(
                entity_type=ProteomicsEvidenceNodeKind.SAMPLE,
                entity_ref="S1",
            ),
        ),
    )
    spectrum = builder.add_spectrum("scan=1001", label="scan=1001", trust_class="high")
    psm = builder.add_psm("psm:1001", label="psm:1001", trust_class="high")
    peptide = builder.add_peptide("PEPTIDE", label="PEPTIDE", trust_class="high")
    protein = builder.add_protein(
        "P11111",
        label="P11111",
        trust_class="reviewed",
        contradiction_ids=("cx-1",),
        context_refs=(
            ProteomicsEvidenceContextRef(
                entity_type=ProteomicsEvidenceNodeKind.SAMPLE,
                entity_ref="S1",
            ),
        ),
    )

    builder.add_sample_contains_run(
        sample.node_id,
        run.node_id,
        source_row_ref="design.tsv:2",
        confidence=1.0,
        reason="sample table assigns run R1 to sample S1",
    )
    builder.add_run_acquired_spectrum(
        run.node_id,
        spectrum.node_id,
        source_row_ref="spectra.mgf:1001",
        confidence=1.0,
        reason="run R1 acquired scan 1001",
    )
    builder.add_spectrum_supports_psm(
        spectrum.node_id,
        psm.node_id,
        source_row_ref="psm.tsv:4",
        confidence=0.97,
        reason="strong spectrum supports accepted PSM",
    )
    builder.add_psm_supports_peptide(
        psm.node_id,
        peptide.node_id,
        source_row_ref="peptide.tsv:4",
        confidence=0.96,
        reason="strong PSM supports peptide PEPTIDE",
    )
    builder.add_peptide_quantifies_protein(
        peptide.node_id,
        protein.node_id,
        source_row_ref="protein_matrix.tsv:4",
        confidence=0.93,
        reason="strong peptide quantifies protein P11111",
    )
    return builder.build()


def test_export_proteomics_evidence_graph_retains_nodes_edges_and_provenance() -> None:
    graph = build_graph_export_fixture()

    bundle = export_proteomics_evidence_graph(graph)

    assert bundle.node_count == 6
    assert bundle.edge_count == 5
    assert bundle.contradiction_node_count == 1
    assert bundle.nodes[0].id == "peptide:PEPTIDE"
    assert bundle.nodes[-1].id == "spectrum:scan=1001"
    protein_node = next(node for node in bundle.nodes if node.id == "protein:P11111")
    assert protein_node.kind == "protein"
    assert protein_node.trust == "reviewed"
    assert protein_node.contradictions == ("cx-1",)
    assert protein_node.context[0].kind == "sample"
    assert protein_node.context[0].ref == "S1"
    peptide_edge = next(
        edge for edge in bundle.edges if edge.relation == "peptide_quantifies_protein"
    )
    assert peptide_edge.row_ref == "protein_matrix.tsv:4"
    assert peptide_edge.confidence == 0.93
    assert peptide_edge.evidence_type == "quantification"
    assert "quantifies protein" in peptide_edge.reason

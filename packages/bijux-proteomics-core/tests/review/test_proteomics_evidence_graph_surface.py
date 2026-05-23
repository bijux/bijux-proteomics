# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import pytest

from bijux_proteomics.review import (
    ProteomicsEvidenceContextRef,
    ProteomicsEvidenceEdge,
    ProteomicsEvidenceGraphBuilder,
    ProteomicsEvidenceNode,
    ProteomicsEvidenceNodeKind,
    build_proteomics_evidence_graph,
)


def test_proteomics_evidence_graph_builder_tracks_required_node_kinds() -> None:
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
    spectrum = builder.add_spectrum("scan=1001", label="spectrum scan=1001")
    precursor = builder.add_precursor("PEPTIDE/2", label="PEPTIDE/2")
    peptide = builder.add_peptide("PEPTIDE", label="PEPTIDE")
    modified_peptide = builder.add_modified_peptide(
        "PEPTIDE[Phospho@S3]",
        label="PEPTIDE[Phospho@S3]",
    )
    psm = builder.add_psm("psm:scan=1001", label="psm scan=1001")
    protein = builder.add_protein("P11111", label="P11111")
    protein_group = builder.add_protein_group("PG:P11111", label="PG:P11111")
    ptm_site = builder.add_ptm_site("P11111:S3:Phospho", label="P11111:S3:Phospho")
    transition = builder.add_transition("y7@654.3", label="y7@654.3")
    quant_value = builder.add_quant_value(
        "quant:S1:P11111",
        label="quant S1 P11111",
        context_refs=(
            ProteomicsEvidenceContextRef(
                entity_type=ProteomicsEvidenceNodeKind.SAMPLE,
                entity_ref="S1",
            ),
            ProteomicsEvidenceContextRef(
                entity_type=ProteomicsEvidenceNodeKind.PROTEIN,
                entity_ref="P11111",
            ),
        ),
    )
    pathway = builder.add_pathway("R-HSA-199420", label="Apoptosis")
    qc_decision = builder.add_qc_decision(
        "qc:R1:pass",
        label="QC pass",
        claim_state="accepted",
        trust_class="high",
        contradiction_ids=("cx-1",),
    )

    builder.add_edge(sample.node_id, run.node_id, "contains_run")
    builder.add_edge(run.node_id, spectrum.node_id, "acquired_spectrum")
    builder.add_edge(spectrum.node_id, precursor.node_id, "assigned_precursor")
    builder.add_edge(precursor.node_id, peptide.node_id, "supports_peptide")
    builder.add_edge(peptide.node_id, modified_peptide.node_id, "modified_form")
    builder.add_edge(modified_peptide.node_id, psm.node_id, "supported_by_psm")
    builder.add_edge(psm.node_id, protein.node_id, "supports_protein")
    builder.add_edge(protein.node_id, protein_group.node_id, "member_of_group")
    builder.add_edge(modified_peptide.node_id, ptm_site.node_id, "localizes_site")
    builder.add_edge(precursor.node_id, transition.node_id, "observed_transition")
    builder.add_edge(protein.node_id, quant_value.node_id, "quantified_by")
    builder.add_edge(protein.node_id, pathway.node_id, "annotated_to_pathway")
    builder.add_edge(run.node_id, qc_decision.node_id, "governed_by_qc")
    builder.add_edge(protein.node_id, pathway.node_id, "annotated_to_pathway")

    graph = builder.build()

    assert graph.summary.node_count == 14
    assert graph.summary.edge_count == 13
    assert graph.summary.contradiction_node_count == 1
    assert graph.summary.node_kind_counts == {
        "modified_peptide": 1,
        "pathway": 1,
        "peptide": 1,
        "precursor": 1,
        "protein": 1,
        "protein_group": 1,
        "psm": 1,
        "ptm_site": 1,
        "qc_decision": 1,
        "quant_value": 1,
        "run": 1,
        "sample": 1,
        "spectrum": 1,
        "transition": 1,
    }
    pathway_edge = next(
        edge
        for edge in graph.edges
        if edge.source_node_id == protein.node_id and edge.target_node_id == pathway.node_id
    )
    assert pathway_edge.support_count == 2
    assert quant_value.context_refs[0].entity_ref == "S1"


def test_proteomics_evidence_graph_rejects_conflicts_and_missing_endpoints() -> None:
    builder = ProteomicsEvidenceGraphBuilder()
    builder.add_sample("S1", label="sample S1")
    with pytest.raises(ValueError, match="conflicting node definition"):
        builder.add_node(
            ProteomicsEvidenceNode(
                node_id="sample:S1",
                entity_type=ProteomicsEvidenceNodeKind.SAMPLE,
                entity_ref="S1",
                label="conflicting sample label",
            )
        )

    with pytest.raises(ValueError, match="target node is missing from builder"):
        builder.add_edge("sample:S1", "run:R1", "contains_run")

    with pytest.raises(ValueError, match="edge target node is missing from graph"):
        build_proteomics_evidence_graph(
            (
                ProteomicsEvidenceNode(
                    node_id="sample:S1",
                    entity_type=ProteomicsEvidenceNodeKind.SAMPLE,
                    entity_ref="S1",
                    label="sample S1",
                ),
            ),
            (
                ProteomicsEvidenceEdge(
                    source_node_id="sample:S1",
                    target_node_id="run:R1",
                    relation="contains_run",
                ),
            ),
        )

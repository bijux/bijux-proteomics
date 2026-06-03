# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import pytest

from bijux_proteomics.review import (
    ProteomicsEvidenceContextRef,
    ProteomicsEvidenceEdge,
    ProteomicsEvidenceEdgeKind,
    ProteomicsEvidenceGraphBuilder,
    ProteomicsEvidenceNode,
    ProteomicsEvidenceNodeKind,
    ProteomicsEvidenceType,
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
        reason="spectrum scan=1001 was acquired in run R1",
    )
    builder.add_spectrum_assigns_precursor(
        spectrum.node_id,
        precursor.node_id,
        source_row_ref="diann.tsv:12",
        confidence=0.97,
        reason="precursor assignment reported for scan=1001",
    )
    builder.add_spectrum_supports_psm(
        spectrum.node_id,
        psm.node_id,
        source_row_ref="psm.tsv:12",
        confidence=0.96,
        reason="search engine accepted psm scan=1001",
    )
    builder.add_precursor_supports_peptide(
        precursor.node_id,
        peptide.node_id,
        source_row_ref="diann.tsv:12",
        confidence=0.95,
        reason="precursor PEPTIDE/2 supports peptide sequence",
    )
    builder.add_psm_supports_peptide(
        psm.node_id,
        peptide.node_id,
        source_row_ref="psm.tsv:12",
        confidence=0.96,
        reason="accepted PSM supports peptide PEPTIDE",
    )
    builder.add_peptide_has_modified_form(
        peptide.node_id,
        modified_peptide.node_id,
        source_row_ref="ptm.tsv:12",
        confidence=0.91,
        reason="localized phospho form was observed for PEPTIDE",
    )
    builder.add_modified_peptide_localizes_ptm_site(
        modified_peptide.node_id,
        ptm_site.node_id,
        source_row_ref="ptm.tsv:12",
        confidence=0.93,
        reason="modified peptide localizes phospho site S3",
    )
    builder.add_peptide_maps_to_protein(
        peptide.node_id,
        protein.node_id,
        source_row_ref="digest_index.tsv:44",
        confidence=1.0,
        reason="peptide maps uniquely to protein P11111",
    )
    builder.add_peptide_quantifies_protein(
        peptide.node_id,
        protein.node_id,
        source_row_ref="feature_matrix.tsv:9",
        confidence=0.88,
        reason="peptide intensity contributes to protein quantification",
    )
    builder.add_protein_member_of_group(
        protein.node_id,
        protein_group.node_id,
        source_row_ref="protein_groups.tsv:6",
        confidence=0.84,
        reason="protein P11111 is a member of group PG:P11111",
    )
    builder.add_ptm_site_belongs_to_protein(
        ptm_site.node_id,
        protein.node_id,
        source_row_ref="site_mapping.tsv:3",
        confidence=1.0,
        reason="site P11111:S3:Phospho belongs to protein P11111",
    )
    builder.add_precursor_supports_transition(
        precursor.node_id,
        transition.node_id,
        source_row_ref="transition_table.tsv:8",
        confidence=0.9,
        reason="targeted assay assigns y7 to precursor PEPTIDE/2",
    )
    builder.add_protein_quantified_by_quant_value(
        protein.node_id,
        quant_value.node_id,
        source_row_ref="protein_matrix.tsv:4",
        confidence=0.89,
        reason="protein abundance matrix contains quantified value for P11111 in S1",
    )
    builder.add_protein_member_of_pathway(
        protein.node_id,
        pathway.node_id,
        source_row_ref="pathway_annotations.tsv:11",
        confidence=0.8,
        reason="pathway annotation links protein P11111 to apoptosis",
    )
    builder.add_run_governed_by_qc_decision(
        run.node_id,
        qc_decision.node_id,
        source_row_ref="qc.tsv:2",
        confidence=1.0,
        reason="run QC accepted run R1",
    )

    graph = builder.build()

    assert graph.summary.node_count == 14
    assert graph.summary.edge_count == 16
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
    assert graph.summary.edge_kind_counts["protein_member_of_pathway"] == 1
    assert graph.summary.evidence_type_counts["quantification"] == 2
    pathway_edge = next(
        edge
        for edge in graph.edges
        if edge.relation is ProteomicsEvidenceEdgeKind.PROTEIN_MEMBER_OF_PATHWAY
    )
    assert pathway_edge.source_row_ref == "pathway_annotations.tsv:11"
    assert pathway_edge.evidence_type is ProteomicsEvidenceType.ANNOTATION
    assert pathway_edge.confidence == 0.8
    assert "annotation links protein" in pathway_edge.reason
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
        builder.add_sample_contains_run(
            "sample:S1",
            "run:R1",
            source_row_ref="design.tsv:2",
            confidence=1.0,
            reason="sample table assigns run R1 to sample S1",
        )

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
                    relation=ProteomicsEvidenceEdgeKind.SAMPLE_CONTAINS_RUN,
                    source_row_ref="design.tsv:2",
                    confidence=1.0,
                    evidence_type=ProteomicsEvidenceType.WORKFLOW_CONTEXT,
                    reason="sample table assigns run R1 to sample S1",
                ),
            ),
        )


def test_proteomics_evidence_graph_tracks_statistical_result_support_edges() -> None:
    builder = ProteomicsEvidenceGraphBuilder()
    protein = builder.add_protein("P11111", label="P11111")
    quant_value = builder.add_quant_value("quant:S1:P11111", label="quant:S1:P11111")
    statistical_result = builder.add_statistical_result(
        "protein:treatment_vs_control:P11111",
        label="protein differential result",
    )

    builder.add_protein_quantified_by_quant_value(
        protein.node_id,
        quant_value.node_id,
        source_row_ref="protein_matrix.tsv:4",
        confidence=0.88,
        reason="protein matrix contains abundance for P11111 in S1",
    )
    builder.add_quant_value_supports_statistical_result(
        quant_value.node_id,
        statistical_result.node_id,
        source_row_ref="protein_stats.tsv:4",
        confidence=0.92,
        reason="protein statistic used quantified protein abundance",
    )
    builder.add_protein_supports_statistical_result(
        protein.node_id,
        statistical_result.node_id,
        source_row_ref="protein_stats.tsv:4",
        confidence=0.87,
        reason="protein P11111 is significant in treatment vs control",
    )

    graph = builder.build()

    assert graph.summary.node_kind_counts["statistical_result"] == 1
    assert (
        graph.summary.edge_kind_counts["quant_value_supports_statistical_result"] == 1
    )
    assert graph.summary.edge_kind_counts["protein_supports_statistical_result"] == 1

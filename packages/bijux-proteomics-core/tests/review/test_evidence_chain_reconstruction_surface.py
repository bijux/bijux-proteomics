# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.review import (
    ProteomicsEvidenceGraph,
    ProteomicsEvidenceGraphBuilder,
    reconstruct_pathway_evidence_chain,
    reconstruct_protein_evidence_chain,
    reconstruct_ptm_site_evidence_chain,
)


def build_reconstruction_fixture_graph() -> ProteomicsEvidenceGraph:
    builder = ProteomicsEvidenceGraphBuilder()

    sample = builder.add_sample("S1", label="sample S1")
    run = builder.add_run("R1", label="run R1")
    spectrum = builder.add_spectrum("scan=1001", label="scan=1001")
    precursor = builder.add_precursor("PEPTIDE/2", label="PEPTIDE/2")
    psm = builder.add_psm("psm:1001", label="psm:1001")
    peptide = builder.add_peptide("PEPTIDE", label="PEPTIDE")
    modified_peptide = builder.add_modified_peptide(
        "PEPTIDE[Phospho@S3]",
        label="PEPTIDE[Phospho@S3]",
    )
    protein = builder.add_protein("P11111", label="P11111")
    protein_group = builder.add_protein_group("PG:P11111", label="PG:P11111")
    quant_value = builder.add_quant_value("quant:S1:P11111", label="quant:S1:P11111")
    ptm_site = builder.add_ptm_site("P11111:S3:Phospho", label="P11111:S3:Phospho")
    pathway = builder.add_pathway("R-HSA-199420", label="Apoptosis")
    protein_result = builder.add_statistical_result(
        "protein:treatment_vs_control:P11111",
        label="protein P11111 differential result",
    )
    ptm_result = builder.add_statistical_result(
        "ptm:treatment_vs_control:P11111:S3:Phospho",
        label="PTM site differential result",
    )
    pathway_result = builder.add_statistical_result(
        "pathway:treatment_vs_control:R-HSA-199420",
        label="pathway enrichment result",
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
        reason="run R1 acquired scan=1001",
    )
    builder.add_spectrum_assigns_precursor(
        spectrum.node_id,
        precursor.node_id,
        source_row_ref="diann.tsv:12",
        confidence=0.96,
        reason="precursor PEPTIDE/2 assigned to scan=1001",
    )
    builder.add_spectrum_supports_psm(
        spectrum.node_id,
        psm.node_id,
        source_row_ref="psm.tsv:12",
        confidence=0.95,
        reason="accepted PSM for scan=1001",
    )
    builder.add_precursor_supports_peptide(
        precursor.node_id,
        peptide.node_id,
        source_row_ref="diann.tsv:12",
        confidence=0.94,
        reason="precursor PEPTIDE/2 supports peptide PEPTIDE",
    )
    builder.add_psm_supports_peptide(
        psm.node_id,
        peptide.node_id,
        source_row_ref="psm.tsv:12",
        confidence=0.95,
        reason="accepted PSM supports peptide PEPTIDE",
    )
    builder.add_peptide_has_modified_form(
        peptide.node_id,
        modified_peptide.node_id,
        source_row_ref="ptm.tsv:5",
        confidence=0.91,
        reason="phospho form observed for PEPTIDE",
    )
    builder.add_modified_peptide_localizes_ptm_site(
        modified_peptide.node_id,
        ptm_site.node_id,
        source_row_ref="ptm.tsv:5",
        confidence=0.93,
        reason="localized phospho site S3",
    )
    builder.add_peptide_maps_to_protein(
        peptide.node_id,
        protein.node_id,
        source_row_ref="digest.tsv:44",
        confidence=1.0,
        reason="peptide maps uniquely to protein P11111",
    )
    builder.add_peptide_quantifies_protein(
        peptide.node_id,
        protein.node_id,
        source_row_ref="features.tsv:9",
        confidence=0.89,
        reason="peptide contributes to protein quantification",
    )
    builder.add_protein_member_of_group(
        protein.node_id,
        protein_group.node_id,
        source_row_ref="proteinGroups.tsv:6",
        confidence=0.84,
        reason="protein belongs to group PG:P11111",
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
        protein_result.node_id,
        source_row_ref="protein_stats.tsv:4",
        confidence=0.92,
        reason="protein statistic used quantified protein abundance",
    )
    builder.add_protein_supports_statistical_result(
        protein.node_id,
        protein_result.node_id,
        source_row_ref="protein_stats.tsv:4",
        confidence=0.87,
        reason="protein P11111 is significant in treatment vs control",
    )
    builder.add_ptm_site_belongs_to_protein(
        ptm_site.node_id,
        protein.node_id,
        source_row_ref="site_mapping.tsv:3",
        confidence=1.0,
        reason="PTM site belongs to protein P11111",
    )
    builder.add_ptm_site_supports_statistical_result(
        ptm_site.node_id,
        ptm_result.node_id,
        source_row_ref="ptm_stats.tsv:6",
        confidence=0.9,
        reason="PTM site is significant in treatment vs control",
    )
    builder.add_protein_member_of_pathway(
        protein.node_id,
        pathway.node_id,
        source_row_ref="pathway.tsv:11",
        confidence=0.81,
        reason="protein P11111 is annotated to apoptosis",
    )
    builder.add_pathway_supports_statistical_result(
        pathway.node_id,
        pathway_result.node_id,
        source_row_ref="pathway_stats.tsv:3",
        confidence=0.78,
        reason="pathway enrichment was significant for apoptosis",
    )
    return builder.build()


def test_reconstruct_protein_evidence_chain_reaches_source_rows_and_final_result() -> (
    None
):
    report = reconstruct_protein_evidence_chain(
        build_reconstruction_fixture_graph(),
        protein_id="P11111",
        statistical_result_id="protein:treatment_vs_control:P11111",
    )

    assert report.claim_node.entity_ref == "P11111"
    assert report.statistical_result is not None
    assert report.statistical_result.entity_ref == "protein:treatment_vs_control:P11111"
    assert any(
        item.input_file == "psm.tsv" and item.row_number == "12"
        for item in report.source_rows
    )
    assert any(
        step.node.entity_ref == "protein:treatment_vs_control:P11111"
        for step in report.chain_nodes
    )
    assert any(
        edge.source_row_ref == "protein_stats.tsv:4" for edge in report.chain_edges
    )


def test_reconstruct_ptm_site_evidence_chain_reaches_localization_and_final_result() -> (
    None
):
    report = reconstruct_ptm_site_evidence_chain(
        build_reconstruction_fixture_graph(),
        ptm_site_id="P11111:S3:Phospho",
        statistical_result_id="ptm:treatment_vs_control:P11111:S3:Phospho",
    )

    assert report.claim_node.entity_ref == "P11111:S3:Phospho"
    assert any(
        item.input_file == "ptm.tsv" and item.row_number == "5"
        for item in report.source_rows
    )
    assert any(
        step.node.entity_ref == "PEPTIDE[Phospho@S3]" for step in report.chain_nodes
    )
    assert any(edge.source_row_ref == "ptm_stats.tsv:6" for edge in report.chain_edges)


def test_reconstruct_pathway_evidence_chain_reaches_annotation_and_final_result() -> (
    None
):
    report = reconstruct_pathway_evidence_chain(
        build_reconstruction_fixture_graph(),
        pathway_id="R-HSA-199420",
        statistical_result_id="pathway:treatment_vs_control:R-HSA-199420",
    )

    assert report.claim_node.entity_ref == "R-HSA-199420"
    assert any(
        item.input_file == "pathway.tsv" and item.row_number == "11"
        for item in report.source_rows
    )
    assert any(step.node.entity_ref == "P11111" for step in report.chain_nodes)
    assert any(
        edge.source_row_ref == "pathway_stats.tsv:3" for edge in report.chain_edges
    )

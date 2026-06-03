# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.review import (
    ProteomicsEvidenceGraph,
    ProteomicsEvidenceGraphBuilder,
    query_pathway_support_proteins,
    query_peptide_support_chain,
    query_protein_evidence_summary,
    query_ptm_site_evidence,
    query_rejected_evidence_path,
    query_sample_qc_reasons,
)


def build_review_query_fixture_graph() -> ProteomicsEvidenceGraph:
    builder = ProteomicsEvidenceGraphBuilder()

    sample = builder.add_sample("S1", label="sample S1")
    run = builder.add_run("R1", label="run R1")
    spectrum = builder.add_spectrum("scan=1001", label="scan=1001")
    precursor = builder.add_precursor("PEPTIDE/2", label="PEPTIDE/2")
    psm = builder.add_psm("psm:1001", label="psm:1001")
    rejected_psm = builder.add_psm(
        "psm:1002",
        label="psm:1002",
        claim_state="rejected",
        trust_class="low",
    )
    peptide = builder.add_peptide("PEPTIDE", label="PEPTIDE")
    modified_peptide = builder.add_modified_peptide(
        "PEPTIDE[Phospho@S3]",
        label="PEPTIDE[Phospho@S3]",
    )
    ptm_site = builder.add_ptm_site("P11111:S3:Phospho", label="P11111:S3:Phospho")
    protein = builder.add_protein("P11111", label="P11111")
    protein_group = builder.add_protein_group("PG:P11111", label="PG:P11111")
    quant_value = builder.add_quant_value("quant:S1:P11111", label="quant:S1:P11111")
    pathway = builder.add_pathway("R-HSA-199420", label="Apoptosis")
    qc_decision = builder.add_qc_decision(
        "qc:R1:fail",
        label="carryover warning",
        claim_state="caution",
        trust_class="medium",
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
    builder.add_spectrum_supports_psm(
        spectrum.node_id,
        rejected_psm.node_id,
        source_row_ref="psm.tsv:13",
        confidence=0.2,
        reason="rejected PSM competing assignment for scan=1001",
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
    builder.add_psm_supports_peptide(
        rejected_psm.node_id,
        peptide.node_id,
        source_row_ref="psm.tsv:13",
        confidence=0.2,
        reason="rejected PSM still points at peptide PEPTIDE",
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
    builder.add_ptm_site_belongs_to_protein(
        ptm_site.node_id,
        protein.node_id,
        source_row_ref="site_mapping.tsv:3",
        confidence=1.0,
        reason="PTM site belongs to protein P11111",
    )
    builder.add_protein_member_of_pathway(
        protein.node_id,
        pathway.node_id,
        source_row_ref="pathway.tsv:11",
        confidence=0.81,
        reason="protein P11111 is annotated to apoptosis",
    )
    builder.add_run_governed_by_qc_decision(
        run.node_id,
        qc_decision.node_id,
        source_row_ref="qc.tsv:2",
        confidence=1.0,
        reason="carryover suspicion downgraded run R1",
    )
    return builder.build()


def test_query_protein_evidence_summary_returns_structured_support() -> None:
    report = query_protein_evidence_summary(
        build_review_query_fixture_graph(),
        protein_id="P11111",
    )

    assert report.protein.entity_ref == "P11111"
    assert [node.entity_ref for node in report.mapped_peptides] == ["PEPTIDE"]
    assert [node.entity_ref for node in report.quant_values] == ["quant:S1:P11111"]
    assert report.support_edge_count == 4


def test_query_peptide_support_chain_returns_deterministic_chain() -> None:
    report = query_peptide_support_chain(
        build_review_query_fixture_graph(),
        peptide_id="PEPTIDE",
    )

    assert report.peptide.entity_ref == "PEPTIDE"
    assert report.step_count >= 6
    assert any(step.node.entity_ref == "scan=1001" for step in report.chain_steps)
    assert any(edge.source_row_ref == "psm.tsv:12" for edge in report.support_edges)


def test_query_ptm_site_evidence_returns_localization_and_mapping_support() -> None:
    report = query_ptm_site_evidence(
        build_review_query_fixture_graph(),
        ptm_site_id="P11111:S3:Phospho",
    )

    assert report.ptm_site.entity_ref == "P11111:S3:Phospho"
    assert [node.entity_ref for node in report.localized_modified_peptides] == [
        "PEPTIDE[Phospho@S3]"
    ]
    assert [node.entity_ref for node in report.proteins] == ["P11111"]
    assert report.support_edge_count >= 5


def test_query_rejected_evidence_path_returns_adjacent_chain() -> None:
    graph = build_review_query_fixture_graph()
    report = query_rejected_evidence_path(
        graph,
        node_id="psm:psm:1002",
    )

    assert report.rejected_node.claim_state == "rejected"
    assert any(step.node.entity_ref == "PEPTIDE" for step in report.path_steps)
    assert any(edge.source_row_ref == "psm.tsv:13" for edge in report.path_edges)


def test_query_pathway_support_proteins_returns_supporting_proteins() -> None:
    report = query_pathway_support_proteins(
        build_review_query_fixture_graph(),
        pathway_id="R-HSA-199420",
    )

    assert report.pathway.entity_ref == "R-HSA-199420"
    assert [node.entity_ref for node in report.supporting_proteins] == ["P11111"]
    assert report.support_edge_count == 1


def test_query_sample_qc_reasons_returns_runs_and_qc_nodes() -> None:
    report = query_sample_qc_reasons(
        build_review_query_fixture_graph(),
        sample_id="S1",
    )

    assert report.sample.entity_ref == "S1"
    assert [node.entity_ref for node in report.runs] == ["R1"]
    assert [node.entity_ref for node in report.qc_decisions] == ["qc:R1:fail"]
    assert report.qc_edges[0].reason == "carryover suspicion downgraded run R1"

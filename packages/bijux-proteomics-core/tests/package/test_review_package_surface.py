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


def test_review_package_exports_evidence_chain_reconstruction_surface() -> None:
    builder = review.ProteomicsEvidenceGraphBuilder()
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
    report = review.reconstruct_protein_evidence_chain(
        builder.build(),
        protein_id="P11111",
        statistical_result_id="protein:treatment_vs_control:P11111",
    )

    assert hasattr(review, "reconstruct_protein_evidence_chain")
    assert hasattr(review, "render_evidence_chain_tsv")
    assert report.source_row_count == 2
    assert "claim_kind\tclaim_id\tstatistical_result_id\trelation" in review.render_evidence_chain_tsv(
        report
    )


def test_review_package_exports_evidence_graph_contradiction_surface() -> None:
    builder = review.ProteomicsEvidenceGraphBuilder()
    protein = builder.add_protein("P11111", label="P11111")
    peptide_a = builder.add_peptide("PEPA", label="PEPA")
    peptide_b = builder.add_peptide("PEPB", label="PEPB")
    protein_result = builder.add_statistical_result(
        "protein:treatment_vs_control:P11111",
        label="protein differential result",
        claim_state="unchanged",
    )
    peptide_a_result = builder.add_statistical_result(
        "peptide:treatment_vs_control:PEPA",
        label="peptide PEPA differential result",
        claim_state="upregulated",
    )
    peptide_b_result = builder.add_statistical_result(
        "peptide:treatment_vs_control:PEPB",
        label="peptide PEPB differential result",
        claim_state="downregulated",
    )

    builder.add_peptide_quantifies_protein(
        peptide_a.node_id,
        protein.node_id,
        source_row_ref="features.tsv:10",
        confidence=0.88,
        reason="PEPA contributes to protein quantification",
    )
    builder.add_peptide_quantifies_protein(
        peptide_b.node_id,
        protein.node_id,
        source_row_ref="features.tsv:11",
        confidence=0.87,
        reason="PEPB contributes to protein quantification",
    )
    builder.add_protein_supports_statistical_result(
        protein.node_id,
        protein_result.node_id,
        source_row_ref="protein_stats.tsv:4",
        confidence=0.9,
        reason="protein P11111 is unchanged in treatment vs control",
    )
    builder.add_peptide_supports_statistical_result(
        peptide_a.node_id,
        peptide_a_result.node_id,
        source_row_ref="peptide_stats.tsv:4",
        confidence=0.84,
        reason="peptide PEPA is upregulated in treatment vs control",
    )
    builder.add_peptide_supports_statistical_result(
        peptide_b.node_id,
        peptide_b_result.node_id,
        source_row_ref="peptide_stats.tsv:5",
        confidence=0.83,
        reason="peptide PEPB is downregulated in treatment vs control",
    )

    report = review.detect_evidence_graph_contradictions(builder.build())

    assert hasattr(review, "detect_evidence_graph_contradictions")
    assert hasattr(review, "render_evidence_graph_contradictions_tsv")
    assert report.contradiction_count == 1
    assert report.entries[0].kind.value == "protein_unchanged_with_changed_peptides"
    assert "contradiction_id\tkind\tseverity\tclaim_node_id" in (
        review.render_evidence_graph_contradictions_tsv(report)
    )


def test_review_package_exports_evidence_graph_confidence_surface() -> None:
    builder = review.ProteomicsEvidenceGraphBuilder()
    spectrum = builder.add_spectrum("scan=1001", label="scan=1001", trust_class="high")
    psm = builder.add_psm("psm:1001", label="psm:1001", trust_class="high")
    peptide = builder.add_peptide("PEPA", label="PEPA", trust_class="high")
    protein = builder.add_protein("P11111", label="P11111", trust_class="high")
    result = builder.add_statistical_result(
        "protein:treatment_vs_control:P11111",
        label="protein differential result",
        claim_state="changed",
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
        reason="strong PSM supports peptide PEPA",
    )
    builder.add_peptide_quantifies_protein(
        peptide.node_id,
        protein.node_id,
        source_row_ref="protein_matrix.tsv:4",
        confidence=0.93,
        reason="strong peptide quantifies protein P11111",
    )
    builder.add_protein_supports_statistical_result(
        protein.node_id,
        result.node_id,
        source_row_ref="protein_stats.tsv:4",
        confidence=0.91,
        reason="strong protein differential result",
    )

    report = review.propagate_evidence_graph_confidence(builder.build())

    assert hasattr(review, "propagate_evidence_graph_confidence")
    assert hasattr(review, "render_evidence_graph_confidence_tsv")
    assert report.entry_count == 1
    assert report.entries[0].confidence_tier.value == "high"
    assert "claim_node_id\tclaim_node_ref\tsubject_node_id" in (
        review.render_evidence_graph_confidence_tsv(report)
    )


def test_review_package_exports_evidence_graph_downgrade_surface() -> None:
    builder = review.ProteomicsEvidenceGraphBuilder()
    protein = builder.add_protein("P11111", label="P11111", trust_class="high")
    peptide = builder.add_peptide("PEPA", label="PEPA", trust_class="high")
    alternate = builder.add_protein("P22222", label="P22222", trust_class="high")
    result = builder.add_statistical_result(
        "protein:treatment_vs_control:P11111",
        label="protein differential result",
        claim_state="changed",
    )
    spectrum = builder.add_spectrum("scan=1001", label="scan=1001", trust_class="high")
    psm = builder.add_psm("psm:1001", label="psm:1001", trust_class="high")

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
        reason="strong PSM supports peptide PEPA",
    )
    builder.add_peptide_quantifies_protein(
        peptide.node_id,
        protein.node_id,
        source_row_ref="protein_matrix.tsv:4",
        confidence=0.93,
        reason="strong peptide quantifies protein P11111",
    )
    builder.add_peptide_maps_to_protein(
        peptide.node_id,
        protein.node_id,
        source_row_ref="digest.tsv:4",
        confidence=1.0,
        reason="PEPA maps to P11111",
    )
    builder.add_peptide_maps_to_protein(
        peptide.node_id,
        alternate.node_id,
        source_row_ref="digest.tsv:5",
        confidence=1.0,
        reason="PEPA also maps to P22222",
    )
    builder.add_protein_supports_statistical_result(
        protein.node_id,
        result.node_id,
        source_row_ref="protein_stats.tsv:4",
        confidence=0.91,
        reason="strong protein differential result",
    )

    report = review.build_evidence_graph_final_result_table(builder.build())

    assert hasattr(review, "build_evidence_graph_final_result_table")
    assert hasattr(review, "render_evidence_graph_final_results_tsv")
    assert report.entry_count == 1
    assert report.entries[0].evidence_tier.value == "ambiguous"
    assert [reason.value for reason in report.entries[0].downgrade_reasons] == [
        "shared_peptide_only"
    ]


def test_review_package_exports_evidence_graph_run_diff_surface() -> None:
    left = review.ProteomicsEvidenceGraphBuilder()
    right = review.ProteomicsEvidenceGraphBuilder()

    left_protein = left.add_protein("P11111", label="P11111", trust_class="high")
    left_peptide = left.add_peptide("PEPA", label="PEPA", trust_class="high")
    left_claim = left.add_statistical_result(
        "protein:treatment_vs_control:P11111",
        label="protein differential result",
        claim_state="changed",
    )
    left_spectrum = left.add_spectrum("scan=1001", label="scan=1001", trust_class="high")
    left_psm = left.add_psm("psm:1001", label="psm:1001", trust_class="high")
    left.add_spectrum_supports_psm(
        left_spectrum.node_id,
        left_psm.node_id,
        source_row_ref="psm.tsv:4",
        confidence=0.97,
        reason="strong spectrum supports accepted PSM",
    )
    left.add_psm_supports_peptide(
        left_psm.node_id,
        left_peptide.node_id,
        source_row_ref="peptide.tsv:4",
        confidence=0.96,
        reason="strong PSM supports peptide PEPA",
    )
    left.add_peptide_quantifies_protein(
        left_peptide.node_id,
        left_protein.node_id,
        source_row_ref="protein_matrix.tsv:4",
        confidence=0.93,
        reason="strong peptide quantifies protein P11111",
    )
    left.add_protein_supports_statistical_result(
        left_protein.node_id,
        left_claim.node_id,
        source_row_ref="protein_stats.tsv:4",
        confidence=0.91,
        reason="strong protein differential result",
    )

    right_protein = right.add_protein("P22222", label="P22222", trust_class="high")
    right_peptide = right.add_peptide("PEPB", label="PEPB", trust_class="high")
    right_claim = right.add_statistical_result(
        "protein:treatment_vs_control:P22222",
        label="protein differential result",
        claim_state="changed",
    )
    right_spectrum = right.add_spectrum("scan=1002", label="scan=1002", trust_class="high")
    right_psm = right.add_psm("psm:1002", label="psm:1002", trust_class="high")
    right.add_spectrum_supports_psm(
        right_spectrum.node_id,
        right_psm.node_id,
        source_row_ref="psm.tsv:5",
        confidence=0.97,
        reason="strong spectrum supports accepted PSM",
    )
    right.add_psm_supports_peptide(
        right_psm.node_id,
        right_peptide.node_id,
        source_row_ref="peptide.tsv:5",
        confidence=0.96,
        reason="strong PSM supports peptide PEPB",
    )
    right.add_peptide_quantifies_protein(
        right_peptide.node_id,
        right_protein.node_id,
        source_row_ref="protein_matrix.tsv:5",
        confidence=0.93,
        reason="strong peptide quantifies protein P22222",
    )
    right.add_protein_supports_statistical_result(
        right_protein.node_id,
        right_claim.node_id,
        source_row_ref="protein_stats.tsv:5",
        confidence=0.91,
        reason="strong protein differential result",
    )

    report = review.compare_evidence_graph_runs(left.build(), right.build())

    assert hasattr(review, "compare_evidence_graph_runs")
    assert hasattr(review, "render_evidence_graph_run_diff_tsv")
    assert report.entry_count == 2
    assert {entry.change_kind.value for entry in report.entries} == {"added", "removed"}

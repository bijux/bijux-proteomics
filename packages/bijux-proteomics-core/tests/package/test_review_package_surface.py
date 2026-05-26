# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics import domain
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
    assert review.EvidenceGraphConfidenceTier is domain.ConfidenceTier
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


def test_review_package_exports_result_query_surface(tmp_path: Path) -> None:
    biological_dir = tmp_path / "biological_report"
    biological_dir.mkdir()
    (biological_dir / "biological_protein_cards.tsv").write_text(
        "\n".join(
            (
                "card_id\tgraph_claim_node_id\tgraph_subject_node_id\tgraph_support_node_ids\tgraph_source_row_refs\tprotein_group_id\trepresentative_protein_ref\tprotein_refs\tgene_symbol\tpeptides\tpeptide_count\tunique_peptide_count\tshared_peptide_count\tobserved_sample_count\tmissing_sample_count\tcondition_a\tcondition_b\tlog2_fold_change\tadjusted_p_value\tsignificant\tevidence_tier\twarning_codes",
                "protein_card_1\tstatistical_result:protein_card_1\tprotein:P11111\tpeptide:PEPA\tdifferential:P11111\tprotein_group_1\tP11111\tP11111\tAKT1\tPEPA\t1\t1\t0\t3\t0\tcontrol\ttreatment\t1.2\t0.01\ttrue\thigh_support\t",
            )
        )
        + "\n",
        encoding="utf-8",
    )
    (biological_dir / "biological_evidence_graph_nodes.tsv").write_text(
        "\n".join(
            (
                "node_id\tentity_type\tentity_ref\tlabel\tclaim_state\ttrust_class\tcontradiction_ids\tcontext_refs",
                "sample:S1\tsample\tS1\tS1\tobserved\thigh\t\trun:R1",
                "run:R1\trun\tR1\tR1\tobserved\thigh\t\tsample:S1",
            )
        )
        + "\n",
        encoding="utf-8",
    )

    report = review.build_result_query_report_from_artifacts(
        (
            review.ResultQueryRequest(
                query_id="protein-significance",
                query_kind=review.ResultQueryKind.PROTEIN_SIGNIFICANCE,
                subject_id="P11111",
            ),
        ),
        biological_report_dir=biological_dir,
    )

    assert hasattr(review, "build_result_query_report_from_artifacts")
    assert review.ResultQueryKind.PROTEIN_SIGNIFICANCE.value == "protein_significance"
    assert report.summary.answered_query_count == 1
    assert "answer_text" in review.render_result_query_answer_tsv(report)


def test_review_package_exports_result_explanation_surface(tmp_path: Path) -> None:
    biological_dir = tmp_path / "biological_report"
    biological_dir.mkdir()
    (biological_dir / "biological_protein_cards.tsv").write_text(
        "\n".join(
            (
                "card_id\tgraph_claim_node_id\tgraph_subject_node_id\tgraph_support_node_ids\tgraph_source_row_refs\tprotein_group_id\trepresentative_protein_ref\tprotein_refs\tgene_symbol\tpeptides\tpeptide_count\tunique_peptide_count\tshared_peptide_count\tobserved_sample_count\tmissing_sample_count\tcondition_a\tcondition_b\tlog2_fold_change\tadjusted_p_value\tsignificant\tevidence_tier\twarning_codes",
                "protein_card_1\tstatistical_result:protein_card_1\tprotein:P11111\tpeptide:PEPA\tdifferential:P11111\tprotein_group_1\tP11111\tP11111\tAKT1\tPEPA\t1\t1\t0\t3\t0\tcontrol\ttreatment\t1.2\t0.01\ttrue\thigh_support\t",
            )
        )
        + "\n",
        encoding="utf-8",
    )
    (biological_dir / "biological_evidence_graph_nodes.tsv").write_text(
        "\n".join(
            (
                "node_id\tentity_type\tentity_ref\tcontext_refs",
                "protein:P11111\tprotein\tP11111\t",
                "statistical_result:protein_card_1\tclaim\tprotein_card_1\tprotein:P11111",
            )
        )
        + "\n",
        encoding="utf-8",
    )

    report = review.build_result_explanation_report_from_artifacts(
        (
            review.ResultExplanationRequest(
                explanation_id="protein",
                explanation_kind=review.ResultExplanationKind.PROTEIN_RESULT,
                subject_id="P11111",
            ),
        ),
        biological_report_dir=biological_dir,
    )

    assert hasattr(review, "build_result_explanation_report_from_artifacts")
    assert review.ResultExplanationKind.PROTEIN_RESULT.value == "protein_result"
    assert report.summary.answered_explanation_count == 1
    assert "claim" in review.render_result_explanation_tsv(report)


def test_review_package_exports_analysis_recommendation_surface(tmp_path: Path) -> None:
    ptm_dir = tmp_path / "ptm_report"
    ptm_dir.mkdir()
    (ptm_dir / "ptm_evidence_cards.tsv").write_text(
        "\n".join(
            (
                "card_id\tsite_key\tprotein_ref\tcondition_a\tcondition_b\tadjusted_p_value\tlog2_fold_change\tcorrected_log2_fold_change\tlocalization_tier\tobserved_sample_count\tprotein_correction_status\tmechanism_reason_codes\twarning_codes\tclaim_ids\tsource_row_refs\tderived_no_source_reason",
                "ptm-card-1\tP11111:S5:Phospho\tP11111\tcontrol\ttreated\t0.03\t1.5\t\tmedium_confidence\t4\tnot_requested\tcontext_supported\t\tptm-claim-1\tptm_localization.tsv:4\t",
            )
        )
        + "\n",
        encoding="utf-8",
    )

    report = review.build_analysis_recommendation_report_from_artifacts(
        ptm_report_dir=ptm_dir,
    )

    assert hasattr(review, "build_analysis_recommendation_report_from_artifacts")
    assert review.AnalysisRecommendationKind.RUN_PTM_CORRECTION.value == "run_ptm_correction"
    assert report.summary.recommendation_count == 1
    assert "detected_condition_code" in review.render_analysis_recommendation_tsv(report)


def test_review_package_exports_compact_result_summary_surface() -> None:
    report = review.CompactResultSummaryReport(
        sections=(
            review.CompactResultSummarySection(
                section_kind=review.CompactResultSummarySectionKind.SAMPLE_QC,
                title="Sample QC",
                entries=(
                    review.CompactResultSummaryEntry(
                        entry_id="sample-qc-1",
                        section_kind=review.CompactResultSummarySectionKind.SAMPLE_QC,
                        summary_text="One governed QC entry was retained.",
                        note="sample QC statements remain tied to explicit QC ledgers",
                    ),
                ),
            ),
        ),
        overview=review.CompactResultSummaryOverview(
            section_count=1,
            entry_count=1,
            sample_qc_entry_count=1,
            strongest_finding_count=0,
            weak_finding_count=0,
            failed_assumption_count=0,
            next_validation_target_count=0,
        ),
        note="compact summaries remain evidence constrained",
    )

    assert hasattr(review, "build_compact_result_summary_report_from_artifacts")
    assert review.CompactResultSummarySectionKind.SAMPLE_QC.value == "sample_qc"
    assert "Sample QC" in review.render_compact_result_summary_markdown(report)
    assert "summary_text" in review.render_compact_result_summary_entry_tsv(report)


def test_review_package_exports_belief_audit_surface() -> None:
    report = review.BeliefAuditReport(
        entries=(
            review.BeliefAuditEntry(
                audit_id="protein:protein-card-1",
                subject_kind=review.BeliefAuditSubjectKind.PROTEIN,
                subject_id="protein-card-1",
                subject_label="P11111",
                claim="Protein P11111 changed between control and treatment.",
                decision="retained as a significant protein result",
                confidence="moderate",
                why_believed="log2 fold change and peptide support were retained on the governed card",
                what_weakens="warning code low_sequence_coverage reduced confidence",
                what_would_falsify="A rerun that removes statistical support would falsify this protein conclusion.",
                result_surfaces=("biological_protein_cards",),
                result_row_ids=("protein-card-1",),
                graph_node_ids=("protein:P11111",),
                note="belief audit remains tied to governed row and graph ids",
            ),
        ),
        summary=review.BeliefAuditSummary(
            entry_count=1,
            protein_entry_count=1,
            ptm_site_entry_count=0,
            pathway_entry_count=0,
            regulator_entry_count=0,
            biomarker_entry_count=0,
            qc_decision_entry_count=0,
        ),
        note="belief audits remain challengeable and traceable to governed artifacts",
    )

    assert hasattr(review, "build_belief_audit_report_from_artifacts")
    assert review.BeliefAuditSubjectKind.PROTEIN.value == "protein"
    assert "<h1>Belief Audit</h1>" in review.render_belief_audit_html(report)
    assert "what_would_falsify" in review.render_belief_audit_tsv(report)


def test_review_package_exports_failure_explanation_surface() -> None:
    report = review.build_failure_explanation_report(
        (
            review.FailureExplanationRequest(
                failure_id="design",
                workflow_name="biological-report",
                failure_text="design table contains rejected rows",
            ),
        )
    )

    assert hasattr(review, "build_failure_explanation_report")
    assert review.FailureExplanationCategory.INVALID_DESIGN.value == "invalid_design"
    assert report.summary.explained_count == 1
    assert (
        "scientific_condition_code" in review.render_failure_explanation_tsv(report)
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


def test_review_package_exports_evidence_graph_external_export_surface() -> None:
    builder = review.ProteomicsEvidenceGraphBuilder()
    sample = builder.add_sample("S1", label="sample S1")
    run = builder.add_run("R1", label="run R1")
    protein = builder.add_protein(
        "P11111",
        label="P11111",
        trust_class="reviewed",
        contradiction_ids=("cx-1",),
    )
    peptide = builder.add_peptide("PEPTIDE", label="PEPTIDE", trust_class="high")
    builder.add_sample_contains_run(
        sample.node_id,
        run.node_id,
        source_row_ref="design.tsv:2",
        confidence=1.0,
        reason="sample table assigns run R1 to sample S1",
    )
    builder.add_peptide_quantifies_protein(
        peptide.node_id,
        protein.node_id,
        source_row_ref="protein_matrix.tsv:4",
        confidence=0.93,
        reason="strong peptide quantifies protein P11111",
    )

    bundle = review.export_proteomics_evidence_graph(builder.build())

    assert hasattr(review, "export_proteomics_evidence_graph")
    assert hasattr(review, "render_proteomics_evidence_graph_nodes_tsv")
    assert hasattr(review, "render_proteomics_evidence_graph_edges_tsv")
    assert hasattr(review, "render_proteomics_evidence_graph_compact_json")
    assert bundle.node_count == 4
    assert bundle.edge_count == 2
    assert bundle.contradiction_node_count == 1


def test_review_package_exports_evidence_aware_ranking_surface() -> None:
    report = review.build_evidence_aware_ranking_report(
        (
            review.EvidenceAwareRankingCandidate(
                candidate_id="protein:P11111",
                entity_kind=review.EvidenceAwareRankingEntityKind.PROTEIN,
                display_label="P11111",
                effect_size=1.2,
                adjusted_p_value=0.01,
                abundance_value=11.0,
                support_count=3,
                annotation_label="kinase",
                effect_score=0.6,
                significance_score=0.33,
                abundance_score=0.8,
                support_score=0.75,
                qc_score=0.8,
                annotation_score=0.7,
                reproducibility_score=0.8,
                confidence_score=0.85,
                note="supported protein result",
            ),
        )
    )

    assert hasattr(review, "build_evidence_aware_ranking_report")
    assert hasattr(review, "render_evidence_aware_ranking_tsv")
    assert report.summary.protein_entry_count == 1
    assert "priority_rank" in review.render_evidence_aware_ranking_tsv(report)


def test_review_package_exports_biological_claim_validation_surface() -> None:
    report = review.build_biological_claim_validation_report(
        (
            review.BiologicalClaimCandidate(
                claim_id="protein-claim:P11111",
                claim_kind=review.BiologicalClaimKind.PROTEIN_ABUNDANCE_CHANGE,
                subject_id="P11111",
                subject_label="TP53",
                claim_text="Protein TP53 decreased in treatment vs control",
                condition_a="control",
                condition_b="treatment",
                asserted_direction=review.BiologicalClaimDirection.DOWN,
                significant=True,
                adjusted_p_value=0.01,
                effect_size=1.1,
                robustness_score=0.8,
                evidence_tier=review.FinalClaimEvidenceTier.HIGH_CONFIDENCE,
                confidence_tier=review.EvidenceGraphConfidenceTier.HIGH,
                source_ids=("protein-mechanism-card:P11111",),
                source_row_refs=("protein_stats.tsv:4",),
                note="strong protein evidence",
            ),
        )
    )

    assert hasattr(review, "build_biological_claim_validation_report")
    assert hasattr(review, "render_supported_biological_claim_tsv")
    assert report.summary.supported_claim_count == 1
    assert "claim_id\tclaim_kind\tstatus" in review.render_supported_biological_claim_tsv(
        report
    )


def test_review_package_exports_biological_hypothesis_surface() -> None:
    report = review.build_biological_hypothesis_report(
        (
            review.BiologicalHypothesisCandidate(
                hypothesis_id="protein-hypothesis:P11111",
                hypothesis_kind=review.BiologicalHypothesisKind.PROTEIN_MECHANISM,
                subject_id="P11111",
                subject_label="TP53",
                claim="TP53 decreased in treatment vs control",
                supporting_protein_refs=("P11111",),
                evidence_node_ids=(
                    "protein:P11111",
                    "statistical_result:protein:control_vs_treatment:P11111",
                ),
                base_confidence_score=0.78,
                source_ids=("protein-mechanism-card:P11111",),
                note="graph-backed protein mechanism support",
            ),
        )
    )

    assert hasattr(review, "build_biological_hypothesis_report")
    assert hasattr(review, "render_biological_hypothesis_tsv")
    assert report.summary.hypothesis_count == 1
    assert "evidence_node_ids" in review.render_biological_hypothesis_tsv(report)


def test_review_package_exports_biomarker_candidate_ranking_surface() -> None:
    report = review.build_biomarker_candidate_ranking_report(
        (
            review.BiomarkerCandidateRankingInput(
                candidate_id="protein:P11111",
                candidate_kind=review.BiomarkerCandidateKind.PROTEIN,
                display_label="TP53",
                target_protein_ref="P11111",
                effect_size=1.4,
                adjusted_p_value=0.01,
                support_count=4,
                effect_score=0.7,
                robustness_score=0.82,
                detectability_score=0.9,
                specificity_score=0.88,
                annotation_score=0.65,
                assay_feasibility_score=0.86,
                sample_qc_score=0.9,
                annotation_labels=("pathway:damage_response", "region:binding_site"),
                source_ids=("biological-card:P11111",),
                note="strong validation-ready protein candidate",
            ),
        )
    )

    assert hasattr(review, "build_biomarker_candidate_ranking_report")
    assert hasattr(review, "render_biomarker_candidate_ranking_tsv")
    assert report.summary.candidate_count == 1
    assert "rank_reason_codes" in review.render_biomarker_candidate_ranking_tsv(report)

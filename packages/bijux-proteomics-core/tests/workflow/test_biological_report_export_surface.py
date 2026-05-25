# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.io.formats import parse_experimental_design_table
from bijux_proteomics.workflow import (
    build_biological_result_report_bundle,
    export_biological_result_report_bundle,
)


def _fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "workflow" / name


def test_biological_report_export_writes_differential_annotation_enrichment_and_plot_assets(
    tmp_path: Path,
) -> None:
    design_entries = tuple(
        parse_experimental_design_table(
            _fixture("biological_report.design.tsv")
        ).accepted_entries
    )
    report = build_biological_result_report_bundle(
        _fixture("biological_report_features.tsv"),
        design_entries,
        proteins_fasta_path=_fixture("biological_report_reference.fasta"),
        context_annotation_tsv_path=_fixture("biological_report_context.tsv"),
        go_annotation_tsv_path=_fixture("biological_report_go.tsv"),
        pathway_membership_tsv_path=_fixture("biological_report_pathways.tsv"),
        complex_membership_tsv_path=_fixture("biological_report_complexes.tsv"),
        condition_a="control",
        condition_b="treatment",
    )

    manifest = export_biological_result_report_bundle(
        report,
        tmp_path / "biological_report",
    )
    output_dir = tmp_path / "biological_report"

    assert manifest.claim_validation_included is True
    assert manifest.hypothesis_summary_included is True
    assert manifest.context_summary_included is True
    assert manifest.go_summary_included is True
    assert manifest.pathway_summary_included is True
    assert manifest.complex_summary_included is True
    assert (output_dir / "manifest.json").exists()
    assert (output_dir / "inputs").is_dir()
    assert (output_dir / "qc").is_dir()
    assert (output_dir / "evidence").is_dir()
    assert (output_dir / "matrices").is_dir()
    assert (output_dir / "stats").is_dir()
    assert (output_dir / "biology").is_dir()
    assert (output_dir / "cards").is_dir()
    assert (output_dir / "reports").is_dir()
    assert (output_dir / "reports" / manifest.artifacts.summary_tsv).exists()
    assert (output_dir / "cards" / manifest.artifacts.protein_card_tsv).exists()
    assert (output_dir / "evidence" / manifest.artifacts.supported_claim_tsv).exists()
    assert (output_dir / "matrices" / manifest.artifacts.pathway_activity_matrix_tsv).exists()
    assert (output_dir / manifest.artifacts.summary_tsv).exists()
    assert (output_dir / manifest.artifacts.differential_tsv).exists()
    assert (output_dir / manifest.artifacts.protein_card_summary_tsv).exists()
    assert (output_dir / manifest.artifacts.protein_card_tsv).exists()
    assert (output_dir / manifest.artifacts.protein_mechanism_card_summary_tsv).exists()
    assert (output_dir / manifest.artifacts.protein_mechanism_card_tsv).exists()
    assert (output_dir / manifest.artifacts.evidence_graph_nodes_tsv).exists()
    assert (output_dir / manifest.artifacts.evidence_graph_edges_tsv).exists()
    assert (output_dir / manifest.artifacts.experiment_confidence_summary_tsv).exists()
    assert (
        output_dir / manifest.artifacts.experiment_confidence_components_tsv
    ).exists()
    assert (output_dir / manifest.artifacts.section_confidence_tsv).exists()
    assert (output_dir / manifest.artifacts.evidence_aware_ranking_tsv).exists()
    assert (output_dir / manifest.artifacts.claim_validation_summary_tsv).exists()
    assert (output_dir / manifest.artifacts.supported_claim_tsv).exists()
    assert (output_dir / manifest.artifacts.rejected_claim_tsv).exists()
    assert (output_dir / manifest.artifacts.biological_hypothesis_summary_tsv).exists()
    assert (output_dir / manifest.artifacts.biological_hypothesis_tsv).exists()
    assert (
        output_dir / manifest.artifacts.rejected_hypothesis_candidate_tsv
    ).exists()
    assert (output_dir / manifest.artifacts.foreground_background_summary_tsv).exists()
    assert (output_dir / manifest.artifacts.foreground_background_entry_tsv).exists()
    assert (output_dir / manifest.artifacts.foreground_background_issue_tsv).exists()
    assert (output_dir / manifest.artifacts.annotation_tsv).exists()
    assert (output_dir / manifest.artifacts.context_summary_tsv).exists()
    assert (output_dir / manifest.artifacts.context_mapping_tsv).exists()
    assert (output_dir / manifest.artifacts.context_term_tsv).exists()
    assert (output_dir / manifest.artifacts.context_unmapped_tsv).exists()
    assert (output_dir / manifest.artifacts.context_rejected_tsv).exists()
    assert (output_dir / manifest.artifacts.pathway_activity_summary_tsv).exists()
    assert (output_dir / manifest.artifacts.pathway_activity_matrix_tsv).exists()
    assert (output_dir / manifest.artifacts.pathway_activity_sample_score_tsv).exists()
    assert (output_dir / manifest.artifacts.pathway_activity_condition_score_tsv).exists()
    assert (
        output_dir / manifest.artifacts.pathway_activity_condition_comparison_tsv
    ).exists()
    assert (
        output_dir / manifest.artifacts.pathway_activity_member_contribution_tsv
    ).exists()
    assert (output_dir / manifest.artifacts.pathway_activity_unresolved_member_tsv).exists()
    assert (output_dir / manifest.artifacts.complex_activity_summary_tsv).exists()
    assert (output_dir / manifest.artifacts.complex_activity_matrix_tsv).exists()
    assert (output_dir / manifest.artifacts.complex_activity_sample_score_tsv).exists()
    assert (output_dir / manifest.artifacts.complex_activity_condition_score_tsv).exists()
    assert (
        output_dir / manifest.artifacts.complex_activity_condition_comparison_tsv
    ).exists()
    assert (
        output_dir / manifest.artifacts.complex_activity_member_contribution_tsv
    ).exists()
    assert (output_dir / manifest.artifacts.complex_activity_unresolved_member_tsv).exists()
    assert (output_dir / manifest.artifacts.go_term_tsv).exists()
    assert (output_dir / manifest.artifacts.pathway_entry_tsv).exists()
    assert (output_dir / manifest.artifacts.complex_entry_tsv).exists()
    assert (output_dir / manifest.artifacts.heatmap_matrix_tsv).exists()
    assert (output_dir / manifest.artifacts.sample_pca_scores_tsv).exists()
    assert (output_dir / manifest.artifacts.volcano_tsv).exists()
    assert (output_dir / manifest.artifacts.volcano_json).exists()
    assert (output_dir / manifest.artifacts.volcano_svg).exists()
    assert (output_dir / manifest.artifacts.volcano_html).exists()
    assert (output_dir / manifest.artifacts.report_html).exists()
    assert "annotation_entry_count" in (
        output_dir / manifest.artifacts.summary_tsv
    ).read_text(encoding="utf-8")
    assert "protein_card_count" in (
        output_dir / manifest.artifacts.summary_tsv
    ).read_text(encoding="utf-8")
    assert "experiment_confidence_score" in (
        output_dir / manifest.artifacts.summary_tsv
    ).read_text(encoding="utf-8")
    assert "overall_score" in (
        output_dir / manifest.artifacts.experiment_confidence_summary_tsv
    ).read_text(encoding="utf-8")
    assert "priority_rank" in (
        output_dir / manifest.artifacts.evidence_aware_ranking_tsv
    ).read_text(encoding="utf-8")
    assert "supported_claim_count" in (
        output_dir / manifest.artifacts.claim_validation_summary_tsv
    ).read_text(encoding="utf-8")
    assert "claim_text" in (
        output_dir / manifest.artifacts.supported_claim_tsv
    ).read_text(encoding="utf-8")
    assert "reason_codes" in (
        output_dir / manifest.artifacts.rejected_claim_tsv
    ).read_text(encoding="utf-8")
    assert "hypothesis_count" in (
        output_dir / manifest.artifacts.biological_hypothesis_summary_tsv
    ).read_text(encoding="utf-8")
    assert "evidence_node_ids" in (
        output_dir / manifest.artifacts.biological_hypothesis_tsv
    ).read_text(encoding="utf-8")
    assert "rejection_reason" in (
        output_dir / manifest.artifacts.rejected_hypothesis_candidate_tsv
    ).read_text(encoding="utf-8")
    assert "foreground_source_kind" in (
        output_dir / manifest.artifacts.foreground_background_summary_tsv
    ).read_text(encoding="utf-8")
    assert "pathway_count" in (
        output_dir / manifest.artifacts.pathway_activity_summary_tsv
    ).read_text(encoding="utf-8")
    assert "pathway_id\tpathway_name\tsource_name\tsource_accession\tC1\tC2\tC3\tT1\tT2\tT3" in (
        output_dir / manifest.artifacts.pathway_activity_matrix_tsv
    ).read_text(encoding="utf-8")
    assert "member_kind\tmember_id\tresolved_protein_refs" in (
        output_dir / manifest.artifacts.pathway_activity_member_contribution_tsv
    ).read_text(encoding="utf-8")
    assert "complex_count" in (
        output_dir / manifest.artifacts.complex_activity_summary_tsv
    ).read_text(encoding="utf-8")
    assert "complex_id\tcomplex_name\tsource_name\tsource_accession\tC1\tC2\tC3\tT1\tT2\tT3" in (
        output_dir / manifest.artifacts.complex_activity_matrix_tsv
    ).read_text(encoding="utf-8")
    assert "limiting_member_ids" in (
        output_dir / manifest.artifacts.complex_activity_sample_score_tsv
    ).read_text(encoding="utf-8")
    assert "member_kind\tmember_id\tresolved_protein_refs" in (
        output_dir / manifest.artifacts.complex_activity_member_contribution_tsv
    ).read_text(encoding="utf-8")
    assert "set_role" in (
        output_dir / manifest.artifacts.foreground_background_entry_tsv
    ).read_text(encoding="utf-8")
    assert "code\tseverity\tmessage" in (
        output_dir / manifest.artifacts.foreground_background_issue_tsv
    ).read_text(encoding="utf-8")
    assert "pathway" in (
        output_dir / manifest.artifacts.evidence_aware_ranking_tsv
    ).read_text(encoding="utf-8")
    assert "metadata_validity" in (
        output_dir / manifest.artifacts.experiment_confidence_components_tsv
    ).read_text(encoding="utf-8")
    assert "section_key\tsection_title\tconfidence_label\trationale" in (
        output_dir / manifest.artifacts.section_confidence_tsv
    ).read_text(encoding="utf-8")
    assert "card_id" in (
        output_dir / manifest.artifacts.protein_card_tsv
    ).read_text(encoding="utf-8")
    assert "identity_level" in (
        output_dir / manifest.artifacts.protein_card_tsv
    ).read_text(encoding="utf-8")
    assert "functional_regions" in (
        output_dir / manifest.artifacts.protein_card_tsv
    ).read_text(encoding="utf-8")
    assert "proteogenomic_support_class" in (
        output_dir / manifest.artifacts.protein_card_tsv
    ).read_text(encoding="utf-8")
    assert "graph_claim_node_id" in (
        output_dir / manifest.artifacts.protein_card_tsv
    ).read_text(encoding="utf-8")
    assert "node_id\tentity_type\tentity_ref" in (
        output_dir / manifest.artifacts.evidence_graph_nodes_tsv
    ).read_text(encoding="utf-8")
    assert "source_node_id\ttarget_node_id\trelation" in (
        output_dir / manifest.artifacts.evidence_graph_edges_tsv
    ).read_text(encoding="utf-8")
    assert "representative_protein_ref" in (
        output_dir / manifest.artifacts.protein_mechanism_card_tsv
    ).read_text(encoding="utf-8")
    assert "evidence_tier" in (
        output_dir / manifest.artifacts.protein_mechanism_card_tsv
    ).read_text(encoding="utf-8")
    assert "downgrade_reasons" in (
        output_dir / manifest.artifacts.protein_mechanism_card_tsv
    ).read_text(encoding="utf-8")
    assert "statistical_result:" in (
        output_dir / manifest.artifacts.protein_card_tsv
    ).read_text(encoding="utf-8")
    assert "annotation_status" in (
        output_dir / manifest.artifacts.annotation_tsv
    ).read_text(encoding="utf-8")
    assert "context_entry_count" in (
        output_dir / manifest.artifacts.summary_tsv
    ).read_text(encoding="utf-8")
    assert "context_kind" in (
        output_dir / manifest.artifacts.context_mapping_tsv
    ).read_text(encoding="utf-8")
    assert "supporting_protein_refs" in (
        output_dir / manifest.artifacts.context_term_tsv
    ).read_text(encoding="utf-8")
    assert "gene_symbol" in (
        output_dir / manifest.artifacts.annotation_tsv
    ).read_text(encoding="utf-8")
    assert "go_term_id" in (
        output_dir / manifest.artifacts.go_term_tsv
    ).read_text(encoding="utf-8")
    assert "pathway_id" in (
        output_dir / manifest.artifacts.pathway_entry_tsv
    ).read_text(encoding="utf-8")
    assert "complex_id" in (
        output_dir / manifest.artifacts.complex_entry_tsv
    ).read_text(encoding="utf-8")
    assert "raw_p_value" in (
        output_dir / manifest.artifacts.volcano_tsv
    ).read_text(encoding="utf-8")
    assert "Protein mechanism cards" in (
        output_dir / manifest.artifacts.report_html
    ).read_text(encoding="utf-8")
    assert "Experiment confidence" in (
        output_dir / manifest.artifacts.report_html
    ).read_text(encoding="utf-8")
    assert "Section confidence" in (
        output_dir / manifest.artifacts.report_html
    ).read_text(encoding="utf-8")
    assert "Evidence-aware ranking" in (
        output_dir / manifest.artifacts.report_html
    ).read_text(encoding="utf-8")
    assert "Validated biological claims" in (
        output_dir / manifest.artifacts.report_html
    ).read_text(encoding="utf-8")
    assert "Biological hypotheses" in (
        output_dir / manifest.artifacts.report_html
    ).read_text(encoding="utf-8")
    assert "Biological hypotheses [exploratory]" in (
        output_dir / manifest.artifacts.report_html
    ).read_text(encoding="utf-8")
    assert "Enrichment foreground/background model" in (
        output_dir / manifest.artifacts.report_html
    ).read_text(encoding="utf-8")
    assert "Pathway activity" in (
        output_dir / manifest.artifacts.report_html
    ).read_text(encoding="utf-8")


def test_biological_report_export_writes_tissue_context_artifacts_and_html(
    tmp_path: Path,
) -> None:
    design_entries = tuple(
        parse_experimental_design_table(
            _fixture("biological_report_tissue_context.design.tsv")
        ).accepted_entries
    )
    report = build_biological_result_report_bundle(
        _fixture("biological_report_features.tsv"),
        design_entries,
        proteins_fasta_path=_fixture("biological_report_reference.fasta"),
        context_annotation_tsv_path=_fixture("biological_report_tissue_markers.tsv"),
        condition_a="control",
        condition_b="treatment",
    )

    manifest = export_biological_result_report_bundle(
        report,
        tmp_path / "biological_report_tissue_context",
    )
    output_dir = tmp_path / "biological_report_tissue_context"

    assert manifest.tissue_context_summary_included is True
    assert report.summary.tissue_mismatch_warning_count == 1
    assert (output_dir / manifest.artifacts.tissue_context_summary_tsv).exists()
    assert (
        output_dir / manifest.artifacts.tissue_context_sample_consistency_tsv
    ).exists()
    assert (
        output_dir / manifest.artifacts.tissue_context_unexpected_signal_tsv
    ).exists()
    assert (
        output_dir / manifest.artifacts.tissue_context_interpretation_tsv
    ).exists()
    assert "mismatch_warning_count" in (
        output_dir / manifest.artifacts.tissue_context_summary_tsv
    ).read_text(encoding="utf-8")
    assert "unexpected_marker_context_dominates" in (
        output_dir / manifest.artifacts.tissue_context_sample_consistency_tsv
    ).read_text(encoding="utf-8")
    assert "context_kind" in (
        output_dir / manifest.artifacts.tissue_context_unexpected_signal_tsv
    ).read_text(encoding="utf-8")
    assert "dominant_unexpected_context_id" in (
        output_dir / manifest.artifacts.tissue_context_interpretation_tsv
    ).read_text(encoding="utf-8")
    assert "Tissue and cell-type context" in (
        output_dir / manifest.artifacts.report_html
    ).read_text(encoding="utf-8")
    assert "Tissue mismatch warnings" in (
        output_dir / manifest.artifacts.report_html
    ).read_text(encoding="utf-8")


def test_biological_report_export_writes_cohort_stratification_artifacts_and_html(
    tmp_path: Path,
) -> None:
    design_entries = tuple(
        parse_experimental_design_table(
            _fixture("biological_report_cohort_stratification.design.tsv")
        ).accepted_entries
    )
    report = build_biological_result_report_bundle(
        _fixture("biological_report_cohort_stratification_features.tsv"),
        design_entries,
        proteins_fasta_path=_fixture("biological_report_reference.fasta"),
        condition_a="control",
        condition_b="treatment",
    )

    manifest = export_biological_result_report_bundle(
        report,
        tmp_path / "biological_report_cohort_stratification",
    )
    output_dir = tmp_path / "biological_report_cohort_stratification"

    assert manifest.cohort_stratification_summary_included is True
    assert report.cohort_stratification_report is not None
    assert (
        output_dir / manifest.artifacts.cohort_stratification_summary_tsv
    ).exists()
    assert (output_dir / manifest.artifacts.cohort_stratum_tsv).exists()
    assert (output_dir / manifest.artifacts.cohort_subgroup_effect_tsv).exists()
    assert (
        output_dir / manifest.artifacts.cohort_interaction_candidate_tsv
    ).exists()
    assert "blocked_stratum_count" in (
        output_dir / manifest.artifacts.cohort_stratification_summary_tsv
    ).read_text(encoding="utf-8")
    assert "blocked_low_subgroup_sample_count" in (
        output_dir / manifest.artifacts.cohort_stratum_tsv
    ).read_text(encoding="utf-8")
    assert "robustness_score" in (
        output_dir / manifest.artifacts.cohort_subgroup_effect_tsv
    ).read_text(encoding="utf-8")
    assert "direction_conflict" in (
        output_dir / manifest.artifacts.cohort_interaction_candidate_tsv
    ).read_text(encoding="utf-8")
    assert "Cohort stratification" in (
        output_dir / manifest.artifacts.report_html
    ).read_text(encoding="utf-8")


def test_biological_report_export_writes_compartment_biology_assets(
    tmp_path: Path,
) -> None:
    design_entries = tuple(
        parse_experimental_design_table(
            _fixture("biological_report.design.tsv")
        ).accepted_entries
    )
    report = build_biological_result_report_bundle(
        _fixture("biological_report_features.tsv"),
        design_entries,
        proteins_fasta_path=_fixture("biological_report_reference.fasta"),
        context_annotation_tsv_path=_fixture("biological_report_compartments.tsv"),
        condition_a="control",
        condition_b="treatment",
    )

    manifest = export_biological_result_report_bundle(
        report,
        tmp_path / "biological_compartment_report",
    )
    output_dir = tmp_path / "biological_compartment_report"

    assert report.compartment_biology_report is not None
    assert (output_dir / manifest.artifacts.compartment_biology_summary_tsv).exists()
    assert (output_dir / manifest.artifacts.compartment_enrichment_tsv).exists()
    assert (output_dir / manifest.artifacts.compartment_activity_matrix_tsv).exists()
    assert (
        output_dir / manifest.artifacts.compartment_activity_sample_score_tsv
    ).exists()
    assert (
        output_dir / manifest.artifacts.compartment_activity_condition_score_tsv
    ).exists()
    assert (
        output_dir / manifest.artifacts.compartment_activity_condition_comparison_tsv
    ).exists()
    assert (
        output_dir / manifest.artifacts.compartment_activity_unresolved_member_tsv
    ).exists()
    assert (
        output_dir / manifest.artifacts.compartment_unknown_localization_tsv
    ).exists()
    assert "compartment_count" in (
        output_dir / manifest.artifacts.compartment_biology_summary_tsv
    ).read_text(encoding="utf-8")
    assert "compartment_id\tcompartment_name\tsource_name\tsource_accession\tC1\tC2\tC3\tT1\tT2\tT3" in (
        output_dir / manifest.artifacts.compartment_activity_matrix_tsv
    ).read_text(encoding="utf-8")
    assert "localization_scope\tprotein_ref\treason" == (
        output_dir / manifest.artifacts.compartment_unknown_localization_tsv
    ).read_text(encoding="utf-8").splitlines()[0]
    assert "Compartment biology" in (
        output_dir / manifest.artifacts.report_html
    ).read_text(encoding="utf-8")
    assert "Complex activity" in (
        output_dir / manifest.artifacts.report_html
    ).read_text(encoding="utf-8")
    assert "Low-confidence sample scores" in (
        output_dir / manifest.artifacts.report_html
    ).read_text(encoding="utf-8")
    assert "Valid for enrichment" in (
        output_dir / manifest.artifacts.report_html
    ).read_text(encoding="utf-8")
    assert "Graph claim" in (
        output_dir / manifest.artifacts.report_html
    ).read_text(encoding="utf-8")
    assert "Identity" in (
        output_dir / manifest.artifacts.report_html
    ).read_text(encoding="utf-8")
    assert "Evidence tier" in (
        output_dir / manifest.artifacts.report_html
    ).read_text(encoding="utf-8")
    assert "Downgrade reasons" in (
        output_dir / manifest.artifacts.report_html
    ).read_text(encoding="utf-8")
    assert "statistical_result:" in (
        output_dir / manifest.artifacts.report_html
    ).read_text(encoding="utf-8")
    assert "Biological result report" in (
        output_dir / manifest.artifacts.report_html
    ).read_text(encoding="utf-8")


def test_biological_report_export_writes_regulator_inference_assets(
    tmp_path: Path,
) -> None:
    design_entries = tuple(
        parse_experimental_design_table(
            _fixture("biological_report.design.tsv")
        ).accepted_entries
    )
    report = build_biological_result_report_bundle(
        _fixture("biological_report_features.tsv"),
        design_entries,
        proteins_fasta_path=_fixture("biological_report_reference.fasta"),
        pathway_membership_tsv_path=_fixture("biological_report_pathways.tsv"),
        regulator_evidence_tsv_path=_fixture("biological_report_regulator_evidence.tsv"),
        regulator_site_signal_tsv_path=_fixture("biological_report_regulator_sites.tsv"),
        condition_a="control",
        condition_b="treatment",
    )

    manifest = export_biological_result_report_bundle(
        report,
        tmp_path / "biological_regulator_report",
    )
    output_dir = tmp_path / "biological_regulator_report"

    assert report.regulator_inference_report is not None
    assert (output_dir / manifest.artifacts.regulator_inference_summary_tsv).exists()
    assert (output_dir / manifest.artifacts.regulator_inference_tsv).exists()
    assert (output_dir / manifest.artifacts.regulator_inference_unresolved_tsv).exists()
    assert (output_dir / manifest.artifacts.regulator_evidence_rejected_tsv).exists()
    assert "entry_count" in (
        output_dir / manifest.artifacts.regulator_inference_summary_tsv
    ).read_text(encoding="utf-8")
    assert "signal_surface" in (
        output_dir / manifest.artifacts.regulator_inference_tsv
    ).read_text(encoding="utf-8")
    assert "target_field" in (
        output_dir / manifest.artifacts.regulator_inference_unresolved_tsv
    ).read_text(encoding="utf-8")
    assert "row_number\treason\tvalues" == (
        output_dir / manifest.artifacts.regulator_evidence_rejected_tsv
    ).read_text(encoding="utf-8").splitlines()[0]
    assert "Regulator inference" in (
        output_dir / manifest.artifacts.report_html
    ).read_text(encoding="utf-8")


def test_biological_report_export_writes_drug_target_assets(
    tmp_path: Path,
) -> None:
    design_entries = tuple(
        parse_experimental_design_table(
            _fixture("biological_report.design.tsv")
        ).accepted_entries
    )
    report = build_biological_result_report_bundle(
        _fixture("biological_report_features.tsv"),
        design_entries,
        proteins_fasta_path=_fixture("biological_report_reference.fasta"),
        context_annotation_tsv_path=_fixture("biological_report_drug_targets.tsv"),
        pathway_membership_tsv_path=_fixture("biological_report_pathways.tsv"),
        condition_a="control",
        condition_b="treatment",
    )

    manifest = export_biological_result_report_bundle(
        report,
        tmp_path / "biological_drug_target_report",
    )
    output_dir = tmp_path / "biological_drug_target_report"

    assert report.drug_target_report is not None
    assert manifest.drug_target_summary_included is True
    assert (output_dir / manifest.artifacts.drug_target_summary_tsv).exists()
    assert (output_dir / manifest.artifacts.drug_target_tsv).exists()
    assert "drug_count" in (
        output_dir / manifest.artifacts.drug_target_summary_tsv
    ).read_text(encoding="utf-8")
    assert "relationship" in (
        output_dir / manifest.artifacts.drug_target_tsv
    ).read_text(encoding="utf-8")
    assert "indirect_pathway_neighbor" in (
        output_dir / manifest.artifacts.drug_target_tsv
    ).read_text(encoding="utf-8")
    assert "Drug-target interpretation" in (
        output_dir / manifest.artifacts.report_html
    ).read_text(encoding="utf-8")


def test_biological_report_export_writes_disease_phenotype_assets(
    tmp_path: Path,
) -> None:
    design_entries = tuple(
        parse_experimental_design_table(
            _fixture("biological_report.design.tsv")
        ).accepted_entries
    )
    report = build_biological_result_report_bundle(
        _fixture("biological_report_features.tsv"),
        design_entries,
        proteins_fasta_path=_fixture("biological_report_reference.fasta"),
        context_annotation_tsv_path=_fixture("biological_report_disease_phenotype.tsv"),
        condition_a="control",
        condition_b="treatment",
    )

    manifest = export_biological_result_report_bundle(
        report,
        tmp_path / "biological_disease_phenotype_report",
    )
    output_dir = tmp_path / "biological_disease_phenotype_report"

    assert report.disease_phenotype_report is not None
    assert manifest.disease_phenotype_summary_included is True
    assert (output_dir / manifest.artifacts.disease_phenotype_summary_tsv).exists()
    assert (output_dir / manifest.artifacts.disease_phenotype_term_tsv).exists()
    assert (
        output_dir / manifest.artifacts.disease_phenotype_unknown_annotation_tsv
    ).exists()
    assert "term_count" in (
        output_dir / manifest.artifacts.disease_phenotype_summary_tsv
    ).read_text(encoding="utf-8")
    assert "context_kind\tterm_id\tterm_name\tsource_name" in (
        output_dir / manifest.artifacts.disease_phenotype_term_tsv
    ).read_text(encoding="utf-8")
    assert "annotation_scope\tprotein_ref\treason" == (
        output_dir / manifest.artifacts.disease_phenotype_unknown_annotation_tsv
    ).read_text(encoding="utf-8").splitlines()[0]
    assert "Disease and phenotype interpretation" in (
        output_dir / manifest.artifacts.report_html
    ).read_text(encoding="utf-8")

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

    assert manifest.context_summary_included is True
    assert manifest.go_summary_included is True
    assert manifest.pathway_summary_included is True
    assert manifest.complex_summary_included is True
    assert (output_dir / manifest.artifacts.summary_tsv).exists()
    assert (output_dir / manifest.artifacts.differential_tsv).exists()
    assert (output_dir / manifest.artifacts.protein_card_summary_tsv).exists()
    assert (output_dir / manifest.artifacts.protein_card_tsv).exists()
    assert (output_dir / manifest.artifacts.protein_mechanism_card_summary_tsv).exists()
    assert (output_dir / manifest.artifacts.protein_mechanism_card_tsv).exists()
    assert (output_dir / manifest.artifacts.experiment_confidence_summary_tsv).exists()
    assert (
        output_dir / manifest.artifacts.experiment_confidence_components_tsv
    ).exists()
    assert (output_dir / manifest.artifacts.evidence_aware_ranking_tsv).exists()
    assert (output_dir / manifest.artifacts.foreground_background_summary_tsv).exists()
    assert (output_dir / manifest.artifacts.foreground_background_entry_tsv).exists()
    assert (output_dir / manifest.artifacts.foreground_background_issue_tsv).exists()
    assert (output_dir / manifest.artifacts.annotation_tsv).exists()
    assert (output_dir / manifest.artifacts.context_summary_tsv).exists()
    assert (output_dir / manifest.artifacts.context_mapping_tsv).exists()
    assert (output_dir / manifest.artifacts.context_term_tsv).exists()
    assert (output_dir / manifest.artifacts.context_unmapped_tsv).exists()
    assert (output_dir / manifest.artifacts.context_rejected_tsv).exists()
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
    assert "foreground_source_kind" in (
        output_dir / manifest.artifacts.foreground_background_summary_tsv
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
    assert "Evidence-aware ranking" in (
        output_dir / manifest.artifacts.report_html
    ).read_text(encoding="utf-8")
    assert "Enrichment foreground/background model" in (
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

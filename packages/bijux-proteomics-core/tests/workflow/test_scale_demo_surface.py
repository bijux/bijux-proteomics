# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.workflow.demo.scale_demo import (
    ScaleDemoConfig,
    render_scale_demo_stage_metrics_tsv,
    render_scale_demo_summary_tsv,
    render_scale_demo_validation_tsv,
    run_scale_demo,
)


def test_run_scale_demo_reports_runtime_memory_row_counts_and_validation(
    tmp_path: Path,
) -> None:
    output_dir = tmp_path / "scale_demo_run"
    report = run_scale_demo(
        ScaleDemoConfig(
            output_dir=output_dir,
            protein_count=24,
            peptides_per_protein=2,
            replicates_per_condition=3,
            pathway_count=8,
        )
    )

    assert report.summary.sample_count == 6
    assert report.summary.protein_count == 24
    assert report.summary.peptide_count == 48
    assert report.summary.generated_feature_row_count == 288
    assert report.summary.parsed_feature_row_count == 288
    assert report.summary.quant_value_row_count == 144
    assert report.summary.graph_node_count > 0
    assert report.summary.graph_edge_count > 0
    assert report.summary.differential_row_count == 24
    assert report.summary.protein_card_row_count == 24
    assert report.summary.exported_artifact_count > 0
    assert report.summary.outputs_validated is True

    assert len(report.stage_metrics) == 5
    assert all(metric.elapsed_seconds >= 0.0 for metric in report.stage_metrics)
    assert all(metric.peak_memory_mib >= 0.0 for metric in report.stage_metrics)
    assert report.validation.outputs_validated is True
    assert report.validation.manifest_artifact_count == report.summary.exported_artifact_count
    assert report.validation.graph_node_row_count == report.summary.graph_node_count
    assert report.validation.graph_edge_row_count == report.summary.graph_edge_count
    assert report.validation.protein_card_row_count == report.summary.protein_card_row_count
    assert report.validation.differential_row_count == report.summary.differential_row_count
    assert report.validation.supported_claim_row_count >= 1

    assert (output_dir / report.artifacts.feature_tsv).exists()
    assert (output_dir / report.artifacts.design_tsv).exists()
    assert (output_dir / report.artifacts.proteins_fasta).exists()
    assert (output_dir / report.artifacts.pathways_tsv).exists()
    assert (output_dir / report.artifacts.summary_tsv).exists()
    assert (output_dir / report.artifacts.stage_metrics_tsv).exists()
    assert (output_dir / report.artifacts.validation_tsv).exists()
    assert (output_dir / report.artifacts.report_json).exists()
    assert (output_dir / report.artifacts.biological_output_dir).is_dir()
    assert (output_dir / report.artifacts.biological_report_manifest_json).exists()
    assert (output_dir / report.artifacts.biological_report_html).exists()
    assert (output_dir / report.artifacts.evidence_graph_nodes_tsv).exists()
    assert (output_dir / report.artifacts.evidence_graph_edges_tsv).exists()
    assert (output_dir / report.artifacts.protein_cards_tsv).exists()
    assert (output_dir / report.artifacts.supported_claims_tsv).exists()

    assert "peak_memory_mib" in render_scale_demo_summary_tsv(report)
    assert "build_report_bundle" in render_scale_demo_stage_metrics_tsv(report)
    assert "outputs_validated" in render_scale_demo_validation_tsv(report)

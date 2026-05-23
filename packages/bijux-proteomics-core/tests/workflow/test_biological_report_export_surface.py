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

    assert manifest.go_summary_included is True
    assert manifest.pathway_summary_included is True
    assert manifest.complex_summary_included is True
    assert (output_dir / manifest.artifacts.summary_tsv).exists()
    assert (output_dir / manifest.artifacts.differential_tsv).exists()
    assert (output_dir / manifest.artifacts.annotation_tsv).exists()
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
    assert "annotation_status" in (
        output_dir / manifest.artifacts.annotation_tsv
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
    assert "Biological result report" in (
        output_dir / manifest.artifacts.report_html
    ).read_text(encoding="utf-8")

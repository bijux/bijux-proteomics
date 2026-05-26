# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.io.formats import parse_experimental_design_table
from bijux_proteomics.workflow import (
    build_maxquant_biological_workflow_bundle,
    export_maxquant_biological_workflow_bundle,
)


def _workflow_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "workflow" / name


def _bundle_fixture(name: str) -> Path:
    return _workflow_fixture("maxquant_biological") / name


def _interpretation_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "interpretation" / name


def test_maxquant_biological_workflow_export_writes_import_lfq_and_report_assets(
    tmp_path: Path,
) -> None:
    design_entries = tuple(
        parse_experimental_design_table(_bundle_fixture("design.tsv")).accepted_entries
    )
    report = build_maxquant_biological_workflow_bundle(
        _bundle_fixture("evidence.txt"),
        design_entries,
        peptides_txt_path=_bundle_fixture("peptides.txt"),
        protein_groups_txt_path=_bundle_fixture("proteinGroups.txt"),
        proteins_fasta_path=_workflow_fixture("biological_report_reference.fasta"),
        config_path=_bundle_fixture("maxquant_settings.txt"),
        annotation_tsv_path=_interpretation_fixture("protein_annotation_custom.tsv"),
        context_annotation_tsv_path=_workflow_fixture("biological_report_context.tsv"),
        go_annotation_tsv_path=_workflow_fixture("biological_report_go.tsv"),
        pathway_membership_tsv_path=_workflow_fixture("biological_report_pathways.tsv"),
        complex_membership_tsv_path=_workflow_fixture("biological_report_complexes.tsv"),
        condition_a="control",
        condition_b="treatment",
    )

    manifest = export_maxquant_biological_workflow_bundle(
        report,
        tmp_path / "maxquant_biological_report",
    )
    output_dir = tmp_path / "maxquant_biological_report"

    assert (output_dir / manifest.artifacts.summary_tsv).exists()
    assert (output_dir / manifest.artifacts.import_summary_tsv).exists()
    assert (output_dir / manifest.artifacts.evidence_tsv).exists()
    assert (output_dir / manifest.artifacts.peptides_tsv).exists()
    assert (output_dir / manifest.artifacts.protein_groups_tsv).exists()
    assert (output_dir / manifest.artifacts.accepted_protein_groups_tsv).exists()
    assert (output_dir / manifest.artifacts.filtered_protein_groups_tsv).exists()
    assert (output_dir / manifest.artifacts.enrichment_foreground_tsv).exists()
    assert (output_dir / manifest.artifacts.lfq_matrix_tsv).exists()
    assert (output_dir / manifest.artifacts.lfq_missingness_tsv).exists()
    assert (output_dir / manifest.artifacts.biological_manifest_json).exists()
    assert (output_dir / manifest.artifacts.protein_card_summary_tsv).exists()
    assert (output_dir / manifest.artifacts.protein_card_tsv).exists()
    assert (output_dir / manifest.artifacts.annotation_tsv).exists()
    assert (output_dir / manifest.artifacts.annotation_unmapped_tsv).exists()
    assert manifest.artifacts.context_mapping_tsv is not None
    assert manifest.artifacts.context_term_tsv is not None
    assert manifest.artifacts.context_unmapped_tsv is not None
    assert manifest.artifacts.context_rejected_tsv is not None
    assert (output_dir / manifest.artifacts.context_mapping_tsv).exists()
    assert (output_dir / manifest.artifacts.context_term_tsv).exists()
    assert (output_dir / manifest.artifacts.context_unmapped_tsv).exists()
    assert (output_dir / manifest.artifacts.context_rejected_tsv).exists()
    assert (output_dir / manifest.artifacts.report_html).exists()
    assert "enrichment_foreground_protein_count" in (
        output_dir / manifest.artifacts.summary_tsv
    ).read_text(encoding="utf-8")
    assert "accepted_protein_group_count" in (
        output_dir / manifest.artifacts.summary_tsv
    ).read_text(encoding="utf-8")
    assert "accepted_evidence_count" in (
        output_dir / manifest.artifacts.import_summary_tsv
    ).read_text(encoding="utf-8")
    assert "entity_id" in (
        output_dir / manifest.artifacts.filtered_protein_groups_tsv
    ).read_text(encoding="utf-8")
    foreground_tsv = (
        output_dir / manifest.artifacts.enrichment_foreground_tsv
    ).read_text(encoding="utf-8")
    assert "card_id" in foreground_tsv
    assert "\ttrue\t" not in foreground_tsv
    assert "entity_id" in (
        output_dir / manifest.artifacts.lfq_matrix_tsv
    ).read_text(encoding="utf-8")
    assert "observed" in (
        output_dir / manifest.artifacts.lfq_missingness_tsv
    ).read_text(encoding="utf-8")
    assert "card_id" in (
        output_dir / manifest.artifacts.protein_card_tsv
    ).read_text(encoding="utf-8")
    assert "context_kind" in (
        output_dir / manifest.artifacts.context_mapping_tsv
    ).read_text(encoding="utf-8")
    assert "Biological result report" in (
        output_dir / manifest.artifacts.report_html
    ).read_text(encoding="utf-8")

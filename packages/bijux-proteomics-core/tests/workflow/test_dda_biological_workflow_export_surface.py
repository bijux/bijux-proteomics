# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.identification import SearchAdapterKind
from bijux_proteomics.io.formats import parse_experimental_design_table
from bijux_proteomics.workflow import (
    build_dda_biological_workflow_bundle,
    export_dda_biological_workflow_bundle,
)


def _fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "workflow" / name


def test_dda_biological_workflow_export_writes_psm_parsimony_lfq_and_report_assets(
    tmp_path: Path,
) -> None:
    design_entries = tuple(
        parse_experimental_design_table(
            _fixture("biological_report.design.tsv")
        ).accepted_entries
    )
    report = build_dda_biological_workflow_bundle(
        _fixture("dda_biological_results.tsv"),
        design_entries,
        proteins_fasta_path=_fixture("biological_report_reference.fasta"),
        adapter_kind=SearchAdapterKind.GENERIC,
        generic_mapping_path=_fixture("dda_biological_mapping.json"),
        go_annotation_tsv_path=_fixture("biological_report_go.tsv"),
        pathway_membership_tsv_path=_fixture("biological_report_pathways.tsv"),
        complex_membership_tsv_path=_fixture("biological_report_complexes.tsv"),
        condition_a="control",
        condition_b="treatment",
    )

    manifest = export_dda_biological_workflow_bundle(
        report,
        tmp_path / "dda_biological_report",
    )
    output_dir = tmp_path / "dda_biological_report"

    assert (output_dir / manifest.artifacts.summary_tsv).exists()
    assert (output_dir / manifest.artifacts.accepted_psm_tsv).exists()
    assert (output_dir / manifest.artifacts.filtered_psm_tsv).exists()
    assert (output_dir / manifest.artifacts.parse_rejected_tsv).exists()
    assert (output_dir / manifest.artifacts.parsimony_summary_tsv).exists()
    assert (output_dir / manifest.artifacts.protein_lfq_matrix_tsv).exists()
    assert (output_dir / manifest.artifacts.protein_lfq_missingness_tsv).exists()
    assert (output_dir / manifest.artifacts.protein_lfq_missingness_mask_tsv).exists()
    assert (output_dir / manifest.artifacts.biological_manifest_json).exists()
    assert (output_dir / manifest.artifacts.report_html).exists()
    assert "accepted_psm_count" in (
        output_dir / manifest.artifacts.summary_tsv
    ).read_text(encoding="utf-8")
    assert "filter_reasons" in (
        output_dir / manifest.artifacts.filtered_psm_tsv
    ).read_text(encoding="utf-8")
    assert "selected_protein_count" in (
        output_dir / manifest.artifacts.parsimony_summary_tsv
    ).read_text(encoding="utf-8")
    assert "entity_id" in (
        output_dir / manifest.artifacts.protein_lfq_matrix_tsv
    ).read_text(encoding="utf-8")
    assert "observed" in (
        output_dir / manifest.artifacts.protein_lfq_missingness_mask_tsv
    ).read_text(encoding="utf-8")
    assert "Biological result report" in (
        output_dir / manifest.artifacts.report_html
    ).read_text(encoding="utf-8")


def test_dda_biological_workflow_export_writes_fragpipe_source_protein_discrepancy_assets(
    tmp_path: Path,
) -> None:
    design_entries = tuple(
        parse_experimental_design_table(
            _fixture("biological_report.design.tsv")
        ).accepted_entries
    )
    report = build_dda_biological_workflow_bundle(
        _fixture("fragpipe_biological_psms.tsv"),
        design_entries,
        proteins_fasta_path=_fixture("biological_report_reference.fasta"),
        adapter_kind=SearchAdapterKind.MSFRAGGER,
        dialect_id="fragpipe-psm",
        source_protein_tsv_path=_fixture("fragpipe_biological_proteins.tsv"),
        go_annotation_tsv_path=_fixture("biological_report_go.tsv"),
        pathway_membership_tsv_path=_fixture("biological_report_pathways.tsv"),
        complex_membership_tsv_path=_fixture("biological_report_complexes.tsv"),
        condition_a="control",
        condition_b="treatment",
    )

    manifest = export_dda_biological_workflow_bundle(
        report,
        tmp_path / "fragpipe_biological_report",
    )
    output_dir = tmp_path / "fragpipe_biological_report"

    assert manifest.artifacts.protein_group_discrepancy_tsv is not None
    assert (output_dir / manifest.artifacts.protein_group_discrepancy_tsv).exists()
    discrepancy_tsv = (
        output_dir / manifest.artifacts.protein_group_discrepancy_tsv
    ).read_text(encoding="utf-8")
    assert "status" in discrepancy_tsv
    assert "source_only" in discrepancy_tsv
    assert "workflow_only" in discrepancy_tsv

# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.io.formats import parse_experimental_design_table
from bijux_proteomics.workflow import (
    build_diann_biological_workflow_bundle,
    export_diann_biological_workflow_bundle,
)


def _fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "workflow" / name


def test_diann_biological_workflow_export_writes_matrix_qc_differential_and_report_assets(
    tmp_path: Path,
) -> None:
    design_entries = tuple(
        parse_experimental_design_table(
            _fixture("diann_biological.design.tsv")
        ).accepted_entries
    )
    report = build_diann_biological_workflow_bundle(
        _fixture("diann_biological_report.tsv"),
        design_entries,
        proteins_fasta_path=_fixture("biological_report_reference.fasta"),
        annotation_tsv_path=(
            Path(__file__).resolve().parent.parent
            / "fixtures"
            / "interpretation"
            / "protein_annotation_custom.tsv"
        ),
        context_annotation_tsv_path=_fixture("biological_report_context.tsv"),
        go_annotation_tsv_path=_fixture("biological_report_go.tsv"),
        pathway_membership_tsv_path=_fixture("biological_report_pathways.tsv"),
        complex_membership_tsv_path=_fixture("biological_report_complexes.tsv"),
        condition_a="control",
        condition_b="treatment",
    )

    manifest = export_diann_biological_workflow_bundle(
        report,
        tmp_path / "diann_biological_report",
    )
    output_dir = tmp_path / "diann_biological_report"

    assert (output_dir / manifest.artifacts.summary_tsv).exists()
    assert (output_dir / manifest.artifacts.import_summary_tsv).exists()
    assert (output_dir / manifest.artifacts.import_rejected_rows_tsv).exists()
    assert (output_dir / manifest.artifacts.import_rejected_evidence_tsv).exists()
    assert (output_dir / manifest.artifacts.rejected_evidence_tsv).exists()
    assert (output_dir / manifest.artifacts.precursor_quantity_matrix_tsv).exists()
    assert (output_dir / manifest.artifacts.precursor_missingness_tsv).exists()
    assert (output_dir / manifest.artifacts.precursor_metadata_tsv).exists()
    assert (output_dir / manifest.artifacts.peptide_quantity_matrix_tsv).exists()
    assert (output_dir / manifest.artifacts.peptide_missingness_tsv).exists()
    assert (output_dir / manifest.artifacts.protein_quantity_matrix_tsv).exists()
    assert (output_dir / manifest.artifacts.protein_missingness_tsv).exists()
    assert (output_dir / manifest.artifacts.protein_rollup_evidence_tsv).exists()
    assert (output_dir / manifest.artifacts.run_qc_summary_tsv).exists()
    assert (output_dir / manifest.artifacts.differential_results_tsv).exists()
    assert (output_dir / manifest.artifacts.differential_qc_summary_tsv).exists()
    assert (output_dir / manifest.artifacts.differential_raw_missingness_tsv).exists()
    assert (
        output_dir / manifest.artifacts.differential_normalized_missingness_tsv
    ).exists()
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
    assert "filtered_q_value_row_count" in (
        output_dir / manifest.artifacts.summary_tsv
    ).read_text(encoding="utf-8")
    assert "accepted_precursor_count" in (
        output_dir / manifest.artifacts.import_summary_tsv
    ).read_text(encoding="utf-8")
    assert "row_number" in (
        output_dir / manifest.artifacts.import_rejected_rows_tsv
    ).read_text(encoding="utf-8")
    assert "reason_code" in (
        output_dir / manifest.artifacts.import_rejected_evidence_tsv
    ).read_text(encoding="utf-8")
    assert (
        "rejected_evidence_id\tsource_surface\tsource_file\trow_number\t"
        "entity_type\tentity_id\treason_code\tdetail\trelated_artifact"
    ) == (
        output_dir / manifest.artifacts.rejected_evidence_tsv
    ).read_text(encoding="utf-8").splitlines()[0]
    assert "precursor_key" in (
        output_dir / manifest.artifacts.precursor_quantity_matrix_tsv
    ).read_text(encoding="utf-8")
    assert "observed" in (
        output_dir / manifest.artifacts.precursor_missingness_tsv
    ).read_text(encoding="utf-8")
    assert "retained_observation_count" in (
        output_dir / manifest.artifacts.precursor_metadata_tsv
    ).read_text(encoding="utf-8")
    assert "peptide_key" in (
        output_dir / manifest.artifacts.peptide_quantity_matrix_tsv
    ).read_text(encoding="utf-8")
    assert "observed" in (
        output_dir / manifest.artifacts.peptide_missingness_tsv
    ).read_text(encoding="utf-8")
    assert "entity_id" in (
        output_dir / manifest.artifacts.protein_quantity_matrix_tsv
    ).read_text(encoding="utf-8")
    assert "observed" in (
        output_dir / manifest.artifacts.protein_missingness_tsv
    ).read_text(encoding="utf-8")
    assert "rollup_stage" in (
        output_dir / manifest.artifacts.protein_rollup_evidence_tsv
    ).read_text(encoding="utf-8")
    assert "run_name\tsample_name\tprecursor_id_count" in (
        output_dir / manifest.artifacts.run_qc_runs_tsv
    ).read_text(encoding="utf-8")
    assert "weak_run_flag_count" in (
        output_dir / manifest.artifacts.run_qc_summary_tsv
    ).read_text(encoding="utf-8")
    assert "entity_id\tcondition_a\tcondition_b" in (
        output_dir / manifest.artifacts.differential_results_tsv
    ).read_text(encoding="utf-8")
    assert "observed" in (
        output_dir / manifest.artifacts.differential_raw_missingness_tsv
    ).read_text(encoding="utf-8")
    assert "contrast_count" in (
        output_dir / manifest.artifacts.differential_qc_summary_tsv
    ).read_text(encoding="utf-8")
    assert "card_id" in (
        output_dir / manifest.artifacts.protein_card_tsv
    ).read_text(encoding="utf-8")
    assert "annotation_status" in (
        output_dir / manifest.artifacts.annotation_tsv
    ).read_text(encoding="utf-8")
    assert "context_kind" in (
        output_dir / manifest.artifacts.context_mapping_tsv
    ).read_text(encoding="utf-8")
    assert "Biological result report" in (
        output_dir / manifest.artifacts.report_html
    ).read_text(encoding="utf-8")

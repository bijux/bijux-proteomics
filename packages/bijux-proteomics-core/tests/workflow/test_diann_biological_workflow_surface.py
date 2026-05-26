# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.io.formats import parse_experimental_design_table
from bijux_proteomics.study import build_experiment_design
from bijux_proteomics.workflow import build_diann_biological_workflow_bundle
from bijux_proteomics.workflow.pipelines.diann_biological_workflow import (
    build_diann_biological_workflow_bundle_from_reports,
    build_diann_quant_matrix_bundle,
)
from bijux_proteomics.identification.diann_import import build_diann_import_report


def _fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "workflow" / name


def test_build_diann_biological_workflow_bundle_preserves_qc_differential_and_biology() -> (
    None
):
    design_entries = tuple(
        parse_experimental_design_table(
            _fixture("diann_biological.design.tsv")
        ).accepted_entries
    )

    report = build_diann_biological_workflow_bundle(
        _fixture("diann_biological_report.tsv"),
        build_experiment_design(design_entries),
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

    assert report.summary.imported_precursor_count == 31
    assert report.summary.rejected_precursor_count == 0
    assert report.summary.rejected_evidence_count == 0
    assert report.summary.imported_protein_group_row_count == 30
    assert report.summary.filtered_q_value_row_count == 1
    assert report.summary.precursor_matrix_row_count == 5
    assert report.summary.protein_matrix_row_count == 5
    assert report.summary.run_count == 6
    assert report.summary.flagged_run_count == 0
    assert report.summary.significant_protein_count >= 3
    assert report.summary.annotation_entry_count == 5
    assert report.summary.protein_card_count == 5
    assert report.summary.context_term_count == 3
    assert report.summary.go_enriched_term_count == 1
    assert report.summary.pathway_enriched_entry_count == 1
    assert report.summary.complex_enriched_entry_count == 1
    assert report.precursor_matrix_report.summary.excluded_q_value_count == 1
    assert report.run_qc_report.summary.flagged_run_count == 0
    assert report.run_qc_report.summary.weak_run_flag_count == 0
    assert report.differential_analysis_report.differential_abundance_report is not None
    assert report.biological_report.summary.significant_protein_count >= 3
    assert report.biological_report.context_mapping_report is not None


def test_diann_biological_workflow_stage_helpers_match_the_monolithic_bundle() -> None:
    design_entries = tuple(
        parse_experimental_design_table(
            _fixture("diann_biological.design.tsv")
        ).accepted_entries
    )
    import_report = build_diann_import_report(_fixture("diann_biological_report.tsv"))
    quant_matrix_bundle = build_diann_quant_matrix_bundle(import_report, max_q_value=0.01)

    staged_report = build_diann_biological_workflow_bundle_from_reports(
        import_report,
        quant_matrix_bundle,
        build_experiment_design(design_entries),
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
        max_q_value=0.01,
    )
    monolithic_report = build_diann_biological_workflow_bundle(
        _fixture("diann_biological_report.tsv"),
        build_experiment_design(design_entries),
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

    assert (
        staged_report.summary.protein_matrix_row_count
        == monolithic_report.summary.protein_matrix_row_count
    )
    assert staged_report.summary.significant_protein_count == (
        monolithic_report.summary.significant_protein_count
    )
    assert (
        staged_report.biological_report.summary.pathway_enriched_entry_count
        == monolithic_report.biological_report.summary.pathway_enriched_entry_count
    )

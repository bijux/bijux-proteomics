# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.identification import SearchAdapterKind
from bijux_proteomics.io.formats import parse_experimental_design_table
from bijux_proteomics.workflow import (
    build_dda_biological_workflow_bundle,
    build_label_free_quant_table_from_protein_lfq_report,
)


def _fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "workflow" / name


def test_build_dda_biological_workflow_bundle_preserves_fdr_inference_lfq_and_biology() -> (
    None
):
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

    assert report.summary.imported_psm_row_count == 34
    assert report.summary.normalized_psm_count == 34
    assert report.summary.best_spectrum_psm_count == 33
    assert report.summary.accepted_psm_count == 30
    assert report.summary.filtered_psm_count == 3
    assert report.summary.inferred_protein_count == 5
    assert report.summary.quantified_protein_count == 5
    assert report.summary.significant_protein_count >= 3
    assert report.summary.sample_count == 6
    assert len({row.spectrum_id for row in report.accepted_psms}) == 30
    assert {reason.value for row in report.filtered_psms for reason in row.reasons} == {
        "q_value_above_threshold",
        "decoy",
        "contaminant",
    }
    assert report.protein_lfq_report.summary.protein_row_count == 5
    assert report.biological_report.summary.go_enriched_term_count == 1
    assert report.biological_report.summary.pathway_enriched_entry_count == 1
    assert report.biological_report.summary.complex_enriched_entry_count == 1


def test_build_label_free_quant_table_from_protein_lfq_report_preserves_protein_and_peptide_context() -> (
    None
):
    design_entries = tuple(
        parse_experimental_design_table(
            _fixture("biological_report.design.tsv")
        ).accepted_entries
    )
    workflow = build_dda_biological_workflow_bundle(
        _fixture("dda_biological_results.tsv"),
        design_entries,
        proteins_fasta_path=_fixture("biological_report_reference.fasta"),
        adapter_kind=SearchAdapterKind.GENERIC,
        generic_mapping_path=_fixture("dda_biological_mapping.json"),
        condition_a="control",
        condition_b="treatment",
    )

    table = build_label_free_quant_table_from_protein_lfq_report(
        workflow.protein_lfq_report
    )

    assert table.entity_level.value == "protein"
    assert table.measure_kind.value == "intensity"
    assert table.sample_ids == ("C1", "C2", "C3", "T1", "T2", "T3")
    assert table.entity_ids == ("O14920", "P04637", "P62993", "Q8N158", "Q9Y243")
    assert table.entity_protein_refs["P04637"] == ("P04637",)
    assert table.entity_member_peptides["P04637"] == ("PEPAAA",)


def test_build_dda_biological_workflow_bundle_tracks_fragpipe_source_protein_discrepancies() -> (
    None
):
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

    assert report.summary.source_protein_group_count == 5
    assert report.summary.protein_group_discrepancy_count == 2
    assert report.summary.source_only_protein_group_count == 1
    assert report.summary.workflow_only_protein_group_count == 1
    by_protein = {
        entry.protein_ref: entry for entry in report.protein_group_discrepancies
    }
    assert by_protein["Q11111"].status.value == "source_only"
    assert by_protein["Q11111"].source_table_present is True
    assert by_protein["P62993"].status.value == "workflow_only"
    assert by_protein["P62993"].quantified_by_workflow is True

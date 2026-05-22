# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.io.formats import parse_experimental_design_table
from bijux_proteomics.workflow import build_maxquant_biological_workflow_bundle


def _workflow_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "workflow" / name


def _bundle_fixture(name: str) -> Path:
    return _workflow_fixture("maxquant_biological") / name


def test_build_maxquant_biological_workflow_bundle_preserves_import_lfq_and_biology() -> (
    None
):
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
        go_annotation_tsv_path=_workflow_fixture("biological_report_go.tsv"),
        pathway_membership_tsv_path=_workflow_fixture("biological_report_pathways.tsv"),
        complex_membership_tsv_path=_workflow_fixture("biological_report_complexes.tsv"),
        condition_a="control",
        condition_b="treatment",
    )

    assert report.summary.imported_evidence_count == 8
    assert report.summary.imported_peptide_row_count == 8
    assert report.summary.imported_protein_group_row_count == 8
    assert report.summary.accepted_protein_group_count == 5
    assert report.summary.filtered_protein_group_count == 3
    assert report.summary.lfq_experiment_count == 6
    assert report.summary.quantified_protein_count == 5
    assert report.summary.significant_protein_count >= 3
    assert report.summary.annotation_entry_count == 5
    assert report.summary.go_enriched_term_count == 1
    assert report.summary.pathway_enriched_entry_count == 1
    assert report.summary.complex_enriched_entry_count == 1
    assert report.import_report.parameter_report is not None
    assert report.lfq_table.sample_ids == ("C1", "C2", "C3", "T1", "T2", "T3")
    assert len(report.filtered_protein_groups) == 3
    assert {
        reason.value
        for entry in report.filtered_protein_groups
        for reason in entry.reasons
    } == {"contaminant", "reverse", "only_identified_by_site"}
    assert report.biological_report.summary.significant_protein_count >= 3


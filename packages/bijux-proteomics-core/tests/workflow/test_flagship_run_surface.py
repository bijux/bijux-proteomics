# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.io.formats import parse_experimental_design_table
from bijux_proteomics.study import build_experiment_design
from bijux_proteomics.workflow import (
    ProteomicsRunEngine,
    build_proteomics_run_bundle,
)


def _fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "workflow" / name


def _bundle_fixture(name: str) -> Path:
    return _fixture("maxquant_biological") / name


def test_build_proteomics_run_bundle_supports_diann_mode() -> None:
    metadata_entries = build_experiment_design(
        tuple(
            parse_experimental_design_table(
                _fixture("diann_biological.design.tsv")
            ).accepted_entries
        )
    )

    report = build_proteomics_run_bundle(
        engine=ProteomicsRunEngine.DIANN,
        metadata_entries=metadata_entries,
        proteins_fasta_path=_fixture("biological_report_reference.fasta"),
        report_tsv_path=_fixture("diann_biological_report.tsv"),
        contrast="control-treatment",
        go_annotation_tsv_path=_fixture("biological_report_go.tsv"),
        pathway_membership_tsv_path=_fixture("biological_report_pathways.tsv"),
        complex_membership_tsv_path=_fixture("biological_report_complexes.tsv"),
    )

    assert report.engine is ProteomicsRunEngine.DIANN
    assert report.diann_workflow is not None
    assert report.summary.metadata_row_count == 6
    assert report.summary.condition_a == "control"
    assert report.summary.condition_b == "treatment"
    assert report.summary.sample_count == 6
    assert report.summary.protein_count == 5
    assert report.summary.significant_protein_count >= 3
    assert report.summary.qc_issue_count == 0
    assert report.summary.enrichment_entry_count >= 3


def test_build_proteomics_run_bundle_supports_maxquant_mode() -> None:
    metadata_entries = build_experiment_design(
        tuple(
            parse_experimental_design_table(
                _bundle_fixture("design.tsv")
            ).accepted_entries
        )
    )

    report = build_proteomics_run_bundle(
        engine=ProteomicsRunEngine.MAXQUANT,
        metadata_entries=metadata_entries,
        proteins_fasta_path=_fixture("biological_report_reference.fasta"),
        report_tsv_path=_bundle_fixture("evidence.txt"),
        peptides_tsv_path=_bundle_fixture("peptides.txt"),
        protein_groups_tsv_path=_bundle_fixture("proteinGroups.txt"),
        config_path=_bundle_fixture("maxquant_settings.txt"),
        contrast="control-treatment",
        go_annotation_tsv_path=_fixture("biological_report_go.tsv"),
        pathway_membership_tsv_path=_fixture("biological_report_pathways.tsv"),
        complex_membership_tsv_path=_fixture("biological_report_complexes.tsv"),
    )

    assert report.engine is ProteomicsRunEngine.MAXQUANT
    assert report.maxquant_workflow is not None
    assert report.summary.metadata_row_count == 6
    assert report.summary.sample_count == 6
    assert report.summary.protein_count == 5
    assert report.summary.significant_protein_count >= 3
    assert report.summary.qc_issue_count == 0
    assert report.summary.enrichment_entry_count >= 3


def test_build_proteomics_run_bundle_supports_fragpipe_mode() -> None:
    metadata_entries = build_experiment_design(
        tuple(
            parse_experimental_design_table(
                _fixture("biological_report.design.tsv")
            ).accepted_entries
        )
    )

    report = build_proteomics_run_bundle(
        engine=ProteomicsRunEngine.FRAGPIPE,
        metadata_entries=metadata_entries,
        proteins_fasta_path=_fixture("biological_report_reference.fasta"),
        report_tsv_path=_fixture("fragpipe_biological_psms.tsv"),
        source_protein_tsv_path=_fixture("fragpipe_biological_proteins.tsv"),
        contrast="control-treatment",
        go_annotation_tsv_path=_fixture("biological_report_go.tsv"),
        pathway_membership_tsv_path=_fixture("biological_report_pathways.tsv"),
        complex_membership_tsv_path=_fixture("biological_report_complexes.tsv"),
    )

    assert report.engine is ProteomicsRunEngine.FRAGPIPE
    assert report.fragpipe_workflow is not None
    assert report.summary.metadata_row_count == 6
    assert report.summary.sample_count == 6
    assert report.summary.protein_count == 5
    assert report.summary.significant_protein_count >= 3
    assert report.summary.qc_issue_count == 0
    assert report.summary.enrichment_entry_count >= 3
    assert report.fragpipe_workflow.summary.accepted_psm_count == 30
    assert report.fragpipe_workflow.summary.protein_group_discrepancy_count == 2


def test_build_proteomics_run_bundle_accepts_explicit_case_control_semantics() -> None:
    metadata_entries = build_experiment_design(
        tuple(
            parse_experimental_design_table(
                _fixture("diann_biological.design.tsv")
            ).accepted_entries
        )
    )

    report = build_proteomics_run_bundle(
        engine=ProteomicsRunEngine.DIANN,
        metadata_entries=metadata_entries,
        proteins_fasta_path=_fixture("biological_report_reference.fasta"),
        report_tsv_path=_fixture("diann_biological_report.tsv"),
        contrast="case-control:treatment-control",
    )

    assert report.summary.condition_a == "treatment"
    assert report.summary.condition_b == "control"

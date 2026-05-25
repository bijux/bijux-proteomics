# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.workflow import (
    AdvancedDiannWorkflowConfig,
    AdvancedMaxquantWorkflowConfig,
    run_advanced_diann_workflow,
    run_advanced_maxquant_workflow,
)

from .workflow_golden_support import assert_workflow_golden_outputs_match


def _workflow_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "workflow" / name


def _interpretation_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "interpretation" / name


def test_advanced_diann_workflow_matches_reviewed_golden_outputs(tmp_path: Path) -> None:
    output_dir = tmp_path / "advanced_diann"
    run_advanced_diann_workflow(
        AdvancedDiannWorkflowConfig(
            result_tsv_path=_workflow_fixture("diann_advanced_report.tsv"),
            design_tsv_path=_workflow_fixture("diann_biological.design.tsv"),
            proteins_fasta_path=_workflow_fixture("diann_advanced_reference.fasta"),
            output_dir=output_dir,
            annotation_tsv_path=_interpretation_fixture("protein_annotation_custom.tsv"),
            context_annotation_tsv_path=_workflow_fixture(
                "biological_report_context.tsv"
            ),
            go_annotation_tsv_path=_workflow_fixture("biological_report_go.tsv"),
            pathway_membership_tsv_path=_workflow_fixture(
                "biological_report_pathways.tsv"
            ),
            complex_membership_tsv_path=_workflow_fixture(
                "biological_report_complexes.tsv"
            ),
            condition_a="control",
            condition_b="treatment",
        )
    )

    assert_workflow_golden_outputs_match("advanced_diann", output_dir)


def test_advanced_maxquant_workflow_matches_reviewed_golden_outputs(
    tmp_path: Path,
) -> None:
    output_dir = tmp_path / "advanced_maxquant"
    run_advanced_maxquant_workflow(
        AdvancedMaxquantWorkflowConfig(
            evidence_txt_path=_workflow_fixture("maxquant_biological/evidence.txt"),
            peptides_txt_path=_workflow_fixture("maxquant_biological/peptides.txt"),
            protein_groups_txt_path=_workflow_fixture(
                "maxquant_biological/proteinGroups.txt"
            ),
            design_tsv_path=_workflow_fixture("maxquant_biological/design.tsv"),
            proteins_fasta_path=_workflow_fixture("biological_report_reference.fasta"),
            output_dir=output_dir,
            config_path=_workflow_fixture("maxquant_biological/maxquant_settings.txt"),
            annotation_tsv_path=_interpretation_fixture("protein_annotation_custom.tsv"),
            context_annotation_tsv_path=_workflow_fixture(
                "biological_report_context.tsv"
            ),
            go_annotation_tsv_path=_workflow_fixture("biological_report_go.tsv"),
            pathway_membership_tsv_path=_workflow_fixture(
                "biological_report_pathways.tsv"
            ),
            complex_membership_tsv_path=_workflow_fixture(
                "biological_report_complexes.tsv"
            ),
            condition_a="control",
            condition_b="treatment",
        )
    )

    assert_workflow_golden_outputs_match("advanced_maxquant", output_dir)

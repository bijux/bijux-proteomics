# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.workflow import (
    AdvancedDiannWorkflowConfig,
    run_advanced_diann_workflow,
    validate_workflow_artifact_manifest,
)


def _workflow_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "workflow" / name


def _format_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "formats" / name


def test_run_advanced_diann_workflow_exports_accepted_downgraded_and_rejected_evidence(
    tmp_path: Path,
) -> None:
    report = run_advanced_diann_workflow(
        AdvancedDiannWorkflowConfig(
            result_tsv_path=_workflow_fixture("diann_advanced_report.tsv"),
            design_tsv_path=_workflow_fixture("diann_biological.design.tsv"),
            proteins_fasta_path=_workflow_fixture("diann_advanced_reference.fasta"),
            output_dir=tmp_path / "advanced_diann_review",
            annotation_tsv_path=(
                Path(__file__).resolve().parent.parent
                / "fixtures"
                / "interpretation"
                / "protein_annotation_custom.tsv"
            ),
            context_annotation_tsv_path=_workflow_fixture("biological_report_context.tsv"),
            go_annotation_tsv_path=_workflow_fixture("biological_report_go.tsv"),
            pathway_membership_tsv_path=_workflow_fixture("biological_report_pathways.tsv"),
            complex_membership_tsv_path=_workflow_fixture("biological_report_complexes.tsv"),
            condition_a="control",
            condition_b="treatment",
        )
    )

    output_dir = tmp_path / "advanced_diann_review"
    accepted_tsv = (
        output_dir / report.manifest.artifacts.accepted_proteins_tsv
    ).read_text(encoding="utf-8")
    downgraded_tsv = (
        output_dir / report.manifest.artifacts.downgraded_proteins_tsv
    ).read_text(encoding="utf-8")
    rejected_evidence_tsv = (
        output_dir / report.manifest.artifacts.rejected_evidence_tsv
    ).read_text(encoding="utf-8")
    belief_audit_tsv = (
        output_dir / report.manifest.artifacts.belief_audit_tsv
    ).read_text(encoding="utf-8")

    assert report.summary.rejected_evidence_count == 1
    assert report.summary.accepted_protein_count >= 1
    assert report.summary.downgraded_protein_count >= 1
    assert report.summary.belief_audit_entry_count >= 1
    assert "Q9Y243" in accepted_tsv
    assert "Q99999" in downgraded_tsv
    assert "shared_peptide_only" in downgraded_tsv
    assert "raw_bad_precursor" in rejected_evidence_tsv
    assert "audit_id\tsubject_kind\tsubject_id" in belief_audit_tsv
    assert (output_dir / "manifest.json").exists()
    assert (output_dir / "inputs").is_dir()
    assert (output_dir / "qc").is_dir()
    assert (output_dir / "evidence").is_dir()
    assert (output_dir / "matrices").is_dir()
    assert (output_dir / "stats").is_dir()
    assert (output_dir / "biology").is_dir()
    assert (output_dir / "cards").is_dir()
    assert (output_dir / "reports").is_dir()
    assert (output_dir / "reports" / report.manifest.artifacts.summary_tsv).exists()
    assert (output_dir / "evidence" / report.manifest.artifacts.accepted_proteins_tsv).exists()
    assert (output_dir / "qc" / report.manifest.artifacts.belief_audit_tsv).exists()
    assert (output_dir / report.manifest.artifacts.diann_workflow_manifest_json).exists()
    assert (output_dir / report.manifest.artifacts.biological_report_manifest_json).exists()
    assert report.manifest.artifacts.supported_claim_tsv is not None
    assert report.manifest.artifacts.rejected_claim_tsv is not None
    assert (output_dir / report.manifest.artifacts.supported_claim_tsv).exists()
    assert (output_dir / report.manifest.artifacts.rejected_claim_tsv).exists()
    layout_manifest = validate_workflow_artifact_manifest(output_dir)
    summary_entry = next(
        entry
        for entry in layout_manifest.artifacts
        if entry.legacy_relative_path == report.manifest.artifacts.summary_tsv
    )
    assert summary_entry.output_table_schema is not None
    assert summary_entry.output_table_schema.columns[0].name == "field"
    evidence_entry = next(
        entry
        for entry in layout_manifest.artifacts
        if entry.legacy_relative_path == report.manifest.artifacts.accepted_proteins_tsv
    )
    assert evidence_entry.output_table_schema is not None
    assert "protein_group_id" in {
        column.name for column in evidence_entry.output_table_schema.columns
    }


def test_run_advanced_diann_workflow_exports_fragment_coelution_when_fragment_evidence_is_supplied(
    tmp_path: Path,
) -> None:
    report = run_advanced_diann_workflow(
        AdvancedDiannWorkflowConfig(
            result_tsv_path=_workflow_fixture("diann_advanced_report.tsv"),
            design_tsv_path=_workflow_fixture("diann_biological.design.tsv"),
            proteins_fasta_path=_workflow_fixture("diann_advanced_reference.fasta"),
            output_dir=tmp_path / "advanced_diann_with_fragments",
            condition_a="control",
            condition_b="treatment",
            fragment_mzml_paths=(_format_fixture("dia_fragment_coelution.mzml"),),
            fragment_target_tsv_path=_format_fixture("dia_fragment_targets.tsv"),
        )
    )

    output_dir = tmp_path / "advanced_diann_with_fragments"

    assert report.fragment_coelution_report is not None
    assert report.summary.fragment_coelution_run_count >= 1
    assert report.manifest.artifacts.fragment_coelution_runs_tsv is not None
    assert report.manifest.artifacts.fragment_coelution_fragments_tsv is not None
    assert (
        output_dir / report.manifest.artifacts.fragment_coelution_runs_tsv
    ).exists()
    assert (
        output_dir / report.manifest.artifacts.fragment_coelution_fragments_tsv
    ).exists()

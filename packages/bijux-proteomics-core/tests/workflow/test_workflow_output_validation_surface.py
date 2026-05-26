# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations
from pathlib import Path

from bijux_proteomics.workflow import (
    AdvancedDiannWorkflowConfig,
    load_workflow_artifact_manifest,
    run_advanced_diann_workflow,
)
from bijux_proteomics.workflow.output_validation import (
    WorkflowOutputValidationCheck,
    WorkflowOutputValidationIssueCode,
    WorkflowOutputValidationStatus,
    build_workflow_output_validation_report,
)


def _workflow_fixture(name: str) -> Path:
    return Path(__file__).resolve().parent.parent / "fixtures" / "workflow" / name


def test_build_workflow_output_validation_report_accepts_completed_advanced_diann_run(
    tmp_path: Path,
) -> None:
    output_dir = tmp_path / "advanced_diann_validation_surface"
    run_advanced_diann_workflow(
        AdvancedDiannWorkflowConfig(
            result_tsv_path=_workflow_fixture("diann_advanced_report.tsv"),
            design_tsv_path=_workflow_fixture("diann_biological.design.tsv"),
            proteins_fasta_path=_workflow_fixture("diann_advanced_reference.fasta"),
            output_dir=output_dir,
            condition_a="control",
            condition_b="treatment",
        )
    )

    validation = build_workflow_output_validation_report(output_dir)
    layout_manifest = load_workflow_artifact_manifest(output_dir)

    assert validation.status is WorkflowOutputValidationStatus.VALID
    assert validation.issue_count == 0
    assert validation.issues == ()
    assert validation.layout_name == "workflow_artifact_layout"
    assert validation.manifest_schema_version == "2026-05-25"
    assert validation.producer_function == layout_manifest.producer_function
    assert validation.artifact_count == len(layout_manifest.artifacts)
    assert validation.checks == (
        WorkflowOutputValidationCheck.MANIFEST_ARTIFACT_LAYOUT,
        WorkflowOutputValidationCheck.DECLARED_ARTIFACT_COMPLETENESS,
        WorkflowOutputValidationCheck.ARTIFACT_INVENTORY,
    )


def test_build_workflow_output_validation_report_rejects_hidden_missing_required_artifact(
    tmp_path: Path,
) -> None:
    output_dir = tmp_path / "advanced_diann_missing_artifact_surface"
    report = run_advanced_diann_workflow(
        AdvancedDiannWorkflowConfig(
            result_tsv_path=_workflow_fixture("diann_advanced_report.tsv"),
            design_tsv_path=_workflow_fixture("diann_biological.design.tsv"),
            proteins_fasta_path=_workflow_fixture("diann_advanced_reference.fasta"),
            output_dir=output_dir,
            condition_a="control",
            condition_b="treatment",
        )
    )

    missing_name = report.manifest.artifacts.belief_audit_tsv
    assert missing_name is not None
    (output_dir / missing_name).unlink()
    (output_dir / "qc" / missing_name).unlink()
    layout_manifest = load_workflow_artifact_manifest(output_dir)
    drifted_manifest = layout_manifest.model_copy(
        update={
            "artifacts": tuple(
                artifact
                for artifact in layout_manifest.artifacts
                if artifact.legacy_relative_path != missing_name
            )
        }
    )
    (output_dir / "manifest.json").write_text(
        drifted_manifest.to_stable_json() + "\n",
        encoding="utf-8",
    )

    validation = build_workflow_output_validation_report(output_dir)

    assert validation.status is WorkflowOutputValidationStatus.INVALID
    assert validation.issue_count == 1
    assert validation.issues[0].check is WorkflowOutputValidationCheck.DECLARED_ARTIFACT_COMPLETENESS
    assert validation.issues[0].code is WorkflowOutputValidationIssueCode.MISSING_REQUIRED_ARTIFACT
    assert validation.issues[0].artifact_relative_path == missing_name
    assert "declared at manifest.artifacts.belief_audit_tsv" in validation.issues[0].message


def test_build_workflow_output_validation_report_marks_missing_manifest_as_invalid(
    tmp_path: Path,
) -> None:
    output_dir = tmp_path / "missing_manifest_validation_surface"
    output_dir.mkdir()
    (output_dir / "notes.txt").write_text("placeholder\n", encoding="utf-8")

    validation = build_workflow_output_validation_report(output_dir)

    assert validation.status is WorkflowOutputValidationStatus.INVALID
    assert validation.issue_count == 1
    assert validation.artifact_count == 0
    assert validation.issues[0].check is WorkflowOutputValidationCheck.MANIFEST_ARTIFACT_LAYOUT
    assert validation.issues[0].code is WorkflowOutputValidationIssueCode.MISSING_MANIFEST
    assert validation.issues[0].artifact_relative_path == "manifest.json"
    assert "workflow artifact manifest is missing" in validation.issues[0].message

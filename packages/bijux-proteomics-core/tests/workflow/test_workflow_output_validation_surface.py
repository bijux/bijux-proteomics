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

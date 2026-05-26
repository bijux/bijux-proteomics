# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.workflow import AdvancedDiannWorkflowConfig
from bijux_proteomics_runtime.workflows.advanced_diann import (
    AdvancedDiannDryRunStatus,
    AdvancedDiannRuntimeStage,
    dry_run_resumable_advanced_diann_workflow,
)


def _workflow_fixture(name: str) -> Path:
    return (
        Path(__file__).resolve().parents[3]
        / "bijux-proteomics-core"
        / "tests"
        / "fixtures"
        / "workflow"
        / name
    )


def test_advanced_diann_dry_run_reports_expected_stages_and_output_plan(
    tmp_path: Path,
) -> None:
    output_dir = tmp_path / "advanced_diann_dry_run"
    report = dry_run_resumable_advanced_diann_workflow(
        AdvancedDiannWorkflowConfig(
            result_tsv_path=_workflow_fixture("diann_advanced_report.tsv"),
            design_tsv_path=_workflow_fixture("diann_biological.design.tsv"),
            proteins_fasta_path=_workflow_fixture("diann_advanced_reference.fasta"),
            output_dir=output_dir,
            condition_a="control",
            condition_b="treatment",
        )
    )

    assert report.status is AdvancedDiannDryRunStatus.READY
    assert report.issues == ()
    assert tuple(entry.stage for entry in report.stage_plan) == (
        AdvancedDiannRuntimeStage.IMPORT,
        AdvancedDiannRuntimeStage.MATRICES,
        AdvancedDiannRuntimeStage.BIOLOGY,
        AdvancedDiannRuntimeStage.REVIEW,
    )
    assert (
        "advanced_diann_workflow_manifest.json"
        in {entry.relative_path for entry in report.output_plan}
    )
    assert (
        "checkpoints/advanced_diann_runtime/advanced-diann-import.json"
        in {entry.relative_path for entry in report.output_plan}
    )
    assert report.supported_contrasts == ("control_vs_treatment",)
    assert not output_dir.exists()

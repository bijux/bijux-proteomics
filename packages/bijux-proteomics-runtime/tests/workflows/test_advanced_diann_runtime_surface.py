# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.workflow import (
    AdvancedDiannWorkflowConfig,
    run_advanced_diann_workflow,
)
from bijux_proteomics_runtime.workflows import (
    AdvancedDiannRuntimeStage,
    AdvancedDiannRuntimeStatus,
    run_resumable_advanced_diann_workflow,
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


def test_resumable_advanced_diann_runtime_reuses_import_and_matrix_stages_after_interruption(
    tmp_path: Path,
) -> None:
    config = AdvancedDiannWorkflowConfig(
        result_tsv_path=_workflow_fixture("diann_advanced_report.tsv"),
        design_tsv_path=_workflow_fixture("diann_biological.design.tsv"),
        proteins_fasta_path=_workflow_fixture("diann_advanced_reference.fasta"),
        output_dir=tmp_path / "advanced_diann_runtime_resume",
        condition_a="control",
        condition_b="treatment",
    )

    interrupted = run_resumable_advanced_diann_workflow(
        config,
        through_stage=AdvancedDiannRuntimeStage.MATRICES,
    )
    resumed = run_resumable_advanced_diann_workflow(config)

    assert interrupted.status is AdvancedDiannRuntimeStatus.INTERRUPTED
    assert interrupted.completed_stage_ids == (
        AdvancedDiannRuntimeStage.IMPORT.value,
        AdvancedDiannRuntimeStage.MATRICES.value,
    )
    assert resumed.status is AdvancedDiannRuntimeStatus.COMPLETED
    assert resumed.reused_stage_ids == (
        AdvancedDiannRuntimeStage.IMPORT.value,
        AdvancedDiannRuntimeStage.MATRICES.value,
    )
    assert resumed.rerun_stage_ids == (
        AdvancedDiannRuntimeStage.BIOLOGY.value,
        AdvancedDiannRuntimeStage.REVIEW.value,
    )
    assert resumed.advanced_report is not None
    assert resumed.advanced_report.summary.accepted_protein_count >= 1
    assert resumed.advanced_report.summary.downgraded_protein_count >= 1


def test_resumable_advanced_diann_runtime_reruns_matrix_stage_when_persisted_matrix_artifact_is_missing(
    tmp_path: Path,
) -> None:
    config = AdvancedDiannWorkflowConfig(
        result_tsv_path=_workflow_fixture("diann_advanced_report.tsv"),
        design_tsv_path=_workflow_fixture("diann_biological.design.tsv"),
        proteins_fasta_path=_workflow_fixture("diann_advanced_reference.fasta"),
        output_dir=tmp_path / "advanced_diann_runtime_missing_matrix",
        condition_a="control",
        condition_b="treatment",
    )

    run_resumable_advanced_diann_workflow(
        config,
        through_stage=AdvancedDiannRuntimeStage.MATRICES,
    )
    (
        config.output_dir
        / "checkpoints"
        / "advanced_diann_runtime"
        / f"{AdvancedDiannRuntimeStage.MATRICES.value}.json"
    ).unlink()

    resumed = run_resumable_advanced_diann_workflow(config)

    assert resumed.reused_stage_ids == (AdvancedDiannRuntimeStage.IMPORT.value,)
    assert AdvancedDiannRuntimeStage.MATRICES.value in resumed.rerun_stage_ids
    assert resumed.advanced_report is not None


def test_resumable_advanced_diann_runtime_matches_core_advanced_diann_summary(
    tmp_path: Path,
) -> None:
    core_config = AdvancedDiannWorkflowConfig(
        result_tsv_path=_workflow_fixture("diann_advanced_report.tsv"),
        design_tsv_path=_workflow_fixture("diann_biological.design.tsv"),
        proteins_fasta_path=_workflow_fixture("diann_advanced_reference.fasta"),
        output_dir=tmp_path / "advanced_diann_core",
        condition_a="control",
        condition_b="treatment",
    )
    runtime_config = core_config.model_copy(
        update={"output_dir": tmp_path / "advanced_diann_runtime"}
    )

    core_report = run_advanced_diann_workflow(core_config)
    runtime_report = run_resumable_advanced_diann_workflow(runtime_config)

    assert runtime_report.status is AdvancedDiannRuntimeStatus.COMPLETED
    assert runtime_report.advanced_report is not None
    assert runtime_report.advanced_report.summary == core_report.summary
    assert runtime_report.advanced_report.manifest.artifacts == core_report.manifest.artifacts

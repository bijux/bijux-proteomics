# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

import pytest

from bijux_proteomics.workflow import AdvancedDiannWorkflowConfig
from bijux_proteomics_runtime.rehydrate import load_completed_run
from bijux_proteomics_runtime.workflows.advanced_diann import (
    AdvancedDiannRuntimeStage,
    run_resumable_advanced_diann_workflow,
)
from bijux_proteomics_runtime.workflows.advanced_diann_archive import (
    archive_completed_advanced_diann_run,
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


def test_archive_completed_advanced_diann_run_writes_manifest_and_rehydrates_queries(
    tmp_path: Path,
) -> None:
    config = AdvancedDiannWorkflowConfig(
        result_tsv_path=_workflow_fixture("diann_advanced_report.tsv"),
        design_tsv_path=_workflow_fixture("diann_biological.design.tsv"),
        proteins_fasta_path=_workflow_fixture("diann_advanced_reference.fasta"),
        output_dir=tmp_path / "advanced_diann_completed_run",
        condition_a="control",
        condition_b="treatment",
    )

    runtime_report = run_resumable_advanced_diann_workflow(config)
    archive_report = archive_completed_advanced_diann_run(
        config,
        runtime_report=runtime_report,
    )
    study_result = load_completed_run(config.output_dir)
    protein = study_result.query_archived_protein(
        representative_protein_ref="O14920"
    )

    assert archive_report.archive_validated is True
    assert archive_report.runtime_report is not None
    assert Path(archive_report.artifacts.result_manifest_json).exists()
    assert Path(archive_report.artifacts.completed_run_report_json).exists()
    assert archive_report.result_manifest.summary.missing_required_file_count == 0
    assert study_result.archive_manifest is not None
    assert protein.representative_protein_ref == "O14920"
    assert protein.object_id == "protein:PG003"


def test_archive_completed_advanced_diann_run_accepts_completed_output_dir_without_runtime_report(
    tmp_path: Path,
) -> None:
    config = AdvancedDiannWorkflowConfig(
        result_tsv_path=_workflow_fixture("diann_advanced_report.tsv"),
        design_tsv_path=_workflow_fixture("diann_biological.design.tsv"),
        proteins_fasta_path=_workflow_fixture("diann_advanced_reference.fasta"),
        output_dir=tmp_path / "advanced_diann_archive_only",
        condition_a="control",
        condition_b="treatment",
    )

    run_resumable_advanced_diann_workflow(config)
    archive_report = archive_completed_advanced_diann_run(config)

    assert archive_report.runtime_report is None
    assert archive_report.study_result_summary.conclusion_count >= 1
    assert tuple(
        command.command_text for command in archive_report.result_manifest.commands
    ) == (
        "bijux_proteomics_runtime.workflows.advanced_diann_archive."
        "archive_completed_advanced_diann_run",
    )


def test_archive_completed_advanced_diann_run_rejects_incomplete_runtime_report(
    tmp_path: Path,
) -> None:
    config = AdvancedDiannWorkflowConfig(
        result_tsv_path=_workflow_fixture("diann_advanced_report.tsv"),
        design_tsv_path=_workflow_fixture("diann_biological.design.tsv"),
        proteins_fasta_path=_workflow_fixture("diann_advanced_reference.fasta"),
        output_dir=tmp_path / "advanced_diann_interrupted_archive",
        condition_a="control",
        condition_b="treatment",
    )

    runtime_report = run_resumable_advanced_diann_workflow(
        config,
        through_stage=AdvancedDiannRuntimeStage.MATRICES,
    )

    with pytest.raises(
        ValueError,
        match="advanced dia-nn archiving requires a completed runtime run report",
    ):
        archive_completed_advanced_diann_run(
            config,
            runtime_report=runtime_report,
        )

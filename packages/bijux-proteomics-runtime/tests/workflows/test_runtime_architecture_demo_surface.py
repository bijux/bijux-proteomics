# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import json
from pathlib import Path

from bijux_proteomics_runtime.rehydrate.loading import load_completed_run
from bijux_proteomics_runtime.workflows.architecture_demo import (
    RuntimeArchitectureDemoConfig,
    run_runtime_architecture_demo,
)


def test_runtime_architecture_demo_persists_runtime_step_artifacts_and_result_archive(
    tmp_path: Path,
) -> None:
    output_dir = tmp_path / "runtime_architecture_demo"
    report = run_runtime_architecture_demo(
        RuntimeArchitectureDemoConfig(output_dir=output_dir)
    )

    assert report.workflow_output_validated is True
    assert report.archive_validated is True
    assert report.scientific_surfaces_preserved is True
    assert report.workflow_output_validation.status.value == "valid"
    assert report.result_manifest.summary.missing_required_file_count == 0
    assert report.result_manifest.summary.source_report_count == 1
    assert report.result_manifest.summary.sample_count == (
        report.rehydrated_study_result_summary.design_entry_count
    )
    assert report.direct_study_result_summary.design_entry_count == (
        report.rehydrated_study_result_summary.design_entry_count
    )
    assert report.direct_study_result_summary.card_surface_count == (
        report.rehydrated_study_result_summary.card_surface_count
    )
    assert report.direct_study_result_summary.conclusion_count == (
        report.rehydrated_study_result_summary.conclusion_count
    )
    assert Path(report.artifacts.demo_output_dir).is_dir()
    assert Path(report.artifacts.demo_report_json).exists()
    assert Path(report.artifacts.biological_report_dir).is_dir()
    assert Path(report.artifacts.workflow_output_validation_json).exists()
    assert Path(report.artifacts.runtime_step_artifacts_json).exists()
    assert Path(report.artifacts.result_manifest_json).exists()
    assert Path(report.artifacts.architecture_demo_report_json).exists()
    assert (Path(report.artifacts.demo_output_dir) / "tmt_review").is_dir()
    assert (Path(report.artifacts.demo_output_dir) / "ptm_review").is_dir()
    assert (Path(report.artifacts.demo_output_dir) / "targeted_validation").is_dir()

    step_ledger = json.loads(
        Path(report.artifacts.runtime_step_artifacts_json).read_text(encoding="utf-8")
    )
    assert [entry["step_id"] for entry in step_ledger["steps"]] == [
        "run-surprising-demo",
        "validate-workflow-output",
        "build-result-archive",
    ]
    assert step_ledger["steps"][0]["status"] == "completed"
    assert step_ledger["steps"][2]["schema_names"] == [
        "result_manifest",
        "proteomics_study_result",
    ]


def test_runtime_architecture_demo_rehydrates_completed_run_from_written_manifest(
    tmp_path: Path,
) -> None:
    output_dir = tmp_path / "runtime_architecture_demo_rehydrate"
    report = run_runtime_architecture_demo(
        RuntimeArchitectureDemoConfig(output_dir=output_dir)
    )

    rehydrated = load_completed_run(output_dir)

    assert rehydrated.summary == report.rehydrated_study_result_summary
    assert rehydrated.archive_manifest.summary == report.result_manifest.summary
    assert rehydrated.archive_manifest.commands[0].command_text.endswith(
        "run_runtime_architecture_demo"
    )

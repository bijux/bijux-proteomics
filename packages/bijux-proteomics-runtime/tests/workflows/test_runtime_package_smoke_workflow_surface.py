# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics_runtime.rehydrate.loading import load_completed_run
from bijux_proteomics_runtime.workflows import (
    RuntimePackageSmokeConfig,
    run_runtime_package_smoke_workflow,
)


def test_runtime_package_smoke_workflow_produces_valid_result_archive(
    tmp_path: Path,
) -> None:
    output_dir = tmp_path / "runtime_package_smoke"
    report = run_runtime_package_smoke_workflow(
        RuntimePackageSmokeConfig(output_dir=output_dir)
    )

    assert report.archive_validated is True
    assert report.scale_demo_outputs_validated is True
    assert report.result_manifest.summary.missing_required_file_count == 0
    assert report.result_manifest.summary.source_report_count == 1
    assert report.result_manifest.summary.sample_count == (
        report.study_result_summary.design_entry_count
    )
    assert report.result_manifest.summary.protein_count > 0
    assert report.study_result_summary.card_surface_count > 0
    assert Path(report.artifacts.result_manifest_json).exists()
    assert Path(report.artifacts.smoke_report_json).exists()
    assert Path(report.artifacts.scale_demo_report_json).exists()


def test_runtime_package_smoke_workflow_rehydrates_completed_run_from_written_manifest(
    tmp_path: Path,
) -> None:
    output_dir = tmp_path / "runtime_package_smoke_rehydrate"
    report = run_runtime_package_smoke_workflow(
        RuntimePackageSmokeConfig(
            output_dir=output_dir,
            protein_count=24,
            peptides_per_protein=3,
            replicates_per_condition=2,
            pathway_count=5,
        )
    )

    rehydrated = load_completed_run(output_dir)

    assert rehydrated.summary == report.study_result_summary
    assert rehydrated.archive_manifest.summary == report.result_manifest.summary
    assert rehydrated.archive_manifest.commands[0].command_text.endswith(
        "run_runtime_package_smoke_workflow"
    )

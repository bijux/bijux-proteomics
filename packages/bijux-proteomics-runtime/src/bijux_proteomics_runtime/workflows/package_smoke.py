# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Compact runtime-owned workflow smoke path over core result archives."""

from __future__ import annotations

from pathlib import Path

from pydantic import ConfigDict, Field

from bijux_proteomics.workflow import (
    ResultManifestReport,
    ScaleDemoConfig,
    ProteomicsStudyResultSummary,
    build_result_manifest_from_artifacts,
    run_scale_demo,
)
from bijux_proteomics_foundation import JsonModel
from bijux_proteomics_runtime.rehydrate.loading import load_completed_run
from bijux_proteomics_runtime.support.workspace import write_text_atomic

_PACKAGE_SMOKE_COMMAND = (
    "bijux_proteomics_runtime.workflows.package_smoke."
    "run_runtime_package_smoke_workflow"
)


class RuntimePackageSmokeConfig(JsonModel):
    """Compact config for one runtime-owned end-to-end workflow smoke run."""

    model_config = ConfigDict(extra="forbid")

    output_dir: Path
    protein_count: int = Field(default=18, ge=12, le=96)
    peptides_per_protein: int = Field(default=3, ge=2, le=6)
    replicates_per_condition: int = Field(default=2, ge=2, le=4)
    pathway_count: int = Field(default=4, ge=3, le=16)


class RuntimePackageSmokeArtifacts(JsonModel):
    """Stable artifact locations written by the runtime package smoke workflow."""

    model_config = ConfigDict(extra="forbid")

    scale_demo_output_dir: str = Field(..., min_length=1)
    scale_demo_report_json: str = Field(..., min_length=1)
    biological_report_dir: str = Field(..., min_length=1)
    result_manifest_json: str = Field(..., min_length=1)
    smoke_report_json: str = Field(..., min_length=1)


class RuntimePackageSmokeWorkflowReport(JsonModel):
    """Reviewable report over the runtime-owned compact workflow smoke run."""

    model_config = ConfigDict(extra="forbid")

    config: RuntimePackageSmokeConfig
    scale_demo_elapsed_seconds: float = Field(..., ge=0.0)
    scale_demo_outputs_validated: bool
    result_manifest: ResultManifestReport
    study_result_summary: ProteomicsStudyResultSummary
    archive_validated: bool
    artifacts: RuntimePackageSmokeArtifacts
    note: str = Field(..., min_length=1)


def run_runtime_package_smoke_workflow(
    config: RuntimePackageSmokeConfig,
) -> RuntimePackageSmokeWorkflowReport:
    """Execute one compact runtime smoke workflow and validate the archived result."""

    output_dir = config.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    scale_demo_output_dir = output_dir / "scale_demo"
    scale_demo_report = run_scale_demo(
        ScaleDemoConfig(
            output_dir=scale_demo_output_dir,
            protein_count=config.protein_count,
            peptides_per_protein=config.peptides_per_protein,
            replicates_per_condition=config.replicates_per_condition,
            pathway_count=config.pathway_count,
        )
    )
    if not scale_demo_report.validation.outputs_validated:
        raise ValueError(
            "runtime package smoke workflow requires a validated core scale-demo export"
        )

    biological_report_dir = (
        scale_demo_output_dir / scale_demo_report.artifacts.biological_output_dir
    ).resolve()
    result_manifest = build_result_manifest_from_artifacts(
        biological_report_dir=biological_report_dir,
        commands=(_PACKAGE_SMOKE_COMMAND,),
    )
    if result_manifest.summary.missing_required_file_count != 0:
        raise ValueError(
            "runtime package smoke workflow requires a complete governed result archive"
        )

    result_manifest_path = output_dir / "result_manifest.json"
    write_text_atomic(result_manifest_path, result_manifest.to_stable_json() + "\n")
    study_result = load_completed_run(output_dir)
    artifacts = RuntimePackageSmokeArtifacts(
        scale_demo_output_dir=str(scale_demo_output_dir),
        scale_demo_report_json=str(
            (scale_demo_output_dir / scale_demo_report.artifacts.report_json).resolve()
        ),
        biological_report_dir=str(biological_report_dir),
        result_manifest_json=str(result_manifest_path.resolve()),
        smoke_report_json=str((output_dir / "runtime_package_smoke_report.json").resolve()),
    )
    report = RuntimePackageSmokeWorkflowReport(
        config=config,
        scale_demo_elapsed_seconds=scale_demo_report.summary.elapsed_seconds,
        scale_demo_outputs_validated=scale_demo_report.validation.outputs_validated,
        result_manifest=result_manifest,
        study_result_summary=study_result.summary,
        archive_validated=True,
        artifacts=artifacts,
        note=(
            "runtime package smoke workflow executes the core public workflow demo, "
            "builds a governed result archive manifest, and rehydrates the completed "
            "run through the runtime archive loader"
        ),
    )
    write_text_atomic(output_dir / "runtime_package_smoke_report.json", report.to_stable_json() + "\n")
    return report


__all__ = [
    "RuntimePackageSmokeArtifacts",
    "RuntimePackageSmokeConfig",
    "RuntimePackageSmokeWorkflowReport",
    "run_runtime_package_smoke_workflow",
]

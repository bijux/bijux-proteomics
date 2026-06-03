# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Runtime-owned architecture demo over the shipped surprising workflow demo."""

from __future__ import annotations

from pathlib import Path

from pydantic import ConfigDict, Field

from bijux_proteomics.workflow import (
    ProteomicsStudyResult,
    ProteomicsStudyResultSummary,
    ResultManifestReport,
    SurprisingDemoConfig,
    SurprisingDemoReport,
    WorkflowOutputValidationReport,
    WorkflowOutputValidationStatus,
    build_result_manifest_from_artifacts,
    build_workflow_output_validation_report,
    run_surprising_demo,
)
from bijux_proteomics_foundation import JsonModel
from bijux_proteomics_runtime.artifacts import StepArtifact, build_step_artifact
from bijux_proteomics_runtime.rehydrate.loading import load_completed_run
from bijux_proteomics_runtime.support.workspace import write_text_atomic

_ARCHITECTURE_DEMO_COMMAND = (
    "bijux_proteomics_runtime.workflows.architecture_demo.run_runtime_architecture_demo"
)


class RuntimeArchitectureDemoConfig(JsonModel):
    """Compact config for one runtime-owned architecture proof demo."""

    model_config = ConfigDict(extra="forbid")

    output_dir: Path
    example_root: Path | None = None


class RuntimeArchitectureDemoArtifacts(JsonModel):
    """Stable artifact locations written by the runtime architecture demo."""

    model_config = ConfigDict(extra="forbid")

    demo_output_dir: str = Field(..., min_length=1)
    demo_report_json: str = Field(..., min_length=1)
    biological_report_dir: str = Field(..., min_length=1)
    workflow_output_validation_json: str = Field(..., min_length=1)
    runtime_step_artifacts_json: str = Field(..., min_length=1)
    result_manifest_json: str = Field(..., min_length=1)
    architecture_demo_report_json: str = Field(..., min_length=1)


class RuntimeArchitectureDemoWorkflowReport(JsonModel):
    """Reviewable report over the runtime-owned architecture proof demo."""

    model_config = ConfigDict(extra="forbid")

    config: RuntimeArchitectureDemoConfig
    demo_elapsed_seconds: float = Field(..., ge=0.0)
    workflow_output_validated: bool
    workflow_output_validation: WorkflowOutputValidationReport
    result_manifest: ResultManifestReport
    direct_study_result_summary: ProteomicsStudyResultSummary
    rehydrated_study_result_summary: ProteomicsStudyResultSummary
    scientific_surfaces_preserved: bool
    archive_validated: bool
    runtime_step_artifacts: tuple[StepArtifact, ...] = Field(default_factory=tuple)
    artifacts: RuntimeArchitectureDemoArtifacts
    note: str = Field(..., min_length=1)


class _RuntimeArchitectureDemoStepLedger(JsonModel):
    """Persisted step-artifact ledger for one architecture demo run."""

    model_config = ConfigDict(extra="forbid")

    steps: tuple[StepArtifact, ...] = Field(default_factory=tuple)


def run_runtime_architecture_demo(
    config: RuntimeArchitectureDemoConfig,
) -> RuntimeArchitectureDemoWorkflowReport:
    """Execute the shipped demo through runtime and archive the resulting study result."""

    output_dir = config.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    demo_output_dir = output_dir / "surprising_demo"
    demo_report = run_surprising_demo(
        SurprisingDemoConfig(
            output_dir=demo_output_dir,
            example_root=config.example_root,
        )
    )
    biological_report_dir = (
        demo_output_dir / demo_report.artifacts.biological_output_dir
    ).resolve()
    workflow_output_validation = build_workflow_output_validation_report(
        biological_report_dir
    )
    if workflow_output_validation.status is not WorkflowOutputValidationStatus.VALID:
        raise ValueError(
            "runtime architecture demo requires a valid governed workflow output directory"
        )

    result_manifest = build_result_manifest_from_artifacts(
        biological_report_dir=biological_report_dir,
        commands=(_ARCHITECTURE_DEMO_COMMAND,),
    )
    if result_manifest.summary.missing_required_file_count != 0:
        raise ValueError(
            "runtime architecture demo requires a complete governed result archive"
        )

    result_manifest_path = output_dir / "result_manifest.json"
    write_text_atomic(result_manifest_path, result_manifest.to_stable_json() + "\n")
    rehydrated_study_result = load_completed_run(output_dir)
    scientific_surfaces_preserved = _archive_preserves_scientific_surfaces(
        demo_report.study_result,
        rehydrated_study_result,
    )
    if not scientific_surfaces_preserved:
        raise ValueError(
            "runtime architecture demo requires archive rehydration to preserve the "
            "scientific design, statistics, cards, and conclusions carried by the "
            "direct demo result"
        )

    runtime_step_artifacts = _build_runtime_step_artifacts(
        config=config,
        demo_report=demo_report,
        biological_report_dir=biological_report_dir,
        workflow_output_validation=workflow_output_validation,
        result_manifest=result_manifest,
        rehydrated_study_result_summary=rehydrated_study_result.summary,
    )
    workflow_output_validation_path = output_dir / "workflow_output_validation.json"
    write_text_atomic(
        workflow_output_validation_path,
        workflow_output_validation.to_stable_json() + "\n",
    )
    runtime_step_artifacts_path = output_dir / "runtime_step_artifacts.json"
    write_text_atomic(
        runtime_step_artifacts_path,
        _RuntimeArchitectureDemoStepLedger(
            steps=runtime_step_artifacts
        ).to_stable_json()
        + "\n",
    )

    artifacts = RuntimeArchitectureDemoArtifacts(
        demo_output_dir=str(demo_output_dir.resolve()),
        demo_report_json=str(
            (demo_output_dir / demo_report.artifacts.report_json).resolve()
        ),
        biological_report_dir=str(biological_report_dir),
        workflow_output_validation_json=str(workflow_output_validation_path.resolve()),
        runtime_step_artifacts_json=str(runtime_step_artifacts_path.resolve()),
        result_manifest_json=str(result_manifest_path.resolve()),
        architecture_demo_report_json=str(
            (output_dir / "runtime_architecture_demo_report.json").resolve()
        ),
    )
    report = RuntimeArchitectureDemoWorkflowReport(
        config=config,
        demo_elapsed_seconds=demo_report.summary.elapsed_seconds,
        workflow_output_validated=True,
        workflow_output_validation=workflow_output_validation,
        result_manifest=result_manifest,
        direct_study_result_summary=demo_report.study_result.summary,
        rehydrated_study_result_summary=rehydrated_study_result.summary,
        scientific_surfaces_preserved=scientific_surfaces_preserved,
        archive_validated=True,
        runtime_step_artifacts=runtime_step_artifacts,
        artifacts=artifacts,
        note=(
            "runtime architecture demo proves the shipped surprising demo travels "
            "through runtime ownership into the public workflow surface, reaches "
            "core-owned report assembly, and preserves the completed study result "
            "through archive validation and runtime rehydration while allowing the "
            "archive loader to add archive-only matrix and QC surfaces"
        ),
    )
    write_text_atomic(
        output_dir / "runtime_architecture_demo_report.json",
        report.to_stable_json() + "\n",
    )
    return report


def _build_runtime_step_artifacts(
    *,
    config: RuntimeArchitectureDemoConfig,
    demo_report: SurprisingDemoReport,
    biological_report_dir: Path,
    workflow_output_validation: WorkflowOutputValidationReport,
    result_manifest: ResultManifestReport,
    rehydrated_study_result_summary: ProteomicsStudyResultSummary,
) -> tuple[StepArtifact, ...]:
    return (
        build_step_artifact(
            step_id="run-surprising-demo",
            description=(
                "runtime invoked the shipped surprising demo through the public workflow "
                "surface and captured the resulting cross-package scientific outputs"
            ),
            status="completed",
            input_payloads={
                "config": config,
                "command": _ARCHITECTURE_DEMO_COMMAND,
            },
            output_payloads={
                "summary": demo_report.summary,
                "study_result_summary": demo_report.study_result.summary,
                "targeted_summary": demo_report.targeted_report.summary,
                "intelligence_summary": demo_report.intelligence_report_contract.summary,
            },
            entity_counts={
                "findings": len(demo_report.findings),
                "claims": len(demo_report.claim_report),
                "qc_surfaces": demo_report.study_result.summary.qc_surface_count,
            },
            schema_names=(
                "surprising_demo_report",
                "proteomics_study_result",
                "intelligence_report_contract",
            ),
        ),
        build_step_artifact(
            step_id="validate-workflow-output",
            description=(
                "runtime validated the core-owned biological workflow output directory "
                "before archiving the completed study result"
            ),
            status="completed",
            input_payloads={
                "biological_output_dir": str(biological_report_dir),
                "producer_function": workflow_output_validation.producer_function,
            },
            output_payloads={"validation": workflow_output_validation},
            entity_counts={
                "artifacts": workflow_output_validation.artifact_count,
                "issues": workflow_output_validation.issue_count,
                "checks": len(workflow_output_validation.checks),
            },
            schema_names=("workflow_output_validation",),
        ),
        build_step_artifact(
            step_id="build-result-archive",
            description=(
                "runtime built the governed result archive manifest and rehydrated the "
                "completed study result without rerunning the workflow"
            ),
            status="completed",
            input_payloads={
                "workflow_output_validation": workflow_output_validation,
                "command": _ARCHITECTURE_DEMO_COMMAND,
            },
            output_payloads={
                "result_manifest": result_manifest,
                "rehydrated_study_result_summary": rehydrated_study_result_summary,
            },
            entity_counts={
                "files": result_manifest.summary.file_count,
                "samples": result_manifest.summary.sample_count,
                "proteins": result_manifest.summary.protein_count,
            },
            schema_names=("result_manifest", "proteomics_study_result"),
        ),
    )


def _archive_preserves_scientific_surfaces(
    direct_result: ProteomicsStudyResult,
    rehydrated_result: ProteomicsStudyResult,
) -> bool:
    return (
        direct_result.design.sample_count == rehydrated_result.design.sample_count
        and direct_result.design.condition_count
        == rehydrated_result.design.condition_count
        and direct_result.design.batch_count == rehydrated_result.design.batch_count
        and direct_result.design.paired_sample_count
        == rehydrated_result.design.paired_sample_count
        and direct_result.design.multiplexed_sample_count
        == rehydrated_result.design.multiplexed_sample_count
        and _normalize_statistic_surfaces(direct_result)
        == _normalize_statistic_surfaces(rehydrated_result)
        and _normalize_card_surfaces(direct_result)
        == _normalize_card_surfaces(rehydrated_result)
        and _normalize_conclusions(direct_result)
        == _normalize_conclusions(rehydrated_result)
    )


def _normalize_statistic_surfaces(
    result: ProteomicsStudyResult,
) -> tuple[tuple[str, int, int], ...]:
    return tuple(
        (
            surface.kind.value,
            surface.entity_count,
            surface.significant_entity_count,
        )
        for surface in result.statistic_surfaces
    )


def _normalize_card_surfaces(
    result: ProteomicsStudyResult,
) -> tuple[tuple[str, int, int], ...]:
    return tuple(
        (
            surface.kind.value,
            surface.card_count,
            surface.warning_count,
        )
        for surface in result.card_surfaces
    )


def _normalize_conclusions(
    result: ProteomicsStudyResult,
) -> tuple[tuple[str, str, str, str, str, float | None, str], ...]:
    return tuple(
        (
            conclusion.conclusion_id,
            conclusion.kind.value,
            conclusion.subject_id,
            conclusion.subject_label,
            conclusion.status,
            conclusion.score,
            conclusion.summary_text,
        )
        for conclusion in result.biological_conclusions
    )


__all__ = [
    "RuntimeArchitectureDemoArtifacts",
    "RuntimeArchitectureDemoConfig",
    "RuntimeArchitectureDemoWorkflowReport",
    "run_runtime_architecture_demo",
]

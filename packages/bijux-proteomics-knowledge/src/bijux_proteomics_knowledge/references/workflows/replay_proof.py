# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Typed replay-proof surfaces for benchmark-backed workflow references."""

from __future__ import annotations

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation.serialization.json_contracts import JsonModel
from bijux_proteomics_knowledge.references.workflows.benchmarks import (
    DEFAULT_BENCHMARK_MANIFESTS,
    BenchmarkManifest,
    BenchmarkPackageArtifactKind,
    KnowledgeWorkflowFamily,
)


class WorkflowReplayArtifactProof(JsonModel):
    """One governed artifact that anchors a replayable benchmark surface."""

    model_config = ConfigDict(extra="forbid")

    artifact_id: str = Field(..., min_length=1)
    artifact_kind: BenchmarkPackageArtifactKind
    repo_relative_path: str = Field(..., min_length=1)
    required_for_replay: bool = True
    note: str = Field(..., min_length=1)


class WorkflowReplayStepProof(JsonModel):
    """One replay step with its artifact anchors and execution boundary."""

    model_config = ConfigDict(extra="forbid")

    step_id: str = Field(..., min_length=1)
    summary: str = Field(..., min_length=1)
    artifact_ids: tuple[str, ...] = Field(default_factory=tuple)
    expected_outputs: tuple[str, ...] = Field(default_factory=tuple)
    outside_repo_execution: bool = False


class WorkflowReplayProofReport(JsonModel):
    """Replay-proof report for one benchmark-backed workflow family."""

    model_config = ConfigDict(extra="forbid")

    report_id: str = Field(..., min_length=1)
    benchmark_id: str = Field(..., min_length=1)
    workflow_family: KnowledgeWorkflowFamily
    benchmark_package_id: str | None = None
    replay_supported: bool
    validating_tests: tuple[str, ...] = Field(default_factory=tuple)
    artifact_proofs: tuple[WorkflowReplayArtifactProof, ...] = Field(
        default_factory=tuple
    )
    replay_steps: tuple[WorkflowReplayStepProof, ...] = Field(default_factory=tuple)
    replay_limit_summary: tuple[str, ...] = Field(default_factory=tuple)
    bounded_by_external_execution: bool = False


class WorkflowReplayProofLedger(JsonModel):
    """Replay-proof ledger across all curated workflow benchmark families."""

    model_config = ConfigDict(extra="forbid")

    reports: tuple[WorkflowReplayProofReport, ...] = Field(default_factory=tuple)


_VALIDATING_TESTS_BY_WORKFLOW: dict[KnowledgeWorkflowFamily, tuple[str, ...]] = {
    KnowledgeWorkflowFamily.DDA: (
        "packages/bijux-proteomics-knowledge/tests/references/test_replay_proof_surface.py",
        "packages/bijux-proteomics-knowledge/tests/references/test_benchmark_packages.py",
        "packages/bijux-proteomics-core/tests/identification/test_search_adapter_loss_surface.py",
    ),
    KnowledgeWorkflowFamily.DIA: (
        "packages/bijux-proteomics-knowledge/tests/references/test_replay_proof_surface.py",
        "packages/bijux-proteomics-core/tests/dia/test_scientific_support_surface.py",
    ),
    KnowledgeWorkflowFamily.PTM: (
        "packages/bijux-proteomics-knowledge/tests/references/test_replay_proof_surface.py",
        "packages/bijux-proteomics-core/tests/ptm/test_ptm_scientific_benchmark_surface.py",
    ),
    KnowledgeWorkflowFamily.LFQ: (
        "packages/bijux-proteomics-knowledge/tests/references/test_replay_proof_surface.py",
        "packages/bijux-proteomics-core/tests/quantification/test_quantification_scientific_benchmark_surface.py",
    ),
    KnowledgeWorkflowFamily.MULTIPLEX: (
        "packages/bijux-proteomics-knowledge/tests/references/test_replay_proof_surface.py",
        "packages/bijux-proteomics-core/tests/quantification/test_quantification_scientific_benchmark_surface.py",
    ),
    KnowledgeWorkflowFamily.TARGETED: (
        "packages/bijux-proteomics-knowledge/tests/references/test_replay_proof_surface.py",
        "packages/bijux-proteomics-core/tests/dia/test_targeted_benchmark_surface.py",
    ),
}


def build_workflow_replay_proof_report(
    manifest: BenchmarkManifest,
) -> WorkflowReplayProofReport:
    """Build a replay-proof report from a benchmark package manifest."""

    package = manifest.benchmark_package
    if package is None:
        return WorkflowReplayProofReport(
            report_id=f"replay_report:{manifest.workflow_family.value}",
            benchmark_id=manifest.benchmark_id,
            workflow_family=manifest.workflow_family,
            replay_supported=False,
            validating_tests=_VALIDATING_TESTS_BY_WORKFLOW[manifest.workflow_family],
            replay_limit_summary=(
                "benchmark manifest has no promoted replay package, so replay proof is limited to manifest review only",
            ),
            bounded_by_external_execution=True,
        )

    artifact_proofs = tuple(
        WorkflowReplayArtifactProof(
            artifact_id=artifact.artifact_id,
            artifact_kind=artifact.artifact_kind,
            repo_relative_path=artifact.repo_relative_path,
            required_for_replay=artifact.required_for_reproduction,
            note=artifact.note,
        )
        for artifact in package.package_artifacts
    )
    replay_steps = tuple(
        WorkflowReplayStepProof(
            step_id=step.step_id,
            summary=step.summary,
            artifact_ids=step.artifact_ids,
            expected_outputs=step.expected_outputs,
            outside_repo_execution=step.outside_repo_execution,
        )
        for step in package.reproduction_steps
    )
    return WorkflowReplayProofReport(
        report_id=f"replay_report:{manifest.workflow_family.value}",
        benchmark_id=manifest.benchmark_id,
        workflow_family=manifest.workflow_family,
        benchmark_package_id=package.package_id,
        replay_supported=True,
        validating_tests=_VALIDATING_TESTS_BY_WORKFLOW[manifest.workflow_family],
        artifact_proofs=artifact_proofs,
        replay_steps=replay_steps,
        replay_limit_summary=(
            *manifest.reproduction_requirements,
            *manifest.fixture_realism_limits,
        ),
        bounded_by_external_execution=any(
            step.outside_repo_execution for step in package.reproduction_steps
        ),
    )


def build_workflow_replay_proof_ledger(
    *,
    workflow_family: KnowledgeWorkflowFamily | None = None,
) -> WorkflowReplayProofLedger:
    """Build replay-proof reports across curated benchmark manifests."""

    manifests = (
        DEFAULT_BENCHMARK_MANIFESTS
        if workflow_family is None
        else tuple(
            manifest
            for manifest in DEFAULT_BENCHMARK_MANIFESTS
            if manifest.workflow_family is workflow_family
        )
    )
    return WorkflowReplayProofLedger(
        reports=tuple(
            build_workflow_replay_proof_report(manifest) for manifest in manifests
        )
    )

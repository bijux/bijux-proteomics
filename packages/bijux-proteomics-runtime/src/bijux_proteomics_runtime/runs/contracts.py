# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Typed runtime context contracts for replay-safe execution state."""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path
import platform
import socket
import sys

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel, hash_payload, hash_text


class RuntimeDatasetKind(StrEnum):
    """Supported dataset identity origins for runtime-managed runs."""

    INLINE_SEQUENCE = "inline_sequence"
    CANDIDATE_STORE = "candidate_store"
    IMPORTED_EVIDENCE = "imported_evidence"


class RuntimeArtifactRetentionClass(StrEnum):
    """Retention classes that keep replay and review artifacts distinct."""

    TRANSIENT = "transient"
    REPLAY_REQUIRED = "replay_required"
    REVIEW_REQUIRED = "review_required"
    FAILURE_FORENSICS = "failure_forensics"
    AUDIT_REQUIRED = "audit_required"


class DatasetIdentity(JsonModel):
    """Stable dataset identity for one runtime execution request."""

    model_config = ConfigDict(extra="forbid")

    dataset_id: str = Field(..., min_length=1)
    dataset_kind: RuntimeDatasetKind
    dataset_fingerprint: str = Field(..., min_length=1)
    source_path: str | None = Field(default=None)


class WorkflowIdentity(JsonModel):
    """Stable workflow identity for one runtime execution request."""

    model_config = ConfigDict(extra="forbid")

    workflow_id: str = Field(..., min_length=1)
    command: str = Field(..., min_length=1)
    workflow_family: str = Field(..., min_length=1)
    import_only: bool = False


class RuntimeEnvironmentIdentity(JsonModel):
    """Stable execution environment identity for one runtime run."""

    model_config = ConfigDict(extra="forbid")

    environment_id: str = Field(..., min_length=1)
    host_name: str = Field(..., min_length=1)
    platform: str = Field(..., min_length=1)
    python_version: str = Field(..., min_length=1)
    working_directory: str = Field(..., min_length=1)


class RuntimeArtifactPolicy(JsonModel):
    """Artifact policy that governs hashing, inlining, and retention defaults."""

    model_config = ConfigDict(extra="forbid")

    artifacts_root: str = Field(..., min_length=1)
    hash_policy_id: str = Field(default="bijux-stable-sha256-v1", min_length=1)
    inline_limit_bytes: int = Field(default=256_000, ge=1)
    retention_by_role: dict[str, RuntimeArtifactRetentionClass] = Field(
        default_factory=dict
    )


class RunLineage(JsonModel):
    """Lineage metadata for resumed and imported runs."""

    model_config = ConfigDict(extra="forbid")

    parent_run_id: str | None = Field(default=None)
    resume_depth: int = Field(default=0, ge=0)


class RunContextContract(JsonModel):
    """Canonical runtime context contract used by replay and audits."""

    model_config = ConfigDict(extra="forbid")

    run_id: str = Field(..., min_length=1)
    started_at: str = Field(..., min_length=1)
    candidate_id: str | None = Field(default=None)
    provider_name: str = Field(..., min_length=1)
    config_fingerprint: str = Field(..., min_length=1)
    dataset: DatasetIdentity
    workflow: WorkflowIdentity
    environment: RuntimeEnvironmentIdentity
    artifact_policy: RuntimeArtifactPolicy
    lineage: RunLineage = Field(default_factory=RunLineage)


def build_runtime_environment(base_dir: Path) -> RuntimeEnvironmentIdentity:
    """Return a stable runtime environment identity for one workspace."""
    payload = {
        "host_name": socket.gethostname(),
        "platform": platform.platform(),
        "python_version": sys.version.split()[0],
        "working_directory": str(base_dir.resolve()),
    }
    environment_id = f"env_{hash_payload(payload)}"
    return RuntimeEnvironmentIdentity(environment_id=environment_id, **payload)


def default_runtime_artifact_policy(artifacts_root: Path) -> RuntimeArtifactPolicy:
    """Return the default runtime artifact policy for one artifacts root."""
    return RuntimeArtifactPolicy(
        artifacts_root=str(artifacts_root),
        retention_by_role={
            "runtime-config": RuntimeArtifactRetentionClass.REPLAY_REQUIRED,
            "runtime-plan": RuntimeArtifactRetentionClass.REPLAY_REQUIRED,
            "runtime-state": RuntimeArtifactRetentionClass.TRANSIENT,
            "runtime-report": RuntimeArtifactRetentionClass.REVIEW_REQUIRED,
            "runtime-telemetry": RuntimeArtifactRetentionClass.AUDIT_REQUIRED,
            "runtime-analysis": RuntimeArtifactRetentionClass.AUDIT_REQUIRED,
            "runtime-execution": RuntimeArtifactRetentionClass.AUDIT_REQUIRED,
            "runtime-status": RuntimeArtifactRetentionClass.REVIEW_REQUIRED,
            "runtime-output": RuntimeArtifactRetentionClass.REPLAY_REQUIRED,
            "runtime-error": RuntimeArtifactRetentionClass.FAILURE_FORENSICS,
            "runtime-failure-report": RuntimeArtifactRetentionClass.FAILURE_FORENSICS,
            "runtime-run-context": RuntimeArtifactRetentionClass.REPLAY_REQUIRED,
            "runtime-artifact-ledger": RuntimeArtifactRetentionClass.AUDIT_REQUIRED,
            "runtime-local-run-bundle": RuntimeArtifactRetentionClass.REPLAY_REQUIRED,
            "runtime-container-run-bundle": RuntimeArtifactRetentionClass.REPLAY_REQUIRED,
            "runtime-scheduler-job-bundle": RuntimeArtifactRetentionClass.REPLAY_REQUIRED,
            "runtime-import-trace": RuntimeArtifactRetentionClass.AUDIT_REQUIRED,
            "runtime-import-run-bundle": RuntimeArtifactRetentionClass.REPLAY_REQUIRED,
            "runtime-resume-checkpoint": RuntimeArtifactRetentionClass.REPLAY_REQUIRED,
            "runtime-integrity-report": RuntimeArtifactRetentionClass.AUDIT_REQUIRED,
            "runtime-replay-contract": RuntimeArtifactRetentionClass.REPLAY_REQUIRED,
            "runtime-preflight-report": RuntimeArtifactRetentionClass.AUDIT_REQUIRED,
        },
    )


def build_run_context_contract(
    *,
    run_id: str,
    started_at: str,
    base_dir: Path,
    config: dict[str, object],
    provider_name: str,
    artifact_policy: RuntimeArtifactPolicy,
    sequence: str,
    command: str,
    workflow_family: str,
    candidate_id: str | None = None,
    dataset_kind: RuntimeDatasetKind = RuntimeDatasetKind.INLINE_SEQUENCE,
    source_path: Path | None = None,
    parent_run_id: str | None = None,
    resume_depth: int = 0,
    import_only: bool = False,
) -> RunContextContract:
    """Build the canonical run-context contract for one runtime execution."""
    dataset_fingerprint = hash_text(sequence)
    source_path_value = None if source_path is None else str(source_path)
    dataset = DatasetIdentity(
        dataset_id=f"dataset_{dataset_fingerprint}",
        dataset_kind=dataset_kind,
        dataset_fingerprint=dataset_fingerprint,
        source_path=source_path_value,
    )
    workflow_fingerprint = hash_payload(
        {
            "command": command,
            "workflow_family": workflow_family,
            "import_only": import_only,
            "provider_name": provider_name,
            "dataset_fingerprint": dataset_fingerprint,
        }
    )
    workflow = WorkflowIdentity(
        workflow_id=f"workflow_{workflow_fingerprint}",
        command=command,
        workflow_family=workflow_family,
        import_only=import_only,
    )
    config_fingerprint = hash_payload(config)
    return RunContextContract(
        run_id=run_id,
        started_at=started_at,
        candidate_id=candidate_id,
        provider_name=provider_name,
        config_fingerprint=config_fingerprint,
        dataset=dataset,
        workflow=workflow,
        environment=build_runtime_environment(base_dir),
        artifact_policy=artifact_policy,
        lineage=RunLineage(parent_run_id=parent_run_id, resume_depth=resume_depth),
    )


__all__ = [
    "DatasetIdentity",
    "RunContextContract",
    "RunLineage",
    "RuntimeArtifactPolicy",
    "RuntimeArtifactRetentionClass",
    "RuntimeDatasetKind",
    "RuntimeEnvironmentIdentity",
    "WorkflowIdentity",
    "build_run_context_contract",
    "build_runtime_environment",
    "default_runtime_artifact_policy",
]

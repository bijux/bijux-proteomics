# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Runtime-owned execution surface bundles for non-local launches."""

from __future__ import annotations

from datetime import UTC, datetime

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel
from bijux_proteomics_runtime.runs.contracts import (
    RunContextContract,
    RuntimeArtifactRetentionClass,
)
from bijux_proteomics_runtime.runtime.control.integrity import (
    require_reusable_artifact_bundle,
)
from bijux_proteomics_runtime.runtime.control.replay import ReplayContract
from bijux_proteomics_runtime.runtime.workspace import RunWorkspace, write_json_atomic


class ArtifactExpectation(JsonModel):
    """Expected runtime-managed artifact for one execution surface."""

    model_config = ConfigDict(extra="forbid")

    artifact_kind: str = Field(..., min_length=1)
    required: bool = True
    retention_class: RuntimeArtifactRetentionClass
    note: str = Field(..., min_length=1)


class ContainerMount(JsonModel):
    """One container mount declared by runtime."""

    model_config = ConfigDict(extra="forbid")

    source_path: str = Field(..., min_length=1)
    target_path: str = Field(..., min_length=1)
    access_mode: str = Field(..., min_length=1)


class ContainerEnvironmentCapture(JsonModel):
    """Stable environment capture for one container launch."""

    model_config = ConfigDict(extra="forbid")

    execution_mode: str = Field(..., min_length=1)
    enabled_predictors: tuple[str, ...] = Field(default_factory=tuple)
    tool_versions: dict[str, str] = Field(default_factory=dict)


class ContainerRunBundle(JsonModel):
    """Replay-safe runtime bundle for one container launch."""

    model_config = ConfigDict(extra="forbid")

    launch_surface: str = Field(default="container", min_length=1)
    run_context: RunContextContract
    replay_contract: ReplayContract
    image_reference: str = Field(..., min_length=1)
    image_digest: str = Field(..., min_length=1)
    mount_maps: tuple[ContainerMount, ...] = Field(default_factory=tuple)
    environment_capture: ContainerEnvironmentCapture
    artifact_expectations: tuple[ArtifactExpectation, ...] = Field(
        default_factory=tuple
    )


class SchedulerLaunchMetadata(JsonModel):
    """Launch metadata that defines one scheduler-submitted runtime job."""

    model_config = ConfigDict(extra="forbid")

    scheduler_system: str = Field(..., min_length=1)
    queue_name: str = Field(..., min_length=1)
    job_name: str = Field(..., min_length=1)
    submitted_at: str = Field(..., min_length=1)
    submission_id: str = Field(..., min_length=1)


class SchedulerReplayBoundary(JsonModel):
    """Boundary that explains what runtime can replay automatically."""

    model_config = ConfigDict(extra="forbid")

    automatic_replay_safe: bool
    requires_human_resume: bool
    note: str = Field(..., min_length=1)


class SchedulerJobBundle(JsonModel):
    """Replay-safe runtime bundle for one scheduler launch."""

    model_config = ConfigDict(extra="forbid")

    launch_surface: str = Field(default="scheduler", min_length=1)
    run_context: RunContextContract
    replay_contract: ReplayContract
    launch_metadata: SchedulerLaunchMetadata
    replay_boundary: SchedulerReplayBoundary
    artifact_expectations: tuple[ArtifactExpectation, ...] = Field(
        default_factory=tuple
    )


def default_artifact_expectations() -> tuple[ArtifactExpectation, ...]:
    """Return the runtime artifacts required across non-local launches."""
    return (
        ArtifactExpectation(
            artifact_kind="runtime-run-context",
            retention_class=RuntimeArtifactRetentionClass.REPLAY_REQUIRED,
            note="run context must survive to explain the launch contract",
        ),
        ArtifactExpectation(
            artifact_kind="runtime-replay-contract",
            retention_class=RuntimeArtifactRetentionClass.REPLAY_REQUIRED,
            note="replay contract must survive to prove rerun boundaries",
        ),
        ArtifactExpectation(
            artifact_kind="runtime-artifact-ledger",
            retention_class=RuntimeArtifactRetentionClass.AUDIT_REQUIRED,
            note="artifact ledger must survive to verify produced outputs",
        ),
        ArtifactExpectation(
            artifact_kind="runtime-status",
            retention_class=RuntimeArtifactRetentionClass.REVIEW_REQUIRED,
            note="run summary must survive for operator and reviewer lookup",
        ),
    )


def default_container_mounts(workspace: RunWorkspace) -> tuple[ContainerMount, ...]:
    """Return the runtime-owned default mount map for container launches."""
    return (
        ContainerMount(
            source_path=str(workspace.base_dir),
            target_path="/workspace",
            access_mode="ro",
        ),
        ContainerMount(
            source_path=str(workspace.artifacts_root),
            target_path="/artifacts",
            access_mode="rw",
        ),
    )


def build_container_run_bundle(
    *,
    workspace: RunWorkspace,
    run_context: RunContextContract,
    replay_contract: ReplayContract,
    config: dict[str, object],
) -> ContainerRunBundle:
    """Build a stable runtime bundle for one container launch."""
    image_reference = str(
        config.get("container_image") or "ghcr.io/bijux/proteomics-runtime:latest"
    )
    image_digest = str(
        config.get("container_image_digest") or "sha256:unknown-container-image"
    )
    return ContainerRunBundle(
        run_context=run_context,
        replay_contract=replay_contract,
        image_reference=image_reference,
        image_digest=image_digest,
        mount_maps=default_container_mounts(workspace),
        environment_capture=ContainerEnvironmentCapture(
            execution_mode=str(config.get("execution_mode") or "auto"),
            enabled_predictors=tuple(
                str(item) for item in (config.get("predictors_enabled") or [])
            ),
            tool_versions={
                str(key): str(value)
                for key, value in (config.get("tool_versions") or {}).items()
            },
        ),
        artifact_expectations=default_artifact_expectations(),
    )


def build_scheduler_job_bundle(
    *,
    run_context: RunContextContract,
    replay_contract: ReplayContract,
    config: dict[str, object],
) -> SchedulerJobBundle:
    """Build a stable runtime bundle for one scheduler launch."""
    scheduler_system = str(config.get("scheduler_system") or "unknown-scheduler")
    queue_name = str(config.get("scheduler_queue") or "default")
    job_name = str(config.get("scheduler_job_name") or f"bijux-{run_context.run_id}")
    submission_id = str(
        config.get("scheduler_submission_id")
        or f"{scheduler_system}:{run_context.run_id}"
    )
    return SchedulerJobBundle(
        run_context=run_context,
        replay_contract=replay_contract,
        launch_metadata=SchedulerLaunchMetadata(
            scheduler_system=scheduler_system,
            queue_name=queue_name,
            job_name=job_name,
            submitted_at=datetime.now(UTC).isoformat(),
            submission_id=submission_id,
        ),
        replay_boundary=SchedulerReplayBoundary(
            automatic_replay_safe=False,
            requires_human_resume=True,
            note="scheduler launches preserve submission metadata but require explicit operator replay",
        ),
        artifact_expectations=default_artifact_expectations(),
    )


def write_container_run_bundle(
    workspace: RunWorkspace, bundle: ContainerRunBundle
) -> None:
    """Persist one container run bundle."""
    write_json_atomic(workspace.container_run_bundle_path, bundle.to_dict())


def write_scheduler_job_bundle(
    workspace: RunWorkspace, bundle: SchedulerJobBundle
) -> None:
    """Persist one scheduler job bundle."""
    write_json_atomic(workspace.scheduler_job_bundle_path, bundle.to_dict())


def load_container_run_bundle(workspace: RunWorkspace) -> ContainerRunBundle:
    """Load one persisted container run bundle."""
    require_reusable_artifact_bundle(
        workspace,
        run_id=workspace.run_id,
        max_artifact_bytes=1_000_000,
        required_artifact_kinds=(
            "runtime-container-run-bundle",
            "runtime-replay-contract",
        ),
    )
    return ContainerRunBundle.load_json(workspace.container_run_bundle_path)


def load_scheduler_job_bundle(workspace: RunWorkspace) -> SchedulerJobBundle:
    """Load one persisted scheduler job bundle."""
    require_reusable_artifact_bundle(
        workspace,
        run_id=workspace.run_id,
        max_artifact_bytes=1_000_000,
        required_artifact_kinds=(
            "runtime-scheduler-job-bundle",
            "runtime-replay-contract",
        ),
    )
    return SchedulerJobBundle.load_json(workspace.scheduler_job_bundle_path)


__all__ = [
    "ArtifactExpectation",
    "ContainerEnvironmentCapture",
    "ContainerMount",
    "ContainerRunBundle",
    "SchedulerJobBundle",
    "SchedulerLaunchMetadata",
    "SchedulerReplayBoundary",
    "build_container_run_bundle",
    "build_scheduler_job_bundle",
    "default_artifact_expectations",
    "default_container_mounts",
    "load_container_run_bundle",
    "load_scheduler_job_bundle",
    "write_container_run_bundle",
    "write_scheduler_job_bundle",
]

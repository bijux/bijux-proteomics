# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Runtime cleanup planning that respects replay and review retention."""

from __future__ import annotations

from pathlib import Path

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel
from bijux_proteomics_runtime.runtime.context import RuntimeArtifactRetentionClass
from bijux_proteomics_runtime.runtime.control.ledger import load_artifact_ledger
from bijux_proteomics_runtime.runtime.workspace import RunWorkspace


class RuntimeCleanupArtifact(JsonModel):
    """One artifact decision inside a runtime cleanup plan."""

    model_config = ConfigDict(extra="forbid")

    artifact_kind: str = Field(..., min_length=1)
    path: str = Field(..., min_length=1)
    retention_class: RuntimeArtifactRetentionClass
    delete: bool
    reason: str = Field(..., min_length=1)


class RuntimeCleanupPlan(JsonModel):
    """Cleanup plan that keeps replay, review, and failure artifacts safe."""

    model_config = ConfigDict(extra="forbid")

    run_id: str = Field(..., min_length=1)
    removable_artifacts: tuple[RuntimeCleanupArtifact, ...] = Field(default_factory=tuple)
    preserved_artifacts: tuple[RuntimeCleanupArtifact, ...] = Field(default_factory=tuple)


def build_runtime_cleanup_plan(workspace: RunWorkspace, *, run_id: str) -> RuntimeCleanupPlan:
    """Build one cleanup plan from the current runtime artifact ledger."""
    removable_artifacts: list[RuntimeCleanupArtifact] = []
    preserved_artifacts: list[RuntimeCleanupArtifact] = []
    for entry in load_artifact_ledger(workspace, run_id).entries:
        artifact = RuntimeCleanupArtifact(
            artifact_kind=entry.artifact_kind,
            path=entry.path,
            retention_class=entry.retention_class,
            delete=entry.retention_class is RuntimeArtifactRetentionClass.TRANSIENT,
            reason=(
                "transient runtime output may be reclaimed after verification"
                if entry.retention_class is RuntimeArtifactRetentionClass.TRANSIENT
                else "retention policy preserves replay, review, or forensic output"
            ),
        )
        if artifact.delete:
            removable_artifacts.append(artifact)
        else:
            preserved_artifacts.append(artifact)
    return RuntimeCleanupPlan(
        run_id=run_id,
        removable_artifacts=tuple(removable_artifacts),
        preserved_artifacts=tuple(preserved_artifacts),
    )


def apply_runtime_cleanup_plan(plan: RuntimeCleanupPlan) -> None:
    """Apply one cleanup plan and delete only approved transient artifacts."""
    for artifact in plan.removable_artifacts:
        path = Path(artifact.path)
        if path.exists():
            path.unlink()


__all__ = [
    "RuntimeCleanupArtifact",
    "RuntimeCleanupPlan",
    "apply_runtime_cleanup_plan",
    "build_runtime_cleanup_plan",
]

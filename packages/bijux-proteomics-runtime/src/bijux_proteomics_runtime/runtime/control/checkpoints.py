# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Runtime checkpoint contracts for safe resume boundaries."""

from __future__ import annotations

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel, hash_payload
from bijux_proteomics_runtime.runs.contracts import RunContextContract
from bijux_proteomics_runtime.runtime.workspace import RunWorkspace, write_json_atomic


class ResumeCheckpoint(JsonModel):
    """One scientifically and operationally sound runtime resume checkpoint."""

    model_config = ConfigDict(extra="forbid")

    checkpoint_id: str = Field(..., min_length=1)
    run_id: str = Field(..., min_length=1)
    lifecycle_state: str = Field(..., min_length=1)
    resume_command: str = Field(..., min_length=1)
    scientific_rationale: str = Field(..., min_length=1)
    operational_rationale: str = Field(..., min_length=1)
    required_artifact_kinds: tuple[str, ...] = Field(default_factory=tuple)


def build_resume_checkpoint(
    *,
    run_context: RunContextContract,
    status: str,
    lifecycle_state: str,
    command: str,
) -> ResumeCheckpoint | None:
    """Return a checkpoint only when the runtime boundary is safe to resume."""
    if status != "partial":
        return None
    if lifecycle_state != "human_review":
        return None
    payload = {
        "run_id": run_context.run_id,
        "lifecycle_state": lifecycle_state,
        "command": command,
        "parent_run_id": run_context.lineage.parent_run_id,
        "resume_depth": run_context.lineage.resume_depth,
    }
    checkpoint_id = f"checkpoint_{hash_payload(payload)}"
    return ResumeCheckpoint(
        checkpoint_id=checkpoint_id,
        run_id=run_context.run_id,
        lifecycle_state=lifecycle_state,
        resume_command="resume",
        scientific_rationale="human review preserves candidate evidence without pretending an incomplete run is final",
        operational_rationale="operator sign-off is required before runtime continues beyond the review hold",
        required_artifact_kinds=(
            "runtime-run-context",
            "runtime-replay-contract",
            "runtime-artifact-ledger",
            "runtime-status",
        ),
    )


def write_resume_checkpoint(
    workspace: RunWorkspace, checkpoint: ResumeCheckpoint
) -> None:
    """Persist one resume checkpoint."""
    write_json_atomic(workspace.resume_checkpoint_path, checkpoint.to_dict())


def load_resume_checkpoint(workspace: RunWorkspace) -> ResumeCheckpoint:
    """Load one persisted resume checkpoint."""
    return ResumeCheckpoint.load_json(workspace.resume_checkpoint_path)


__all__ = [
    "ResumeCheckpoint",
    "build_resume_checkpoint",
    "load_resume_checkpoint",
    "write_resume_checkpoint",
]

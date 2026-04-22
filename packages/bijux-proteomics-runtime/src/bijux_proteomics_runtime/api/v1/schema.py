# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""API request/response schemas."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import AnyUrl, BaseModel, ConfigDict, Field, model_validator

from agentic_proteins.core.failures import FailureType
from agentic_proteins.core.status import (
    ExecutionStatus,
    Outcome,
    ToolStatus,
    WorkflowState,
)


class ErrorResponse(BaseModel):
    """ErrorResponse."""

    model_config = ConfigDict(extra="forbid")

    type: AnyUrl = Field(default=AnyUrl("about:blank"), description="Problem type URI.")
    title: str = Field(..., description="Short, human-readable summary.")
    status: int = Field(..., description="HTTP status code.")
    detail: str = Field(..., description="Human-readable explanation.")
    instance: str = Field(..., description="URI reference for this occurrence.")


class VersionInfo(BaseModel):
    """VersionInfo."""

    model_config = ConfigDict(extra="forbid")

    app: str = Field(..., description="Application version.")
    git_commit: str = Field(..., description="Git commit hash.")
    tool_versions: dict[str, str] = Field(
        default_factory=dict, description="Tool version mapping."
    )


class RunResponse(BaseModel):
    """RunResponse."""

    model_config = ConfigDict(extra="forbid")

    run_id: str = Field(..., min_length=1, description="Run identifier.")
    candidate_id: str = Field(..., min_length=1, description="Candidate identifier.")
    command: str = Field(..., description="Command name.")
    execution_status: ExecutionStatus = Field(..., description="Execution status.")
    workflow_state: WorkflowState = Field(..., description="Workflow state.")
    outcome: Outcome = Field(..., description="Outcome.")
    provider: str = Field(..., description="Provider name.")
    tool_status: ToolStatus = Field(..., description="Tool status.")
    qc_status: str = Field(..., description="QC status.")
    artifacts_dir: str = Field(..., description="Artifacts directory.")
    warnings: list[str] = Field(default_factory=list, description="Warnings.")
    failure: FailureType | None = Field(default=None, description="Failure type.")
    version: VersionInfo = Field(..., description="Version info.")


class RunRequest(BaseModel):
    """RunRequest."""

    model_config = ConfigDict(extra="forbid")

    sequence: str | None = Field(
        default=None, min_length=1, description="Inline sequence."
    )
    sequence_file: str | None = Field(
        default=None, min_length=1, description="FASTA file path on server."
    )
    ground_truth: str | None = Field(
        default=None, description="Optional ground-truth reference."
    )
    rounds: int = Field(1, ge=1, description="Loop iterations.")
    provider: str | None = Field(default=None, description="Optional provider.")
    artifacts_dir: str | None = Field(default=None, description="Artifacts root.")
    dry_run: bool = Field(default=False, description="Dry-run mode.")
    execution_mode: str = Field(default="auto", description="Provider execution mode.")

    @model_validator(mode="after")
    def _check_sequence(self) -> RunRequest:
        """_check_sequence."""
        if self.sequence and self.sequence_file:
            raise ValueError("Provide sequence or sequence_file, not both.")
        if not self.sequence and not self.sequence_file:
            raise ValueError("Provide sequence or sequence_file.")
        return self


class ResumeRequest(BaseModel):
    """ResumeRequest."""

    model_config = ConfigDict(extra="forbid")

    run_id: str | None = Field(
        default=None, min_length=1, description="Run identifier."
    )
    candidate_id: str | None = Field(
        default=None, min_length=1, description="Candidate identifier."
    )
    rounds: int = Field(1, ge=1, description="Loop iterations.")
    provider: str | None = Field(default=None, description="Optional provider.")
    artifacts_dir: str | None = Field(default=None, description="Artifacts root.")
    execution_mode: str = Field(default="auto", description="Provider execution mode.")

    @model_validator(mode="after")
    def _check_resume_target(self) -> ResumeRequest:
        """_check_resume_target."""
        if not self.run_id and not self.candidate_id:
            raise ValueError("Provide run_id or candidate_id.")
        return self


class CompareRequest(BaseModel):
    """CompareRequest."""

    model_config = ConfigDict(extra="forbid")

    run_id_a: str = Field(..., min_length=1, description="First run id.")
    run_id_b: str = Field(..., min_length=1, description="Second run id.")


class CompareResponse(BaseModel):
    """CompareResponse."""

    model_config = ConfigDict(extra="forbid")

    run_ids: dict[str, str | None] = Field(..., description="Run ids.")
    final_outcome: dict[str, dict[str, Any]] = Field(
        ..., description="Final outcome summaries."
    )
    candidate_trajectories: dict[str, Any] = Field(
        ..., description="Candidate trajectories."
    )
    iteration_deltas: dict[str, Any] = Field(..., description="Iteration deltas.")


class ApiCandidateStructure(BaseModel):
    """ApiCandidateStructure."""

    model_config = ConfigDict(extra="forbid")

    structure_id: str = Field(..., description="Structure identifier.")
    provider: str = Field(..., description="Provider name.")
    pdb_text: str | None = Field(default=None, description="Optional PDB.")
    metrics: dict[str, float] = Field(
        default_factory=dict, description="Structure metrics."
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Structure metadata."
    )


class ApiCandidate(BaseModel):
    """ApiCandidate."""

    model_config = ConfigDict(extra="forbid")

    candidate_id: str = Field(..., min_length=1, description="Candidate identifier.")
    sequence: str = Field(..., min_length=1, description="Sequence.")
    structures: list[ApiCandidateStructure] = Field(
        default_factory=list, description="Structures."
    )
    metrics: dict[str, float] = Field(
        default_factory=dict, description="Candidate metrics."
    )
    flags: list[str] = Field(default_factory=list, description="Flags.")
    provenance: dict[str, Any] = Field(
        default_factory=dict, description="Provenance metadata."
    )
    confidence: dict[str, Any] = Field(
        default_factory=dict, description="Confidence vector."
    )
    created_at: str = Field(..., description="Created timestamp.")


class InspectResponse(BaseModel):
    """InspectResponse."""

    model_config = ConfigDict(extra="forbid")

    candidate: ApiCandidate = Field(..., description="Candidate.")
    qc_status: str | None = Field(default=None, description="QC status.")
    artifacts: dict[str, str] = Field(
        default_factory=dict, description="Artifact paths."
    )


class HealthResponse(BaseModel):
    """HealthResponse."""

    model_config = ConfigDict(extra="forbid")

    status: str = Field(..., description="Health status.")


class ReadyResponse(BaseModel):
    """ReadyResponse."""

    model_config = ConfigDict(extra="forbid")

    status: str = Field(..., description="Readiness status.")
    providers: dict[str, Any] = Field(
        default_factory=dict, description="Provider readiness details."
    )


class ApiEnvelope(BaseModel):
    """ApiEnvelope."""

    model_config = ConfigDict(extra="forbid")

    status: Literal["ok", "error"] = Field(..., description="Response status.")
    data: (
        RunResponse
        | InspectResponse
        | CompareResponse
        | HealthResponse
        | ReadyResponse
        | None
    ) = Field(default=None, description="Successful response payload.")
    error: ErrorResponse | None = Field(
        default=None, description="Structured error payload."
    )
    meta: dict[str, Any] = Field(default_factory=dict, description="Meta fields.")

# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""API request/response schemas."""

from __future__ import annotations

from enum import StrEnum
from typing import Any, Literal

from pydantic import AnyUrl, BaseModel, ConfigDict, Field, model_validator

from bijux_proteomics_runtime.core.failures import FailureType
from bijux_proteomics_runtime.core.status import (
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
    runtime: str = Field(..., description="Canonical runtime identity.")


class ReadyResponse(BaseModel):
    """ReadyResponse."""

    model_config = ConfigDict(extra="forbid")

    status: str = Field(..., description="Readiness status.")
    runtime: str = Field(..., description="Canonical runtime identity.")
    providers: dict[str, Any] = Field(
        default_factory=dict, description="Provider readiness details."
    )


class RuntimeHealthComponentState(StrEnum):
    """Health state for one runtime service component."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    FAILED = "failed"


class RuntimeHealthComponent(BaseModel):
    """One runtime health component check."""

    model_config = ConfigDict(extra="forbid")

    component: str = Field(..., min_length=1, description="Component identifier.")
    state: RuntimeHealthComponentState = Field(..., description="Component health.")
    detail: str = Field(..., min_length=1, description="Human-readable detail.")
    remediation_hint: str = Field(
        ..., min_length=1, description="Operator remediation hint."
    )


class RuntimeHealthResponse(BaseModel):
    """Typed runtime health report across storage, cache, tool, and manifest checks."""

    model_config = ConfigDict(extra="forbid")

    status: str = Field(..., description="Aggregate health status.")
    runtime: str = Field(..., description="Canonical runtime identity.")
    components: list[RuntimeHealthComponent] = Field(
        default_factory=list,
        description="Per-component health details.",
    )


class RuntimeDocumentAvailability(StrEnum):
    """Availability state for one runtime-managed document surface."""

    AVAILABLE = "available"
    MISSING = "missing"
    TOO_LARGE = "too_large"
    UNSUPPORTED = "unsupported"


class RuntimeArtifactRecord(BaseModel):
    """Stable runtime artifact descriptor for lookup and review."""

    model_config = ConfigDict(extra="forbid")

    run_id: str = Field(..., min_length=1, description="Run identifier.")
    artifact_key: str = Field(..., min_length=1, description="Stable artifact key.")
    artifact_kind: str = Field(..., min_length=1, description="Artifact kind.")
    path: str = Field(..., min_length=1, description="Repository-local artifact path.")
    size_bytes: int = Field(..., ge=0, description="Artifact size in bytes.")
    sha256: str = Field(..., min_length=64, max_length=64, description="Artifact hash.")
    tags: list[str] = Field(default_factory=list, description="Artifact tags.")
    description: str = Field(..., min_length=1, description="Artifact description.")


class RuntimeDocumentReference(BaseModel):
    """Stable reference to a runtime evidence or review document."""

    model_config = ConfigDict(extra="forbid")

    run_id: str = Field(..., min_length=1, description="Run identifier.")
    document_kind: str = Field(..., min_length=1, description="Document kind.")
    availability: RuntimeDocumentAvailability = Field(
        ..., description="Availability state for this document."
    )
    path: str = Field(..., min_length=1, description="Repository-local document path.")
    size_bytes: int = Field(
        default=0, ge=0, description="Document size in bytes when known."
    )
    sha256: str | None = Field(default=None, description="Document hash when known.")
    note: str = Field(..., min_length=1, description="Human-readable availability note.")
    content: dict[str, Any] | None = Field(
        default=None,
        description="Inline document content when small enough and requested.",
    )


class RuntimeStatusResponse(BaseModel):
    """Stable runtime status response for one run."""

    model_config = ConfigDict(extra="forbid")

    summary: RunResponse = Field(..., description="Canonical run summary.")
    evidence_bundle: RuntimeDocumentReference = Field(
        ..., description="Evidence-bundle availability for the run."
    )
    review_packet: RuntimeDocumentReference = Field(
        ..., description="Review-packet availability for the run."
    )


class RunArtifactsResponse(BaseModel):
    """Stable artifact listing for one run."""

    model_config = ConfigDict(extra="forbid")

    run_id: str = Field(..., min_length=1, description="Run identifier.")
    artifacts: list[RuntimeArtifactRecord] = Field(
        default_factory=list, description="Artifacts attached to the run."
    )


class RunEvidenceResponse(BaseModel):
    """Stable evidence-bundle availability response for one run."""

    model_config = ConfigDict(extra="forbid")

    run_id: str = Field(..., min_length=1, description="Run identifier.")
    evidence_bundle: RuntimeDocumentReference = Field(
        ..., description="Evidence-bundle availability."
    )


class RunReviewResponse(BaseModel):
    """Stable review-packet availability response for one run."""

    model_config = ConfigDict(extra="forbid")

    run_id: str = Field(..., min_length=1, description="Run identifier.")
    review_packet: RuntimeDocumentReference = Field(
        ..., description="Review-packet availability."
    )


class ApiEnvelope(BaseModel):
    """ApiEnvelope."""

    model_config = ConfigDict(extra="forbid")

    status: Literal["ok", "error"] = Field(..., description="Response status.")
    data: (
        RunResponse
        | RuntimeStatusResponse
        | RunArtifactsResponse
        | RunEvidenceResponse
        | RunReviewResponse
        | InspectResponse
        | CompareResponse
        | HealthResponse
        | ReadyResponse
        | RuntimeHealthResponse
        | None
    ) = Field(default=None, description="Successful response payload.")
    error: ErrorResponse | None = Field(
        default=None, description="Structured error payload."
    )
    meta: dict[str, Any] = Field(default_factory=dict, description="Meta fields.")

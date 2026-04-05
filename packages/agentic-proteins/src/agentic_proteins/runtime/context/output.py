# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Run output schemas."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

from agentic_proteins.agents.schemas import CoordinatorDecisionType
from agentic_proteins.domain.metrics.quality import QCStatus


class RunStatus(str, Enum):
    """RunStatus."""

    SUCCESS = "success"
    PARTIAL = "partial"
    FAILURE = "failure"


class ErrorDetail(BaseModel):
    """ErrorDetail."""

    model_config = ConfigDict(extra="forbid")

    error_type: str = Field(..., min_length=1, description="Failure type code.")
    message: str = Field(..., min_length=1, description="Error message.")


class VersionInfo(BaseModel):
    """VersionInfo."""

    model_config = ConfigDict(extra="forbid")

    app_version: str = Field(..., min_length=1, description="Application version.")
    git_commit: str = Field(..., min_length=1, description="Git commit hash.")
    tool_versions: dict[str, str] = Field(
        default_factory=dict,
        description="Tool name -> version.",
    )


class RunOutput(BaseModel):
    """RunOutput."""

    model_config = ConfigDict(extra="forbid")

    run_id: str = Field(..., min_length=1, description="Run identifier.")
    candidate_id: str = Field(..., min_length=1, description="Candidate identifier.")
    lifecycle_state: str = Field(..., min_length=1, description="Run lifecycle state.")
    status: RunStatus = Field(RunStatus.FAILURE, description="Run status.")
    failure_type: str = Field(..., min_length=1, description="Failure type code.")
    plan_fingerprint: str = Field(..., min_length=1, description="Plan fingerprint.")
    tool_status: str = Field(..., min_length=1, description="Tool execution status.")
    report: dict = Field(default_factory=dict, description="Report payload.")
    qc_status: QCStatus = Field(QCStatus.REJECT, description="QC status.")
    coordinator_decision: CoordinatorDecisionType = Field(
        CoordinatorDecisionType.TERMINATE,
        description="Coordinator decision.",
    )
    errors: list[ErrorDetail] = Field(default_factory=list, description="Errors.")
    warnings: list[str] = Field(default_factory=list, description="Warnings.")
    version_info: VersionInfo = Field(..., description="Version metadata.")

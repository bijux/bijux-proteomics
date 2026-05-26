# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Run output schemas."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from bijux_proteomics_intelligence.candidates.schema import Candidate
from bijux_proteomics_intelligence.candidates.quality import QCStatus
from bijux_proteomics_runtime.execution.agents.schemas import CoordinatorDecisionType


class RunStatus(StrEnum):
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
    report: dict[str, Any] = Field(default_factory=dict, description="Report payload.")
    qc_status: QCStatus = Field(QCStatus.REJECT, description="QC status.")
    coordinator_decision: CoordinatorDecisionType = Field(
        CoordinatorDecisionType.TERMINATE,
        description="Coordinator decision.",
    )
    errors: list[ErrorDetail] = Field(default_factory=list, description="Errors.")
    warnings: list[str] = Field(default_factory=list, description="Warnings.")
    version_info: VersionInfo = Field(..., description="Version metadata.")


class RuntimeFlowResult(BaseModel):
    """Typed result for the canonical runtime flow before summary materialization."""

    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    candidate_id: str = Field(..., min_length=1, description="Candidate identifier.")
    candidate: Candidate | None = Field(
        default=None,
        description="Updated candidate payload when the flow produced one.",
    )
    plan_fingerprint: str = Field(..., min_length=1, description="Plan fingerprint.")
    tool_status: str = Field(..., min_length=1, description="Tool execution status.")
    report_raw_json: dict[str, Any] = Field(
        default_factory=dict,
        alias="report",
        description="Raw report payload emitted by the runtime flow.",
    )
    qc_status: QCStatus = Field(QCStatus.REJECT, description="QC status.")
    coordinator_decision: CoordinatorDecisionType = Field(
        CoordinatorDecisionType.TERMINATE,
        description="Coordinator decision.",
    )
    failure_type: str = Field("", description="Failure type code.")
    lifecycle_state: str = Field(..., min_length=1, description="Run lifecycle state.")

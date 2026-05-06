# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Execution adapters from program specs into Agentic Proteins."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from bijux_proteomics.domain.errors import (
    ProgramValidationError,
    ReviewGateBlockedError,
)
from bijux_proteomics.interfaces.execution.backend import ExecutionRequest
from bijux_proteomics.interfaces.execution.runtime_adapter import require_backend
from bijux_proteomics.domain.programs import ProgramSpec, program_summary
from bijux_proteomics.domain.repositories import ReviewDecision, ensure_review_clearance
from bijux_proteomics.domain.validation import validate_program


class ProgramExecutionRequest(BaseModel):
    """Program execution request."""

    model_config = ConfigDict(extra="forbid", arbitrary_types_allowed=True)

    program: ProgramSpec = Field(..., description="Program to execute.")
    candidate_sequence: str = Field(
        ..., min_length=1, description="Sequence to evaluate."
    )
    base_dir: Path = Field(..., description="Workspace root.")
    rounds: int = Field(default=1, ge=1, description="Agentic loop iterations.")
    provider: str | None = Field(
        default=None, description="Optional provider override."
    )
    execution_mode: str = Field(default="auto", description="Provider execution mode.")
    artifacts_dir: Path | None = Field(
        default=None, description="Artifact root override."
    )
    review_decisions: list[ReviewDecision] = Field(
        default_factory=list,
        description="Recorded review decisions attached to the execution request.",
    )
    backend: Any = Field(
        default=None,
        description="Injected execution backend for runtime work.",
    )


def execute_program(request: ProgramExecutionRequest) -> dict[str, Any]:
    """Run an approved program sequence through the agent runtime."""
    issues = validate_program(request.program)
    if issues:
        raise ProgramValidationError(
            "program is not ready for execution: "
            + "; ".join(issue.message for issue in issues),
            issue_codes=[issue.code for issue in issues],
        )
    blocked_gates = ensure_review_clearance(
        request.program,
        request.review_decisions,
    )
    if blocked_gates:
        raise ReviewGateBlockedError(
            "blocking review gates require approval before execution: "
            + ", ".join(gate.gate_id for gate in blocked_gates)
        )

    backend = require_backend(request.backend)
    result = backend.execute(
        ExecutionRequest(
            candidate_sequence=request.candidate_sequence,
            base_dir=request.base_dir,
            rounds=request.rounds,
            provider=request.provider,
            execution_mode=request.execution_mode,
            artifacts_dir=request.artifacts_dir,
            require_human_decision=bool(request.program.review_gates),
        )
    )
    provenance = result.setdefault("program", {})
    provenance.update(program_summary(request.program))
    provenance["review_gate_ids"] = [
        gate.gate_id for gate in request.program.review_gates
    ]
    provenance["assay_ids"] = [assay.assay_id for assay in request.program.assay_panel]
    return result

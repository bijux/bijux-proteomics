# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Execution adapters from program specs into Agentic Proteins."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from bijux_proteomics.exceptions import ReviewGateBlockedError
from bijux_proteomics.programs import ProgramSpec, program_summary
from bijux_proteomics.repositories import ReviewDecision, ensure_review_clearance


class ProgramExecutionRequest(BaseModel):
    """Program execution request."""

    model_config = ConfigDict(extra="forbid")

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


def execute_program(request: ProgramExecutionRequest) -> dict[str, Any]:
    """Run an approved program sequence through the agent runtime."""
    blocked_gates = ensure_review_clearance(
        request.program,
        request.review_decisions,
    )
    if blocked_gates:
        raise ReviewGateBlockedError(
            "blocking review gates require approval before execution: "
            + ", ".join(gate.gate_id for gate in blocked_gates)
        )

    from agentic_proteins.runtime import RunManager
    from agentic_proteins.runtime.infra import RunConfig

    config = RunConfig(
        loop_max_iterations=request.rounds,
        predictors_enabled=[request.provider] if request.provider else None,
        artifacts_dir=str(request.artifacts_dir) if request.artifacts_dir else None,
        execution_mode=request.execution_mode,
        require_human_decision=bool(request.program.review_gates),
    )
    result = RunManager(base_dir=request.base_dir, config=config).run(
        request.candidate_sequence
    )
    provenance = result.setdefault("program", {})
    provenance.update(program_summary(request.program))
    provenance["review_gate_ids"] = [
        gate.gate_id for gate in request.program.review_gates
    ]
    provenance["assay_ids"] = [assay.assay_id for assay in request.program.assay_panel]
    return result

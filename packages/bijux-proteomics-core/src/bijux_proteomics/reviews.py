# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Human review checkpoints for protein programs."""

from __future__ import annotations

from bijux_proteomics_foundation import GateId
from pydantic import BaseModel, ConfigDict, Field


class ReviewGate(BaseModel):
    """Human oversight checkpoint before expensive actions."""

    model_config = ConfigDict(extra="forbid")

    gate_id: GateId = Field(..., description="Stable review gate identifier.")
    name: str = Field(..., min_length=1, description="Review gate name.")
    required_roles: list[str] = Field(
        default_factory=list,
        description="Roles that must sign off.",
    )
    decision_inputs: list[str] = Field(
        default_factory=list,
        description="Evidence and artifacts needed for signoff.",
    )
    blocking: bool = Field(
        default=True,
        description="Whether execution must stop until approval is recorded.",
    )

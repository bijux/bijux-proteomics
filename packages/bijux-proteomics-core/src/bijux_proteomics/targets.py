# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Target models for protein programs."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field
from bijux_proteomics_foundation import TargetId
from bijux_proteomics.sequences import ProteinSequence


class ProteinTarget(BaseModel):
    """Target definition for a discovery or engineering program."""

    model_config = ConfigDict(extra="forbid")

    target_id: TargetId = Field(..., description="Stable target identifier.")
    name: str = Field(..., min_length=1, description="Human-readable target name.")
    sequence: ProteinSequence = Field(..., description="Reference amino-acid sequence.")
    organism: str = Field(..., min_length=1, description="Source organism.")
    mechanism: str = Field(
        ..., min_length=1, description="Working biological hypothesis."
    )
    desired_outcomes: list[str] = Field(
        default_factory=list,
        description="Desired biological or engineering outcomes.",
    )
    blocked_outcomes: list[str] = Field(
        default_factory=list,
        description="Known failure modes or safety concerns.",
    )

# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Program lifecycle helpers."""

from __future__ import annotations

from pydantic import ConfigDict, Field

from bijux_proteomics.program_spec import ProgramStage
from bijux_proteomics_foundation import JsonModel, ProgramId


class ProgramLifecycle(JsonModel):
    """Transition history for a protein program."""

    model_config = ConfigDict(extra="forbid")

    program_id: ProgramId = Field(..., description="Program identifier.")
    current_stage: ProgramStage = Field(..., description="Current lifecycle stage.")
    visited_stages: list[ProgramStage] = Field(
        default_factory=list,
        description="Visited lifecycle stages in order.",
    )


def advance_stage(lifecycle: ProgramLifecycle, next_stage: ProgramStage) -> ProgramLifecycle:
    """Advance to a new stage while preserving visit history."""
    visited = list(lifecycle.visited_stages)
    if not visited or visited[-1] is not lifecycle.current_stage:
        visited.append(lifecycle.current_stage)
    visited.append(next_stage)
    return lifecycle.model_copy(
        update={"current_stage": next_stage, "visited_stages": visited}
    )

# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Structured ranking outcomes and rejection reasons."""

from __future__ import annotations

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import CandidateId, JsonModel


class CandidateRejection(JsonModel):
    """Structured rejection outcome for a screened-out candidate."""

    model_config = ConfigDict(extra="forbid")

    candidate_id: CandidateId = Field(..., description="Rejected candidate identifier.")
    reasons: list[str] = Field(
        default_factory=list,
        description="Concrete reasons for rejection.",
    )


class TieBreakExplanation(JsonModel):
    """Record of how a tie was broken between candidates."""

    model_config = ConfigDict(extra="forbid")

    winner_candidate_id: CandidateId = Field(..., description="Candidate chosen after tie-break.")
    compared_candidate_id: CandidateId = Field(..., description="Candidate not selected.")
    rules_applied: list[str] = Field(
        default_factory=list,
        description="Tie-break rules applied in order.",
    )

# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Structured ranking outcomes and rejection reasons."""

from __future__ import annotations

from enum import StrEnum

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import CandidateId, JsonModel


class RejectionReasonCode(StrEnum):
    """Stable rejection reason categories."""

    LOW_METRIC_FRACTION = "low_metric_fraction"
    LOW_EVIDENCE_SUPPORT = "low_evidence_support"
    LOW_MANUFACTURABILITY = "low_manufacturability"
    HIGH_SEQUENCE_COMPLEXITY = "high_sequence_complexity"
    HIGH_RESIDUAL_RISK = "high_residual_risk"
    CONTEXT_MISMATCH = "context_mismatch"


class CandidateRejection(JsonModel):
    """Structured rejection outcome for a screened-out candidate."""

    model_config = ConfigDict(extra="forbid")

    candidate_id: CandidateId = Field(..., description="Rejected candidate identifier.")
    reasons: list[str] = Field(
        default_factory=list,
        description="Concrete reasons for rejection.",
    )
    reason_codes: list[RejectionReasonCode] = Field(
        default_factory=list,
        description="Stable reason codes for downstream automation.",
    )
    blocking: bool = Field(
        default=True,
        description="Whether this rejection blocks progression for the candidate.",
    )
    recommended_experiments: list[str] = Field(
        default_factory=list,
        description="Experiments that could resolve the rejection.",
    )
    reopen_conditions: list[str] = Field(
        default_factory=list,
        description="Conditions under which the candidate can be reconsidered.",
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

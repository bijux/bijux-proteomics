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
    LOW_METRIC_COVERAGE = "low_metric_coverage"
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

    winner_candidate_id: CandidateId = Field(
        ..., description="Candidate chosen after tie-break."
    )
    compared_candidate_id: CandidateId = Field(
        ..., description="Candidate not selected."
    )
    rules_applied: list[str] = Field(
        default_factory=list,
        description="Tie-break rules applied in order.",
    )


class RejectionActionPlan(JsonModel):
    """Concrete remediation plan derived from a candidate rejection."""

    model_config = ConfigDict(extra="forbid")

    candidate_id: CandidateId = Field(..., description="Rejected candidate identifier.")
    experiments: list[str] = Field(
        default_factory=list, description="Follow-up experiments."
    )
    revisit_conditions: list[str] = Field(
        default_factory=list, description="Conditions to revisit the candidate."
    )


class RejectionSummary(JsonModel):
    """Summary analytics across candidate rejections."""

    model_config = ConfigDict(extra="forbid")

    rejection_count: int = Field(
        ..., ge=0, description="Number of rejected candidates summarized."
    )
    by_reason_code: dict[str, int] = Field(
        default_factory=dict, description="Rejection counts by reason code."
    )
    blocking_rejection_count: int = Field(
        ..., ge=0, description="Count of blocking rejections."
    )


def build_rejection_action_plan(rejection: CandidateRejection) -> RejectionActionPlan:
    """Build an action plan from rejection reason taxonomy."""
    experiments: list[str] = []
    revisit_conditions: list[str] = []
    if RejectionReasonCode.LOW_METRIC_FRACTION in rejection.reason_codes:
        experiments.append("run focused potency and selectivity assays")
        revisit_conditions.append("criterion fraction reaches policy floor")
    if RejectionReasonCode.LOW_METRIC_COVERAGE in rejection.reason_codes:
        experiments.append(
            "collect missing criterion-linked assay metrics before reranking"
        )
        revisit_conditions.append("all blocking criterion metrics are present")
    if RejectionReasonCode.LOW_EVIDENCE_SUPPORT in rejection.reason_codes:
        experiments.append("collect orthogonal evidence across at least two modalities")
        revisit_conditions.append("evidence_support >= 0.4")
    if RejectionReasonCode.LOW_MANUFACTURABILITY in rejection.reason_codes:
        experiments.append("run expression and aggregation developability panel")
        revisit_conditions.append("manufacturability_score >= 0.5")
    if not experiments:
        experiments.append("review candidate with scientist for bespoke follow-up")
    return RejectionActionPlan(
        candidate_id=rejection.candidate_id,
        experiments=experiments,
        revisit_conditions=revisit_conditions,
    )


def summarize_rejections(rejections: list[CandidateRejection]) -> RejectionSummary:
    """Summarize rejection drivers across rejected candidates."""
    reason_counts: dict[str, int] = {}
    blocking_count = 0
    for rejection in rejections:
        if rejection.blocking:
            blocking_count += 1
        for reason_code in rejection.reason_codes:
            reason_counts[reason_code.value] = (
                reason_counts.get(reason_code.value, 0) + 1
            )
    return RejectionSummary(
        rejection_count=len(rejections),
        by_reason_code=reason_counts,
        blocking_rejection_count=blocking_count,
    )

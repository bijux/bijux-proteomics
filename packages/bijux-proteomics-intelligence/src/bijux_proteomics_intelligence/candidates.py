# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Candidate lifecycle models for protein design decisions."""

from __future__ import annotations

from enum import StrEnum

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import CandidateId, ProgramId
from bijux_proteomics_intelligence.briefs import CandidateAssessment, LiabilityFlag
from bijux_proteomics_intelligence.serialization import JsonModel


class CandidateStatus(StrEnum):
    """Lifecycle states for a candidate sequence."""

    PROPOSED = "proposed"
    SCREENED = "screened"
    PRIORITIZED = "prioritized"
    ADVANCED = "advanced"
    REJECTED = "rejected"


class CandidateProposal(JsonModel):
    """A newly proposed candidate with rationale and origin."""

    model_config = ConfigDict(extra="forbid")

    candidate_id: CandidateId = Field(..., description="Stable candidate identifier.")
    program_id: ProgramId = Field(..., description="Program identifier.")
    sequence: str = Field(..., min_length=1, description="Candidate protein sequence.")
    origin: str = Field(..., min_length=1, description="Where the candidate came from.")
    rationale: str = Field(..., min_length=1, description="Why the candidate was proposed.")


class CandidateRiskProfile(JsonModel):
    """Structured view of candidate liabilities and residual risk."""

    model_config = ConfigDict(extra="forbid")

    candidate_id: CandidateId = Field(..., description="Stable candidate identifier.")
    liabilities: list[LiabilityFlag] = Field(
        default_factory=list,
        description="Risks carried by the candidate.",
    )
    residual_risk: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Aggregated residual risk score.",
    )


class CandidateScreeningResult(JsonModel):
    """Outcome of initial computational or experimental screening."""

    model_config = ConfigDict(extra="forbid")

    candidate_id: CandidateId = Field(..., description="Stable candidate identifier.")
    passed_filters: bool = Field(..., description="Whether the candidate passed screening.")
    filter_notes: list[str] = Field(
        default_factory=list,
        description="Reasons for pass or fail.",
    )
    assessment: CandidateAssessment = Field(
        ...,
        description="Assessment metrics carried into ranking.",
    )


class CandidateDecision(JsonModel):
    """Decision taken on a candidate after review or ranking."""

    model_config = ConfigDict(extra="forbid")

    candidate_id: CandidateId = Field(..., description="Stable candidate identifier.")
    status: CandidateStatus = Field(..., description="Lifecycle status after the decision.")
    decision_summary: str = Field(
        ...,
        min_length=1,
        description="Human-readable explanation of the decision.",
    )


class CandidatePortfolio(JsonModel):
    """Portfolio view of candidates under one program."""

    model_config = ConfigDict(extra="forbid")

    program_id: ProgramId = Field(..., description="Program identifier.")
    proposals: list[CandidateProposal] = Field(
        default_factory=list,
        description="All proposed candidates.",
    )
    screening_results: list[CandidateScreeningResult] = Field(
        default_factory=list,
        description="Screening outcomes for the portfolio.",
    )
    decisions: list[CandidateDecision] = Field(
        default_factory=list,
        description="Latest lifecycle decisions for each candidate.",
    )


def build_risk_profile(assessment: CandidateAssessment) -> CandidateRiskProfile:
    """Build a risk profile from an assessment."""
    total_severity = sum(flag.severity for flag in assessment.liabilities)
    residual_risk = min(total_severity / 20.0, 1.0)
    return CandidateRiskProfile(
        candidate_id=assessment.candidate_id,
        liabilities=assessment.liabilities,
        residual_risk=round(residual_risk, 4),
    )


def portfolio_status(portfolio: CandidatePortfolio) -> dict[str, int]:
    """Count candidates by lifecycle status."""
    counts = {status.value: 0 for status in CandidateStatus}
    for decision in portfolio.decisions:
        counts[decision.status.value] += 1
    return counts

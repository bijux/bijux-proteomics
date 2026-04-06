# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Candidate lifecycle models for protein design decisions."""

from __future__ import annotations

from datetime import UTC, datetime
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
    DEFERRED = "deferred"
    PARKED = "parked"
    ADVANCED = "advanced"
    REJECTED = "rejected"
    REOPENED = "reopened"


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
    manufacturability_risk: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Risk that the candidate is hard to express or handle.",
    )
    safety_risk: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Risk of safety or immunogenicity issues.",
    )
    assay_risk: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Risk that assays will fail or be inconclusive.",
    )
    evidence_uncertainty_risk: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Risk contributed by weak or uncertain evidence.",
    )
    novelty_risk: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Risk contributed by unsupported novelty.",
    )
    sequence_complexity_risk: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Risk contributed by sequence-derived complexity signals.",
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


class CandidateTransition(JsonModel):
    """One audited lifecycle transition for a candidate."""

    model_config = ConfigDict(extra="forbid")

    candidate_id: CandidateId = Field(..., description="Stable candidate identifier.")
    from_status: CandidateStatus = Field(..., description="Previous lifecycle status.")
    to_status: CandidateStatus = Field(..., description="New lifecycle status.")
    reason: str = Field(..., min_length=1, description="Why the transition happened.")
    review_gate_id: str | None = Field(
        default=None,
        description="Optional review gate that authorized the transition.",
    )
    evidence_ids: list[str] = Field(
        default_factory=list,
        description="Evidence references supporting the transition.",
    )
    changed_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="When the transition was recorded.",
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


class PortfolioSelectionPolicy(JsonModel):
    """Policy for selecting a balanced shortlist from ranked candidates."""

    model_config = ConfigDict(extra="forbid")

    policy_id: str = Field(..., min_length=1, description="Stable policy identifier.")
    selection_size: int = Field(
        default=3,
        ge=1,
        description="Maximum number of candidates to keep in the shortlist.",
    )
    max_candidates_per_liability_code: int = Field(
        default=1,
        ge=1,
        description="Maximum shortlisted candidates that may share a liability code.",
    )


class PortfolioSelectionResult(JsonModel):
    """Balanced shortlist built from ranked candidates and risk profiles."""

    model_config = ConfigDict(extra="forbid")

    selected_candidate_ids: list[str] = Field(
        default_factory=list,
        description="Candidate identifiers chosen for the shortlist.",
    )
    deferred_candidate_ids: list[str] = Field(
        default_factory=list,
        description="Candidate identifiers left out of the shortlist.",
    )
    rationale: list[str] = Field(
        default_factory=list,
        description="Why candidates were selected or deferred.",
    )


class SequenceRiskSignals(JsonModel):
    """Sequence-derived features that influence candidate risk interpretation."""

    model_config = ConfigDict(extra="forbid")

    candidate_id: CandidateId = Field(..., description="Candidate identifier.")
    length: int = Field(..., ge=1, description="Sequence length.")
    hydrophobic_fraction: float = Field(..., ge=0.0, le=1.0, description="Hydrophobic residue fraction.")
    acidic_basic_balance: float = Field(..., ge=0.0, le=1.0, description="Charge-balance proxy.")
    glyco_motif_count: int = Field(..., ge=0, description="Count of NXS or NXT motifs.")


class ParetoFrontResult(JsonModel):
    """Pareto-optimal candidate set across competing objectives."""

    model_config = ConfigDict(extra="forbid")

    frontier_candidate_ids: list[str] = Field(
        default_factory=list,
        description="Candidate identifiers on the Pareto frontier.",
    )
    dominated_candidate_ids: list[str] = Field(
        default_factory=list,
        description="Candidate identifiers dominated by at least one frontier candidate.",
    )


class CandidateLifecycleSummary(JsonModel):
    """Summary view of candidate transition history."""

    model_config = ConfigDict(extra="forbid")

    candidate_id: CandidateId = Field(..., description="Candidate identifier.")
    transition_count: int = Field(..., ge=0, description="Number of recorded transitions.")
    latest_status: CandidateStatus = Field(..., description="Latest lifecycle status.")
    visited_statuses: list[CandidateStatus] = Field(
        default_factory=list,
        description="Ordered statuses visited by the candidate.",
    )


ALLOWED_CANDIDATE_TRANSITIONS: dict[CandidateStatus, set[CandidateStatus]] = {
    CandidateStatus.PROPOSED: {CandidateStatus.SCREENED, CandidateStatus.REJECTED, CandidateStatus.DEFERRED},
    CandidateStatus.SCREENED: {
        CandidateStatus.PRIORITIZED,
        CandidateStatus.REJECTED,
        CandidateStatus.DEFERRED,
        CandidateStatus.PARKED,
    },
    CandidateStatus.PRIORITIZED: {
        CandidateStatus.ADVANCED,
        CandidateStatus.REJECTED,
        CandidateStatus.DEFERRED,
    },
    CandidateStatus.DEFERRED: {CandidateStatus.REOPENED, CandidateStatus.REJECTED},
    CandidateStatus.PARKED: {CandidateStatus.REOPENED, CandidateStatus.REJECTED},
    CandidateStatus.REOPENED: {CandidateStatus.SCREENED, CandidateStatus.PRIORITIZED},
    CandidateStatus.ADVANCED: set(),
    CandidateStatus.REJECTED: {CandidateStatus.REOPENED},
}


def build_risk_profile(assessment: CandidateAssessment) -> CandidateRiskProfile:
    """Build a risk profile from an assessment."""
    developability_severity = sum(
        flag.severity
        for flag in assessment.liabilities
        if "aggregation" in flag.code or "develop" in flag.code
    )
    safety_severity = sum(
        flag.severity
        for flag in assessment.liabilities
        if "safety" in flag.code or "immun" in flag.code or "tox" in flag.code
    )
    assay_severity = sum(
        flag.severity
        for flag in assessment.liabilities
        if "assay" in flag.code or "screen" in flag.code
    )
    general_severity = sum(flag.severity for flag in assessment.liabilities)
    manufacturability_risk = min(
        (1.0 - assessment.manufacturability_score) * 0.6 + (developability_severity / 10.0),
        1.0,
    )
    safety_risk = min(safety_severity / 10.0, 1.0)
    assay_risk = min(assay_severity / 10.0, 1.0)
    evidence_uncertainty_risk = min(
        (1.0 - assessment.evidence_support) * 0.5 + assessment.uncertainty * 0.5,
        1.0,
    )
    novelty_risk = min(
        max(0.0, general_severity - developability_severity - safety_severity - assay_severity)
        / 10.0,
        1.0,
    )
    sequence_features = sequence_risk_signals(
        CandidateProposal(
            candidate_id=assessment.candidate_id,
            program_id="derived-profile",
            sequence=assessment.sequence,
            origin="risk-profile",
            rationale="derive sequence risk signals for candidate profile",
        )
    )
    sequence_complexity_risk = min(
        max(0.0, sequence_features.hydrophobic_fraction - 0.45) * 1.5
        + max(0.0, 0.4 - sequence_features.acidic_basic_balance),
        1.0,
    )
    residual_risk = min(
        (
            manufacturability_risk * 0.25
            + safety_risk * 0.25
            + assay_risk * 0.15
            + evidence_uncertainty_risk * 0.2
            + novelty_risk * 0.1
            + sequence_complexity_risk * 0.05
        ),
        1.0,
    )
    return CandidateRiskProfile(
        candidate_id=assessment.candidate_id,
        liabilities=assessment.liabilities,
        manufacturability_risk=round(manufacturability_risk, 4),
        safety_risk=round(safety_risk, 4),
        assay_risk=round(assay_risk, 4),
        evidence_uncertainty_risk=round(evidence_uncertainty_risk, 4),
        novelty_risk=round(novelty_risk, 4),
        sequence_complexity_risk=round(sequence_complexity_risk, 4),
        residual_risk=round(residual_risk, 4),
    )


def transition_candidate(
    candidate_id: str,
    current_status: CandidateStatus,
    next_status: CandidateStatus,
    *,
    reason: str,
    review_gate_id: str | None = None,
    evidence_ids: list[str] | None = None,
) -> CandidateTransition:
    """Transition a candidate through the allowed lifecycle states."""
    allowed = ALLOWED_CANDIDATE_TRANSITIONS.get(current_status, set())
    if next_status not in allowed:
        raise ValueError(
            f"cannot move candidate from {current_status.value} to {next_status.value}"
        )
    evidence_ids = evidence_ids or []
    if (
        next_status
        in {CandidateStatus.PRIORITIZED, CandidateStatus.ADVANCED, CandidateStatus.REOPENED}
        and not evidence_ids
    ):
        raise ValueError("prioritized, advanced, and reopened transitions require evidence references")
    return CandidateTransition(
        candidate_id=candidate_id,
        from_status=current_status,
        to_status=next_status,
        reason=reason,
        review_gate_id=review_gate_id,
        evidence_ids=evidence_ids,
    )


def portfolio_status(portfolio: CandidatePortfolio) -> dict[str, int]:
    """Count candidates by lifecycle status."""
    counts = {status.value: 0 for status in CandidateStatus}
    for decision in portfolio.decisions:
        counts[decision.status.value] += 1
    return counts


def select_portfolio_shortlist(
    ranking: list[CandidateAssessment],
    risk_profiles: list[CandidateRiskProfile],
    policy: PortfolioSelectionPolicy | None = None,
) -> PortfolioSelectionResult:
    """Select a shortlist that preserves score quality without collapsing diversity."""
    policy = policy or PortfolioSelectionPolicy(policy_id="balanced-shortlist")
    risk_map = {profile.candidate_id: profile for profile in risk_profiles}
    selected_candidate_ids: list[str] = []
    deferred_candidate_ids: list[str] = []
    rationale: list[str] = []
    liability_counts: dict[str, int] = {}

    for candidate in ranking:
        if len(selected_candidate_ids) >= policy.selection_size:
            deferred_candidate_ids.append(candidate.candidate_id)
            rationale.append(
                f"deferred {candidate.candidate_id} because the shortlist is already full"
            )
            continue
        profile = risk_map.get(candidate.candidate_id)
        liability_codes = sorted(
            {
                flag.code
                for flag in (profile.liabilities if profile is not None else [])
            }
        )
        overrepresented = [
            code
            for code in liability_codes
            if liability_counts.get(code, 0) >= policy.max_candidates_per_liability_code
        ]
        if overrepresented:
            deferred_candidate_ids.append(candidate.candidate_id)
            rationale.append(
                f"deferred {candidate.candidate_id} to avoid overloading the shortlist with "
                + ", ".join(overrepresented)
            )
            continue
        selected_candidate_ids.append(candidate.candidate_id)
        for code in liability_codes:
            liability_counts[code] = liability_counts.get(code, 0) + 1
        if liability_codes:
            rationale.append(
                f"selected {candidate.candidate_id} while preserving liability diversity across "
                + ", ".join(liability_codes)
            )
        else:
            rationale.append(
                f"selected {candidate.candidate_id} because it adds a clean risk profile to the shortlist"
            )
    return PortfolioSelectionResult(
        selected_candidate_ids=selected_candidate_ids,
        deferred_candidate_ids=deferred_candidate_ids,
        rationale=rationale,
    )


def sequence_risk_signals(candidate: CandidateProposal) -> SequenceRiskSignals:
    """Compute lightweight sequence-derived risk signals for one candidate."""
    sequence = candidate.sequence.upper()
    hydrophobic = {"A", "V", "I", "L", "M", "F", "W", "Y"}
    acidic = {"D", "E"}
    basic = {"K", "R", "H"}
    length = len(sequence)
    hydrophobic_fraction = (
        sum(1 for residue in sequence if residue in hydrophobic) / max(length, 1)
    )
    acidic_count = sum(1 for residue in sequence if residue in acidic)
    basic_count = sum(1 for residue in sequence if residue in basic)
    acidic_basic_balance = 1.0 - min(abs(acidic_count - basic_count) / max(length, 1), 1.0)
    glyco_motif_count = sum(
        1
        for index in range(max(length - 2, 0))
        if sequence[index] == "N" and sequence[index + 1] != "P" and sequence[index + 2] in {"S", "T"}
    )
    return SequenceRiskSignals(
        candidate_id=candidate.candidate_id,
        length=length,
        hydrophobic_fraction=round(hydrophobic_fraction, 4),
        acidic_basic_balance=round(acidic_basic_balance, 4),
        glyco_motif_count=glyco_motif_count,
    )


def select_pareto_candidates(
    assessments: list[CandidateAssessment],
) -> ParetoFrontResult:
    """Select Pareto-optimal candidates across support, manufacturability, and uncertainty."""
    frontier: list[str] = []
    dominated: list[str] = []
    for left in assessments:
        left_dominated = False
        for right in assessments:
            if right.candidate_id == left.candidate_id:
                continue
            if (
                right.evidence_support >= left.evidence_support
                and right.manufacturability_score >= left.manufacturability_score
                and right.uncertainty <= left.uncertainty
                and (
                    right.evidence_support > left.evidence_support
                    or right.manufacturability_score > left.manufacturability_score
                    or right.uncertainty < left.uncertainty
                )
            ):
                left_dominated = True
                break
        if left_dominated:
            dominated.append(left.candidate_id)
        else:
            frontier.append(left.candidate_id)
    return ParetoFrontResult(
        frontier_candidate_ids=sorted(frontier),
        dominated_candidate_ids=sorted(dominated),
    )


def summarize_candidate_lifecycle(
    transitions: list[CandidateTransition],
) -> CandidateLifecycleSummary:
    """Summarize ordered transition history for one candidate."""
    if not transitions:
        raise ValueError("at least one transition is required to summarize lifecycle")
    ordered = sorted(transitions, key=lambda transition: transition.changed_at)
    candidate_id = ordered[0].candidate_id
    latest_status = ordered[-1].to_status
    visited: list[CandidateStatus] = [ordered[0].from_status]
    for transition in ordered:
        if transition.to_status not in visited:
            visited.append(transition.to_status)
    return CandidateLifecycleSummary(
        candidate_id=candidate_id,
        transition_count=len(ordered),
        latest_status=latest_status,
        visited_statuses=visited,
    )

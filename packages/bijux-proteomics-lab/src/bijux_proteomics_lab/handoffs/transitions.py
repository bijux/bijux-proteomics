# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Transition-review owners for targeted lab follow-up work."""

from __future__ import annotations

from enum import StrEnum

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import AssayId, JsonModel
from bijux_proteomics_lab.handoffs.risk import (
    AssayRiskAssessment,
    assess_assay_risk,
)


class TransitionReviewDisposition(StrEnum):
    """Disposition for one targeted transition candidate."""

    APPROVED = "approved"
    EXPLORATORY = "exploratory"
    REFUSED = "refused"


class TargetedTransitionCandidate(JsonModel):
    """Candidate transition for targeted follow-up review."""

    model_config = ConfigDict(extra="forbid")

    transition_id: str = Field(..., min_length=1)
    peptide_sequence: str = Field(..., min_length=1)
    precursor_mz: float = Field(..., gt=0.0)
    product_mz: float = Field(..., gt=0.0)
    peptide_uniqueness_score: float = Field(..., ge=0.0, le=1.0)
    localization_probability: float | None = Field(default=None, ge=0.0, le=1.0)
    quant_reproducibility_score: float = Field(..., ge=0.0, le=1.0)
    assay_feasibility_score: float = Field(..., ge=0.0, le=1.0)
    predicted_failure_risk: float = Field(..., ge=0.0, le=1.0)
    required_controls: tuple[str, ...] = Field(default_factory=tuple)


class TargetedTransitionReviewEntry(JsonModel):
    """Review outcome for one targeted transition candidate."""

    model_config = ConfigDict(extra="forbid")

    transition_id: str = Field(..., min_length=1)
    disposition: TransitionReviewDisposition
    risk_assessment: AssayRiskAssessment
    missing_controls: tuple[str, ...] = Field(default_factory=tuple)
    reasons: tuple[str, ...] = Field(default_factory=tuple)


class TargetedTransitionReview(JsonModel):
    """Review summary for a targeted transition list."""

    model_config = ConfigDict(extra="forbid")

    assay_id: AssayId = Field(..., description="Assay identifier.")
    approved_transition_ids: tuple[str, ...] = Field(default_factory=tuple)
    exploratory_transition_ids: tuple[str, ...] = Field(default_factory=tuple)
    refused_transition_ids: tuple[str, ...] = Field(default_factory=tuple)
    readiness_score: float = Field(..., ge=0.0, le=1.0)
    entries: tuple[TargetedTransitionReviewEntry, ...] = Field(default_factory=tuple)
    notes: tuple[str, ...] = Field(default_factory=tuple)


def review_targeted_transition_candidates(
    *,
    assay_id: AssayId,
    candidates: tuple[TargetedTransitionCandidate, ...],
    available_controls: tuple[str, ...] = (),
) -> TargetedTransitionReview:
    """Review targeted transitions using assay feasibility and explicit scientific risk."""
    available_control_set = set(available_controls)
    entries: list[TargetedTransitionReviewEntry] = []

    for candidate in candidates:
        risk_assessment = assess_assay_risk(
            assay_id=assay_id,
            peptide_uniqueness_score=candidate.peptide_uniqueness_score,
            localization_probability=candidate.localization_probability,
            quant_reproducibility_score=candidate.quant_reproducibility_score,
            assay_feasibility_score=candidate.assay_feasibility_score,
            predicted_failure_risk=candidate.predicted_failure_risk,
        )
        missing_controls = tuple(
            sorted(
                control
                for control in candidate.required_controls
                if control not in available_control_set
            )
        )
        reasons: list[str] = []
        if missing_controls:
            reasons.append("missing required controls: " + ", ".join(missing_controls))
        if not risk_assessment.supported_for_follow_up:
            reasons.append(
                f"assay risk score {risk_assessment.overall_risk_score:.2f} is too high for confident transition approval"
            )
        elif risk_assessment.overall_risk_score >= 0.3:
            reasons.append(
                f"assay risk score {risk_assessment.overall_risk_score:.2f} keeps the transition exploratory"
            )
        if candidate.assay_feasibility_score < 0.65:
            reasons.append("assay feasibility is too weak for direct targeted handoff")

        if (
            not missing_controls
            and risk_assessment.supported_for_follow_up
            and candidate.assay_feasibility_score >= 0.75
        ):
            disposition = TransitionReviewDisposition.APPROVED
            reasons.append("transition is feasible enough for targeted follow-up")
        elif (
            candidate.assay_feasibility_score >= 0.55
            and risk_assessment.overall_risk_score < 0.6
        ):
            disposition = TransitionReviewDisposition.EXPLORATORY
            reasons.append("transition may be used only as exploratory follow-up")
        else:
            disposition = TransitionReviewDisposition.REFUSED
            reasons.append("transition is not responsible to schedule as written")

        entries.append(
            TargetedTransitionReviewEntry(
                transition_id=candidate.transition_id,
                disposition=disposition,
                risk_assessment=risk_assessment,
                missing_controls=missing_controls,
                reasons=tuple(reasons),
            )
        )

    approved_transition_ids = tuple(
        entry.transition_id
        for entry in entries
        if entry.disposition is TransitionReviewDisposition.APPROVED
    )
    exploratory_transition_ids = tuple(
        entry.transition_id
        for entry in entries
        if entry.disposition is TransitionReviewDisposition.EXPLORATORY
    )
    refused_transition_ids = tuple(
        entry.transition_id
        for entry in entries
        if entry.disposition is TransitionReviewDisposition.REFUSED
    )
    readiness_score = (
        round(
            max(
                0.0,
                min(
                    (
                        (len(approved_transition_ids) / max(len(entries), 1)) * 0.75
                        + (len(exploratory_transition_ids) / max(len(entries), 1))
                        * 0.25
                    ),
                    1.0,
                ),
            ),
            4,
        )
        if entries
        else 0.0
    )
    notes = (
        ("targeted transition review is ready for handoff",)
        if approved_transition_ids
        else ("no transition is currently ready for responsible targeted handoff",)
    )
    return TargetedTransitionReview(
        assay_id=assay_id,
        approved_transition_ids=approved_transition_ids,
        exploratory_transition_ids=exploratory_transition_ids,
        refused_transition_ids=refused_transition_ids,
        readiness_score=readiness_score,
        entries=tuple(entries),
        notes=notes,
    )


__all__ = [
    "TargetedTransitionCandidate",
    "TargetedTransitionReview",
    "TargetedTransitionReviewEntry",
    "TransitionReviewDisposition",
    "review_targeted_transition_candidates",
]

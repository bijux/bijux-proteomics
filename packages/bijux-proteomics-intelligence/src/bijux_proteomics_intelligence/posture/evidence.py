# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Evidence posture summaries and recommendation gating for intelligence."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation.serialization.json_models import JsonModel
from bijux_proteomics_foundation.refusals import OperationRefusal, RefusalKind
from bijux_proteomics_foundation.results import OperationResult
from bijux_proteomics_foundation.states import SupportState
from bijux_proteomics_knowledge.memory.evidence import (
    EvidenceBundle,
    compute_bundle_trust,
    flag_conflicting_evidence,
    plan_evidence_refresh,
)


class ContradictionPosture(StrEnum):
    """Contradiction posture over one evidence bundle."""

    CLEAR = "clear"
    UNRESOLVED = "unresolved"
    BLOCKING = "blocking"


class FreshnessPosture(StrEnum):
    """Freshness posture over one evidence bundle."""

    CURRENT = "current"
    AGING = "aging"
    STALE = "stale"


class EvidenceContradictionSummary(JsonModel):
    """Decision-facing summary of contradiction pressure in one evidence bundle."""

    model_config = ConfigDict(extra="forbid")

    bundle_id: str = Field(..., min_length=1)
    target_id: str = Field(..., min_length=1)
    conflict_count: int = Field(default=0, ge=0)
    dominant_conflict_types: tuple[str, ...] = Field(default_factory=tuple)
    conflicting_evidence_ids: tuple[str, ...] = Field(default_factory=tuple)
    posture: ContradictionPosture
    blocking_conflict_count: int = Field(default=0, ge=0)
    exact_conflict_reasons: tuple[str, ...] = Field(default_factory=tuple)
    unresolved_questions: tuple[str, ...] = Field(default_factory=tuple)
    contradiction_pressure: float = Field(..., ge=0.0, le=1.0)
    resolution_actions: tuple[str, ...] = Field(default_factory=tuple)


class EvidenceFreshnessSummary(JsonModel):
    """Decision-facing summary of freshness pressure in one evidence bundle."""

    model_config = ConfigDict(extra="forbid")

    bundle_id: str = Field(..., min_length=1)
    target_id: str = Field(..., min_length=1)
    trust_score: float = Field(..., ge=0.0, le=1.0)
    stale_records: tuple[str, ...] = Field(default_factory=tuple)
    aging_records: tuple[str, ...] = Field(default_factory=tuple)
    posture: FreshnessPosture
    stale_record_reasons: dict[str, str] = Field(default_factory=dict)
    aging_record_reasons: dict[str, str] = Field(default_factory=dict)
    decisive_stale_records: tuple[str, ...] = Field(default_factory=tuple)
    decisive_aging_records: tuple[str, ...] = Field(default_factory=tuple)
    freshness_score: float = Field(..., ge=0.0, le=1.0)
    refresh_actions: tuple[str, ...] = Field(default_factory=tuple)


def summarize_evidence_contradictions(
    bundle: EvidenceBundle,
) -> EvidenceContradictionSummary:
    """Summarize contradiction pressure for one evidence bundle."""
    conflicts = flag_conflicting_evidence(bundle)
    conflict_types: dict[str, int] = {}
    conflicting_ids: set[str] = set()
    resolution_actions: set[str] = set()
    for conflict in conflicts:
        conflict_types[conflict.conflict_type] = (
            conflict_types.get(conflict.conflict_type, 0) + 1
        )
        conflicting_ids.update((conflict.left_evidence_id, conflict.right_evidence_id))
        resolution_actions.add(f"resolve {conflict.conflict_type.replace('_', ' ')}")
    exact_conflict_reasons = tuple(
        sorted({conflict.reason.strip() for conflict in conflicts if conflict.reason})
    )
    dominant_types = tuple(
        sorted(conflict_types, key=lambda item: (-conflict_types[item], item))
    )
    contradiction_pressure = round(
        min(len(conflicts) / max(len(bundle.records), 1), 1.0),
        4,
    )
    blocking_conflict_count = sum(
        1 for conflict in conflicts if conflict.severity.lower() in {"high", "critical"}
    )
    posture = ContradictionPosture.CLEAR
    if conflicts:
        if len(conflicts) >= 2 or contradiction_pressure >= 0.45:
            posture = ContradictionPosture.BLOCKING
        else:
            posture = ContradictionPosture.UNRESOLVED
    unresolved_questions = tuple(
        sorted(
            f"resolve contradiction: {reason}"
            for reason in exact_conflict_reasons
        )
    )
    return EvidenceContradictionSummary(
        bundle_id=bundle.bundle_id,
        target_id=bundle.target_id,
        conflict_count=len(conflicts),
        dominant_conflict_types=dominant_types,
        conflicting_evidence_ids=tuple(sorted(conflicting_ids)),
        posture=posture,
        blocking_conflict_count=blocking_conflict_count,
        exact_conflict_reasons=exact_conflict_reasons,
        unresolved_questions=unresolved_questions,
        contradiction_pressure=contradiction_pressure,
        resolution_actions=tuple(sorted(resolution_actions)),
    )


def summarize_evidence_freshness(
    bundle: EvidenceBundle,
    *,
    now: datetime | None = None,
) -> EvidenceFreshnessSummary:
    """Summarize freshness pressure for one evidence bundle."""
    current_time = now or datetime.now(UTC)
    trust = compute_bundle_trust(bundle, now=current_time)
    refresh_plan = plan_evidence_refresh(bundle, now=current_time)
    aging_count = len(refresh_plan.aging_records)
    freshness_score = round(
        max(0.0, trust.trust_score - (0.05 * aging_count)),
        4,
    )
    stale_ids = set(refresh_plan.stale_records)
    aging_ids = set(refresh_plan.aging_records)
    stale_record_reasons = {
        need.evidence_id: need.reason
        for need in refresh_plan.refresh_needs
        if need.evidence_id in stale_ids
    }
    aging_record_reasons = {
        need.evidence_id: need.reason
        for need in refresh_plan.refresh_needs
        if need.evidence_id in aging_ids
    }
    decisive_stale_records = tuple(
        sorted(
            record.evidence_id
            for record in bundle.records
            if record.evidence_id in stale_ids and record.strength.value == "decisive"
        )
    )
    decisive_aging_records = tuple(
        sorted(
            record.evidence_id
            for record in bundle.records
            if record.evidence_id in aging_ids and record.strength.value == "decisive"
        )
    )
    posture = FreshnessPosture.CURRENT
    if refresh_plan.stale_records:
        posture = FreshnessPosture.STALE
    elif refresh_plan.aging_records:
        posture = FreshnessPosture.AGING
    refresh_actions = tuple(
        sorted({need.suggested_action for need in refresh_plan.refresh_needs})
    )
    return EvidenceFreshnessSummary(
        bundle_id=bundle.bundle_id,
        target_id=bundle.target_id,
        trust_score=trust.trust_score,
        stale_records=tuple(sorted(refresh_plan.stale_records)),
        aging_records=tuple(sorted(refresh_plan.aging_records)),
        posture=posture,
        stale_record_reasons=stale_record_reasons,
        aging_record_reasons=aging_record_reasons,
        decisive_stale_records=decisive_stale_records,
        decisive_aging_records=decisive_aging_records,
        freshness_score=freshness_score,
        refresh_actions=refresh_actions,
    )


def assess_recommendation_readiness(
    bundle: EvidenceBundle,
    *,
    now: datetime | None = None,
    minimum_trust_score: float = 0.6,
    minimum_record_count: int = 2,
) -> OperationResult:
    """Return whether the current evidence posture supports an explicit recommendation."""
    freshness = summarize_evidence_freshness(bundle, now=now)
    contradictions = summarize_evidence_contradictions(bundle)
    recommended_actions: set[str] = set(freshness.refresh_actions)
    recommended_actions.update(contradictions.resolution_actions)
    evidence_kinds = {record.kind for record in bundle.records}
    decisive_record_count = sum(1 for record in bundle.records if record.strength.value == "decisive")
    source_types = {record.source_type for record in bundle.records}
    grounding_reasons: set[str] = set()
    if len(bundle.records) < minimum_record_count:
        grounding_reasons.add(
            f"bundle carries only {len(bundle.records)} evidence records and is incomplete for recommendation gating"
        )
    if len(evidence_kinds) < 2:
        grounding_reasons.add(
            f"bundle covers only {len(evidence_kinds)} evidence kind and lacks orthogonal support"
        )
    if decisive_record_count == 0:
        grounding_reasons.add(
            "bundle lacks decisive evidence records for grounded recommendation support"
        )
    if len(source_types) == 1 and next(iter(source_types)).value != "lab_assay":
        grounding_reasons.add(
            "bundle depends on one non-lab source category and lacks direct experimental grounding"
        )

    if contradictions.posture is ContradictionPosture.BLOCKING:
        reason_details = tuple(
            sorted(
                {
                    *contradictions.exact_conflict_reasons,
                    *contradictions.unresolved_questions,
                    f"contradiction pressure={contradictions.contradiction_pressure:.2f}",
                }
            )
        )
        refusal = OperationRefusal(
            operation="intelligence_recommendation",
            kind=RefusalKind.AMBIGUOUS,
            code="contradictory_evidence",
            reason="evidence contradictions remain unresolved",
            reason_details=reason_details,
            recommended_actions=tuple(sorted(recommended_actions)),
        )
        return OperationResult.refused(
            operation="intelligence_recommendation",
            summary="recommendation refused because the evidence posture remains contradictory",
            refusal=refusal,
        )
    if grounding_reasons:
        refusal = OperationRefusal(
            operation="intelligence_recommendation",
            kind=RefusalKind.UNSUPPORTED,
            code="thin_grounding_support",
            reason="evidence posture is too thin or weak for a grounded recommendation",
            reason_details=tuple(sorted(grounding_reasons)),
            recommended_actions=tuple(sorted(recommended_actions)),
        )
        return OperationResult.refused(
            operation="intelligence_recommendation",
            summary="recommendation refused because grounding remains too thin or weak",
            refusal=refusal,
        )
    degradation_reasons: set[str] = set()
    degradation_state = SupportState.INCOMPLETE
    if contradictions.posture is ContradictionPosture.UNRESOLVED:
        degradation_state = SupportState.AMBIGUOUS
        degradation_reasons.update(contradictions.unresolved_questions)
        degradation_reasons.add(
            f"contradiction pressure={contradictions.contradiction_pressure:.2f}"
        )
    if freshness.posture is FreshnessPosture.STALE:
        degradation_state = SupportState.AMBIGUOUS
        degradation_reasons.update(
            f"{record_id}: {reason}"
            for record_id, reason in freshness.stale_record_reasons.items()
        )
        degradation_reasons.add(
            f"{len(freshness.stale_records)} evidence records are stale and should be refreshed"
        )
    elif freshness.posture is FreshnessPosture.AGING:
        degradation_reasons.update(
            f"{record_id}: {reason}"
            for record_id, reason in freshness.aging_record_reasons.items()
        )
        degradation_reasons.add(
            f"{len(freshness.aging_records)} evidence records are nearing expiry"
        )
    if freshness.trust_score < minimum_trust_score:
        degradation_state = SupportState.AMBIGUOUS
        degradation_reasons.add(
            f"bundle trust score {freshness.trust_score:.2f} is below the minimum recommendation threshold"
        )
    if degradation_reasons:
        return OperationResult.degraded_success(
            operation="intelligence_recommendation",
            summary="recommendation is usable only with explicit evidence posture caveats",
            state=degradation_state,
            degradation_reasons=tuple(sorted({*degradation_reasons, *freshness.refresh_actions})),
        )
    return OperationResult.success(
        operation="intelligence_recommendation",
        summary="evidence posture is strong enough for an explicit recommendation",
    )


__all__ = [
    "ContradictionPosture",
    "EvidenceContradictionSummary",
    "EvidenceFreshnessSummary",
    "FreshnessPosture",
    "assess_recommendation_readiness",
    "summarize_evidence_contradictions",
    "summarize_evidence_freshness",
]

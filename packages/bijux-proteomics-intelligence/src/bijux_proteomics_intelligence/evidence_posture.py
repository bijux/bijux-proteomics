# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Evidence posture summaries and recommendation gating for intelligence."""

from __future__ import annotations

from datetime import UTC, datetime

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation.json_models import JsonModel
from bijux_proteomics_foundation.refusals import OperationRefusal, RefusalKind
from bijux_proteomics_foundation.results import OperationResult
from bijux_proteomics_foundation.states import SupportState
from bijux_proteomics_knowledge import (
    EvidenceBundle,
    compute_bundle_trust,
    flag_conflicting_evidence,
    plan_evidence_refresh,
)


class EvidenceContradictionSummary(JsonModel):
    """Decision-facing summary of contradiction pressure in one evidence bundle."""

    model_config = ConfigDict(extra="forbid")

    bundle_id: str = Field(..., min_length=1)
    target_id: str = Field(..., min_length=1)
    conflict_count: int = Field(default=0, ge=0)
    dominant_conflict_types: tuple[str, ...] = Field(default_factory=tuple)
    conflicting_evidence_ids: tuple[str, ...] = Field(default_factory=tuple)
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
    dominant_types = tuple(
        sorted(conflict_types, key=lambda item: (-conflict_types[item], item))
    )
    contradiction_pressure = round(
        min(len(conflicts) / max(len(bundle.records), 1), 1.0),
        4,
    )
    return EvidenceContradictionSummary(
        bundle_id=bundle.bundle_id,
        target_id=bundle.target_id,
        conflict_count=len(conflicts),
        dominant_conflict_types=dominant_types,
        conflicting_evidence_ids=tuple(sorted(conflicting_ids)),
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
    refresh_actions = tuple(
        sorted({need.suggested_action for need in refresh_plan.refresh_needs})
    )
    return EvidenceFreshnessSummary(
        bundle_id=bundle.bundle_id,
        target_id=bundle.target_id,
        trust_score=trust.trust_score,
        stale_records=tuple(sorted(refresh_plan.stale_records)),
        aging_records=tuple(sorted(refresh_plan.aging_records)),
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
    reasons: list[str] = []
    recommended_actions: set[str] = set(freshness.refresh_actions)
    recommended_actions.update(contradictions.resolution_actions)

    if len(bundle.records) < minimum_record_count:
        reasons.append(
            f"bundle carries only {len(bundle.records)} evidence records and is incomplete for recommendation gating"
        )
    if freshness.trust_score < minimum_trust_score:
        reasons.append(
            f"bundle trust score {freshness.trust_score:.2f} is below the minimum recommendation threshold"
        )
    if contradictions.conflict_count:
        reasons.append(
            f"bundle contains {contradictions.conflict_count} evidence conflicts that keep the recommendation ambiguous"
        )
    if freshness.stale_records:
        reasons.append(
            f"{len(freshness.stale_records)} evidence records are stale and should be refreshed"
        )

    if contradictions.conflict_count:
        refusal = OperationRefusal(
            operation="intelligence_recommendation",
            kind=RefusalKind.AMBIGUOUS,
            code="contradictory_evidence",
            reason="evidence contradictions remain unresolved",
            reason_details=tuple(sorted(reasons)),
            recommended_actions=tuple(sorted(recommended_actions)),
        )
        return OperationResult.refused(
            operation="intelligence_recommendation",
            summary="recommendation refused because the evidence posture remains contradictory",
            refusal=refusal,
        )
    if reasons:
        refusal = OperationRefusal(
            operation="intelligence_recommendation",
            kind=RefusalKind.UNSUPPORTED,
            code="incomplete_recommendation_evidence",
            reason="evidence posture is too weak or incomplete for recommendation",
            reason_details=tuple(sorted(reasons)),
            recommended_actions=tuple(sorted(recommended_actions)),
        )
        return OperationResult.refused(
            operation="intelligence_recommendation",
            summary="recommendation refused because evidence support is too weak or incomplete",
            refusal=refusal,
        )
    if freshness.aging_records:
        return OperationResult.degraded_success(
            operation="intelligence_recommendation",
            summary="recommendation is usable but aging evidence should be refreshed soon",
            state=SupportState.INCOMPLETE,
            degradation_reasons=tuple(
                sorted(
                    {
                        f"{len(freshness.aging_records)} evidence records are nearing expiry",
                        *freshness.refresh_actions,
                    }
                )
            ),
        )
    return OperationResult.success(
        operation="intelligence_recommendation",
        summary="evidence posture is strong enough for an explicit recommendation",
    )


__all__ = [
    "EvidenceContradictionSummary",
    "EvidenceFreshnessSummary",
    "assess_recommendation_readiness",
    "summarize_evidence_contradictions",
    "summarize_evidence_freshness",
]

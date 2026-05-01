# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Lab planning production surfaces for iteration 16."""

from __future__ import annotations

from enum import StrEnum
import random

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel


class LabCostModelInput(JsonModel):
    """Cost inputs for one planned assay action."""

    model_config = ConfigDict(extra="forbid")

    action_id: str = Field(..., min_length=1)
    reagent_cost: float = Field(..., ge=0.0)
    instrument_cost: float = Field(..., ge=0.0)
    staff_cost: float = Field(..., ge=0.0)
    opportunity_cost: float = Field(..., ge=0.0)
    uncertainty_fraction: float = Field(..., ge=0.0, le=1.0)


class LabCostModelEntry(JsonModel):
    """Computed cost summary with bounded uncertainty interval."""

    model_config = ConfigDict(extra="forbid")

    action_id: str = Field(..., min_length=1)
    expected_total_cost: float = Field(..., ge=0.0)
    low_estimate: float = Field(..., ge=0.0)
    high_estimate: float = Field(..., ge=0.0)


class LabCostModelReport(JsonModel):
    """Cost model report across planned assay actions."""

    model_config = ConfigDict(extra="forbid")

    entries: tuple[LabCostModelEntry, ...] = Field(default_factory=tuple)


def build_lab_cost_model_report(
    actions: tuple[LabCostModelInput, ...],
) -> LabCostModelReport:
    """Model reagent/instrument/staff/opportunity costs with uncertainty intervals."""

    entries = []
    for action in actions:
        expected = (
            action.reagent_cost
            + action.instrument_cost
            + action.staff_cost
            + action.opportunity_cost
        )
        swing = expected * action.uncertainty_fraction
        entries.append(
            LabCostModelEntry(
                action_id=action.action_id,
                expected_total_cost=expected,
                low_estimate=max(0.0, expected - swing),
                high_estimate=expected + swing,
            )
        )

    entries.sort(key=lambda entry: entry.action_id)
    return LabCostModelReport(entries=tuple(entries))


class PlateRandomizationStrategy(StrEnum):
    """Randomization/blocking strategies for plate layout planning."""

    FULL_RANDOM = "full_random"
    BLOCK_BY_CONDITION = "block_by_condition"
    BLOCK_BY_BATCH = "block_by_batch"


class PlateRandomizationRequest(JsonModel):
    """Input for reproducible plate randomization strategy planning."""

    model_config = ConfigDict(extra="forbid")

    plate_id: str = Field(..., min_length=1)
    strategy: PlateRandomizationStrategy
    sample_ids: tuple[str, ...] = Field(default_factory=tuple)
    block_labels: tuple[str, ...] = Field(default_factory=tuple)
    seed: int = Field(..., ge=0)


class PlateRandomizationIssue(JsonModel):
    """Support/refusal issue for selected randomization strategy."""

    model_config = ConfigDict(extra="forbid")

    code: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)


class PlateRandomizationPlan(JsonModel):
    """Reproducible randomization output with explicit strategy support state."""

    model_config = ConfigDict(extra="forbid")

    plate_id: str = Field(..., min_length=1)
    strategy: PlateRandomizationStrategy
    supported: bool
    assignment_order: tuple[str, ...] = Field(default_factory=tuple)
    issues: tuple[PlateRandomizationIssue, ...] = Field(default_factory=tuple)


def build_plate_randomization_plan(
    request: PlateRandomizationRequest,
) -> PlateRandomizationPlan:
    """Support/refuse randomization strategies with deterministic seeded assignment."""

    issues: list[PlateRandomizationIssue] = []
    if not request.sample_ids:
        issues.append(
            PlateRandomizationIssue(
                code="missing_samples",
                message="plate randomization requires at least one sample",
            )
        )
    if request.strategy is not PlateRandomizationStrategy.FULL_RANDOM and (
        not request.block_labels or len(request.block_labels) != len(request.sample_ids)
    ):
        issues.append(
            PlateRandomizationIssue(
                code="invalid_block_labels",
                message=(
                    "blocking strategies require one block label per sample for "
                    "deterministic constrained assignment"
                ),
            )
        )

    if issues:
        return PlateRandomizationPlan(
            plate_id=request.plate_id,
            strategy=request.strategy,
            supported=False,
            assignment_order=(),
            issues=tuple(issues),
        )

    rng = random.Random(request.seed)
    ordered = list(request.sample_ids)
    if request.strategy is PlateRandomizationStrategy.FULL_RANDOM:
        rng.shuffle(ordered)
    else:
        grouped: dict[str, list[str]] = {}
        for sample_id, block in zip(request.sample_ids, request.block_labels, strict=False):
            grouped.setdefault(block, []).append(sample_id)
        block_keys = sorted(grouped)
        rng.shuffle(block_keys)
        ordered = []
        for block in block_keys:
            samples = grouped[block]
            rng.shuffle(samples)
            ordered.extend(samples)

    return PlateRandomizationPlan(
        plate_id=request.plate_id,
        strategy=request.strategy,
        supported=True,
        assignment_order=tuple(ordered),
        issues=(),
    )


class ValidationStageProgressionInput(JsonModel):
    """Evidence summary used for discovery-to-validation progression decisions."""

    model_config = ConfigDict(extra="forbid")

    candidate_id: str = Field(..., min_length=1)
    evidence_strength: float = Field(..., ge=0.0, le=1.0)
    replication_count: int = Field(..., ge=0)
    qc_pass_rate: float = Field(..., ge=0.0, le=1.0)
    contradiction_count: int = Field(..., ge=0)


class ValidationStageProgressionPolicy(JsonModel):
    """Threshold policy for progression into validation and targeted follow-up."""

    model_config = ConfigDict(extra="forbid")

    min_evidence_strength: float = Field(default=0.7, ge=0.0, le=1.0)
    min_replication_count: int = Field(default=2, ge=0)
    min_qc_pass_rate: float = Field(default=0.8, ge=0.0, le=1.0)
    max_contradiction_count: int = Field(default=1, ge=0)


class ValidationStageProgressionDecision(JsonModel):
    """Decision for whether candidate can progress to validation/follow-up stages."""

    model_config = ConfigDict(extra="forbid")

    candidate_id: str = Field(..., min_length=1)
    eligible_for_validation: bool
    eligible_for_targeted_follow_up: bool
    reasons: tuple[str, ...] = Field(default_factory=tuple)


def evaluate_validation_stage_progression_policy(
    *,
    payload: ValidationStageProgressionInput,
    policy: ValidationStageProgressionPolicy | None = None,
) -> ValidationStageProgressionDecision:
    """Evaluate evidence thresholds for progression into validation and follow-up stages."""

    active = policy if policy is not None else ValidationStageProgressionPolicy()
    reasons: list[str] = []

    if payload.evidence_strength < active.min_evidence_strength:
        reasons.append("evidence_strength below validation threshold")
    if payload.replication_count < active.min_replication_count:
        reasons.append("replication_count below validation threshold")
    if payload.qc_pass_rate < active.min_qc_pass_rate:
        reasons.append("qc_pass_rate below validation threshold")
    if payload.contradiction_count > active.max_contradiction_count:
        reasons.append("contradiction_count above allowed threshold")

    validation = not reasons
    follow_up = validation or (
        payload.evidence_strength >= 0.5
        and payload.replication_count >= 1
        and payload.qc_pass_rate >= 0.6
    )
    if not follow_up and not reasons:
        reasons.append("insufficient evidence for targeted follow-up")

    return ValidationStageProgressionDecision(
        candidate_id=payload.candidate_id,
        eligible_for_validation=validation,
        eligible_for_targeted_follow_up=follow_up,
        reasons=tuple(reasons),
    )


class LabOutcomeIngestionRecord(JsonModel):
    """Observed lab outcome event for evidence/lifecycle ingestion."""

    model_config = ConfigDict(extra="forbid")

    outcome_id: str = Field(..., min_length=1)
    candidate_id: str = Field(..., min_length=1)
    observed_status: str = Field(..., min_length=1)
    evidence_pointer_id: str = Field(..., min_length=1)
    observed_at_utc: str = Field(..., min_length=1)


class LabOutcomeIngestionPolicy(JsonModel):
    """Versioned policy for lab outcome ingestion behavior."""

    model_config = ConfigDict(extra="forbid")

    policy_id: str = Field(..., min_length=1)
    policy_version: str = Field(..., min_length=1)


class LabOutcomeIngestionUpdate(JsonModel):
    """Derived update from one ingested lab outcome."""

    model_config = ConfigDict(extra="forbid")

    candidate_id: str = Field(..., min_length=1)
    lifecycle_state: str = Field(..., min_length=1)
    evidence_update: str = Field(..., min_length=1)


class LabOutcomeIngestionReport(JsonModel):
    """Ingestion report with versioned policy trace and updates."""

    model_config = ConfigDict(extra="forbid")

    policy_id: str = Field(..., min_length=1)
    policy_version: str = Field(..., min_length=1)
    updates: tuple[LabOutcomeIngestionUpdate, ...] = Field(default_factory=tuple)


def ingest_lab_outcomes_with_versioned_policy(
    *,
    outcomes: tuple[LabOutcomeIngestionRecord, ...],
    policy: LabOutcomeIngestionPolicy,
) -> LabOutcomeIngestionReport:
    """Ingest outcomes and produce evidence/lifecycle updates with policy version trace."""

    updates = []
    for outcome in outcomes:
        status = outcome.observed_status.lower()
        if status in {"validated", "confirmed"}:
            lifecycle = "validation_confirmed"
        elif status in {"failed", "rejected"}:
            lifecycle = "requires_reassessment"
        else:
            lifecycle = "under_review"

        updates.append(
            LabOutcomeIngestionUpdate(
                candidate_id=outcome.candidate_id,
                lifecycle_state=lifecycle,
                evidence_update=(
                    f"link {outcome.evidence_pointer_id} from {outcome.outcome_id} "
                    f"at {outcome.observed_at_utc}"
                ),
            )
        )

    updates.sort(key=lambda item: item.candidate_id)
    return LabOutcomeIngestionReport(
        policy_id=policy.policy_id,
        policy_version=policy.policy_version,
        updates=tuple(updates),
    )


class LabRiskDashboardInput(JsonModel):
    """Aggregated risk inputs for one candidate in dashboard summaries."""

    model_config = ConfigDict(extra="forbid")

    candidate_id: str = Field(..., min_length=1)
    evidence_gap_count: int = Field(..., ge=0)
    target_risk_score: float = Field(..., ge=0.0, le=1.0)
    sample_constraint_score: float = Field(..., ge=0.0, le=1.0)
    capacity_pressure_score: float = Field(..., ge=0.0, le=1.0)
    mitigation_actions: tuple[str, ...] = Field(default_factory=tuple)


class LabRiskDashboardEntry(JsonModel):
    """Dashboard row summarizing lab planning risks and mitigations."""

    model_config = ConfigDict(extra="forbid")

    candidate_id: str = Field(..., min_length=1)
    composite_risk_score: float = Field(..., ge=0.0)
    evidence_gap_count: int = Field(..., ge=0)
    mitigation_actions: tuple[str, ...] = Field(default_factory=tuple)


class LabRiskDashboardReport(JsonModel):
    """Risk dashboard data for evidence gaps, constraints, capacity, and mitigations."""

    model_config = ConfigDict(extra="forbid")

    entries: tuple[LabRiskDashboardEntry, ...] = Field(default_factory=tuple)


def build_lab_risk_dashboard_report(
    items: tuple[LabRiskDashboardInput, ...],
) -> LabRiskDashboardReport:
    """Summarize evidence gaps, target/sample/capacity risks, and mitigations."""

    entries = []
    for item in items:
        composite = (
            (0.3 * item.target_risk_score)
            + (0.25 * item.sample_constraint_score)
            + (0.25 * item.capacity_pressure_score)
            + (0.2 * min(1.0, item.evidence_gap_count / 5.0))
        )
        entries.append(
            LabRiskDashboardEntry(
                candidate_id=item.candidate_id,
                composite_risk_score=composite,
                evidence_gap_count=item.evidence_gap_count,
                mitigation_actions=tuple(sorted(set(item.mitigation_actions))),
            )
        )

    entries.sort(key=lambda entry: (-entry.composite_risk_score, entry.candidate_id))
    return LabRiskDashboardReport(entries=tuple(entries))

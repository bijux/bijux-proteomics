# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Priority and practicality scoring for lab planning."""

from __future__ import annotations

from pydantic import ConfigDict, Field

from bijux_proteomics.domain.program_spec import ProgramSpec
from bijux_proteomics_foundation import AssayId, BatchId, JsonModel, ProgramId
from bijux_proteomics_knowledge.memory.models.evidence import (
    EvidenceBundle,
    assess_decision_readiness,
    compute_bundle_trust,
    flag_conflicting_evidence,
)
from bijux_proteomics_lab.outcomes import (
    AssayResultState,
    ExperimentOutcome,
    assess_batch_outcome,
    triage_batch_failures,
)

from bijux_proteomics_lab.planning.assays import (
    AssayObservation,
    ExperimentPlan,
    MaterialInventory,
    MaterialRequirement,
    ProgressDecision,
)
from bijux_proteomics_lab.planning.scheduling import (
    FamilyCapacity,
    InstrumentAvailability,
    LabCapacity,
    build_execution_capacity_advisory,
    prioritize_batches_by_material_feasibility,
    schedule_experiment_plan,
    schedule_with_family_capacity,
    summarize_schedule_pressure,
)

class NextAssayPriority(JsonModel):
    """Priority score for selecting the next assay based on information gain."""

    model_config = ConfigDict(extra="forbid")

    assay_id: AssayId = Field(..., description="Assay identifier.")
    score: float = Field(..., description="Priority score.")
    estimated_cost: float = Field(
        default=0.0,
        ge=0.0,
        description="Estimated relative execution cost for this assay.",
    )
    estimated_days: float = Field(
        default=0.0,
        ge=0.0,
        description="Estimated time-to-result in days.",
    )
    reasons: list[str] = Field(
        default_factory=list, description="Short rationale points."
    )

class CandidatePrioritySignal(JsonModel):
    """External candidate-priority input aligned against lab assays."""

    model_config = ConfigDict(extra="forbid")

    candidate_id: str = Field(..., min_length=1)
    score: float = Field(..., ge=0.0)
    assay_ids: list[AssayId] = Field(default_factory=list)
    decision_ready: bool = True
    contradiction_pressure: float = Field(default=0.0, ge=0.0, le=1.0)
    freshness_pressure: float = Field(default=0.0, ge=0.0, le=1.0)
    unresolved_questions: list[str] = Field(default_factory=list)
    recommended_action: str | None = Field(default=None, min_length=1)
    policy_lineage_id: str | None = Field(default=None, min_length=1)
    rationale: list[str] = Field(default_factory=list)

class LabPriorityQueueAlignment(JsonModel):
    """Alignment report between candidate ranking signals and assay priorities."""

    model_config = ConfigDict(extra="forbid")

    program_id: ProgramId = Field(..., description="Program identifier.")
    prioritized_assay_ids: list[AssayId] = Field(default_factory=list)
    unaligned_candidate_ids: list[str] = Field(default_factory=list)
    skeptical_candidate_ids: list[str] = Field(default_factory=list)
    held_candidate_ids: list[str] = Field(default_factory=list)
    candidate_assay_scores: dict[str, float] = Field(default_factory=dict)
    notes: list[str] = Field(default_factory=list)

class FollowUpPracticalityReport(JsonModel):
    """Practicality report for candidate follow-up under real lab constraints."""

    model_config = ConfigDict(extra="forbid")

    program_id: ProgramId = Field(..., description="Program identifier.")
    practical_candidate_ids: list[str] = Field(default_factory=list)
    impractical_candidate_ids: list[str] = Field(default_factory=list)
    constrained_candidate_ids: list[str] = Field(default_factory=list)
    material_blocked_candidate_ids: list[str] = Field(default_factory=list)
    executable_batch_ids: list[BatchId] = Field(default_factory=list)
    blocked_batch_ids: list[BatchId] = Field(default_factory=list)
    estimated_total_cost: float = Field(default=0.0, ge=0.0)
    practicality_score: float = Field(default=0.0, ge=0.0, le=1.0)
    blockers: list[str] = Field(default_factory=list)
    schedule_pressure_notes: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)

class InformationGainBreakdown(JsonModel):
    """Multiparameter information-gain score components for an assay."""

    model_config = ConfigDict(extra="forbid")

    assay_id: AssayId = Field(..., description="Assay identifier.")
    uncertainty_reduction: float = Field(
        ..., ge=0.0, le=1.0, description="Expected uncertainty reduction."
    )
    contradiction_resolution_value: float = Field(
        ..., ge=0.0, le=1.0, description="Expected contradiction resolution value."
    )
    falsification_value: float = Field(
        ..., ge=0.0, le=1.0, description="Expected hypothesis falsification value."
    )
    decision_gate_impact: float = Field(
        ..., ge=0.0, le=1.0, description="Impact on near-term decision gates."
    )
    orthogonal_confirmation_value: float = Field(
        ..., ge=0.0, le=1.0, description="Orthogonal confirmation contribution."
    )
    burden_penalty: float = Field(
        ..., ge=0.0, le=1.0, description="Relative execution burden penalty."
    )
    final_score: float = Field(
        ..., ge=0.0, le=1.0, description="Combined information-gain score."
    )

class GateImpactScore(JsonModel):
    """Decision-gate impact score for an assay in the current experiment plan."""

    model_config = ConfigDict(extra="forbid")

    assay_id: AssayId = Field(..., description="Assay identifier.")
    batch_id: BatchId = Field(..., description="Batch containing the assay.")
    blocking_gate_count: int = Field(
        ..., ge=0, description="Count of blocking review gates tied to the batch."
    )
    impact_score: float = Field(
        ..., ge=0.0, le=1.0, description="Combined decision-gate impact score."
    )
    rationale: list[str] = Field(
        default_factory=list, description="Human-readable impact rationale."
    )

class AssayExecutionBurden(JsonModel):
    """Estimated execution burden for one assay inside an experiment plan."""

    model_config = ConfigDict(extra="forbid")

    assay_id: AssayId = Field(..., description="Assay identifier.")
    batch_id: BatchId = Field(..., description="Batch containing the assay.")
    burden_score: float = Field(
        ..., ge=0.0, le=1.0, description="Relative burden score."
    )
    estimated_days: float = Field(
        ..., ge=0.0, description="Estimated turnaround time in days."
    )
    drivers: list[str] = Field(
        default_factory=list, description="Primary burden drivers."
    )

class LabCycleBrief(JsonModel):
    """Decision brief for the next laboratory cycle."""

    model_config = ConfigDict(extra="forbid")

    program_id: ProgramId = Field(..., description="Program identifier.")
    ready_for_progression: bool = Field(
        ..., description="Whether current evidence supports progression."
    )
    top_gate_impacts: list[GateImpactScore] = Field(
        default_factory=list, description="Highest gate-impact assays."
    )
    highest_burden_assays: list[AssayExecutionBurden] = Field(
        default_factory=list,
        description="Assays expected to create the most execution burden.",
    )
    next_assay_priorities: list[NextAssayPriority] = Field(
        default_factory=list,
        description="Highest-priority assays based on information gain.",
    )
    notes: list[str] = Field(
        default_factory=list, description="Summary notes for review."
    )

class MaterialReservation(JsonModel):
    """Material reservation request tied to a specific batch."""

    model_config = ConfigDict(extra="forbid")

    batch_id: BatchId = Field(..., description="Batch identifier.")
    material_id: str = Field(..., min_length=1, description="Material identifier.")
    reserved_units: float = Field(..., ge=0.0, description="Reserved quantity.")
    unit: str = Field(..., min_length=1, description="Unit of measure.")
    feasible: bool = Field(
        ..., description="Whether reservation is feasible with current inventory."
    )

class LabExecutionDirective(JsonModel):
    """Operational directive for the next lab cycle based on outcome triage."""

    model_config = ConfigDict(extra="forbid")

    batch_id: BatchId = Field(..., description="Batch identifier.")
    decision: ProgressDecision = Field(
        ..., description="Operational next-step decision."
    )
    escalation_assay_ids: list[AssayId] = Field(
        default_factory=list, description="Assays requiring escalation."
    )
    immediate_actions: list[str] = Field(
        default_factory=list, description="Immediate execution actions."
    )

class PlanningPolicy(JsonModel):
    """Weights and penalties for information-gain planning calculations."""

    model_config = ConfigDict(extra="forbid")

    policy_id: str = Field(
        ..., min_length=1, description="Stable planning policy identifier."
    )
    uncertainty_weight: float = Field(
        default=0.22, ge=0.0, le=1.0, description="Weight for uncertainty reduction."
    )
    contradiction_weight: float = Field(
        default=0.2, ge=0.0, le=1.0, description="Weight for contradiction resolution."
    )
    falsification_weight: float = Field(
        default=0.18, ge=0.0, le=1.0, description="Weight for falsification value."
    )
    gate_impact_weight: float = Field(
        default=0.2, ge=0.0, le=1.0, description="Weight for decision-gate impact."
    )
    orthogonal_weight: float = Field(
        default=0.2, ge=0.0, le=1.0, description="Weight for orthogonal confirmation."
    )
    blocking_burden_penalty: float = Field(
        default=0.2, ge=0.0, le=1.0, description="Burden penalty for blocking assays."
    )
    non_blocking_burden_penalty: float = Field(
        default=0.12,
        ge=0.0,
        le=1.0,
        description="Burden penalty for non-blocking assays.",
    )

def prioritize_next_assays(
    program: ProgramSpec,
    bundle: EvidenceBundle,
    observations: list[AssayObservation],
    *,
    policy: PlanningPolicy | None = None,
) -> list[NextAssayPriority]:
    """Rank pending assays by expected information gain and decision impact."""
    observed_ids = {observation.assay_id for observation in observations}
    trust = compute_bundle_trust(bundle)
    readiness = assess_decision_readiness(
        bundle, [need.value for need in program.evidence_needs]
    )
    ranked: list[NextAssayPriority] = []
    contradictions = flag_conflicting_evidence(bundle)
    policy = policy or PlanningPolicy(policy_id="default-planning-policy")
    for assay in program.assay_panel:
        if assay.assay_id in observed_ids:
            continue
        breakdown = score_assay_information_gain(
            assay_id=assay.assay_id,
            blocking=assay.blocking,
            readiness_ready=readiness.ready,
            trust_score=trust.trust_score,
            contradiction_count=len(contradictions),
            policy=policy,
        )
        reasons: list[str] = []
        if breakdown.decision_gate_impact >= 0.7:
            reasons.append("blocking assay with direct gate impact")
        if breakdown.contradiction_resolution_value > 0.0:
            reasons.append("assay can resolve active evidence contradictions")
        if breakdown.uncertainty_reduction >= 0.6:
            reasons.append("assay expected to reduce uncertainty substantially")
        estimated_cost = 1.5 if assay.blocking else 1.0
        estimated_days = 4.0 if assay.blocking else 2.0
        ranked.append(
            NextAssayPriority(
                assay_id=assay.assay_id,
                score=breakdown.final_score,
                estimated_cost=estimated_cost,
                estimated_days=estimated_days,
                reasons=reasons or ["assay reduces residual uncertainty"],
            )
        )
    return sorted(ranked, key=lambda item: item.score, reverse=True)

def align_lab_priority_queue(
    program: ProgramSpec,
    priorities: list[NextAssayPriority],
    candidate_signals: list[CandidatePrioritySignal],
) -> LabPriorityQueueAlignment:
    """Align externally ranked candidates with the lab assay-priority queue."""
    assay_scores = {priority.assay_id: priority.score for priority in priorities}
    aligned_rows: list[tuple[float, str]] = []
    unaligned_candidate_ids: list[str] = []
    skeptical_candidate_ids: list[str] = []
    held_candidate_ids: list[str] = []
    candidate_assay_scores: dict[str, float] = {}
    for signal in candidate_signals:
        if signal.recommended_action and "hold" in signal.recommended_action.lower():
            held_candidate_ids.append(signal.candidate_id)
            continue
        matched_assays = [
            assay_id for assay_id in signal.assay_ids if assay_id in assay_scores
        ]
        if not matched_assays:
            unaligned_candidate_ids.append(signal.candidate_id)
            continue
        skepticism_penalty = 0.0
        if not signal.decision_ready:
            skepticism_penalty += 0.5
        skepticism_penalty += signal.contradiction_pressure * 0.75
        skepticism_penalty += signal.freshness_pressure * 0.35
        skepticism_penalty += min(len(signal.unresolved_questions) * 0.08, 0.24)
        if signal.policy_lineage_id is None:
            skepticism_penalty += 0.15
        if skepticism_penalty >= 0.45:
            skeptical_candidate_ids.append(signal.candidate_id)
        for assay_id in matched_assays:
            combined_score = round(
                max(0.0, signal.score + assay_scores[assay_id] - skepticism_penalty),
                4,
            )
            candidate_assay_scores[f"{signal.candidate_id}:{assay_id}"] = combined_score
            aligned_rows.append((combined_score, assay_id))
    aligned_rows.sort(key=lambda row: (-row[0], row[1]))
    prioritized_assay_ids = list(
        dict.fromkeys(assay_id for _, assay_id in aligned_rows)
    )
    notes = (
        ["candidate-ranking signals reinforce the aligned assay queue"]
        if prioritized_assay_ids
        else ["no candidate-ranking signals aligned with the current assay queue"]
    )
    if unaligned_candidate_ids:
        notes.append("some candidate signals were not mapped to lab assays")
    if skeptical_candidate_ids:
        notes.append(
            "skeptical penalties downgraded some candidate-driven assay requests"
        )
    if held_candidate_ids:
        notes.append(
            "hold recommendations were excluded from the executable assay queue"
        )
    return LabPriorityQueueAlignment(
        program_id=program.program_id,
        prioritized_assay_ids=prioritized_assay_ids,
        unaligned_candidate_ids=sorted(unaligned_candidate_ids),
        skeptical_candidate_ids=sorted(skeptical_candidate_ids),
        held_candidate_ids=sorted(held_candidate_ids),
        candidate_assay_scores=candidate_assay_scores,
        notes=notes,
    )

def build_follow_up_practicality_report(
    plan: ExperimentPlan,
    capacity: LabCapacity,
    instrument_availability: list[InstrumentAvailability],
    candidate_signals: list[CandidatePrioritySignal],
    *,
    budget_limit: float,
    estimated_batch_cost: float = 1.0,
    family_capacities: list[FamilyCapacity] | None = None,
    material_requirements: list[MaterialRequirement] | None = None,
    inventory: list[MaterialInventory] | None = None,
) -> FollowUpPracticalityReport:
    """Assess whether candidate follow-up requests are practical under live constraints."""
    capacity_advisory = build_execution_capacity_advisory(
        plan,
        capacity,
        instrument_availability,
        budget_limit=budget_limit,
        estimated_batch_cost=estimated_batch_cost,
    )
    scheduled = (
        schedule_with_family_capacity(plan, capacity, family_capacities)
        if family_capacities
        else schedule_experiment_plan(plan, capacity)
    )
    schedule_pressure = summarize_schedule_pressure(scheduled, capacity)
    schedule_blocked_batches = {
        batch.batch_id
        for batch in scheduled.scheduled_batches
        if batch.deferred_assay_ids
    } | set(scheduled.unscheduled_batches)
    schedule_pressure_notes: list[str] = []
    if schedule_pressure.assay_slot_utilization >= 0.85:
        schedule_pressure_notes.append("schedule pressure is near cycle saturation")
    if schedule_pressure.deferred_assay_count > 0:
        schedule_pressure_notes.append(
            "schedule pressure from family or slot limits deferred part of the requested follow-up work"
        )
    material_blocked_batches: set[str] = set()
    if material_requirements is not None and inventory is not None:
        material_blocked_batches = {
            row.batch_id
            for row in prioritize_batches_by_material_feasibility(
                plan, material_requirements, inventory
            )
            if not row.material_ready
        }
    feasible_batches = set(capacity_advisory.feasible_batch_ids)
    assay_to_batch = {
        assay_id: batch.batch_id
        for batch in plan.batches
        for assay_id in batch.assay_ids
    }
    practical_candidate_ids: list[str] = []
    impractical_candidate_ids: list[str] = []
    constrained_candidate_ids: list[str] = []
    material_blocked_candidate_ids: list[str] = []
    blockers: list[str] = []

    for signal in candidate_signals:
        if signal.recommended_action and "hold" in signal.recommended_action.lower():
            impractical_candidate_ids.append(signal.candidate_id)
            blockers.append(f"{signal.candidate_id} remains on hold upstream")
            continue
        matched_batch_ids = {
            assay_to_batch[assay_id]
            for assay_id in signal.assay_ids
            if assay_id in assay_to_batch
        }
        if not matched_batch_ids:
            impractical_candidate_ids.append(signal.candidate_id)
            blockers.append(
                f"{signal.candidate_id} is not mapped to any planned executable batch"
            )
            continue
        if matched_batch_ids.issubset(material_blocked_batches) and material_blocked_batches:
            impractical_candidate_ids.append(signal.candidate_id)
            material_blocked_candidate_ids.append(signal.candidate_id)
            blockers.append(
                f"{signal.candidate_id} only maps to follow-up batches that lack required materials"
            )
            continue
        if not signal.decision_ready or signal.contradiction_pressure >= 0.45:
            impractical_candidate_ids.append(signal.candidate_id)
            blockers.append(
                f"{signal.candidate_id} is not analytically ready for operational spend"
            )
            continue
        executable_batch_ids = (
            (matched_batch_ids & feasible_batches)
            - schedule_blocked_batches
            - material_blocked_batches
        )
        if not executable_batch_ids:
            impractical_candidate_ids.append(signal.candidate_id)
            blockers.append(f"{signal.candidate_id} only maps to deferred batch work")
            continue
        if matched_batch_ids & material_blocked_batches:
            constrained_candidate_ids.append(signal.candidate_id)
            material_blocked_candidate_ids.append(signal.candidate_id)
            blockers.append(
                f"{signal.candidate_id} still carries material constraints on part of the requested follow-up work"
            )
        if matched_batch_ids & schedule_blocked_batches:
            constrained_candidate_ids.append(signal.candidate_id)
            blockers.append(
                f"{signal.candidate_id} still carries schedule pressure on part of the requested follow-up work"
            )
        practical_candidate_ids.append(signal.candidate_id)

    notes = list(capacity_advisory.notes)
    notes.extend(schedule_pressure_notes)
    if material_blocked_batches:
        notes.append("material feasibility further narrows which follow-up batches are responsible to schedule")
    if blockers:
        notes.append(
            "candidate practicality is constrained by both analytical skepticism and lab capacity"
        )

    return FollowUpPracticalityReport(
        program_id=plan.program_id,
        practical_candidate_ids=sorted(practical_candidate_ids),
        impractical_candidate_ids=sorted(impractical_candidate_ids),
        constrained_candidate_ids=sorted(set(constrained_candidate_ids)),
        material_blocked_candidate_ids=sorted(set(material_blocked_candidate_ids)),
        executable_batch_ids=capacity_advisory.feasible_batch_ids,
        blocked_batch_ids=capacity_advisory.deferred_batch_ids,
        estimated_total_cost=capacity_advisory.estimated_total_cost,
        practicality_score=capacity_advisory.practicality_score,
        blockers=sorted(set(blockers)),
        schedule_pressure_notes=schedule_pressure_notes,
        notes=notes,
    )

def score_assay_information_gain(
    *,
    assay_id: AssayId,
    blocking: bool,
    readiness_ready: bool,
    trust_score: float,
    contradiction_count: int,
    policy: PlanningPolicy | None = None,
) -> InformationGainBreakdown:
    """Score assay information gain using explicit scientific planning dimensions."""
    policy = policy or PlanningPolicy(policy_id="default-planning-policy")
    uncertainty_reduction = 0.7 if not readiness_ready else 0.4
    contradiction_resolution_value = min(1.0, contradiction_count * 0.25)
    falsification_value = 0.7 if blocking else 0.5
    decision_gate_impact = 0.9 if blocking else 0.4
    orthogonal_confirmation_value = 0.6 if trust_score < 0.7 else 0.3
    burden_penalty = (
        policy.blocking_burden_penalty
        if blocking
        else policy.non_blocking_burden_penalty
    )
    final_score = round(
        max(
            0.0,
            min(
                (
                    uncertainty_reduction * policy.uncertainty_weight
                    + contradiction_resolution_value * policy.contradiction_weight
                    + falsification_value * policy.falsification_weight
                    + decision_gate_impact * policy.gate_impact_weight
                    + orthogonal_confirmation_value * policy.orthogonal_weight
                    - burden_penalty
                ),
                1.0,
            ),
        ),
        4,
    )
    return InformationGainBreakdown(
        assay_id=assay_id,
        uncertainty_reduction=uncertainty_reduction,
        contradiction_resolution_value=contradiction_resolution_value,
        falsification_value=falsification_value,
        decision_gate_impact=decision_gate_impact,
        orthogonal_confirmation_value=orthogonal_confirmation_value,
        burden_penalty=burden_penalty,
        final_score=final_score,
    )

def score_assay_gate_impact(plan: ExperimentPlan) -> list[GateImpactScore]:
    """Score assay-level impact on decision gates using batch gate load and priority."""
    results: list[GateImpactScore] = []
    for batch in plan.batches:
        gate_count = len(batch.blocking_review_gates)
        base_impact = min(1.0, gate_count * 0.25)
        priority_bonus = max(0.0, 0.2 - ((batch.priority - 1) * 0.03))
        score = round(max(0.0, min(base_impact + priority_bonus, 1.0)), 4)
        for assay_id in batch.assay_ids:
            rationale: list[str] = []
            if gate_count > 0:
                rationale.append(f"batch blocks {gate_count} review gate(s)")
            if batch.priority <= 2:
                rationale.append(
                    "high-priority batch contributes to near-term decisioning"
                )
            if not rationale:
                rationale.append("limited direct gate pressure")
            results.append(
                GateImpactScore(
                    assay_id=assay_id,
                    batch_id=batch.batch_id,
                    blocking_gate_count=gate_count,
                    impact_score=score,
                    rationale=rationale,
                )
            )
    return sorted(results, key=lambda item: item.impact_score, reverse=True)

def estimate_assay_execution_burden(plan: ExperimentPlan) -> list[AssayExecutionBurden]:
    """Estimate execution burden for each assay from batch planning context."""
    burdens: list[AssayExecutionBurden] = []
    for batch in plan.batches:
        sample_pressure = min(0.4, len(set(batch.sample_requirements)) * 0.1)
        gate_pressure = min(0.3, len(batch.blocking_review_gates) * 0.1)
        priority_pressure = min(0.2, max(0, 3 - batch.priority) * 0.05)
        base_score = round(
            max(
                0.0, min(0.2 + sample_pressure + gate_pressure + priority_pressure, 1.0)
            ),
            4,
        )
        base_days = 2.0 + (sample_pressure * 6.0) + (gate_pressure * 4.0)
        for assay_id in batch.assay_ids:
            assay_kind = batch.assay_sample_kinds.get(assay_id, "other")
            kind_penalty = (
                0.15 if assay_kind in {"cellular", "developability"} else 0.05
            )
            burden_score = round(max(0.0, min(base_score + kind_penalty, 1.0)), 4)
            drivers = [f"sample kind={assay_kind}"]
            if batch.sample_requirements:
                drivers.append(
                    f"requires {len(batch.sample_requirements)} material type(s)"
                )
            if batch.blocking_review_gates:
                drivers.append(
                    f"coupled to {len(batch.blocking_review_gates)} review gate(s)"
                )
            burdens.append(
                AssayExecutionBurden(
                    assay_id=assay_id,
                    batch_id=batch.batch_id,
                    burden_score=burden_score,
                    estimated_days=round(base_days + (kind_penalty * 4.0), 2),
                    drivers=drivers,
                )
            )
    return sorted(burdens, key=lambda item: item.burden_score, reverse=True)

def build_lab_cycle_brief(
    program: ProgramSpec,
    plan: ExperimentPlan,
    bundle: EvidenceBundle,
    observations: list[AssayObservation],
) -> LabCycleBrief:
    """Build a cycle-level decision brief combining impact, burden, and priorities."""
    readiness = assess_decision_readiness(
        bundle, [need.value for need in program.evidence_needs]
    )
    gate_impacts = score_assay_gate_impact(plan)[:5]
    burdens = estimate_assay_execution_burden(plan)[:5]
    priorities = prioritize_next_assays(program, bundle, observations)[:5]
    notes: list[str] = []
    if gate_impacts and gate_impacts[0].impact_score >= 0.7:
        notes.append("high gate pressure detected in current assay backlog")
    if burdens and burdens[0].burden_score >= 0.7:
        notes.append("execution burden is concentrated in top-priority batches")
    if not readiness.ready:
        notes.append("decision readiness remains blocked by evidence gaps")
    if not notes:
        notes.append("cycle is balanced for execution and decision support")
    return LabCycleBrief(
        program_id=program.program_id,
        ready_for_progression=readiness.ready,
        top_gate_impacts=gate_impacts,
        highest_burden_assays=burdens,
        next_assay_priorities=priorities,
        notes=notes,
    )

def plan_material_reservations(
    plan: ExperimentPlan,
    requirements: list[MaterialRequirement],
    inventory: list[MaterialInventory],
) -> list[MaterialReservation]:
    """Plan per-batch material reservations from requirements and inventory."""
    requirement_map = {item.sample_kind: item for item in requirements}
    inventory_map = {item.material_id: item.available_units for item in inventory}
    reservations: list[MaterialReservation] = []
    for batch in plan.batches:
        for sample_kind in batch.sample_requirements:
            requirement = requirement_map.get(sample_kind)
            if requirement is None:
                continue
            available = inventory_map.get(requirement.material_id, 0.0)
            reserved_units = min(requirement.minimum_units, available)
            feasible = available >= requirement.minimum_units
            reservations.append(
                MaterialReservation(
                    batch_id=batch.batch_id,
                    material_id=requirement.material_id,
                    reserved_units=round(reserved_units, 4),
                    unit=requirement.unit,
                    feasible=feasible,
                )
            )
            inventory_map[requirement.material_id] = max(
                0.0, available - reserved_units
            )
    return reservations

def derive_lab_execution_directive(outcome: ExperimentOutcome) -> LabExecutionDirective:
    """Derive an operational directive from batch outcome and triage signals."""
    assessment = assess_batch_outcome(outcome)
    triage = triage_batch_failures(outcome)
    actions: list[str] = []
    if triage.escalation_assay_ids:
        actions.append(f"escalate assays: {', '.join(triage.escalation_assay_ids)}")
    if assessment.technical_or_repro_failures > 0:
        decision = ProgressDecision.HOLD
        actions.append(
            "resolve technical or reproducibility failures before progression"
        )
    elif any(
        assay.result_state is AssayResultState.FAILED_BIOLOGICAL
        for assay in outcome.assay_outcomes
    ):
        decision = ProgressDecision.REDESIGN
        actions.append("redesign biological hypothesis and assay sequence")
    else:
        decision = ProgressDecision.ADVANCE
        actions.append("promote ready outcomes and advance to next cycle")
    return LabExecutionDirective(
        batch_id=outcome.batch_id,
        decision=decision,
        escalation_assay_ids=triage.escalation_assay_ids,
        immediate_actions=actions,
    )

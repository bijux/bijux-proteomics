# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Capacity and schedule shaping for lab planning."""

from __future__ import annotations

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import BatchId, JsonModel, ProgramId
from bijux_proteomics_foundation.identity.identifiers import CycleId

from bijux_proteomics_lab.planning.assays import (
    AssayDependency,
    AssayFamily,
    ExperimentPlan,
    MaterialInventory,
    MaterialRequirement,
    assay_family,
    dependency_order,
)

class LabCapacity(JsonModel):
    """Available execution capacity for one planning cycle."""

    model_config = ConfigDict(extra="forbid")

    cycle_id: CycleId = Field(..., description="Stable cycle identifier.")
    max_batches: int = Field(..., ge=1, description="Maximum batch slots in the cycle.")
    max_assays_per_batch: int = Field(
        ...,
        ge=1,
        description="Maximum assays that fit in one batch slot.",
    )

class InstrumentAvailability(JsonModel):
    """Available time budget for one instrument or execution platform."""

    model_config = ConfigDict(extra="forbid")

    instrument_id: str = Field(..., min_length=1)
    available_days: float = Field(..., ge=0.0)
    supported_sample_kinds: list[str] = Field(default_factory=list)

class ExecutionCapacityAdvisory(JsonModel):
    """Combined advisory for budget, cycle capacity, and instrument availability."""

    model_config = ConfigDict(extra="forbid")

    program_id: ProgramId = Field(..., description="Program identifier.")
    feasible_batch_ids: list[BatchId] = Field(default_factory=list)
    deferred_batch_ids: list[BatchId] = Field(default_factory=list)
    deferred_reasons: dict[BatchId, str] = Field(default_factory=dict)
    estimated_total_cost: float = Field(default=0.0, ge=0.0)
    budget_remaining: float = Field(..., ge=0.0)
    practicality_score: float = Field(default=0.0, ge=0.0, le=1.0)
    notes: list[str] = Field(default_factory=list)

class FamilyCapacity(JsonModel):
    """Capacity limits for one assay family in a cycle."""

    model_config = ConfigDict(extra="forbid")

    family: AssayFamily = Field(..., description="Assay family.")
    max_assays: int = Field(..., ge=0, description="Maximum assays from this family.")

class ScheduledBatch(JsonModel):
    """Batch assigned to a concrete lab cycle."""

    model_config = ConfigDict(extra="forbid")

    batch_id: BatchId = Field(..., description="Stable batch identifier.")
    cycle_id: CycleId = Field(..., description="Assigned cycle identifier.")
    assay_ids: list[str] = Field(default_factory=list, description="Scheduled assays.")
    deferred_assay_ids: list[str] = Field(
        default_factory=list,
        description="Assays deferred because of capacity limits.",
    )

class ScheduledPlan(JsonModel):
    """Experiment plan after capacity-aware scheduling."""

    model_config = ConfigDict(extra="forbid")

    program_id: ProgramId = Field(..., description="Program identifier.")
    scheduled_batches: list[ScheduledBatch] = Field(
        default_factory=list,
        description="Capacity-aware scheduled batches.",
    )
    unscheduled_batches: list[str] = Field(
        default_factory=list,
        description="Batches deferred to a later cycle.",
    )

class ScheduleScenarioSummary(JsonModel):
    """Scenario summary for capacity scheduling sensitivity."""

    model_config = ConfigDict(extra="forbid")

    scenario_id: str = Field(..., min_length=1, description="Scenario identifier.")
    scheduled_batch_count: int = Field(
        ..., ge=0, description="Number of scheduled batches."
    )
    deferred_assay_count: int = Field(
        ..., ge=0, description="Number of deferred assays."
    )

class ScheduleScenarioComparison(JsonModel):
    """Comparison report across multiple scheduling scenarios."""

    model_config = ConfigDict(extra="forbid")

    program_id: ProgramId = Field(..., description="Program identifier.")
    scenarios: list[ScheduleScenarioSummary] = Field(
        default_factory=list, description="Scenario summaries."
    )
    recommended_scenario_id: str | None = Field(
        default=None, description="Scenario with lowest deferred assay load."
    )

class SchedulePressureReport(JsonModel):
    """Capacity pressure summary for a scheduled plan."""

    model_config = ConfigDict(extra="forbid")

    cycle_id: CycleId = Field(..., description="Cycle identifier.")
    scheduled_batch_count: int = Field(
        default=0, ge=0, description="Number of scheduled batches."
    )
    unscheduled_batch_count: int = Field(
        default=0, ge=0, description="Number of unscheduled batches."
    )
    assay_slot_utilization: float = Field(
        ..., ge=0.0, le=1.0, description="Used assay slots / total slots."
    )
    deferred_assay_count: int = Field(
        default=0, ge=0, description="Deferred assays due to capacity limits."
    )

class MaterialFeasibilityPriority(JsonModel):
    """Batch prioritization signal based on material feasibility."""

    model_config = ConfigDict(extra="forbid")

    batch_id: BatchId = Field(..., description="Batch identifier.")
    material_ready: bool = Field(
        ..., description="Whether required materials are available."
    )
    missing_material_ids: list[str] = Field(
        default_factory=list, description="Missing materials for this batch."
    )
    priority_score: float = Field(
        ..., ge=0.0, le=1.0, description="Material-feasibility priority score."
    )

def schedule_experiment_plan(
    plan: ExperimentPlan,
    capacity: LabCapacity,
    dependencies: list[AssayDependency] | None = None,
) -> ScheduledPlan:
    """Fit an experiment plan into available lab capacity."""
    dependencies = dependencies or []
    scheduled_batches: list[ScheduledBatch] = []
    for batch in plan.batches[: capacity.max_batches]:
        ordered_assays = dependency_order(batch.assay_ids, dependencies)
        scheduled_batches.append(
            ScheduledBatch(
                batch_id=batch.batch_id,
                cycle_id=capacity.cycle_id,
                assay_ids=ordered_assays[: capacity.max_assays_per_batch],
                deferred_assay_ids=ordered_assays[capacity.max_assays_per_batch :],
            )
        )
    unscheduled_batches = [
        batch.batch_id for batch in plan.batches[capacity.max_batches :]
    ]
    return ScheduledPlan(
        program_id=plan.program_id,
        scheduled_batches=scheduled_batches,
        unscheduled_batches=unscheduled_batches,
    )

def build_execution_capacity_advisory(
    plan: ExperimentPlan,
    capacity: LabCapacity,
    instrument_availability: list[InstrumentAvailability],
    *,
    budget_limit: float,
    estimated_batch_cost: float = 1.0,
) -> ExecutionCapacityAdvisory:
    """Assess which planned batches fit current budget and instrument capacity."""
    supported_sample_kinds = {
        sample_kind
        for item in instrument_availability
        for sample_kind in item.supported_sample_kinds
    }
    instrument_days = sum(item.available_days for item in instrument_availability)
    feasible_batch_ids: list[str] = []
    deferred_batch_ids: list[str] = []
    deferred_reasons: dict[str, str] = {}
    budget_remaining = budget_limit
    estimated_total_cost = 0.0
    notes: list[str] = []
    for batch in plan.batches:
        has_supported_sample_kind = any(
            sample_kind in supported_sample_kinds
            for sample_kind in batch.sample_requirements
        )
        batch_cost = estimated_batch_cost * (
            1.0
            + (max(len(set(batch.sample_requirements)) - 1, 0) * 0.25)
            + (0.15 if batch.priority == 1 else 0.0)
        )
        if (
            len(feasible_batch_ids) >= capacity.max_batches
            or instrument_days < 1.0
            or budget_remaining < batch_cost
            or (batch.sample_requirements and not has_supported_sample_kind)
        ):
            deferred_batch_ids.append(batch.batch_id)
            if len(feasible_batch_ids) >= capacity.max_batches:
                deferred_reasons[batch.batch_id] = "cycle batch capacity exhausted"
            elif instrument_days < 1.0:
                deferred_reasons[batch.batch_id] = "instrument time is exhausted"
            elif budget_remaining < batch_cost:
                deferred_reasons[batch.batch_id] = "budget cannot absorb the batch cost"
            else:
                deferred_reasons[batch.batch_id] = (
                    "instrument support does not cover the batch sample requirements"
                )
            continue
        feasible_batch_ids.append(batch.batch_id)
        budget_remaining = max(0.0, budget_remaining - batch_cost)
        estimated_total_cost += batch_cost
        instrument_days = max(0.0, instrument_days - 1.0)
    if deferred_batch_ids:
        notes.append(
            "some batches were deferred by budget, cycle capacity, or instrument support"
        )
    if not feasible_batch_ids:
        notes.append("no planned batches fit current execution constraints")
    practicality_score = (
        round(
            max(
                0.0,
                min(
                    (
                        (len(feasible_batch_ids) / max(len(plan.batches), 1)) * 0.7
                        + (budget_remaining / max(budget_limit, 1.0)) * 0.3
                    ),
                    1.0,
                ),
            ),
            4,
        )
        if plan.batches
        else 1.0
    )
    return ExecutionCapacityAdvisory(
        program_id=plan.program_id,
        feasible_batch_ids=feasible_batch_ids,
        deferred_batch_ids=deferred_batch_ids,
        deferred_reasons=deferred_reasons,
        estimated_total_cost=round(estimated_total_cost, 4),
        budget_remaining=round(budget_remaining, 4),
        practicality_score=practicality_score,
        notes=notes,
    )

def schedule_with_family_capacity(
    plan: ExperimentPlan,
    capacity: LabCapacity,
    family_capacities: list[FamilyCapacity],
) -> ScheduledPlan:
    """Schedule while enforcing per-family assay limits."""
    family_budget = {item.family: item.max_assays for item in family_capacities}
    scheduled_batches: list[ScheduledBatch] = []

    for batch in plan.batches[: capacity.max_batches]:
        selected: list[str] = []
        deferred: list[str] = []
        for assay_id in batch.assay_ids:
            sample_kind = batch.assay_sample_kinds.get(assay_id, "other")
            family = assay_family(sample_kind)
            if family_budget.get(family, 0) <= 0:
                deferred.append(assay_id)
                continue
            family_budget[family] -= 1
            selected.append(assay_id)
        scheduled_batches.append(
            ScheduledBatch(
                batch_id=batch.batch_id,
                cycle_id=capacity.cycle_id,
                assay_ids=selected[: capacity.max_assays_per_batch],
                deferred_assay_ids=deferred + selected[capacity.max_assays_per_batch :],
            )
        )
    unscheduled_batches = [
        batch.batch_id for batch in plan.batches[capacity.max_batches :]
    ]
    return ScheduledPlan(
        program_id=plan.program_id,
        scheduled_batches=scheduled_batches,
        unscheduled_batches=unscheduled_batches,
    )

def compare_schedule_scenarios(
    plan: ExperimentPlan,
    scenarios: list[LabCapacity],
) -> ScheduleScenarioComparison:
    """Compare scheduling outcomes across capacity scenarios."""
    summaries: list[ScheduleScenarioSummary] = []
    for capacity in scenarios:
        scheduled = schedule_experiment_plan(plan, capacity)
        deferred = sum(
            len(batch.deferred_assay_ids) for batch in scheduled.scheduled_batches
        )
        summaries.append(
            ScheduleScenarioSummary(
                scenario_id=capacity.cycle_id,
                scheduled_batch_count=len(scheduled.scheduled_batches),
                deferred_assay_count=deferred,
            )
        )
    recommended = (
        min(summaries, key=lambda item: item.deferred_assay_count).scenario_id
        if summaries
        else None
    )
    return ScheduleScenarioComparison(
        program_id=plan.program_id,
        scenarios=summaries,
        recommended_scenario_id=recommended,
    )

def summarize_schedule_pressure(
    scheduled: ScheduledPlan,
    capacity: LabCapacity,
) -> SchedulePressureReport:
    """Summarize scheduling pressure against available cycle capacity."""
    total_slots = capacity.max_batches * capacity.max_assays_per_batch
    used_slots = sum(len(batch.assay_ids) for batch in scheduled.scheduled_batches)
    deferred = sum(
        len(batch.deferred_assay_ids) for batch in scheduled.scheduled_batches
    )
    utilization = round((used_slots / total_slots), 4) if total_slots else 0.0
    return SchedulePressureReport(
        cycle_id=capacity.cycle_id,
        scheduled_batch_count=len(scheduled.scheduled_batches),
        unscheduled_batch_count=len(scheduled.unscheduled_batches),
        assay_slot_utilization=max(0.0, min(utilization, 1.0)),
        deferred_assay_count=deferred,
    )

def prioritize_batches_by_material_feasibility(
    plan: ExperimentPlan,
    requirements: list[MaterialRequirement],
    inventory: list[MaterialInventory],
) -> list[MaterialFeasibilityPriority]:
    """Rank batches by material feasibility so executable work is scheduled first."""
    requirement_map = {item.sample_kind: item for item in requirements}
    inventory_map = {item.material_id: item.available_units for item in inventory}
    ranked: list[MaterialFeasibilityPriority] = []
    for batch in plan.batches:
        missing: list[str] = []
        for sample_kind in batch.sample_requirements:
            requirement = requirement_map.get(sample_kind)
            if requirement is None:
                continue
            available = inventory_map.get(requirement.material_id, 0.0)
            if available < requirement.minimum_units:
                missing.append(requirement.material_id)
        material_ready = not missing
        base = 1.0 if material_ready else 0.4
        priority_score = round(
            max(0.0, min(base - ((batch.priority - 1) * 0.05), 1.0)), 4
        )
        ranked.append(
            MaterialFeasibilityPriority(
                batch_id=batch.batch_id,
                material_ready=material_ready,
                missing_material_ids=sorted(missing),
                priority_score=priority_score,
            )
        )
    return sorted(
        ranked,
        key=lambda item: (not item.material_ready, -item.priority_score, item.batch_id),
    )

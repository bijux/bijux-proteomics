# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Operational readiness metadata for executable lab work."""

from __future__ import annotations

from pydantic import ConfigDict, Field

from bijux_proteomics_foundation import JsonModel, ProgramId
from bijux_proteomics_lab.planning import (
    ExperimentPlan,
    InstrumentAvailability,
    LabCapacity,
    MaterialInventory,
    MaterialRequirement,
    assess_material_constraints,
    build_execution_capacity_advisory,
)


class StaffingAvailability(JsonModel):
    """Available staffing for one role in the current planning cycle."""

    model_config = ConfigDict(extra="forbid")

    role_name: str = Field(..., min_length=1)
    available_operators: int = Field(..., ge=0)
    required_operators: int = Field(..., ge=0)
    available_operator_days: float = Field(..., ge=0.0)


class ReviewBacklogSnapshot(JsonModel):
    """Current review and execution backlog relevant to a planning cycle."""

    model_config = ConfigDict(extra="forbid")

    queued_review_entries: int = Field(..., ge=0)
    blocking_gate_ids: tuple[str, ...] = Field(default_factory=tuple)
    deferred_batch_ids: tuple[str, ...] = Field(default_factory=tuple)
    oldest_entry_days: float = Field(..., ge=0.0)


class ReagentAvailability(JsonModel):
    """Available reagent or sample stock with lead-time visibility."""

    model_config = ConfigDict(extra="forbid")

    material_id: str = Field(..., min_length=1)
    available_units: float = Field(..., ge=0.0)
    minimum_units: float = Field(..., gt=0.0)
    unit: str = Field(..., min_length=1)
    lead_time_days: float = Field(..., ge=0.0)


class OperationalReadinessReport(JsonModel):
    """Operational readiness decision across cost, capacity, backlog, and risk."""

    model_config = ConfigDict(extra="forbid")

    program_id: ProgramId = Field(..., description="Program identifier.")
    ready_for_execution: bool = Field(
        ..., description="Whether the current plan is operationally ready."
    )
    estimated_total_batch_cost: float = Field(..., ge=0.0)
    budget_limit: float = Field(..., ge=0.0)
    budget_remaining: float = Field(..., ge=0.0)
    deferred_batch_ids: list[str] = Field(default_factory=list)
    blocking_material_ids: list[str] = Field(default_factory=list)
    understaffed_roles: list[str] = Field(default_factory=list)
    long_lead_material_ids: list[str] = Field(default_factory=list)
    backlog_pressure_score: float = Field(..., ge=0.0, le=1.0)
    risk_notes: list[str] = Field(default_factory=list)


def _build_material_inventory(
    reagent_inventory: list[ReagentAvailability],
) -> list[MaterialInventory]:
    return [
        MaterialInventory(
            material_id=item.material_id,
            available_units=item.available_units,
        )
        for item in reagent_inventory
    ]


def _build_material_requirements(
    reagent_inventory: list[ReagentAvailability],
) -> list[MaterialRequirement]:
    return [
        MaterialRequirement(
            material_id=item.material_id,
            sample_kind=item.material_id,
            minimum_units=item.minimum_units,
            unit=item.unit,
        )
        for item in reagent_inventory
    ]


def _backlog_pressure_score(
    backlog: ReviewBacklogSnapshot,
    capacity: LabCapacity,
) -> float:
    queue_pressure = min(
        1.0,
        backlog.queued_review_entries / max(capacity.max_batches * 2, 1),
    )
    age_pressure = min(1.0, backlog.oldest_entry_days / 14.0)
    blocked_gate_pressure = min(1.0, len(backlog.blocking_gate_ids) / 3.0)
    return round((queue_pressure + age_pressure + blocked_gate_pressure) / 3.0, 4)


def build_operational_readiness_report(
    plan: ExperimentPlan,
    *,
    capacity: LabCapacity,
    instrument_availability: list[InstrumentAvailability],
    reagent_inventory: list[ReagentAvailability],
    staffing: list[StaffingAvailability],
    backlog: ReviewBacklogSnapshot,
    budget_limit: float,
    estimated_batch_cost: float = 1.0,
) -> OperationalReadinessReport:
    """Summarize whether a plan is executable under live lab constraints."""
    capacity_advisory = build_execution_capacity_advisory(
        plan,
        capacity,
        instrument_availability,
        budget_limit=budget_limit,
        estimated_batch_cost=estimated_batch_cost,
    )
    material_report = assess_material_constraints(
        plan,
        _build_material_requirements(reagent_inventory),
        _build_material_inventory(reagent_inventory),
    )
    understaffed_roles = sorted(
        item.role_name
        for item in staffing
        if item.available_operators < item.required_operators
        or item.available_operator_days < float(item.required_operators)
    )
    long_lead_material_ids = sorted(
        item.material_id
        for item in reagent_inventory
        if item.available_units < item.minimum_units or item.lead_time_days > 7.0
    )
    backlog_pressure_score = _backlog_pressure_score(backlog, capacity)
    estimated_total_batch_cost = round(len(plan.batches) * estimated_batch_cost, 4)

    risk_notes = list(capacity_advisory.notes)
    risk_notes.extend(material_report.notes)
    if understaffed_roles:
        risk_notes.append(
            "understaffed roles block execution: " + ", ".join(understaffed_roles)
        )
    if backlog.blocking_gate_ids:
        risk_notes.append(
            "blocking review gates remain queued: "
            + ", ".join(sorted(backlog.blocking_gate_ids))
        )
    if long_lead_material_ids:
        risk_notes.append(
            "long-lead materials need replenishment: "
            + ", ".join(long_lead_material_ids)
        )
    if backlog_pressure_score >= 0.6:
        risk_notes.append("review backlog pressure is elevated for this cycle")

    ready_for_execution = not (
        capacity_advisory.deferred_batch_ids
        or material_report.blocking_material_ids
        or understaffed_roles
        or backlog.blocking_gate_ids
        or backlog_pressure_score >= 0.8
        or long_lead_material_ids
    )
    return OperationalReadinessReport(
        program_id=plan.program_id,
        ready_for_execution=ready_for_execution,
        estimated_total_batch_cost=estimated_total_batch_cost,
        budget_limit=budget_limit,
        budget_remaining=capacity_advisory.budget_remaining,
        deferred_batch_ids=[
            *capacity_advisory.deferred_batch_ids,
            *backlog.deferred_batch_ids,
        ],
        blocking_material_ids=material_report.blocking_material_ids,
        understaffed_roles=understaffed_roles,
        long_lead_material_ids=long_lead_material_ids,
        backlog_pressure_score=backlog_pressure_score,
        risk_notes=risk_notes,
    )


__all__ = [
    "OperationalReadinessReport",
    "ReagentAvailability",
    "ReviewBacklogSnapshot",
    "StaffingAvailability",
    "build_operational_readiness_report",
]

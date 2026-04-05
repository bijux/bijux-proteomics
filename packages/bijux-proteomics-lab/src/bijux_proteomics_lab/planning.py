# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Experiment planning helpers."""

from __future__ import annotations

from enum import StrEnum

from pydantic import ConfigDict, Field

from bijux_proteomics.programs import ProgramSpec
from bijux_proteomics_knowledge import (
    EvidenceBundle,
    assess_decision_readiness,
    evidence_gaps,
)
from bijux_proteomics_lab.schema import SchemaMetadata
from bijux_proteomics_lab.serialization import JsonModel


class AssayObservation(JsonModel):
    """Observed assay result."""

    model_config = ConfigDict(extra="forbid")

    assay_id: str = Field(..., min_length=1, description="Assay identifier.")
    metric: str = Field(..., min_length=1, description="Observed metric.")
    value: float = Field(..., description="Observed value.")
    unit: str | None = Field(default=None, description="Measurement unit.")
    passed: bool = Field(..., description="Whether the observation met expectations.")


class ExperimentBatch(JsonModel):
    """Batch of experiments with a shared purpose."""

    model_config = ConfigDict(extra="forbid")

    batch_id: str = Field(..., min_length=1, description="Stable batch identifier.")
    objective: str = Field(..., min_length=1, description="Batch objective.")
    assay_ids: list[str] = Field(
        default_factory=list,
        description="Assays in the batch.",
    )
    blocking_review_gates: list[str] = Field(
        default_factory=list,
        description="Review gates that must clear this batch.",
    )
    priority: int = Field(..., ge=1, description="Execution priority.")


class ExperimentPlan(JsonModel):
    """Experiment plan derived from a program definition."""

    model_config = ConfigDict(extra="forbid")

    program_id: str = Field(..., min_length=1, description="Program identifier.")
    document_schema: SchemaMetadata = Field(
        default_factory=SchemaMetadata,
        description="Schema and provenance metadata.",
    )
    evidence_gaps: list[str] = Field(
        default_factory=list,
        description="Evidence gaps that remain open.",
    )
    review_queue: list[str] = Field(
        default_factory=list,
        description="Review gates that block execution.",
    )
    batches: list[ExperimentBatch] = Field(
        default_factory=list,
        description="Ordered experiment batches.",
    )


class ProgressDecision(StrEnum):
    """Next-step decision after reviewing evidence and assay data."""

    ADVANCE = "advance"
    HOLD = "hold"
    REDESIGN = "redesign"


class ReviewPacket(JsonModel):
    """Review-ready summary for human decision makers."""

    model_config = ConfigDict(extra="forbid")

    program_id: str = Field(..., min_length=1, description="Program identifier.")
    ready_for_synthesis: bool = Field(
        ...,
        description="Whether the current state is ready for synthesis or next spend.",
    )
    blocking_findings: list[str] = Field(
        default_factory=list,
        description="Issues that stop progression.",
    )
    recommended_actions: list[str] = Field(
        default_factory=list,
        description="Actions that should happen before the next decision.",
    )


class ClosedLoopPlan(JsonModel):
    """Recommended next cycle based on evidence and assay outcomes."""

    model_config = ConfigDict(extra="forbid")

    program_id: str = Field(..., min_length=1, description="Program identifier.")
    document_schema: SchemaMetadata = Field(
        default_factory=SchemaMetadata,
        description="Schema and provenance metadata.",
    )
    decision: ProgressDecision = Field(..., description="Recommended next decision.")
    evidence_backlog: list[str] = Field(
        default_factory=list,
        description="Evidence work that should happen next.",
    )
    assay_backlog: list[str] = Field(
        default_factory=list,
        description="Assays that should run next.",
    )
    notes: list[str] = Field(
        default_factory=list,
        description="Short reasoning notes for the recommendation.",
    )


class LabCapacity(JsonModel):
    """Available execution capacity for one planning cycle."""

    model_config = ConfigDict(extra="forbid")

    cycle_id: str = Field(..., min_length=1, description="Stable cycle identifier.")
    max_batches: int = Field(..., ge=1, description="Maximum batch slots in the cycle.")
    max_assays_per_batch: int = Field(
        ...,
        ge=1,
        description="Maximum assays that fit in one batch slot.",
    )


class ScheduledBatch(JsonModel):
    """Batch assigned to a concrete lab cycle."""

    model_config = ConfigDict(extra="forbid")

    batch_id: str = Field(..., min_length=1, description="Stable batch identifier.")
    cycle_id: str = Field(..., min_length=1, description="Assigned cycle identifier.")
    assay_ids: list[str] = Field(default_factory=list, description="Scheduled assays.")
    deferred_assay_ids: list[str] = Field(
        default_factory=list,
        description="Assays deferred because of capacity limits.",
    )


class ScheduledPlan(JsonModel):
    """Experiment plan after capacity-aware scheduling."""

    model_config = ConfigDict(extra="forbid")

    program_id: str = Field(..., min_length=1, description="Program identifier.")
    scheduled_batches: list[ScheduledBatch] = Field(
        default_factory=list,
        description="Capacity-aware scheduled batches.",
    )
    unscheduled_batches: list[str] = Field(
        default_factory=list,
        description="Batches deferred to a later cycle.",
    )


def plan_experiment_batches(
    program: ProgramSpec,
    bundle: EvidenceBundle | None = None,
) -> ExperimentPlan:
    """Build a two-lane plan with blocking work first."""
    blocking_assays = [
        assay.assay_id for assay in program.assay_panel if assay.blocking
    ]
    supporting_assays = [
        assay.assay_id for assay in program.assay_panel if not assay.blocking
    ]
    batches: list[ExperimentBatch] = []
    if blocking_assays:
        batches.append(
            ExperimentBatch(
                batch_id=f"{program.program_id}-gate-batch",
                objective="De-risk the program before expensive work starts.",
                assay_ids=blocking_assays,
                blocking_review_gates=[
                    gate.gate_id for gate in program.review_gates if gate.blocking
                ],
                priority=1,
            )
        )
    if supporting_assays:
        batches.append(
            ExperimentBatch(
                batch_id=f"{program.program_id}-optimization-batch",
                objective="Expand confidence and rank promising candidates.",
                assay_ids=supporting_assays,
                blocking_review_gates=[],
                priority=2 if batches else 1,
            )
        )
    required_kinds = [need.value for need in program.evidence_needs]
    gaps = evidence_gaps(bundle, required_kinds) if bundle else required_kinds
    return ExperimentPlan(
        program_id=program.program_id,
        evidence_gaps=gaps,
        review_queue=[gate.gate_id for gate in program.review_gates if gate.blocking],
        batches=batches,
    )


def build_review_packet(
    program: ProgramSpec,
    bundle: EvidenceBundle,
    observations: list[AssayObservation],
) -> ReviewPacket:
    """Build a human review summary from evidence and assay outcomes."""
    required_kinds = [need.value for need in program.evidence_needs]
    readiness = assess_decision_readiness(bundle, required_kinds)
    failed_assays = [
        observation.assay_id for observation in observations if not observation.passed
    ]
    blockers = list(readiness.blockers)
    if failed_assays:
        blockers.append("failed assays: " + ", ".join(failed_assays))

    recommendations = list(readiness.recommendations)
    if failed_assays:
        recommendations.append(
            "repeat or redesign around assays: " + ", ".join(failed_assays)
        )

    return ReviewPacket(
        program_id=program.program_id,
        ready_for_synthesis=not blockers,
        blocking_findings=blockers,
        recommended_actions=recommendations,
    )


def recommend_next_cycle(
    program: ProgramSpec,
    bundle: EvidenceBundle,
    observations: list[AssayObservation],
) -> ClosedLoopPlan:
    """Recommend the next closed-loop action for the program."""
    review_packet = build_review_packet(program, bundle, observations)
    failed_assays = [
        observation.assay_id for observation in observations if not observation.passed
    ]
    pending_assays = [
        assay.assay_id
        for assay in program.assay_panel
        if assay.assay_id not in {observation.assay_id for observation in observations}
    ]

    if review_packet.ready_for_synthesis and not pending_assays:
        return ClosedLoopPlan(
            program_id=program.program_id,
            decision=ProgressDecision.ADVANCE,
            evidence_backlog=[],
            assay_backlog=[],
            notes=["evidence and assays support progression to the next spend"],
        )
    if failed_assays:
        return ClosedLoopPlan(
            program_id=program.program_id,
            decision=ProgressDecision.REDESIGN,
            evidence_backlog=evidence_gaps(
                bundle,
                [need.value for need in program.evidence_needs],
            ),
            assay_backlog=failed_assays,
            notes=["failed assays indicate the design loop should change before progression"],
        )
    return ClosedLoopPlan(
        program_id=program.program_id,
        decision=ProgressDecision.HOLD,
        evidence_backlog=evidence_gaps(
            bundle,
            [need.value for need in program.evidence_needs],
        ),
        assay_backlog=pending_assays,
        notes=["complete missing evidence and assay work before progression"],
    )


def schedule_experiment_plan(
    plan: ExperimentPlan,
    capacity: LabCapacity,
) -> ScheduledPlan:
    """Fit an experiment plan into available lab capacity."""
    scheduled_batches: list[ScheduledBatch] = []
    unscheduled_batches: list[str] = []
    for batch in plan.batches[: capacity.max_batches]:
        scheduled_batches.append(
            ScheduledBatch(
                batch_id=batch.batch_id,
                cycle_id=capacity.cycle_id,
                assay_ids=batch.assay_ids[: capacity.max_assays_per_batch],
                deferred_assay_ids=batch.assay_ids[capacity.max_assays_per_batch :],
            )
        )
    for batch in plan.batches[capacity.max_batches :]:
        unscheduled_batches.append(batch.batch_id)
    return ScheduledPlan(
        program_id=plan.program_id,
        scheduled_batches=scheduled_batches,
        unscheduled_batches=unscheduled_batches,
    )

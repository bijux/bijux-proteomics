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
    compute_bundle_trust,
    evidence_gaps,
    triangulate_evidence,
)
from bijux_proteomics_foundation import (
    AssayId,
    BatchId,
    CycleId,
    DocumentSchema,
    JsonModel,
    ProgramId,
)


class AssayObservation(JsonModel):
    """Observed assay result."""

    model_config = ConfigDict(extra="forbid")

    assay_id: AssayId = Field(..., description="Assay identifier.")
    metric: str = Field(..., min_length=1, description="Observed metric.")
    value: float = Field(..., description="Observed value.")
    unit: str | None = Field(default=None, description="Measurement unit.")
    passed: bool = Field(..., description="Whether the observation met expectations.")


class ExperimentBatch(JsonModel):
    """Batch of experiments with a shared purpose."""

    model_config = ConfigDict(extra="forbid")

    batch_id: BatchId = Field(..., description="Stable batch identifier.")
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
    sample_requirements: list[str] = Field(
        default_factory=list,
        description="Material requirements that must be available for the batch.",
    )
    assay_sample_kinds: dict[str, str] = Field(
        default_factory=dict,
        description="Per-assay sample kind mapping used for capacity scheduling.",
    )


class AssayDependency(JsonModel):
    """Dependency edge between assays."""

    model_config = ConfigDict(extra="forbid")

    assay_id: AssayId = Field(..., description="Dependent assay identifier.")
    requires_assay_id: AssayId = Field(..., description="Prerequisite assay identifier.")


class AssayIntent(JsonModel):
    """Intent and prerequisites for an assay in the planning layer."""

    model_config = ConfigDict(extra="forbid")

    assay_id: AssayId = Field(..., description="Assay identifier.")
    objective: str = Field(..., min_length=1, description="Why the assay is planned.")
    prerequisite_assay_ids: list[AssayId] = Field(
        default_factory=list,
        description="Assays that must complete first.",
    )


class AssayFamily(StrEnum):
    """Coarse assay families used for planning batches."""

    BIOPHYSICAL = "biophysical"
    EXPRESSION = "expression"
    CELLULAR = "cellular"
    DEVELOPABILITY = "developability"
    OTHER = "other"


class ExperimentPlan(JsonModel):
    """Experiment plan derived from a program definition."""

    model_config = ConfigDict(extra="forbid")

    program_id: ProgramId = Field(..., description="Program identifier.")
    document_schema: DocumentSchema = Field(
        default_factory=lambda: DocumentSchema(created_by="bijux-proteomics-lab"),
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


class MaterialRequirement(JsonModel):
    """Material needed to execute planned work."""

    model_config = ConfigDict(extra="forbid")

    material_id: str = Field(..., min_length=1, description="Stable material identifier.")
    sample_kind: str = Field(..., min_length=1, description="Type of sample or reagent.")
    minimum_units: float = Field(
        ...,
        gt=0.0,
        description="Minimum quantity required for execution.",
    )
    unit: str = Field(..., min_length=1, description="Unit of measure.")


class MaterialInventory(JsonModel):
    """Available material inventory for a planning cycle."""

    model_config = ConfigDict(extra="forbid")

    material_id: str = Field(..., min_length=1, description="Stable material identifier.")
    available_units: float = Field(
        ...,
        ge=0.0,
        description="Available quantity for the planning cycle.",
    )


class MaterialConstraintReport(JsonModel):
    """Material feasibility assessment for an experiment plan."""

    model_config = ConfigDict(extra="forbid")

    program_id: ProgramId = Field(..., description="Program identifier.")
    blocking_material_ids: list[str] = Field(
        default_factory=list,
        description="Materials that are insufficient for planned work.",
    )
    notes: list[str] = Field(
        default_factory=list,
        description="Human-readable explanation of the material constraints.",
    )


class ProgressDecision(StrEnum):
    """Next-step decision after reviewing evidence and assay data."""

    ADVANCE = "advance"
    HOLD = "hold"
    REDESIGN = "redesign"


class ReviewPacket(JsonModel):
    """Review-ready summary for human decision makers."""

    model_config = ConfigDict(extra="forbid")

    program_id: ProgramId = Field(..., description="Program identifier.")
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

    program_id: ProgramId = Field(..., description="Program identifier.")
    document_schema: DocumentSchema = Field(
        default_factory=lambda: DocumentSchema(created_by="bijux-proteomics-lab"),
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
    evidence_trust_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Trust score used to weight the recommendation.",
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


class NextAssayPriority(JsonModel):
    """Priority score for selecting the next assay based on information gain."""

    model_config = ConfigDict(extra="forbid")

    assay_id: AssayId = Field(..., description="Assay identifier.")
    score: float = Field(..., description="Priority score.")
    reasons: list[str] = Field(default_factory=list, description="Short rationale points.")


class OrthogonalConfirmationPlan(JsonModel):
    """Recommendation for orthogonal confirmation assays."""

    model_config = ConfigDict(extra="forbid")

    decision_tag: str = Field(..., min_length=1, description="Decision context evaluated.")
    required: bool = Field(..., description="Whether orthogonal confirmation is required.")
    suggested_assay_ids: list[str] = Field(
        default_factory=list,
        description="Assays suggested for orthogonal confirmation.",
    )


def dependency_order(
    assay_ids: list[AssayId],
    dependencies: list[AssayDependency],
) -> list[AssayId]:
    """Return assay ids with prerequisites placed earlier when possible."""
    ordered: list[AssayId] = []
    remaining = list(assay_ids)
    while remaining:
        progressed = False
        for assay_id in list(remaining):
            prerequisites = [
                dependency.requires_assay_id
                for dependency in dependencies
                if dependency.assay_id == assay_id
            ]
            if all(prerequisite in ordered or prerequisite not in assay_ids for prerequisite in prerequisites):
                ordered.append(assay_id)
                remaining.remove(assay_id)
                progressed = True
        if not progressed:
            ordered.extend(remaining)
            break
    return ordered


def assay_family(sample_kind: str) -> AssayFamily:
    """Infer a planning family from the assay sample kind."""
    lowered = sample_kind.lower()
    if "biophys" in lowered or "protein" in lowered:
        return AssayFamily.BIOPHYSICAL
    if "express" in lowered:
        return AssayFamily.EXPRESSION
    if "cell" in lowered:
        return AssayFamily.CELLULAR
    if "develop" in lowered or "aggregation" in lowered or "stability" in lowered:
        return AssayFamily.DEVELOPABILITY
    return AssayFamily.OTHER


def assay_family_priority(family: AssayFamily) -> int:
    """Return scientific execution priority for assay families."""
    order = {
        AssayFamily.BIOPHYSICAL: 1,
        AssayFamily.EXPRESSION: 2,
        AssayFamily.CELLULAR: 3,
        AssayFamily.DEVELOPABILITY: 4,
        AssayFamily.OTHER: 5,
    }
    return order[family]


def plan_experiment_batches(
    program: ProgramSpec,
    bundle: EvidenceBundle | None = None,
    dependencies: list[AssayDependency] | None = None,
) -> ExperimentPlan:
    """Build dependency-aware batches grouped by blocking status and assay family."""
    dependencies = dependencies or []
    batches: list[ExperimentBatch] = []
    grouped: dict[tuple[bool, AssayFamily], list[object]] = {}
    for assay in program.assay_panel:
        grouped.setdefault((assay.blocking, assay_family(assay.sample_kind)), []).append(assay)
    priority = 1
    for (blocking, family), assays in sorted(
        grouped.items(),
        key=lambda item: (not item[0][0], assay_family_priority(item[0][1])),
    ):
        ordered_assays = dependency_order([assay.assay_id for assay in assays], dependencies)
        batches.append(
            ExperimentBatch(
                batch_id=f"{program.program_id}-{family.value}-{'gate' if blocking else 'support'}",
                objective=(
                    "De-risk the program before expensive work starts."
                    if blocking
                    else "Expand confidence and rank promising candidates."
                ),
                assay_ids=ordered_assays,
                blocking_review_gates=[
                    gate.gate_id for gate in program.review_gates if gate.blocking
                ]
                if blocking
                else [],
                priority=priority,
                sample_requirements=sorted({assay.sample_kind for assay in assays}),
                assay_sample_kinds={assay.assay_id: assay.sample_kind for assay in assays},
            )
        )
        priority += 1
    required_kinds = [need.value for need in program.evidence_needs]
    gaps = evidence_gaps(bundle, required_kinds) if bundle else required_kinds
    return ExperimentPlan(
        program_id=program.program_id,
        evidence_gaps=gaps,
        review_queue=[gate.gate_id for gate in program.review_gates if gate.blocking],
        batches=batches,
    )


def assess_material_constraints(
    plan: ExperimentPlan,
    requirements: list[MaterialRequirement],
    inventory: list[MaterialInventory],
) -> MaterialConstraintReport:
    """Check whether the planned work is supported by available material."""
    inventory_map = {item.material_id: item.available_units for item in inventory}
    blocking_material_ids: list[str] = []
    notes: list[str] = []

    for requirement in requirements:
        available = inventory_map.get(requirement.material_id, 0.0)
        if available < requirement.minimum_units:
            blocking_material_ids.append(requirement.material_id)
            notes.append(
                f"{requirement.material_id} only has {available:g} {requirement.unit} available "
                f"but needs {requirement.minimum_units:g} {requirement.unit}"
            )
    if not blocking_material_ids:
        notes.append("available materials support the current experiment batches")
    return MaterialConstraintReport(
        program_id=plan.program_id,
        blocking_material_ids=blocking_material_ids,
        notes=notes,
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
    trust = compute_bundle_trust(bundle)
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
            evidence_trust_score=trust.trust_score,
        )
    if failed_assays or trust.trust_score < 0.5:
        return ClosedLoopPlan(
            program_id=program.program_id,
            decision=ProgressDecision.REDESIGN,
            evidence_backlog=evidence_gaps(
                bundle,
                [need.value for need in program.evidence_needs],
            ),
            assay_backlog=failed_assays,
            notes=[
                "failed assays indicate the design loop should change before progression"
                if failed_assays
                else "low evidence trust indicates the program should be reworked before progression"
            ],
            evidence_trust_score=trust.trust_score,
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
        evidence_trust_score=trust.trust_score,
    )


def schedule_experiment_plan(
    plan: ExperimentPlan,
    capacity: LabCapacity,
    dependencies: list[AssayDependency] | None = None,
) -> ScheduledPlan:
    """Fit an experiment plan into available lab capacity."""
    dependencies = dependencies or []
    scheduled_batches: list[ScheduledBatch] = []
    unscheduled_batches: list[str] = []
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
    for batch in plan.batches[capacity.max_batches :]:
        unscheduled_batches.append(batch.batch_id)
    return ScheduledPlan(
        program_id=plan.program_id,
        scheduled_batches=scheduled_batches,
        unscheduled_batches=unscheduled_batches,
    )


def schedule_with_family_capacity(
    plan: ExperimentPlan,
    capacity: LabCapacity,
    family_capacities: list[FamilyCapacity],
) -> ScheduledPlan:
    """Schedule while enforcing per-family assay limits."""
    family_budget = {item.family: item.max_assays for item in family_capacities}
    scheduled_batches: list[ScheduledBatch] = []
    unscheduled_batches: list[str] = []

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
    for batch in plan.batches[capacity.max_batches :]:
        unscheduled_batches.append(batch.batch_id)
    return ScheduledPlan(
        program_id=plan.program_id,
        scheduled_batches=scheduled_batches,
        unscheduled_batches=unscheduled_batches,
    )


def prioritize_next_assays(
    program: ProgramSpec,
    bundle: EvidenceBundle,
    observations: list[AssayObservation],
) -> list[NextAssayPriority]:
    """Rank pending assays by expected information gain and decision impact."""
    observed_ids = {observation.assay_id for observation in observations}
    trust = compute_bundle_trust(bundle)
    readiness = assess_decision_readiness(bundle, [need.value for need in program.evidence_needs])
    ranked: list[NextAssayPriority] = []
    for assay in program.assay_panel:
        if assay.assay_id in observed_ids:
            continue
        score = 0.5
        reasons: list[str] = []
        if assay.blocking:
            score += 0.3
            reasons.append("blocking assay with direct gate impact")
        if not readiness.ready:
            score += 0.1
            reasons.append("program is not decision-ready")
        if trust.trust_score < 0.7:
            score += 0.1
            reasons.append("evidence trust is below target")
        ranked.append(
            NextAssayPriority(
                assay_id=assay.assay_id,
                score=round(min(score, 1.0), 4),
                reasons=reasons or ["assay reduces residual uncertainty"],
            )
        )
    return sorted(ranked, key=lambda item: item.score, reverse=True)


def recommend_orthogonal_confirmation(
    program: ProgramSpec,
    bundle: EvidenceBundle,
    *,
    decision_tag: str = "progression",
    minimum_convergence_score: float = 0.5,
) -> OrthogonalConfirmationPlan:
    """Recommend orthogonal assays when modality convergence is weak."""
    triangulation = triangulate_evidence(bundle, decision_tag=decision_tag)
    required = triangulation.convergence_score < minimum_convergence_score
    suggested = [
        assay.assay_id
        for assay in program.assay_panel
        if not assay.blocking
    ][:3]
    return OrthogonalConfirmationPlan(
        decision_tag=decision_tag,
        required=required,
        suggested_assay_ids=suggested if required else [],
    )

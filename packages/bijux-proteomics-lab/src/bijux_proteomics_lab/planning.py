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
    flag_conflicting_evidence,
    triangulate_evidence,
)
from bijux_proteomics_lab.outcomes import (
    AssayResultState,
    ExperimentOutcome,
    assess_batch_outcome,
    summarize_experiment_outcome,
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
    replicate_values: list[float] = Field(
        default_factory=list,
        description="Raw replicate values captured for the observation.",
    )
    summary_statistic: str | None = Field(default=None, description="Summary statistic used for decisioning.")
    dispersion: float | None = Field(default=None, ge=0.0, description="Replicate dispersion signal.")
    qc_state: str = Field(default="passed", description="QC state such as passed, warning, or failed.")
    normalization_method: str | None = Field(default=None, description="Normalization method applied.")
    censoring_flag: bool = Field(default=False, description="Whether the observation was censored by detection limits.")
    interpretation_confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Confidence in interpretation quality for this observation.",
    )


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
    promotion_ready_count: int = Field(
        default=0,
        ge=0,
        description="Number of assay outcomes that are ready for evidence promotion.",
    )
    technical_failure_count: int = Field(
        default=0,
        ge=0,
        description="Technical/reproducibility failure count used in the recommendation.",
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
    reasons: list[str] = Field(default_factory=list, description="Short rationale points.")


class InformationGainBreakdown(JsonModel):
    """Multiparameter information-gain score components for an assay."""

    model_config = ConfigDict(extra="forbid")

    assay_id: AssayId = Field(..., description="Assay identifier.")
    uncertainty_reduction: float = Field(..., ge=0.0, le=1.0, description="Expected uncertainty reduction.")
    contradiction_resolution_value: float = Field(..., ge=0.0, le=1.0, description="Expected contradiction resolution value.")
    falsification_value: float = Field(..., ge=0.0, le=1.0, description="Expected hypothesis falsification value.")
    decision_gate_impact: float = Field(..., ge=0.0, le=1.0, description="Impact on near-term decision gates.")
    orthogonal_confirmation_value: float = Field(..., ge=0.0, le=1.0, description="Orthogonal confirmation contribution.")
    burden_penalty: float = Field(..., ge=0.0, le=1.0, description="Relative execution burden penalty.")
    final_score: float = Field(..., ge=0.0, le=1.0, description="Combined information-gain score.")


class OrthogonalConfirmationPlan(JsonModel):
    """Recommendation for orthogonal confirmation assays."""

    model_config = ConfigDict(extra="forbid")

    decision_tag: str = Field(..., min_length=1, description="Decision context evaluated.")
    required: bool = Field(..., description="Whether orthogonal confirmation is required.")
    suggested_assay_ids: list[str] = Field(
        default_factory=list,
        description="Assays suggested for orthogonal confirmation.",
    )


class ConflictResolutionPlan(JsonModel):
    """Assay recommendation plan for resolving evidence conflicts."""

    model_config = ConfigDict(extra="forbid")

    conflict_count: int = Field(..., ge=0, description="Number of detected conflicts.")
    suggested_assay_ids: list[str] = Field(
        default_factory=list,
        description="Assays recommended to resolve contradictory evidence.",
    )
    notes: list[str] = Field(default_factory=list, description="Human-readable plan notes.")


class UncertaintyReductionPlan(JsonModel):
    """Assay plan focused on reducing decision uncertainty."""

    model_config = ConfigDict(extra="forbid")

    decision_tag: str = Field(..., min_length=1, description="Decision context under uncertainty reduction.")
    prioritized_assay_ids: list[str] = Field(
        default_factory=list,
        description="Assays ordered by uncertainty reduction value.",
    )
    residual_uncertainty: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Estimated residual uncertainty after planned assays.",
    )
    notes: list[str] = Field(default_factory=list, description="Plan notes for reviewers.")


class NextBestExperiment(JsonModel):
    """Single next-best experiment recommendation."""

    model_config = ConfigDict(extra="forbid")

    assay_id: AssayId = Field(..., description="Recommended assay identifier.")
    prerequisite_assay_ids: list[AssayId] = Field(
        default_factory=list,
        description="Prerequisites that should run first.",
    )
    expected_information_gain: float = Field(..., ge=0.0, le=1.0, description="Expected information gain score.")
    rationale: list[str] = Field(default_factory=list, description="Short rationale for recommendation.")


class PlanningPolicy(JsonModel):
    """Weights and penalties for information-gain planning calculations."""

    model_config = ConfigDict(extra="forbid")

    policy_id: str = Field(..., min_length=1, description="Stable planning policy identifier.")
    uncertainty_weight: float = Field(default=0.22, ge=0.0, le=1.0, description="Weight for uncertainty reduction.")
    contradiction_weight: float = Field(default=0.2, ge=0.0, le=1.0, description="Weight for contradiction resolution.")
    falsification_weight: float = Field(default=0.18, ge=0.0, le=1.0, description="Weight for falsification value.")
    gate_impact_weight: float = Field(default=0.2, ge=0.0, le=1.0, description="Weight for decision-gate impact.")
    orthogonal_weight: float = Field(default=0.2, ge=0.0, le=1.0, description="Weight for orthogonal confirmation.")
    blocking_burden_penalty: float = Field(default=0.2, ge=0.0, le=1.0, description="Burden penalty for blocking assays.")
    non_blocking_burden_penalty: float = Field(
        default=0.12,
        ge=0.0,
        le=1.0,
        description="Burden penalty for non-blocking assays.",
    )


class DependencyCycleReport(JsonModel):
    """Cycle detection report for assay dependency graphs."""

    model_config = ConfigDict(extra="forbid")

    has_cycle: bool = Field(..., description="Whether a dependency cycle exists.")
    cycle_assay_ids: list[str] = Field(default_factory=list, description="Assays participating in a detected cycle.")


class DependencyIntegrityReport(JsonModel):
    """Integrity report for dependency graphs used in assay planning."""

    model_config = ConfigDict(extra="forbid")

    unknown_assay_ids: list[str] = Field(
        default_factory=list,
        description="Dependency assay IDs not present in the planned assay set.",
    )
    unknown_prerequisite_ids: list[str] = Field(
        default_factory=list,
        description="Prerequisite assay IDs not present in the planned assay set.",
    )
    self_dependency_assay_ids: list[str] = Field(
        default_factory=list,
        description="Assays that depend on themselves.",
    )
    cycle_report: DependencyCycleReport = Field(
        ...,
        description="Detected cycle information for valid dependency edges.",
    )


class DependencyCriticalPath(JsonModel):
    """Critical dependency path summary for assay execution order."""

    model_config = ConfigDict(extra="forbid")

    ordered_assay_ids: list[AssayId] = Field(default_factory=list, description="Critical path assay order.")
    path_length: int = Field(default=0, ge=0, description="Number of assays in the critical path.")


class SchedulePressureReport(JsonModel):
    """Capacity pressure summary for a scheduled plan."""

    model_config = ConfigDict(extra="forbid")

    cycle_id: CycleId = Field(..., description="Cycle identifier.")
    scheduled_batch_count: int = Field(default=0, ge=0, description="Number of scheduled batches.")
    unscheduled_batch_count: int = Field(default=0, ge=0, description="Number of unscheduled batches.")
    assay_slot_utilization: float = Field(..., ge=0.0, le=1.0, description="Used assay slots / total slots.")
    deferred_assay_count: int = Field(default=0, ge=0, description="Deferred assays due to capacity limits.")


class MaterialFeasibilityPriority(JsonModel):
    """Batch prioritization signal based on material feasibility."""

    model_config = ConfigDict(extra="forbid")

    batch_id: BatchId = Field(..., description="Batch identifier.")
    material_ready: bool = Field(..., description="Whether required materials are available.")
    missing_material_ids: list[str] = Field(default_factory=list, description="Missing materials for this batch.")
    priority_score: float = Field(..., ge=0.0, le=1.0, description="Material-feasibility priority score.")


def assess_dependency_integrity(
    assay_ids: list[AssayId],
    dependencies: list[AssayDependency],
) -> DependencyIntegrityReport:
    """Assess dependency integrity across unknown, invalid, and cyclic edges."""
    assay_id_set = set(assay_ids)
    unknown_assay_ids = sorted(
        {dependency.assay_id for dependency in dependencies if dependency.assay_id not in assay_id_set}
    )
    unknown_prerequisite_ids = sorted(
        {dependency.requires_assay_id for dependency in dependencies if dependency.requires_assay_id not in assay_id_set}
    )
    self_dependency_assay_ids = sorted(
        {dependency.assay_id for dependency in dependencies if dependency.assay_id == dependency.requires_assay_id}
    )
    valid_dependencies = [
        dependency
        for dependency in dependencies
        if dependency.assay_id in assay_id_set
        and dependency.requires_assay_id in assay_id_set
        and dependency.assay_id != dependency.requires_assay_id
    ]
    return DependencyIntegrityReport(
        unknown_assay_ids=unknown_assay_ids,
        unknown_prerequisite_ids=unknown_prerequisite_ids,
        self_dependency_assay_ids=self_dependency_assay_ids,
        cycle_report=detect_dependency_cycle(assay_ids, valid_dependencies),
    )


def dependency_order(
    assay_ids: list[AssayId],
    dependencies: list[AssayDependency],
) -> list[AssayId]:
    """Return assay ids with prerequisites placed earlier when possible."""
    dependency_integrity = assess_dependency_integrity(assay_ids, dependencies)
    valid_dependencies = [
        dependency
        for dependency in dependencies
        if dependency.assay_id not in dependency_integrity.unknown_assay_ids
        and dependency.requires_assay_id not in dependency_integrity.unknown_prerequisite_ids
        and dependency.assay_id not in dependency_integrity.self_dependency_assay_ids
    ]
    ordered: list[AssayId] = []
    remaining = list(assay_ids)
    while remaining:
        progressed = False
        for assay_id in list(remaining):
            prerequisites = [
                dependency.requires_assay_id
                for dependency in valid_dependencies
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


def detect_dependency_cycle(
    assay_ids: list[AssayId],
    dependencies: list[AssayDependency],
) -> DependencyCycleReport:
    """Detect whether assay dependencies contain a cycle."""
    edges = {assay_id: [] for assay_id in assay_ids}
    for dependency in dependencies:
        if dependency.assay_id in edges and dependency.requires_assay_id in edges:
            edges[dependency.assay_id].append(dependency.requires_assay_id)

    visiting: set[str] = set()
    visited: set[str] = set()
    cycle_nodes: set[str] = set()

    def _visit(node: str) -> bool:
        if node in visiting:
            cycle_nodes.add(node)
            return True
        if node in visited:
            return False
        visiting.add(node)
        for neighbor in edges.get(node, []):
            if _visit(neighbor):
                cycle_nodes.add(node)
                return True
        visiting.remove(node)
        visited.add(node)
        return False

    has_cycle = any(_visit(node) for node in edges)
    return DependencyCycleReport(
        has_cycle=has_cycle,
        cycle_assay_ids=sorted(cycle_nodes),
    )


def dependency_critical_path(
    assay_ids: list[AssayId],
    dependencies: list[AssayDependency],
) -> DependencyCriticalPath:
    """Compute a longest dependency path for assay execution planning."""
    prerequisites: dict[str, list[str]] = {assay_id: [] for assay_id in assay_ids}
    for dependency in dependencies:
        if dependency.assay_id in prerequisites and dependency.requires_assay_id in prerequisites:
            prerequisites[dependency.assay_id].append(dependency.requires_assay_id)

    memo: dict[str, list[str]] = {}

    def longest_path(node: str, stack: set[str]) -> list[str]:
        if node in memo:
            return memo[node]
        if node in stack:
            return [node]
        stack.add(node)
        best: list[str] = []
        for prereq in prerequisites.get(node, []):
            candidate = longest_path(prereq, stack)
            if len(candidate) > len(best):
                best = candidate
        stack.remove(node)
        memo[node] = best + [node]
        return memo[node]

    best_overall: list[str] = []
    for assay_id in assay_ids:
        candidate = longest_path(assay_id, set())
        if len(candidate) > len(best_overall):
            best_overall = candidate
    return DependencyCriticalPath(
        ordered_assay_ids=best_overall,
        path_length=len(best_overall),
    )


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
        observation.assay_id
        for observation in observations
        if _observation_blocks_progression(observation)
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


def _observation_blocks_progression(observation: AssayObservation) -> bool:
    """Return whether an observation should block progression."""
    if not observation.passed:
        return True
    if observation.qc_state.lower() in {"failed", "warning"}:
        return True
    if observation.censoring_flag:
        return True
    if observation.interpretation_confidence < 0.6:
        return True
    return False


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
    *,
    policy: PlanningPolicy | None = None,
) -> list[NextAssayPriority]:
    """Rank pending assays by expected information gain and decision impact."""
    observed_ids = {observation.assay_id for observation in observations}
    trust = compute_bundle_trust(bundle)
    readiness = assess_decision_readiness(bundle, [need.value for need in program.evidence_needs])
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
    burden_penalty = policy.blocking_burden_penalty if blocking else policy.non_blocking_burden_penalty
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


def plan_conflict_resolution_assays(
    program: ProgramSpec,
    bundle: EvidenceBundle,
) -> ConflictResolutionPlan:
    """Recommend assays that can resolve current evidence conflicts."""
    conflicts = flag_conflicting_evidence(bundle)
    if not conflicts:
        return ConflictResolutionPlan(
            conflict_count=0,
            suggested_assay_ids=[],
            notes=["no active evidence conflicts require assay resolution"],
        )
    suggested = [assay.assay_id for assay in program.assay_panel][:3]
    return ConflictResolutionPlan(
        conflict_count=len(conflicts),
        suggested_assay_ids=suggested,
        notes=[
            "prioritize assays with orthogonal readouts to resolve conflict pairs",
        ],
    )


def plan_uncertainty_reduction_assays(
    program: ProgramSpec,
    bundle: EvidenceBundle,
    observations: list[AssayObservation],
    *,
    decision_tag: str = "progression",
) -> UncertaintyReductionPlan:
    """Plan assays that most reduce uncertainty for a target decision tag."""
    priorities = prioritize_next_assays(program, bundle, observations)
    prioritized = [item.assay_id for item in priorities[:5]]
    top_score = priorities[0].score if priorities else 0.0
    residual_uncertainty = round(max(0.0, 1.0 - top_score), 4)
    notes = (
        [f"selected top {len(prioritized)} assays by information-gain score for {decision_tag}"]
        if prioritized
        else [f"no pending assays available for {decision_tag} uncertainty reduction"]
    )
    return UncertaintyReductionPlan(
        decision_tag=decision_tag,
        prioritized_assay_ids=prioritized,
        residual_uncertainty=residual_uncertainty,
        notes=notes,
    )


def recommend_next_best_experiment(
    program: ProgramSpec,
    bundle: EvidenceBundle,
    observations: list[AssayObservation],
    dependencies: list[AssayDependency] | None = None,
) -> NextBestExperiment | None:
    """Recommend the next best experiment with dependency awareness."""
    priorities = prioritize_next_assays(program, bundle, observations)
    if not priorities:
        return None
    dependencies = dependencies or []
    top = priorities[0]
    prerequisites = sorted(
        {
            dependency.requires_assay_id
            for dependency in dependencies
            if dependency.assay_id == top.assay_id
        }
    )
    rationale = list(top.reasons)
    if prerequisites:
        rationale.append("assay has prerequisite dependencies that should be scheduled first")
    if top.estimated_cost > 1.2:
        rationale.append("assay has elevated execution burden but highest current information gain")
    return NextBestExperiment(
        assay_id=top.assay_id,
        prerequisite_assay_ids=prerequisites,
        expected_information_gain=top.score,
        rationale=rationale or ["highest ranked by information-gain scoring"],
    )


def recommend_next_cycle_from_outcome(
    program: ProgramSpec,
    bundle: EvidenceBundle,
    outcome: ExperimentOutcome,
) -> ClosedLoopPlan:
    """Recommend the next cycle by combining evidence trust with normalized assay outcomes."""
    summary = summarize_experiment_outcome(outcome)
    assessment = assess_batch_outcome(outcome)
    trust = compute_bundle_trust(bundle)
    failed_assays = [
        assay.assay_id
        for assay in outcome.assay_outcomes
        if assay.result_state
        in {
            AssayResultState.FAILED_BIOLOGICAL,
            AssayResultState.FAILED_TECHNICAL,
            AssayResultState.FAILED_REPRODUCIBILITY,
            AssayResultState.INCONCLUSIVE,
        }
    ]
    if summary.failed_technical_count > 0 or summary.failed_reproducibility_count > 0:
        return ClosedLoopPlan(
            program_id=program.program_id,
            decision=ProgressDecision.HOLD,
            evidence_backlog=evidence_gaps(bundle, [need.value for need in program.evidence_needs]),
            assay_backlog=failed_assays,
            notes=["repair assay execution quality before making redesign or progression calls"],
            evidence_trust_score=trust.trust_score,
            promotion_ready_count=assessment.promotion_ready_count,
            technical_failure_count=assessment.technical_or_repro_failures,
        )
    if summary.failed_biological_count > 0:
        return ClosedLoopPlan(
            program_id=program.program_id,
            decision=ProgressDecision.REDESIGN,
            evidence_backlog=evidence_gaps(bundle, [need.value for need in program.evidence_needs]),
            assay_backlog=failed_assays,
            notes=["biological failures indicate the candidate hypothesis should be redesigned"],
            evidence_trust_score=trust.trust_score,
            promotion_ready_count=assessment.promotion_ready_count,
            technical_failure_count=assessment.technical_or_repro_failures,
        )
    plan = recommend_next_cycle(
        program,
        bundle,
        [
            AssayObservation(
                assay_id=assay.assay_id,
                metric="outcome_state",
                value=1.0 if assay.passed else 0.0,
                passed=assay.passed,
            )
            for assay in outcome.assay_outcomes
        ],
    )
    return plan.model_copy(
        update={
            "promotion_ready_count": assessment.promotion_ready_count,
            "technical_failure_count": assessment.technical_or_repro_failures,
        }
    )


def summarize_schedule_pressure(
    scheduled: ScheduledPlan,
    capacity: LabCapacity,
) -> SchedulePressureReport:
    """Summarize scheduling pressure against available cycle capacity."""
    total_slots = capacity.max_batches * capacity.max_assays_per_batch
    used_slots = sum(len(batch.assay_ids) for batch in scheduled.scheduled_batches)
    deferred = sum(len(batch.deferred_assay_ids) for batch in scheduled.scheduled_batches)
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
        priority_score = round(max(0.0, min(base - ((batch.priority - 1) * 0.05), 1.0)), 4)
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

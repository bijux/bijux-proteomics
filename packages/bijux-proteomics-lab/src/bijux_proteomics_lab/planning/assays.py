# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Experiment planning helpers."""

from __future__ import annotations

from enum import StrEnum

from pydantic import ConfigDict, Field

from bijux_proteomics.domain.assays import AssayRequirement
from bijux_proteomics.domain.program_spec import ProgramSpec
from bijux_proteomics.workflow.blueprint import workflow_blueprint_for_program
from bijux_proteomics_foundation import (
    AssayId,
    BatchId,
    DocumentSchema,
    JsonModel,
    ProgramId,
)
from bijux_proteomics_knowledge.memory.models.evidence import (
    EvidenceBundle,
    assess_decision_readiness,
    compute_bundle_trust,
    evidence_gaps,
    flag_conflicting_evidence,
    triangulate_evidence,
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
    summary_statistic: str | None = Field(
        default=None, description="Summary statistic used for decisioning."
    )
    dispersion: float | None = Field(
        default=None, ge=0.0, description="Replicate dispersion signal."
    )
    qc_state: str = Field(
        default="passed", description="QC state such as passed, warning, or failed."
    )
    normalization_method: str | None = Field(
        default=None, description="Normalization method applied."
    )
    censoring_flag: bool = Field(
        default=False,
        description="Whether the observation was censored by detection limits.",
    )
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
    requires_assay_id: AssayId = Field(
        ..., description="Prerequisite assay identifier."
    )


class AssayIntent(JsonModel):
    """Intent and prerequisites for an assay in the planning layer."""

    model_config = ConfigDict(extra="forbid")

    assay_id: AssayId = Field(..., description="Assay identifier.")
    objective: str = Field(..., min_length=1, description="Why the assay is planned.")
    prerequisite_assay_ids: list[AssayId] = Field(
        default_factory=list,
        description="Assays that must complete first.",
    )


class AssayPlanKind(StrEnum):
    """Distinguish scientific planning advice from executable lab work."""

    ADVISORY = "advisory"
    EXECUTABLE = "executable"


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


class AdvisoryAssayRecommendation(JsonModel):
    """Scientifically motivated assay recommendation that is not execution-ready."""

    model_config = ConfigDict(extra="forbid")

    assay_id: AssayId = Field(..., description="Assay identifier.")
    objective: str = Field(..., min_length=1, description="Scientific purpose.")
    blocking: bool = Field(..., description="Whether the assay blocks progression.")
    rationale: list[str] = Field(
        default_factory=list,
        description="Reasoning for recommending the assay.",
    )


class EvidenceNeedWetLabAction(JsonModel):
    """Concrete wet-lab action mapping for one unmet evidence need."""

    model_config = ConfigDict(extra="forbid")

    evidence_need: str = Field(..., min_length=1)
    assay_ids: list[AssayId] = Field(
        default_factory=list,
        description="Assays that can reduce this evidence gap.",
    )
    blocking_assay_ids: list[AssayId] = Field(
        default_factory=list,
        description="Mapped assays that also block progression.",
    )
    sample_kinds: list[str] = Field(
        default_factory=list,
        description="Sample modalities required to execute the mapped work.",
    )
    wet_lab_actions: list[str] = Field(
        default_factory=list,
        description="Concrete lab-facing actions implied by the evidence gap.",
    )
    notes: list[str] = Field(default_factory=list)


class AdvisoryAssayPlan(JsonModel):
    """Advisory assay plan for scientific prioritization before execution prep."""

    model_config = ConfigDict(extra="forbid")

    program_id: ProgramId = Field(..., description="Program identifier.")
    plan_kind: AssayPlanKind = Field(default=AssayPlanKind.ADVISORY)
    open_evidence_gaps: list[str] = Field(
        default_factory=list,
        description="Evidence gaps that still shape scientific assay priority.",
    )
    recommendations: list[AdvisoryAssayRecommendation] = Field(
        default_factory=list,
        description="Scientifically motivated assay recommendations.",
    )
    evidence_need_actions: list[EvidenceNeedWetLabAction] = Field(
        default_factory=list,
        description="Open evidence needs translated into wet-lab actions.",
    )
    executable: bool = Field(
        default=False,
        description="Advisory plans are not direct lab execution instructions.",
    )


class ExecutableAssayInstruction(JsonModel):
    """Concrete assay instruction ready for laboratory execution review."""

    model_config = ConfigDict(extra="forbid")

    instruction_id: str = Field(..., min_length=1)
    assay_id: AssayId = Field(..., description="Assay identifier.")
    batch_id: BatchId = Field(..., description="Batch identifier.")
    sample_kind: str = Field(..., min_length=1)
    objective: str = Field(..., min_length=1)
    blocking: bool = Field(..., description="Whether the assay blocks progression.")
    preflight_checks: list[str] = Field(
        default_factory=list,
        description="Checks that must pass before the assay is run.",
    )


class ExecutableAssayPlan(JsonModel):
    """Operational assay plan ready for lab execution review."""

    model_config = ConfigDict(extra="forbid")

    program_id: ProgramId = Field(..., description="Program identifier.")
    batch_id: BatchId = Field(..., description="Batch identifier.")
    plan_kind: AssayPlanKind = Field(default=AssayPlanKind.EXECUTABLE)
    instructions: list[ExecutableAssayInstruction] = Field(
        default_factory=list,
        description="Executable assay instructions for one batch.",
    )
    blocked_by: list[str] = Field(
        default_factory=list,
        description="Operational blockers that still prevent execution.",
    )
    ready_for_execution: bool = Field(
        ..., description="Whether the executable plan can proceed as written."
    )


class LabQueuePrioritizationInput(JsonModel):
    """Inputs used to prioritize candidate placement in a follow-up queue."""

    model_config = ConfigDict(extra="forbid")

    candidate_id: str = Field(..., min_length=1)
    candidate_score: float = Field(..., ge=0.0, le=1.0)
    evidence_gap_count: int = Field(..., ge=0)
    cost_score: float = Field(..., ge=0.0, le=1.0)
    capacity_pressure_score: float = Field(..., ge=0.0, le=1.0)
    assay_constraint_penalty: float = Field(..., ge=0.0, le=1.0)


class LabQueuePrioritizationEntry(JsonModel):
    """Prioritized follow-up queue entry with rationale score."""

    model_config = ConfigDict(extra="forbid")

    candidate_id: str = Field(..., min_length=1)
    queue_priority_score: float
    queue_rank: int = Field(..., ge=1)


class LabQueuePrioritizationReport(JsonModel):
    """Queue prioritization report for candidate follow-up actions."""

    model_config = ConfigDict(extra="forbid")

    entries: tuple[LabQueuePrioritizationEntry, ...] = Field(default_factory=tuple)


def build_lab_queue_prioritization_report(
    items: tuple[LabQueuePrioritizationInput, ...],
) -> LabQueuePrioritizationReport:
    """Prioritize follow-up queue placement with explicit evidence and burden tradeoffs."""

    scored: list[tuple[str, float]] = []
    for item in items:
        gap_bonus = min(1.0, item.evidence_gap_count / 5.0)
        score = (
            (0.4 * item.candidate_score)
            + (0.2 * gap_bonus)
            + (0.15 * (1.0 - item.cost_score))
            + (0.15 * (1.0 - item.capacity_pressure_score))
            + (0.1 * (1.0 - item.assay_constraint_penalty))
        )
        scored.append((item.candidate_id, score))

    scored.sort(key=lambda row: (-row[1], row[0]))
    entries = tuple(
        LabQueuePrioritizationEntry(
            candidate_id=candidate_id,
            queue_priority_score=score,
            queue_rank=index + 1,
        )
        for index, (candidate_id, score) in enumerate(scored)
    )
    return LabQueuePrioritizationReport(entries=entries)


class ExecutionPlanUncertaintyReport(JsonModel):
    """Uncertainty summary attached to an executable assay plan."""

    model_config = ConfigDict(extra="forbid")

    batch_id: BatchId = Field(..., description="Batch identifier.")
    uncertain_instruction_ids: list[str] = Field(default_factory=list)
    uncertainty_sources: list[str] = Field(default_factory=list)
    readiness_confidence: float = Field(..., ge=0.0, le=1.0)
    notes: list[str] = Field(default_factory=list)


class WorkflowBatchOutline(JsonModel):
    """Execution-oriented outline derived from the scientific workflow."""

    model_config = ConfigDict(extra="forbid")

    program_id: ProgramId = Field(..., description="Program identifier.")
    gate_assay_ids: list[AssayId] = Field(
        default_factory=list,
        description="Blocking assays that should anchor the first batch.",
    )
    support_assay_ids: list[AssayId] = Field(
        default_factory=list,
        description="Non-blocking assays that can follow gate assays.",
    )
    review_gate_ids: list[str] = Field(
        default_factory=list,
        description="Review gates that consume workflow outputs.",
    )
    missing_evidence_needs: list[str] = Field(
        default_factory=list,
        description="Evidence kinds still missing before workflow closure.",
    )


class MaterialRequirement(JsonModel):
    """Material needed to execute planned work."""

    model_config = ConfigDict(extra="forbid")

    material_id: str = Field(
        ..., min_length=1, description="Stable material identifier."
    )
    sample_kind: str = Field(
        ..., min_length=1, description="Type of sample or reagent."
    )
    minimum_units: float = Field(
        ...,
        gt=0.0,
        description="Minimum quantity required for execution.",
    )
    unit: str = Field(..., min_length=1, description="Unit of measure.")


class MaterialInventory(JsonModel):
    """Available material inventory for a planning cycle."""

    model_config = ConfigDict(extra="forbid")

    material_id: str = Field(
        ..., min_length=1, description="Stable material identifier."
    )
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
    advancement_evidence: AdvancementEvidencePacket


class AdvancementEvidenceItem(JsonModel):
    """One evidence item explicitly carried into an advancement review."""

    model_config = ConfigDict(extra="forbid")

    evidence_id: str = Field(..., min_length=1)
    kind: str = Field(..., min_length=1)
    confidence: float = Field(..., ge=0.0, le=1.0)
    strength: str = Field(..., min_length=1)
    claim: str = Field(..., min_length=1)


class AdvancementEvidencePacket(JsonModel):
    """Exact evidence set used to justify or block advancement."""

    model_config = ConfigDict(extra="forbid")

    bundle_id: str = Field(..., min_length=1)
    target_id: str = Field(..., min_length=1)
    evidence_ids: list[str] = Field(default_factory=list)
    required_evidence_kinds: list[str] = Field(default_factory=list)
    missing_evidence_kinds: list[str] = Field(default_factory=list)
    items: list[AdvancementEvidenceItem] = Field(default_factory=list)


class ReviewRiskProfile(JsonModel):
    """Risk summary attached to a decision brief."""

    model_config = ConfigDict(extra="forbid")

    trust_score: float = Field(
        ..., ge=0.0, le=1.0, description="Evidence trust score for the current bundle."
    )
    conflict_count: int = Field(
        ..., ge=0, description="Number of active evidence conflicts."
    )
    triangulation_score: float = Field(
        ..., ge=0.0, le=1.0, description="Triangulation convergence score."
    )
    risk_level: str = Field(
        ..., min_length=1, description="Overall risk level: low, medium, or high."
    )


class LabReviewPacketBundle(JsonModel):
    """Review packet bundle that carries assay rationale and unresolved risks."""

    model_config = ConfigDict(extra="forbid")

    review_packet: ReviewPacket
    assay_rationale_by_id: dict[str, list[str]] = Field(
        default_factory=dict,
        description="Assay rationale grouped by assay identifier.",
    )
    target_evidence_ids: list[str] = Field(
        default_factory=list,
        description="Evidence records tied directly to the target decision brief.",
    )
    unresolved_risks: list[str] = Field(
        default_factory=list,
        description="Open blockers and missing evidence that remain unresolved.",
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


class LabExecutionRequest(JsonModel):
    """Explicit handoff request from computational review into lab execution."""

    model_config = ConfigDict(extra="forbid")

    program_id: ProgramId = Field(..., description="Program identifier.")
    batch_id: BatchId = Field(..., description="Requested batch identifier.")
    evidence_ids: list[str] = Field(
        default_factory=list,
        description="Evidence records attached to the request.",
    )
    requested_instruction_ids: list[str] = Field(
        default_factory=list,
        description="Execution instructions requested from the lab.",
    )
    requested_assay_ids: list[AssayId] = Field(
        default_factory=list,
        description="Assays carried into the lab request.",
    )
    scientific_rationale: list[str] = Field(
        default_factory=list,
        description="Scientific rationale points carried from review.",
    )
    unresolved_risks: list[str] = Field(
        default_factory=list,
        description="Open blockers or missing readiness conditions.",
    )
    ready_for_lab_review: bool = Field(
        ..., description="Whether the request is coherent for lab review."
    )


class DependencyCycleReport(JsonModel):
    """Cycle detection report for assay dependency graphs."""

    model_config = ConfigDict(extra="forbid")

    has_cycle: bool = Field(..., description="Whether a dependency cycle exists.")
    cycle_assay_ids: list[str] = Field(
        default_factory=list, description="Assays participating in a detected cycle."
    )


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

    ordered_assay_ids: list[AssayId] = Field(
        default_factory=list, description="Critical path assay order."
    )
    path_length: int = Field(
        default=0, ge=0, description="Number of assays in the critical path."
    )


class PlanValidationIssue(JsonModel):
    """Validation issue for experiment plan structure."""

    model_config = ConfigDict(extra="forbid")

    code: str = Field(..., min_length=1, description="Stable issue code.")
    message: str = Field(..., min_length=1, description="Human-readable issue message.")


def assess_dependency_integrity(
    assay_ids: list[AssayId],
    dependencies: list[AssayDependency],
) -> DependencyIntegrityReport:
    """Assess dependency integrity across unknown, invalid, and cyclic edges."""
    assay_id_set = set(assay_ids)
    unknown_assay_ids = sorted(
        {
            dependency.assay_id
            for dependency in dependencies
            if dependency.assay_id not in assay_id_set
        }
    )
    unknown_prerequisite_ids = sorted(
        {
            dependency.requires_assay_id
            for dependency in dependencies
            if dependency.requires_assay_id not in assay_id_set
        }
    )
    self_dependency_assay_ids = sorted(
        {
            dependency.assay_id
            for dependency in dependencies
            if dependency.assay_id == dependency.requires_assay_id
        }
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
        and dependency.requires_assay_id
        not in dependency_integrity.unknown_prerequisite_ids
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
            if all(
                prerequisite in ordered or prerequisite not in assay_ids
                for prerequisite in prerequisites
            ):
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
    edges: dict[str, list[str]] = {assay_id: [] for assay_id in assay_ids}
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
        if (
            dependency.assay_id in prerequisites
            and dependency.requires_assay_id in prerequisites
        ):
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
    """Build dependency-aware batches grouped by blocking status and assay family.

    Inputs:
    ``program`` defines the governed assay panel, ``bundle`` optionally supplies
    current evidence coverage, and ``dependencies`` optionally constrain assay
    execution order.

    Outputs:
    Returns one ``ExperimentPlan`` with prioritized batches, review-gate queues,
    and open evidence gaps.

    Failure Modes:
    Propagates dependency ordering errors if the supplied assay dependencies
    cannot produce a valid execution order.

    Scientific Caveats:
    The plan prioritizes governed assay needs only; it does not confirm sample
    inventory, reagent readiness, or experimental success likelihood.
    """
    dependencies = dependencies or []
    batches: list[ExperimentBatch] = []
    grouped: dict[tuple[bool, AssayFamily], list[AssayRequirement]] = {}
    for assay in program.assay_panel:
        grouped.setdefault(
            (assay.blocking, assay_family(assay.sample_kind)), []
        ).append(assay)
    priority = 1
    for (blocking, family), assays in sorted(
        grouped.items(),
        key=lambda item: (not item[0][0], assay_family_priority(item[0][1])),
    ):
        ordered_assays = dependency_order(
            [assay.assay_id for assay in assays], dependencies
        )
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
                assay_sample_kinds={
                    assay.assay_id: assay.sample_kind for assay in assays
                },
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


def build_advisory_assay_plan(
    program: ProgramSpec,
    bundle: EvidenceBundle | None = None,
) -> AdvisoryAssayPlan:
    """Build a scientific assay-priority plan that is not execution-ready.

    Inputs:
    ``program`` defines the assay panel and ``bundle`` optionally supplies the
    current evidence state used to identify open gaps.

    Outputs:
    Returns one ``AdvisoryAssayPlan`` with recommended assays and mapped
    wet-lab actions for unresolved evidence needs.

    Failure Modes:
    This function does not raise governed public exceptions under normal typed
    input use.

    Scientific Caveats:
    The advisory plan is intentionally non-executable guidance; it does not
    schedule batches or prove that follow-up assays are operationally feasible.
    """
    required_kinds = [need.value for need in program.evidence_needs]
    open_gaps = evidence_gaps(bundle, required_kinds) if bundle else required_kinds
    recommendations = [
        AdvisoryAssayRecommendation(
            assay_id=assay.assay_id,
            objective=assay.purpose,
            blocking=assay.blocking,
            rationale=[
                (
                    "blocking assay for the next review gate"
                    if assay.blocking
                    else "support assay for confidence expansion"
                ),
                f"sample kind: {assay.sample_kind}",
                *(
                    [f"targets evidence gaps: {', '.join(open_gaps[:2])}"]
                    if open_gaps
                    else []
                ),
            ],
        )
        for assay in program.assay_panel
    ]
    evidence_need_actions = [
        _map_evidence_need_to_wet_lab_actions(program=program, evidence_need=gap)
        for gap in open_gaps
    ]
    return AdvisoryAssayPlan(
        program_id=program.program_id,
        open_evidence_gaps=open_gaps,
        recommendations=recommendations,
        evidence_need_actions=evidence_need_actions,
    )


def build_executable_assay_plan(
    plan: ExperimentPlan,
    *,
    batch_id: BatchId,
    available_sample_kinds: list[str] | None = None,
) -> ExecutableAssayPlan:
    """Convert one planned batch into execution-ready lab instructions.

    Inputs:
    ``plan`` supplies the governed experiment batches, ``batch_id`` selects the
    batch to realize, and ``available_sample_kinds`` optionally declares the
    currently available sample inventory.

    Outputs:
    Returns one ``ExecutableAssayPlan`` with instruction rows, blocking reasons,
    and a ready-for-execution flag.

    Failure Modes:
    Raises ``ValueError`` if ``batch_id`` does not exist in the supplied
    experiment plan.

    Scientific Caveats:
    Execution readiness is based on governed plan structure, review gates, and
    declared sample kinds only; it does not guarantee assay performance or data
    quality.
    """
    batch = next(
        (candidate for candidate in plan.batches if candidate.batch_id == batch_id),
        None,
    )
    if batch is None:
        raise ValueError(f"unknown batch_id: {batch_id}")
    available_sample_kind_set = set(available_sample_kinds or [])
    missing_sample_kinds = [
        sample_kind
        for sample_kind in batch.sample_requirements
        if sample_kind not in available_sample_kind_set
    ]
    blocked_by = [
        *[f"review gate pending: {gate_id}" for gate_id in batch.blocking_review_gates],
        *[
            f"missing sample kind: {sample_kind}"
            for sample_kind in missing_sample_kinds
        ],
    ]
    instructions = [
        ExecutableAssayInstruction(
            instruction_id=f"{batch.batch_id}:{assay_id}",
            assay_id=assay_id,
            batch_id=batch.batch_id,
            sample_kind=batch.assay_sample_kinds.get(assay_id, "unspecified"),
            objective=batch.objective,
            blocking=bool(batch.blocking_review_gates),
            preflight_checks=[
                *[
                    f"confirm review gate {gate_id} cleared"
                    for gate_id in batch.blocking_review_gates
                ],
                *[
                    f"confirm sample inventory for {sample_kind}"
                    for sample_kind in batch.sample_requirements
                ],
            ],
        )
        for assay_id in batch.assay_ids
    ]
    return ExecutableAssayPlan(
        program_id=plan.program_id,
        batch_id=batch.batch_id,
        instructions=instructions,
        blocked_by=blocked_by,
        ready_for_execution=not blocked_by,
    )


def report_execution_plan_uncertainty(
    executable_plan: ExecutableAssayPlan,
    *,
    open_evidence_gaps: list[str] | None = None,
) -> ExecutionPlanUncertaintyReport:
    """Summarize uncertainty that still affects a lab execution plan."""
    open_evidence_gaps = open_evidence_gaps or []
    uncertainty_sources = [
        *executable_plan.blocked_by,
        *(f"open evidence gap: {gap}" for gap in open_evidence_gaps),
    ]
    confidence = 1.0
    if executable_plan.blocked_by:
        confidence -= 0.4
    if open_evidence_gaps:
        confidence -= min(0.4, len(open_evidence_gaps) * 0.1)
    return ExecutionPlanUncertaintyReport(
        batch_id=executable_plan.batch_id,
        uncertain_instruction_ids=[
            instruction.instruction_id for instruction in executable_plan.instructions
        ],
        uncertainty_sources=uncertainty_sources,
        readiness_confidence=round(max(0.0, confidence), 4),
        notes=(
            ["execution uncertainty should be resolved before scheduling"]
            if uncertainty_sources
            else ["execution plan is fully specified at current scope"]
        ),
    )


def build_lab_execution_request(
    review_packet: ReviewPacket,
    executable_plan: ExecutableAssayPlan,
) -> LabExecutionRequest:
    """Package review evidence and executable instructions into one lab request."""
    return LabExecutionRequest(
        program_id=review_packet.program_id,
        batch_id=executable_plan.batch_id,
        evidence_ids=list(review_packet.advancement_evidence.evidence_ids),
        requested_instruction_ids=[
            instruction.instruction_id for instruction in executable_plan.instructions
        ],
        requested_assay_ids=[
            instruction.assay_id for instruction in executable_plan.instructions
        ],
        scientific_rationale=list(review_packet.recommended_actions),
        unresolved_risks=[
            *review_packet.blocking_findings,
            *executable_plan.blocked_by,
        ],
        ready_for_lab_review=(
            review_packet.ready_for_synthesis and executable_plan.ready_for_execution
        ),
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
    trust = compute_bundle_trust(bundle)
    conflicts = flag_conflicting_evidence(bundle)
    triangulation = triangulate_evidence(bundle, decision_tag="progression")
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
    advancement_evidence = _build_advancement_evidence_packet(
        program=program,
        bundle=bundle,
    )
    risk_profile = build_review_risk_profile(
        trust_score=trust.trust_score,
        conflict_count=len(conflicts),
        triangulation_score=triangulation.convergence_score,
    )
    recommendations.append(f"review risk level: {risk_profile.risk_level}")

    return ReviewPacket(
        program_id=program.program_id,
        ready_for_synthesis=not blockers,
        blocking_findings=blockers,
        recommended_actions=recommendations,
        advancement_evidence=advancement_evidence,
    )


def build_lab_review_packet_bundle(
    program: ProgramSpec,
    bundle: EvidenceBundle,
    observations: list[AssayObservation],
) -> LabReviewPacketBundle:
    """Bundle review findings with assay rationale and unresolved target risks."""
    review_packet = build_review_packet(program, bundle, observations)
    assay_rationale_by_id = {
        assay.assay_id: [
            assay.purpose,
            f"readout: {assay.readout}",
            f"sample kind: {assay.sample_kind}",
        ]
        for assay in program.assay_panel
    }
    unresolved_risks = [
        *review_packet.blocking_findings,
        *review_packet.advancement_evidence.missing_evidence_kinds,
    ]
    return LabReviewPacketBundle(
        review_packet=review_packet,
        assay_rationale_by_id=assay_rationale_by_id,
        target_evidence_ids=list(review_packet.advancement_evidence.evidence_ids),
        unresolved_risks=unresolved_risks,
    )


def build_workflow_batch_outline(
    program: ProgramSpec,
    bundle: EvidenceBundle,
) -> WorkflowBatchOutline:
    """Project the scientific workflow into gate and support assay batches."""
    blueprint = workflow_blueprint_for_program(program)
    gate_assay_ids = list(blueprint.blocking_assay_ids)
    support_assay_ids = [
        assay.assay_id
        for assay in program.assay_panel
        if assay.assay_id not in set(gate_assay_ids)
    ]
    return WorkflowBatchOutline(
        program_id=program.program_id,
        gate_assay_ids=gate_assay_ids,
        support_assay_ids=support_assay_ids,
        review_gate_ids=list(blueprint.blocking_review_gate_ids),
        missing_evidence_needs=evidence_gaps(
            bundle,
            [need.value for need in program.evidence_needs],
        ),
    )


def _observation_blocks_progression(observation: AssayObservation) -> bool:
    """Return whether an observation should block progression."""
    return (
        not observation.passed
        or observation.qc_state.lower() in {"failed", "warning"}
        or observation.censoring_flag
        or observation.interpretation_confidence < 0.6
    )


def _map_evidence_need_to_wet_lab_actions(
    *,
    program: ProgramSpec,
    evidence_need: str,
) -> EvidenceNeedWetLabAction:
    mapped_assays = [
        assay
        for assay in program.assay_panel
        if _assay_supports_evidence_need(assay=assay, evidence_need=evidence_need)
    ]
    if not mapped_assays:
        mapped_assays = [assay for assay in program.assay_panel if assay.blocking]
    assay_ids = [assay.assay_id for assay in mapped_assays]
    sample_kinds = sorted({assay.sample_kind for assay in mapped_assays})
    wet_lab_actions = [
        f"prepare {assay.sample_kind} material for {assay.assay_id}"
        for assay in mapped_assays
    ]
    wet_lab_actions.extend(
        f"capture {assay.readout} acceptance criteria for {assay.assay_id}"
        for assay in mapped_assays
    )
    notes = (
        [
            "direct assay-to-evidence mapping inferred from assay purpose, readout, and sample modality"
        ]
        if mapped_assays
        else ["no assay is currently mapped to this evidence need"]
    )
    return EvidenceNeedWetLabAction(
        evidence_need=evidence_need,
        assay_ids=assay_ids,
        blocking_assay_ids=[
            assay.assay_id for assay in mapped_assays if assay.blocking
        ],
        sample_kinds=sample_kinds,
        wet_lab_actions=wet_lab_actions,
        notes=notes,
    )


def _assay_supports_evidence_need(
    *,
    assay: AssayRequirement,
    evidence_need: str,
) -> bool:
    normalized_need = evidence_need.strip().lower()
    haystack = " ".join(
        (
            assay.assay_id,
            assay.purpose,
            assay.readout,
            assay.sample_kind,
        )
    ).lower()
    keyword_map = {
        "literature": (),
        "structure": ("structure", "binding", "stability", "fold", "thermal"),
        "assay": ("assay", "binding", "activity", "readout", "engagement"),
        "pathway": ("pathway", "cell", "cellular", "signaling", "phenotype"),
        "safety": ("safety", "tox", "viability", "selectivity", "off-target"),
    }
    keywords = keyword_map.get(normalized_need, (normalized_need,))
    return not keywords or any(keyword in haystack for keyword in keywords)


def _build_advancement_evidence_packet(
    *,
    program: ProgramSpec,
    bundle: EvidenceBundle,
) -> AdvancementEvidencePacket:
    required_kinds = [need.value for need in program.evidence_needs]
    relevant_records = [
        record
        for record in bundle.records
        if not record.decision_tags or "progression" in record.decision_tags
    ]
    selected_records = []
    seen_kinds: set[str] = set()
    for required_kind in required_kinds:
        best_record = next(
            (
                record
                for record in sorted(
                    relevant_records,
                    key=lambda candidate: (
                        candidate.kind.value != required_kind,
                        -candidate.confidence,
                        candidate.evidence_id,
                    ),
                )
                if record.kind.value == required_kind
            ),
            None,
        )
        if best_record is not None:
            selected_records.append(best_record)
            seen_kinds.add(required_kind)
    if not selected_records:
        selected_records = sorted(
            relevant_records,
            key=lambda record: (-record.confidence, record.evidence_id),
        )
    return AdvancementEvidencePacket(
        bundle_id=bundle.bundle_id,
        target_id=bundle.target_id,
        evidence_ids=[record.evidence_id for record in selected_records],
        required_evidence_kinds=required_kinds,
        missing_evidence_kinds=[
            required_kind
            for required_kind in required_kinds
            if required_kind not in seen_kinds
        ],
        items=[
            AdvancementEvidenceItem(
                evidence_id=record.evidence_id,
                kind=record.kind.value,
                confidence=round(record.confidence, 4),
                strength=record.strength.value,
                claim=record.claim,
            )
            for record in selected_records
        ],
    )


def build_review_risk_profile(
    *,
    trust_score: float,
    conflict_count: int,
    triangulation_score: float,
) -> ReviewRiskProfile:
    """Build a compact risk profile from evidence quality indicators."""
    if conflict_count > 0 or trust_score < 0.5 or triangulation_score < 0.4:
        level = "high"
    elif trust_score < 0.7 or triangulation_score < 0.6:
        level = "medium"
    else:
        level = "low"
    return ReviewRiskProfile(
        trust_score=round(trust_score, 4),
        conflict_count=conflict_count,
        triangulation_score=round(triangulation_score, 4),
        risk_level=level,
    )


def validate_experiment_plan(plan: ExperimentPlan) -> list[PlanValidationIssue]:
    """Validate experiment plan structure before scheduling."""
    issues: list[PlanValidationIssue] = []
    batch_ids = [batch.batch_id for batch in plan.batches]
    if len(batch_ids) != len(set(batch_ids)):
        issues.append(
            PlanValidationIssue(
                code="duplicate-batch-id",
                message="experiment plan contains duplicate batch_id values",
            )
        )
    priorities = [batch.priority for batch in plan.batches]
    if priorities and sorted(priorities) != priorities:
        issues.append(
            PlanValidationIssue(
                code="priority-order-invalid",
                message="batch priorities should be non-decreasing in plan order",
            )
        )
    issues.extend(
        PlanValidationIssue(
            code="empty-assay-batch",
            message=f"{batch.batch_id} should include at least one assay_id",
        )
        for batch in plan.batches
        if not batch.assay_ids
    )
    return issues

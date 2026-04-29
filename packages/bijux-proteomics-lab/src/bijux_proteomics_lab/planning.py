# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Experiment planning helpers."""

from __future__ import annotations

from enum import StrEnum

from pydantic import ConfigDict, Field

from bijux_proteomics.assays import AssayRequirement
from bijux_proteomics.programs import ProgramSpec
from bijux_proteomics.workflow_blueprint import workflow_blueprint_for_program
from bijux_proteomics_foundation import (
    AssayId,
    BatchId,
    CycleId,
    DocumentSchema,
    JsonModel,
    ProgramId,
)
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
    triage_batch_failures,
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


class ReviewRiskProfile(JsonModel):
    """Risk summary attached to a review packet."""

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
    reasons: list[str] = Field(
        default_factory=list, description="Short rationale points."
    )


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


class HypothesisFalsificationPlan(JsonModel):
    """Plan ranking assays by hypothesis-falsification value."""

    model_config = ConfigDict(extra="forbid")

    hypothesis: str = Field(
        ..., min_length=1, description="Scientific hypothesis under test."
    )
    prioritized_assay_ids: list[AssayId] = Field(
        default_factory=list, description="Assays ranked by falsification value."
    )
    rationale: list[str] = Field(
        default_factory=list, description="Rationale notes for assay ranking."
    )


class AssayPortfolioBalanceReport(JsonModel):
    """Coverage and concentration report across assay families."""

    model_config = ConfigDict(extra="forbid")

    program_id: ProgramId = Field(..., description="Program identifier.")
    family_counts: dict[str, int] = Field(
        default_factory=dict, description="Assay counts by family."
    )
    dominant_family: str | None = Field(
        default=None, description="Most represented assay family."
    )
    concentration_ratio: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Share of assays in dominant family."
    )
    orthogonal_coverage_ready: bool = Field(
        default=False, description="Whether at least three families are represented."
    )
    notes: list[str] = Field(
        default_factory=list, description="Portfolio balance commentary."
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


class GateCoverageGapReport(JsonModel):
    """Report of review-gate coverage and uncovered gates."""

    model_config = ConfigDict(extra="forbid")

    program_id: ProgramId = Field(..., description="Program identifier.")
    covered_gates: list[str] = Field(
        default_factory=list, description="Gates covered by planned batches."
    )
    uncovered_gates: list[str] = Field(
        default_factory=list, description="Gates in queue with no planned coverage."
    )
    notes: list[str] = Field(
        default_factory=list, description="Coverage interpretation notes."
    )


class AssayContradictionPressure(JsonModel):
    """Contradiction pressure score for each assay in a plan."""

    model_config = ConfigDict(extra="forbid")

    assay_id: AssayId = Field(..., description="Assay identifier.")
    pressure_score: float = Field(
        ..., ge=0.0, le=1.0, description="Contradiction pressure score."
    )
    rationale: list[str] = Field(
        default_factory=list, description="Pressure rationale notes."
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


class OrthogonalConfirmationPlan(JsonModel):
    """Recommendation for orthogonal confirmation assays."""

    model_config = ConfigDict(extra="forbid")

    decision_tag: str = Field(
        ..., min_length=1, description="Decision context evaluated."
    )
    required: bool = Field(
        ..., description="Whether orthogonal confirmation is required."
    )
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
    notes: list[str] = Field(
        default_factory=list, description="Human-readable plan notes."
    )


class UncertaintyReductionPlan(JsonModel):
    """Assay plan focused on reducing decision uncertainty."""

    model_config = ConfigDict(extra="forbid")

    decision_tag: str = Field(
        ..., min_length=1, description="Decision context under uncertainty reduction."
    )
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
    notes: list[str] = Field(
        default_factory=list, description="Plan notes for reviewers."
    )


class NextBestExperiment(JsonModel):
    """Single next-best experiment recommendation."""

    model_config = ConfigDict(extra="forbid")

    assay_id: AssayId = Field(..., description="Recommended assay identifier.")
    prerequisite_assay_ids: list[AssayId] = Field(
        default_factory=list,
        description="Prerequisites that should run first.",
    )
    expected_information_gain: float = Field(
        ..., ge=0.0, le=1.0, description="Expected information gain score."
    )
    rationale: list[str] = Field(
        default_factory=list, description="Short rationale for recommendation."
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


class OrthogonalPolicy(JsonModel):
    """Policy configuration for orthogonal confirmation planning."""

    model_config = ConfigDict(extra="forbid")

    policy_id: str = Field(
        ..., min_length=1, description="Stable orthogonal policy identifier."
    )
    decision_tag: str = Field(
        default="progression",
        min_length=1,
        description="Decision tag under evaluation.",
    )
    minimum_convergence_score: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Minimum acceptable convergence score.",
    )
    required_modalities: list[str] = Field(
        default_factory=lambda: ["literature", "assay", "structure"],
        description="Modalities expected before skipping orthogonal confirmation.",
    )


class ConflictAssayPolicy(JsonModel):
    """Policy for selecting assays to resolve conflicting evidence."""

    model_config = ConfigDict(extra="forbid")

    policy_id: str = Field(
        ..., min_length=1, description="Stable conflict-assay policy identifier."
    )
    max_suggestions: int = Field(
        default=3, ge=1, description="Maximum number of suggested assays."
    )
    blocking_bonus: float = Field(
        default=0.25, ge=0.0, le=1.0, description="Score bonus for blocking assays."
    )
    contradiction_weight: float = Field(
        default=0.3, ge=0.0, le=1.0, description="Weight for contradiction burden."
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
    """Build dependency-aware batches grouped by blocking status and assay family."""
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
    """Build a scientific assay-priority plan that is not execution-ready."""
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
    return AdvisoryAssayPlan(
        program_id=program.program_id,
        open_evidence_gaps=open_gaps,
        recommendations=recommendations,
    )


def build_executable_assay_plan(
    plan: ExperimentPlan,
    *,
    batch_id: BatchId,
    available_sample_kinds: list[str] | None = None,
) -> ExecutableAssayPlan:
    """Convert one planned batch into execution-ready lab instructions."""
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
        *[
            f"review gate pending: {gate_id}"
            for gate_id in batch.blocking_review_gates
        ],
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


def plan_hypothesis_falsification_assays(
    *,
    hypothesis: str,
    intents: list[AssayIntent],
    contradictions: list[str],
    blocked_assay_ids: list[str] | None = None,
) -> HypothesisFalsificationPlan:
    """Rank assays by expected value for falsifying a target hypothesis."""
    blocked = set(blocked_assay_ids or [])
    scores: list[tuple[str, float, list[str]]] = []
    contradiction_pressure = min(1.0, len(contradictions) * 0.2)
    for intent in intents:
        if intent.assay_id in blocked:
            continue
        objective = intent.objective.lower()
        objective_bonus = (
            0.5
            if any(token in objective for token in ["falsif", "counter", "orthogonal"])
            else 0.25
        )
        prereq_penalty = min(0.3, len(intent.prerequisite_assay_ids) * 0.1)
        score = round(
            max(
                0.0, min(objective_bonus + contradiction_pressure - prereq_penalty, 1.0)
            ),
            4,
        )
        reasons = [f"objective={intent.objective}"]
        if contradiction_pressure > 0:
            reasons.append(
                "active evidence contradictions increase falsification value"
            )
        if prereq_penalty > 0:
            reasons.append("prerequisites reduce immediate execution value")
        scores.append((intent.assay_id, score, reasons))
    scores.sort(key=lambda item: item[1], reverse=True)
    return HypothesisFalsificationPlan(
        hypothesis=hypothesis,
        prioritized_assay_ids=[item[0] for item in scores],
        rationale=[
            f"{assay_id}: {', '.join(reasons)}" for assay_id, _, reasons in scores
        ],
    )


def summarize_assay_portfolio_balance(
    plan: ExperimentPlan,
) -> AssayPortfolioBalanceReport:
    """Summarize assay-family balance for an experiment plan."""
    counts: dict[str, int] = {}
    for batch in plan.batches:
        for assay_id in batch.assay_ids:
            sample_kind = batch.assay_sample_kinds.get(assay_id, "other")
            family = assay_family(sample_kind).value
            counts[family] = counts.get(family, 0) + 1
    total = sum(counts.values())
    dominant_family = None
    concentration = 0.0
    if counts and total > 0:
        dominant_family, dominant_count = max(counts.items(), key=lambda item: item[1])
        concentration = round(dominant_count / total, 4)
    orthogonal_coverage_ready = (
        len([family for family, value in counts.items() if value > 0]) >= 3
    )
    notes: list[str] = []
    if dominant_family is not None and concentration >= 0.7:
        notes.append(f"portfolio is heavily concentrated in {dominant_family}")
    if not orthogonal_coverage_ready:
        notes.append("add assays from additional families for orthogonal coverage")
    if not notes:
        notes.append("assay portfolio has balanced modality coverage")
    return AssayPortfolioBalanceReport(
        program_id=plan.program_id,
        family_counts=counts,
        dominant_family=dominant_family,
        concentration_ratio=concentration,
        orthogonal_coverage_ready=orthogonal_coverage_ready,
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


def assess_gate_coverage_gaps(plan: ExperimentPlan) -> GateCoverageGapReport:
    """Assess whether review queue gates are covered by planned batches."""
    covered: set[str] = set()
    for batch in plan.batches:
        covered.update(batch.blocking_review_gates)
    queued = set(plan.review_queue)
    uncovered = sorted(queued - covered)
    notes: list[str] = []
    if uncovered:
        notes.append("some queued review gates have no explicit assay batch coverage")
    else:
        notes.append("all queued review gates are represented in planned batches")
    return GateCoverageGapReport(
        program_id=plan.program_id,
        covered_gates=sorted(covered),
        uncovered_gates=uncovered,
        notes=notes,
    )


def map_assay_contradiction_pressure(
    *,
    intents: list[AssayIntent],
    contradiction_count: int,
    blocked_assay_ids: list[str] | None = None,
) -> list[AssayContradictionPressure]:
    """Map contradiction pressure scores to assay intents."""
    blocked = set(blocked_assay_ids or [])
    base = min(1.0, contradiction_count * 0.2)
    rows: list[AssayContradictionPressure] = []
    for intent in intents:
        score = base
        rationale: list[str] = [f"contradiction_count={contradiction_count}"]
        if intent.prerequisite_assay_ids:
            score = max(0.0, score - 0.1)
            rationale.append("prerequisites reduce immediate contradiction pressure")
        if intent.assay_id in blocked:
            score = max(0.0, score - 0.2)
            rationale.append("assay is blocked in current cycle")
        rows.append(
            AssayContradictionPressure(
                assay_id=intent.assay_id,
                pressure_score=round(max(0.0, min(score, 1.0)), 4),
                rationale=rationale,
            )
        )
    return sorted(rows, key=lambda item: item.pressure_score, reverse=True)


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


def recommend_orthogonal_confirmation(
    program: ProgramSpec,
    bundle: EvidenceBundle,
    *,
    decision_tag: str = "progression",
    minimum_convergence_score: float = 0.5,
    policy: OrthogonalPolicy | None = None,
) -> OrthogonalConfirmationPlan:
    """Recommend orthogonal assays when modality convergence is weak."""
    policy = policy or OrthogonalPolicy(policy_id="default-orthogonal-policy")
    effective_tag = (
        policy.decision_tag if decision_tag == "progression" else decision_tag
    )
    effective_threshold = (
        minimum_convergence_score
        if minimum_convergence_score != 0.5
        else policy.minimum_convergence_score
    )
    triangulation = triangulate_evidence(
        bundle,
        decision_tag=effective_tag,
        required_modalities=policy.required_modalities,
    )
    required = triangulation.convergence_score < effective_threshold or bool(
        triangulation.missing_required_modalities
    )
    suggested = [assay.assay_id for assay in program.assay_panel if not assay.blocking][
        :3
    ]
    return OrthogonalConfirmationPlan(
        decision_tag=effective_tag,
        required=required,
        suggested_assay_ids=suggested if required else [],
    )


def plan_conflict_resolution_assays(
    program: ProgramSpec,
    bundle: EvidenceBundle,
    *,
    policy: ConflictAssayPolicy | None = None,
) -> ConflictResolutionPlan:
    """Recommend assays that can resolve current evidence conflicts."""
    policy = policy or ConflictAssayPolicy(policy_id="default-conflict-assay-policy")
    conflicts = flag_conflicting_evidence(bundle)
    if not conflicts:
        return ConflictResolutionPlan(
            conflict_count=0,
            suggested_assay_ids=[],
            notes=["no active evidence conflicts require assay resolution"],
        )
    contradiction_count = len(conflicts)
    ranked: list[tuple[float, str]] = []
    for assay in program.assay_panel:
        score = contradiction_count * policy.contradiction_weight
        if assay.blocking:
            score += policy.blocking_bonus
        ranked.append((score, assay.assay_id))
    ranked.sort(reverse=True)
    suggested = [assay_id for _, assay_id in ranked[: policy.max_suggestions]]
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
        [
            f"selected top {len(prioritized)} assays by information-gain score for {decision_tag}"
        ]
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
        rationale.append(
            "assay has prerequisite dependencies that should be scheduled first"
        )
    if top.estimated_cost > 1.2:
        rationale.append(
            "assay has elevated execution burden but highest current information gain"
        )
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
            evidence_backlog=evidence_gaps(
                bundle, [need.value for need in program.evidence_needs]
            ),
            assay_backlog=failed_assays,
            notes=[
                "repair assay execution quality before making redesign or progression calls"
            ],
            evidence_trust_score=trust.trust_score,
            promotion_ready_count=assessment.promotion_ready_count,
            technical_failure_count=assessment.technical_or_repro_failures,
        )
    if summary.failed_biological_count > 0:
        return ClosedLoopPlan(
            program_id=program.program_id,
            decision=ProgressDecision.REDESIGN,
            evidence_backlog=evidence_gaps(
                bundle, [need.value for need in program.evidence_needs]
            ),
            assay_backlog=failed_assays,
            notes=[
                "biological failures indicate the candidate hypothesis should be redesigned"
            ],
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

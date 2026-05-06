# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Next-cycle planning and contradiction resolution for lab execution."""

from __future__ import annotations

from pydantic import ConfigDict, Field

from bijux_proteomics.domain.program_spec import ProgramSpec
from bijux_proteomics_foundation import AssayId, JsonModel, ProgramId
from bijux_proteomics_knowledge.memory.models.evidence import (
    EvidenceBundle,
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

from bijux_proteomics_lab.planning.assays import (
    AssayDependency,
    AssayFamily,
    AssayIntent,
    AssayObservation,
    ClosedLoopPlan,
    ExperimentPlan,
    ProgressDecision,
    assay_family,
    build_review_packet,
)
from bijux_proteomics_lab.planning.priorities import prioritize_next_assays
from bijux_proteomics_lab.planning.scheduling import (
    LabCapacity,
    compare_schedule_scenarios,
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

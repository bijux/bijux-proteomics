# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

from bijux_proteomics.domain.assays import AssayRequirement
from bijux_proteomics.domain.program_spec import EvidenceNeed, create_program_spec
from bijux_proteomics.domain.reviews import ReviewGate
from bijux_proteomics_knowledge.memory.models.evidence import (
    EvidenceBundle,
    EvidenceKind,
    EvidenceRecord,
    EvidenceStrength,
)
from bijux_proteomics_lab.outcomes import (
    AssayOutcome,
    AssayResultState,
    ExperimentOutcome,
    RerunPolicy,
)
from bijux_proteomics_lab.planning import (
    AdvisoryAssayPlan,
    AssayDependency,
    AssayFamily,
    AssayIntent,
    AssayObservation,
    AssayPlanKind,
    CandidatePrioritySignal,
    ConflictAssayPolicy,
    ExecutableAssayPlan,
    ExperimentBatch,
    ExperimentPlan,
    FamilyCapacity,
    InstrumentAvailability,
    LabCapacity,
    MaterialInventory,
    MaterialRequirement,
    OrthogonalPolicy,
    PlanningPolicy,
    ProgressDecision,
    align_lab_priority_queue,
    assay_family_priority,
    assess_dependency_integrity,
    assess_gate_coverage_gaps,
    assess_material_constraints,
    build_advisory_assay_plan,
    build_executable_assay_plan,
    build_execution_capacity_advisory,
    build_follow_up_practicality_report,
    build_lab_cycle_brief,
    build_lab_execution_request,
    build_lab_review_packet_bundle,
    build_review_packet,
    build_review_risk_profile,
    build_workflow_batch_outline,
    compare_schedule_scenarios,
    dependency_critical_path,
    dependency_order,
    derive_lab_execution_directive,
    detect_dependency_cycle,
    estimate_assay_execution_burden,
    map_assay_contradiction_pressure,
    plan_conflict_resolution_assays,
    plan_experiment_batches,
    plan_hypothesis_falsification_assays,
    plan_material_reservations,
    plan_uncertainty_reduction_assays,
    prioritize_batches_by_material_feasibility,
    prioritize_next_assays,
    recommend_next_best_experiment,
    recommend_next_cycle,
    recommend_next_cycle_from_outcome,
    recommend_orthogonal_confirmation,
    report_execution_plan_uncertainty,
    schedule_experiment_plan,
    schedule_with_family_capacity,
    score_assay_gate_impact,
    score_assay_information_gain,
    summarize_assay_portfolio_balance,
    summarize_schedule_pressure,
    validate_experiment_plan,
)
from bijux_proteomics_lab.readiness import (
    ControlReadinessSignal,
    EvidenceReadinessSignal,
    OperationalReadinessReport,
    ProvenanceReadinessSignal,
    ReagentAvailability,
    ReviewBacklogSnapshot,
    StaffingAvailability,
    build_operational_readiness_report,
)


def _planning_fixture(name: str) -> dict[str, object]:
    return cast(
        dict[str, object],
        json.loads(
            (
                Path(__file__).resolve().parents[1] / "fixtures" / "planning" / name
            ).read_text(encoding="utf-8")
        ),
    )


def test_align_lab_priority_queue_reconciles_candidate_and_assay_priority() -> None:
    program = create_program_spec(
        program_id="prog-align",
        name="alignment plan",
        objective="align intelligence scoring with the lab queue",
        target_id="target-align",
        target_name="Target Align",
        sequence="ACDEFGHIKLMNPQRSTVWY",
        organism="human",
        mechanism="stabilize the active state",
    )
    program.assay_panel.extend(
        [
            AssayRequirement(
                assay_id="gate-binding",
                purpose="confirm target engagement",
                readout="binding_score",
                sample_kind="biophysical",
                blocking=True,
            ),
            AssayRequirement(
                assay_id="support-expression",
                purpose="check expression robustness",
                readout="yield_mg_per_l",
                sample_kind="expression",
                blocking=False,
            ),
        ]
    )
    program.evidence_needs = [EvidenceNeed.STRUCTURE]
    bundle = EvidenceBundle(bundle_id="bundle-align", target_id="target-align")
    priorities = prioritize_next_assays(program, bundle, [])

    alignment = align_lab_priority_queue(
        program,
        priorities,
        [
            CandidatePrioritySignal(
                candidate_id="cand-1",
                score=0.9,
                assay_ids=["support-expression", "gate-binding"],
                decision_ready=True,
                contradiction_pressure=0.08,
                freshness_pressure=0.04,
                policy_lineage_id="policy-balanced",
            ),
            CandidatePrioritySignal(
                candidate_id="cand-2",
                score=0.3,
                assay_ids=["unknown-assay"],
            ),
            CandidatePrioritySignal(
                candidate_id="cand-3",
                score=0.95,
                assay_ids=["gate-binding"],
                decision_ready=False,
                contradiction_pressure=0.52,
                unresolved_questions=["orthogonal assay remains unresolved"],
                recommended_action="hold candidate until contradictions are resolved",
            ),
            CandidatePrioritySignal(
                candidate_id="cand-4",
                score=0.98,
                assay_ids=["gate-binding"],
                decision_ready=True,
                contradiction_pressure=0.02,
                freshness_pressure=0.01,
                grounding_pressure=0.62,
                grounding_findings=[
                    "knowledge support still depends on one narrow non-lab source family"
                ],
                policy_lineage_id="policy-balanced",
            ),
        ],
    )

    assert alignment.prioritized_assay_ids[0] == "gate-binding"
    assert alignment.unaligned_candidate_ids == ["cand-2"]
    assert alignment.held_candidate_ids == ["cand-3"]
    assert "cand-4" in alignment.skeptical_candidate_ids
    assert (
        alignment.candidate_assay_scores["cand-1:gate-binding"]
        > alignment.candidate_assay_scores["cand-4:gate-binding"]
    )


def test_build_follow_up_practicality_report_blocks_candidates_without_practical_path() -> (
    None
):
    plan = ExperimentPlan(
        program_id="prog-practicality",
        batches=[
            ExperimentBatch(
                batch_id="b1",
                objective="binding batch",
                assay_ids=["gate-binding"],
                priority=1,
                sample_requirements=["biophysical"],
            ),
            ExperimentBatch(
                batch_id="b2",
                objective="cellular batch",
                assay_ids=["cell-response"],
                priority=2,
                sample_requirements=["cellular"],
            ),
        ],
    )

    report = build_follow_up_practicality_report(
        plan,
        LabCapacity(cycle_id="cycle-1", max_batches=1, max_assays_per_batch=2),
        [
            InstrumentAvailability(
                instrument_id="orbitrap",
                available_days=1.0,
                supported_sample_kinds=["biophysical"],
            )
        ],
        [
            CandidatePrioritySignal(
                candidate_id="cand-practical",
                score=0.9,
                assay_ids=["gate-binding"],
                decision_ready=True,
                contradiction_pressure=0.1,
                freshness_pressure=0.05,
                policy_lineage_id="policy-balanced",
            ),
            CandidatePrioritySignal(
                candidate_id="cand-impractical",
                score=0.95,
                assay_ids=["cell-response"],
                decision_ready=False,
                contradiction_pressure=0.52,
                recommended_action="hold candidate until contradictions are resolved",
            ),
            CandidatePrioritySignal(
                candidate_id="cand-thin-grounding",
                score=0.99,
                assay_ids=["gate-binding"],
                decision_ready=True,
                contradiction_pressure=0.04,
                freshness_pressure=0.02,
                grounding_pressure=0.58,
                grounding_findings=[
                    "orthogonal grounding remains missing for the requested follow-up"
                ],
                policy_lineage_id="policy-balanced",
            ),
        ],
        budget_limit=1.5,
    )

    assert report.practical_candidate_ids == ["cand-practical"]
    assert report.impractical_candidate_ids == [
        "cand-impractical",
        "cand-thin-grounding",
    ]
    assert report.executable_batch_ids == ["b1"]
    assert report.blocked_batch_ids == ["b2"]
    assert report.practicality_score == 0.42
    assert any(
        "grounded strongly enough" in blocker for blocker in report.blockers
    )


def test_realistic_proteomics_planning_fixture_exercises_lab_priority_surfaces() -> (
    None
):
    fixture = _planning_fixture("proteomics_lab_planning_fixture.json")
    program_data = fixture["program"]
    assert isinstance(program_data, dict)
    program = create_program_spec(
        program_id=program_data["program_id"],
        name=program_data["name"],
        objective=program_data["objective"],
        target_id=program_data["target_id"],
        target_name=program_data["target_name"],
        sequence=program_data["sequence"],
        organism=program_data["organism"],
        mechanism=program_data["mechanism"],
    )
    evidence_needs = cast(list[str], fixture["evidence_needs"])
    assays = cast(list[dict[str, Any]], fixture["assays"])
    records = cast(list[dict[str, Any]], fixture["records"])
    candidate_signals = cast(list[dict[str, Any]], fixture["candidate_signals"])

    program.evidence_needs = [EvidenceNeed(item) for item in evidence_needs]
    program.assay_panel.extend(AssayRequirement(**assay) for assay in assays)
    bundle = EvidenceBundle(
        bundle_id="bundle-proteomics-lab",
        target_id=program.target.target_id,
        records=[EvidenceRecord(**record) for record in records],
    )

    advisory = build_advisory_assay_plan(program, bundle)
    priorities = prioritize_next_assays(program, bundle, [])
    alignment = align_lab_priority_queue(
        program,
        priorities,
        [CandidatePrioritySignal(**row) for row in candidate_signals],
    )
    capacity_advisory = build_execution_capacity_advisory(
        ExperimentPlan(
            program_id=program.program_id,
            batches=[
                ExperimentBatch(
                    batch_id="b-phospho",
                    objective="run proteomics confirmation assays",
                    assay_ids=["target-engagement-prm", "phosphosite-panel"],
                    priority=1,
                    sample_requirements=["biophysical", "cellular"],
                )
            ],
        ),
        LabCapacity(
            cycle_id="cycle-proteomics",
            max_batches=1,
            max_assays_per_batch=2,
        ),
        [
            InstrumentAvailability(
                instrument_id="orbitrap-exploris",
                available_days=2.0,
                supported_sample_kinds=["biophysical", "cellular"],
            )
        ],
        budget_limit=2.0,
    )

    assert advisory.open_evidence_gaps == ["assay", "pathway"]
    assert alignment.prioritized_assay_ids[0] == "phosphosite-panel"
    assert capacity_advisory.feasible_batch_ids == ["b-phospho"]


def test_constrained_capacity_fixture_keeps_partly_schedulable_follow_up_explicit() -> (
    None
):
    fixture = _planning_fixture("constrained_capacity_follow_up.json")

    report = build_follow_up_practicality_report(
        ExperimentPlan.model_validate(fixture["plan"]),
        LabCapacity.model_validate(fixture["capacity"]),
        [
            InstrumentAvailability.model_validate(item)
            for item in cast(
                list[dict[str, object]], fixture["instrument_availability"]
            )
        ],
        [
            CandidatePrioritySignal.model_validate(item)
            for item in cast(list[dict[str, object]], fixture["candidate_signals"])
        ],
        budget_limit=cast(float, fixture["budget_limit"]),
        estimated_batch_cost=cast(float, fixture["estimated_batch_cost"]),
        family_capacities=[
            FamilyCapacity.model_validate(item)
            for item in cast(list[dict[str, object]], fixture["family_capacities"])
        ],
        material_requirements=[
            MaterialRequirement.model_validate(item)
            for item in cast(list[dict[str, object]], fixture["material_requirements"])
        ],
        inventory=[
            MaterialInventory.model_validate(item)
            for item in cast(list[dict[str, object]], fixture["inventory"])
        ],
    )

    assert report.practical_candidate_ids == ["cand-hybrid"]
    assert report.impractical_candidate_ids == ["cand-cellular"]
    assert report.constrained_candidate_ids == ["cand-hybrid"]
    assert report.material_blocked_candidate_ids == []
    assert any("schedule pressure" in note for note in report.schedule_pressure_notes)


def test_score_assay_gate_impact_prioritizes_blocking_gates() -> None:
    plan = ExperimentPlan(
        program_id="prog-1",
        review_queue=[],
        evidence_gaps=[],
        batches=[
            ExperimentBatch(
                batch_id="b1",
                objective="gate-critical batch",
                assay_ids=["a1"],
                blocking_review_gates=["gate-a", "gate-b"],
                priority=1,
            ),
            ExperimentBatch(
                batch_id="b2",
                objective="support batch",
                assay_ids=["a2"],
                blocking_review_gates=[],
                priority=4,
            ),
        ],
    )

    scores = score_assay_gate_impact(plan)

    assert scores[0].assay_id == "a1"
    assert scores[0].impact_score > scores[1].impact_score


def test_estimate_assay_execution_burden_accounts_for_sample_kind_and_gates() -> None:
    plan = ExperimentPlan(
        program_id="prog-1",
        review_queue=[],
        evidence_gaps=[],
        batches=[
            ExperimentBatch(
                batch_id="b1",
                objective="cell assay batch",
                assay_ids=["cell-a"],
                blocking_review_gates=["gate-a"],
                priority=1,
                sample_requirements=["cell-line", "compound"],
                assay_sample_kinds={"cell-a": "cellular"},
            ),
            ExperimentBatch(
                batch_id="b2",
                objective="simple expression batch",
                assay_ids=["exp-a"],
                blocking_review_gates=[],
                priority=3,
                sample_requirements=["protein"],
                assay_sample_kinds={"exp-a": "expression"},
            ),
        ],
    )

    burden = estimate_assay_execution_burden(plan)

    assert burden[0].assay_id == "cell-a"
    assert burden[0].burden_score > burden[1].burden_score


def test_build_lab_cycle_brief_combines_impact_burden_and_priorities() -> None:
    program = create_program_spec(
        program_id="prog-brief",
        name="brief test",
        objective="build cycle brief",
        target_id="target-brief",
        target_name="Target",
        sequence="ACDEFGHIKLMNPQRSTVWY",
        organism="human",
        mechanism="stabilize function",
    )
    program.assay_panel.append(
        AssayRequirement(
            assay_id="binding-a",
            purpose="confirm binding",
            readout="binding_score",
            sample_kind="biophysical",
            blocking=True,
        )
    )
    bundle = EvidenceBundle(bundle_id="bundle-brief", target_id="target-brief")
    plan = ExperimentPlan(
        program_id="prog-brief",
        review_queue=[],
        evidence_gaps=[],
        batches=[
            ExperimentBatch(
                batch_id="b1",
                objective="critical batch",
                assay_ids=["binding-a"],
                blocking_review_gates=["gate-1"],
                priority=1,
                sample_requirements=["protein"],
                assay_sample_kinds={"binding-a": "biophysical"},
            )
        ],
    )

    brief = build_lab_cycle_brief(program, plan, bundle, observations=[])

    assert brief.program_id == "prog-brief"
    assert brief.top_gate_impacts
    assert brief.next_assay_priorities


def test_score_assay_information_gain_reflects_gate_and_conflict_pressure() -> None:
    breakdown = score_assay_information_gain(
        assay_id="assay-priority",
        blocking=True,
        readiness_ready=False,
        trust_score=0.5,
        contradiction_count=2,
    )

    assert breakdown.decision_gate_impact == 0.9
    assert breakdown.contradiction_resolution_value > 0.0
    assert 0.0 <= breakdown.final_score <= 1.0


def test_prioritize_next_assays_prefers_blocking_and_unobserved_work() -> None:
    program = create_program_spec(
        program_id="prog-priority",
        name="priority model",
        objective="rank next assays by information gain",
        target_id="target-priority",
        target_name="Target Priority",
        sequence="ACDEFGHIKLMNPQRSTVWY",
        organism="human",
        mechanism="drive next experiment selection by decision impact",
    )
    program.assay_panel.extend(
        [
            AssayRequirement(
                assay_id="a-block",
                purpose="blocking readout",
                readout="binding_score",
                sample_kind="biophysical",
                blocking=True,
            ),
            AssayRequirement(
                assay_id="a-support",
                purpose="supporting readout",
                readout="yield",
                sample_kind="expression",
                blocking=False,
            ),
        ]
    )
    bundle = EvidenceBundle(bundle_id="bundle-priority", target_id="target-priority")

    ranked = prioritize_next_assays(
        program,
        bundle,
        [
            AssayObservation(
                assay_id="a-support", metric="yield", value=1.0, passed=True
            )
        ],
    )

    assert ranked[0].assay_id == "a-block"
    assert ranked[0].estimated_cost > 0


def test_score_assay_information_gain_supports_custom_planning_policy() -> None:
    breakdown = score_assay_information_gain(
        assay_id="assay-policy",
        blocking=False,
        readiness_ready=True,
        trust_score=0.8,
        contradiction_count=0,
        policy=PlanningPolicy(
            policy_id="aggressive-policy",
            uncertainty_weight=0.5,
            contradiction_weight=0.1,
            falsification_weight=0.1,
            gate_impact_weight=0.1,
            orthogonal_weight=0.2,
            non_blocking_burden_penalty=0.05,
        ),
    )

    assert breakdown.final_score > 0.0

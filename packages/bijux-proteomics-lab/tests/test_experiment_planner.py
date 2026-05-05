# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

from bijux_proteomics.domain.assays import AssayRequirement
from bijux_proteomics.domain.program_spec import EvidenceNeed, create_program_spec
from bijux_proteomics.domain.reviews import ReviewGate
from bijux_proteomics_knowledge.memory.evidence import (
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
    OperationalReadinessReport,
    ReagentAvailability,
    ReviewBacklogSnapshot,
    StaffingAvailability,
    build_operational_readiness_report,
)


def _planning_fixture(name: str) -> dict[str, object]:
    return cast(
        dict[str, object],
        json.loads(
            (Path(__file__).parent / "fixtures" / "planning" / name).read_text(
                encoding="utf-8"
            )
        ),
    )


def test_plan_experiment_batches_prioritizes_blocking_assays() -> None:
    program = create_program_spec(
        program_id="prog-1",
        name="binder recovery",
        objective="recover binding and reduce aggregation",
        target_id="target-1",
        target_name="Target",
        sequence="ACDEFGHIKLMNPQRSTVWY",
        organism="human",
        mechanism="stabilize a binding competent state",
    )
    program.review_gates.append(
        ReviewGate(
            gate_id="synthesis-review",
            name="Synthesis review",
            required_roles=["scientist"],
            decision_inputs=["evidence_bundle"],
            blocking=True,
        )
    )
    program.assay_panel.extend(
        [
            AssayRequirement(
                assay_id="primary-binding",
                purpose="confirm target engagement",
                readout="binding_score",
                sample_kind="biophysical",
                blocking=True,
            ),
            AssayRequirement(
                assay_id="expression-screen",
                purpose="check manufacturability",
                readout="yield_mg_per_l",
                sample_kind="expression",
                blocking=False,
            ),
        ]
    )
    bundle = EvidenceBundle(
        bundle_id="bundle-1",
        target_id="target-1",
        records=[
            EvidenceRecord(
                evidence_id="lit-1",
                kind=EvidenceKind.LITERATURE,
                title="Paper",
                source="PMID:1",
                claim="Target is tractable.",
                confidence=0.8,
                strength=EvidenceStrength.SUPPORTING,
            )
        ],
    )

    plan = plan_experiment_batches(
        program,
        bundle,
        dependencies=[
            AssayDependency(
                assay_id="expression-screen", requires_assay_id="primary-binding"
            )
        ],
    )

    assert [batch.batch_id for batch in plan.batches] == [
        "prog-1-biophysical-gate",
        "prog-1-expression-support",
    ]
    assert plan.review_queue == ["synthesis-review"]
    assert "structure" in plan.evidence_gaps
    assert AssayFamily.BIOPHYSICAL.value in plan.batches[0].batch_id


def test_build_review_packet_marks_failed_assays_as_blockers() -> None:
    program = create_program_spec(
        program_id="prog-1",
        name="binder recovery",
        objective="recover binding and reduce aggregation",
        target_id="target-1",
        target_name="Target",
        sequence="ACDEFGHIKLMNPQRSTVWY",
        organism="human",
        mechanism="stabilize a binding competent state",
    )
    bundle = EvidenceBundle(
        bundle_id="bundle-1",
        target_id="target-1",
        records=[
            EvidenceRecord(
                evidence_id="lit-1",
                kind=EvidenceKind.LITERATURE,
                title="Paper",
                source="PMID:1",
                claim="Target is tractable.",
                confidence=0.9,
                strength=EvidenceStrength.SUPPORTING,
            ),
            EvidenceRecord(
                evidence_id="assay-1",
                kind=EvidenceKind.ASSAY,
                title="Assay",
                source="lab",
                claim="A first candidate retains activity.",
                confidence=0.8,
                strength=EvidenceStrength.DECISIVE,
            ),
            EvidenceRecord(
                evidence_id="structure-1",
                kind=EvidenceKind.STRUCTURE,
                title="Structure",
                source="model",
                claim="Fold remains plausible.",
                confidence=0.8,
                strength=EvidenceStrength.SUPPORTING,
            ),
        ],
    )

    packet = build_review_packet(
        program,
        bundle,
        [
            AssayObservation(
                assay_id="primary-binding",
                metric="binding_score",
                value=0.42,
                passed=False,
            )
        ],
    )

    assert packet.ready_for_synthesis is False
    assert "failed assays: primary-binding" in packet.blocking_findings
    assert packet.advancement_evidence.evidence_ids == [
        "lit-1",
        "structure-1",
        "assay-1",
    ]
    assert packet.advancement_evidence.missing_evidence_kinds == []


def test_build_lab_review_packet_bundle_carries_rationale_and_open_risks() -> None:
    program = create_program_spec(
        program_id="prog-review-bundle",
        name="review bundle",
        objective="bundle review rationale and unresolved risks",
        target_id="target-review",
        target_name="Target Review",
        sequence="ACDEFGHIKLMNPQRSTVWY",
        organism="human",
        mechanism="stabilize a productive conformation",
    )
    program.evidence_needs = [EvidenceNeed.LITERATURE, EvidenceNeed.STRUCTURE]
    program.assay_panel.append(
        AssayRequirement(
            assay_id="gate-binding",
            purpose="confirm target engagement",
            readout="binding_score",
            sample_kind="biophysical",
            blocking=True,
        )
    )
    bundle = EvidenceBundle(
        bundle_id="bundle-review",
        target_id="target-review",
        records=[
            EvidenceRecord(
                evidence_id="lit-1",
                kind=EvidenceKind.LITERATURE,
                title="Paper",
                source="PMID:1",
                claim="Literature supports tractability.",
                confidence=0.9,
                strength=EvidenceStrength.SUPPORTING,
            )
        ],
    )

    packet_bundle = build_lab_review_packet_bundle(program, bundle, [])

    assert packet_bundle.assay_rationale_by_id["gate-binding"][0] == (
        "confirm target engagement"
    )
    assert packet_bundle.target_evidence_ids == ["lit-1"]
    assert "structure" in packet_bundle.unresolved_risks


def test_build_advisory_assay_plan_stays_scientific_and_non_executable() -> None:
    program = create_program_spec(
        program_id="prog-advisory",
        name="advisory plan",
        objective="separate scientific advice from execution directives",
        target_id="target-advisory",
        target_name="Target Advisory",
        sequence="ACDEFGHIKLMNPQRSTVWY",
        organism="human",
        mechanism="stabilize a productive state",
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
    program.evidence_needs = [EvidenceNeed.STRUCTURE, EvidenceNeed.ASSAY]

    plan = build_advisory_assay_plan(program)

    assert isinstance(plan, AdvisoryAssayPlan)
    assert plan.plan_kind is AssayPlanKind.ADVISORY
    assert plan.executable is False
    assert plan.recommendations[0].blocking is True
    assert [mapping.evidence_need for mapping in plan.evidence_need_actions] == [
        "structure",
        "assay",
    ]
    assert plan.evidence_need_actions[0].assay_ids == ["gate-binding"]
    assert plan.evidence_need_actions[0].sample_kinds == ["biophysical"]
    assert (
        "prepare biophysical material for gate-binding"
        in plan.evidence_need_actions[0].wet_lab_actions
    )


def test_build_executable_assay_plan_requires_operational_readiness() -> None:
    plan = ExperimentPlan(
        program_id="prog-exec",
        review_queue=["gate-a"],
        evidence_gaps=[],
        batches=[
            ExperimentBatch(
                batch_id="batch-exec",
                objective="execute the gate assay",
                assay_ids=["gate-binding"],
                blocking_review_gates=["gate-a"],
                priority=1,
                sample_requirements=["protein"],
                assay_sample_kinds={"gate-binding": "biophysical"},
            )
        ],
    )

    blocked = build_executable_assay_plan(
        plan,
        batch_id="batch-exec",
        available_sample_kinds=[],
    )
    ready = build_executable_assay_plan(
        plan,
        batch_id="batch-exec",
        available_sample_kinds=["protein"],
    )

    assert isinstance(blocked, ExecutableAssayPlan)
    assert blocked.plan_kind is AssayPlanKind.EXECUTABLE
    assert blocked.ready_for_execution is False
    assert "review gate pending: gate-a" in blocked.blocked_by
    assert "missing sample kind: protein" in blocked.blocked_by
    assert ready.instructions[0].instruction_id == "batch-exec:gate-binding"


def test_build_lab_execution_request_preserves_review_evidence_and_instructions() -> (
    None
):
    program = create_program_spec(
        program_id="prog-handoff",
        name="handoff plan",
        objective="carry computational review into a lab request",
        target_id="target-handoff",
        target_name="Target Handoff",
        sequence="ACDEFGHIKLMNPQRSTVWY",
        organism="human",
        mechanism="stabilize an active conformation",
    )
    program.evidence_needs = [EvidenceNeed.LITERATURE, EvidenceNeed.STRUCTURE]
    bundle = EvidenceBundle(
        bundle_id="bundle-handoff",
        target_id="target-handoff",
        records=[
            EvidenceRecord(
                evidence_id="lit-1",
                kind=EvidenceKind.LITERATURE,
                title="Paper",
                source="PMID:1",
                claim="Literature supports tractability.",
                confidence=0.9,
                strength=EvidenceStrength.SUPPORTING,
            ),
            EvidenceRecord(
                evidence_id="structure-1",
                kind=EvidenceKind.STRUCTURE,
                title="Model",
                source="AlphaFold",
                claim="Fold is compatible with binding.",
                confidence=0.8,
                strength=EvidenceStrength.SUPPORTING,
            ),
        ],
    )
    review_packet = build_review_packet(program, bundle, [])
    executable_plan = ExecutableAssayPlan(
        program_id=program.program_id,
        batch_id="batch-handoff",
        instructions=[],
        blocked_by=[],
        ready_for_execution=True,
    )

    request = build_lab_execution_request(review_packet, executable_plan)

    assert request.evidence_ids == ["lit-1", "structure-1"]
    assert request.batch_id == "batch-handoff"
    assert request.scientific_rationale
    assert request.unresolved_risks == [
        "not enough decisive evidence for an irreversible decision"
    ]
    assert request.ready_for_lab_review is False


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
        ],
    )

    assert alignment.prioritized_assay_ids[0] == "gate-binding"
    assert alignment.unaligned_candidate_ids == ["cand-2"]
    assert alignment.held_candidate_ids == ["cand-3"]


def test_build_execution_capacity_advisory_combines_budget_and_instrument_pressure() -> (
    None
):
    plan = ExperimentPlan(
        program_id="prog-capacity",
        batches=[
            ExperimentBatch(
                batch_id="b1",
                objective="binding batch",
                assay_ids=["a1"],
                priority=1,
                sample_requirements=["biophysical"],
            ),
            ExperimentBatch(
                batch_id="b2",
                objective="cellular batch",
                assay_ids=["a2"],
                priority=2,
                sample_requirements=["cellular"],
            ),
        ],
    )

    advisory = build_execution_capacity_advisory(
        plan,
        LabCapacity(cycle_id="cycle-1", max_batches=1, max_assays_per_batch=2),
        [
            InstrumentAvailability(
                instrument_id="orbitrap",
                available_days=1.0,
                supported_sample_kinds=["biophysical"],
            )
        ],
        budget_limit=1.5,
    )

    assert advisory.feasible_batch_ids == ["b1"]
    assert advisory.deferred_batch_ids == ["b2"]
    assert advisory.deferred_reasons == {
        "b2": "cycle batch capacity exhausted",
    }
    assert advisory.estimated_total_cost == 1.15
    assert advisory.budget_remaining == 0.35
    assert advisory.practicality_score == 0.42


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
        ],
        budget_limit=1.5,
    )

    assert report.practical_candidate_ids == ["cand-practical"]
    assert report.impractical_candidate_ids == ["cand-impractical"]
    assert report.executable_batch_ids == ["b1"]
    assert report.blocked_batch_ids == ["b2"]
    assert report.practicality_score == 0.42


def test_build_operational_readiness_report_combines_budget_staffing_and_backlog() -> (
    None
):
    plan = ExperimentPlan(
        program_id="prog-readiness",
        batches=[
            ExperimentBatch(
                batch_id="b1",
                objective="binding batch",
                assay_ids=["a1"],
                priority=1,
                sample_requirements=["biophysical"],
            ),
            ExperimentBatch(
                batch_id="b2",
                objective="cellular batch",
                assay_ids=["a2"],
                priority=2,
                sample_requirements=["cellular"],
            ),
        ],
    )

    report = build_operational_readiness_report(
        plan,
        capacity=LabCapacity(
            cycle_id="cycle-readiness",
            max_batches=1,
            max_assays_per_batch=2,
        ),
        instrument_availability=[
            InstrumentAvailability(
                instrument_id="orbitrap",
                available_days=1.0,
                supported_sample_kinds=["biophysical"],
            )
        ],
        reagent_inventory=[
            ReagentAvailability(
                material_id="protein",
                available_units=0.5,
                minimum_units=1.0,
                unit="mg",
                lead_time_days=10.0,
            )
        ],
        staffing=[
            StaffingAvailability(
                role_name="mass-spec-operator",
                available_operators=0,
                required_operators=1,
                available_operator_days=0.0,
            )
        ],
        backlog=ReviewBacklogSnapshot(
            queued_review_entries=4,
            blocking_gate_ids=("gate-a",),
            deferred_batch_ids=("b3",),
            oldest_entry_days=9.0,
        ),
        budget_limit=1.5,
    )

    assert isinstance(report, OperationalReadinessReport)
    assert report.ready_for_execution is False
    assert report.deferred_batch_ids[:2] == ["b2", "b3"]
    assert report.blocking_material_ids == ["protein"]
    assert report.understaffed_roles == ["mass-spec-operator"]
    assert report.long_lead_material_ids == ["protein"]
    assert report.backlog_pressure_score > 0.5
    assert any(
        "blocking review gates remain queued" in note for note in report.risk_notes
    )


def test_report_execution_plan_uncertainty_makes_blockers_explicit() -> None:
    executable_plan = ExecutableAssayPlan(
        program_id="prog-uncertainty",
        batch_id="batch-uncertainty",
        instructions=[],
        blocked_by=["review gate pending: gate-a"],
        ready_for_execution=False,
    )

    report = report_execution_plan_uncertainty(
        executable_plan,
        open_evidence_gaps=["structure"],
    )

    assert "review gate pending: gate-a" in report.uncertainty_sources
    assert "open evidence gap: structure" in report.uncertainty_sources
    assert report.readiness_confidence < 1.0


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


def test_build_workflow_batch_outline_separates_gate_and_support_assays() -> None:
    program = create_program_spec(
        program_id="prog-outline",
        name="workflow outline",
        objective="tie scientific workflow to lab batch ordering",
        target_id="target-outline",
        target_name="Target Outline",
        sequence="ACDEFGHIKLMNPQRSTVWY",
        organism="human",
        mechanism="stabilize target state",
    )
    program.assay_panel.extend(
        [
            AssayRequirement(
                assay_id="assay-primary-binding",
                purpose="confirm target engagement",
                readout="binding_score",
                sample_kind="biophysical",
                blocking=True,
            ),
            AssayRequirement(
                assay_id="assay-expression-screen",
                purpose="check manufacturability",
                readout="yield_mg_per_l",
                sample_kind="expression",
                blocking=False,
            ),
        ]
    )
    program.review_gates.append(
        ReviewGate(
            gate_id="review-pre-synthesis",
            name="Pre-synthesis review",
            required_roles=["scientist"],
            decision_inputs=["assay-primary-binding"],
            blocking=True,
        )
    )
    bundle = EvidenceBundle(
        bundle_id="bundle-outline",
        target_id="target-outline",
        records=[
            EvidenceRecord(
                evidence_id="lit-1",
                kind=EvidenceKind.LITERATURE,
                title="Paper",
                source="PMID:1",
                claim="Target is tractable.",
                confidence=0.8,
                strength=EvidenceStrength.SUPPORTING,
            )
        ],
    )

    outline = build_workflow_batch_outline(program, bundle)

    assert outline.gate_assay_ids == ["assay-primary-binding"]
    assert outline.support_assay_ids == ["assay-expression-screen"]
    assert outline.review_gate_ids == ["review-pre-synthesis"]
    assert "structure" in outline.missing_evidence_needs


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


def test_plan_hypothesis_falsification_assays_prioritizes_counter_assays() -> None:
    plan = plan_hypothesis_falsification_assays(
        hypothesis="binder stability mechanism is causal",
        intents=[
            AssayIntent(
                assay_id="a1",
                objective="orthogonal counter-check for mechanism",
                prerequisite_assay_ids=[],
            ),
            AssayIntent(
                assay_id="a2",
                objective="supporting readout",
                prerequisite_assay_ids=["a1"],
            ),
        ],
        contradictions=["activity increased while engagement dropped"],
    )

    assert plan.prioritized_assay_ids[0] == "a1"


def test_summarize_assay_portfolio_balance_flags_concentration() -> None:
    plan = ExperimentPlan(
        program_id="prog-balance",
        batches=[
            ExperimentBatch(
                batch_id="b1",
                objective="binding sweep",
                assay_ids=["a1", "a2", "a3"],
                priority=1,
                assay_sample_kinds={
                    "a1": "biophysical",
                    "a2": "biophysical",
                    "a3": "biophysical",
                },
            ),
            ExperimentBatch(
                batch_id="b2",
                objective="small expression check",
                assay_ids=["a4"],
                priority=2,
                assay_sample_kinds={"a4": "expression"},
            ),
        ],
    )

    report = summarize_assay_portfolio_balance(plan)

    assert report.dominant_family == "biophysical"
    assert report.concentration_ratio >= 0.7
    assert report.orthogonal_coverage_ready is False


def test_plan_material_reservations_marks_infeasible_allocations() -> None:
    plan = ExperimentPlan(
        program_id="prog-mat",
        batches=[
            ExperimentBatch(
                batch_id="b1",
                objective="reserve",
                assay_ids=["a1"],
                priority=1,
                sample_requirements=["protein"],
            )
        ],
    )
    reservations = plan_material_reservations(
        plan,
        requirements=[
            MaterialRequirement(
                material_id="mat-1",
                sample_kind="protein",
                minimum_units=10.0,
                unit="mg",
            )
        ],
        inventory=[MaterialInventory(material_id="mat-1", available_units=4.0)],
    )

    assert reservations[0].feasible is False
    assert reservations[0].reserved_units == 4.0


def test_derive_lab_execution_directive_holds_on_technical_failure() -> None:
    directive = derive_lab_execution_directive(
        ExperimentOutcome(
            batch_id="b1",
            assay_outcomes=[
                AssayOutcome(
                    assay_id="a1",
                    passed=False,
                    result_state=AssayResultState.FAILED_TECHNICAL,
                    observation_summary="instrument drift",
                )
            ],
            rerun_policy=RerunPolicy.NEVER,
        )
    )

    assert directive.decision is ProgressDecision.HOLD
    assert any("technical" in action for action in directive.immediate_actions)


def test_assess_gate_coverage_gaps_reports_uncovered_queue_gates() -> None:
    plan = ExperimentPlan(
        program_id="prog-gate-gap",
        review_queue=["gate-a", "gate-b"],
        batches=[
            ExperimentBatch(
                batch_id="b1",
                objective="covers gate a",
                assay_ids=["a1"],
                blocking_review_gates=["gate-a"],
                priority=1,
            )
        ],
    )

    report = assess_gate_coverage_gaps(plan)

    assert report.uncovered_gates == ["gate-b"]


def test_map_assay_contradiction_pressure_orders_highest_pressure_first() -> None:
    rows = map_assay_contradiction_pressure(
        intents=[
            AssayIntent(
                assay_id="a1",
                objective="resolve contradiction",
                prerequisite_assay_ids=[],
            ),
            AssayIntent(
                assay_id="a2",
                objective="secondary check",
                prerequisite_assay_ids=["a1"],
            ),
        ],
        contradiction_count=3,
    )

    assert rows[0].assay_id == "a1"
    assert rows[0].pressure_score >= rows[1].pressure_score


def test_compare_schedule_scenarios_recommends_lowest_deferred_assay_load() -> None:
    plan = ExperimentPlan(
        program_id="prog-sim",
        batches=[
            ExperimentBatch(
                batch_id="b1",
                objective="batch",
                assay_ids=["a1", "a2"],
                priority=1,
            )
        ],
    )
    comparison = compare_schedule_scenarios(
        plan,
        scenarios=[
            LabCapacity(cycle_id="tight", max_batches=1, max_assays_per_batch=1),
            LabCapacity(cycle_id="relaxed", max_batches=1, max_assays_per_batch=3),
        ],
    )

    assert comparison.recommended_scenario_id == "relaxed"


def test_build_review_risk_profile_classifies_high_risk_conflict_states() -> None:
    profile = build_review_risk_profile(
        trust_score=0.45,
        conflict_count=1,
        triangulation_score=0.3,
    )

    assert profile.risk_level == "high"


def test_build_review_packet_blocks_qc_warning_even_if_passed() -> None:
    program = create_program_spec(
        program_id="prog-qc",
        name="qc warning",
        objective="block warning observations",
        target_id="target-qc",
        target_name="Target",
        sequence="ACDEFGHIKLMNPQRSTVWY",
        organism="human",
        mechanism="gate quality signals",
    )
    bundle = EvidenceBundle(bundle_id="bundle-qc", target_id="target-qc")
    packet = build_review_packet(
        program,
        bundle,
        [
            AssayObservation(
                assay_id="assay-qc",
                metric="binding_score",
                value=0.9,
                passed=True,
                qc_state="warning",
                interpretation_confidence=0.95,
            )
        ],
    )

    assert packet.ready_for_synthesis is False
    assert any("assay-qc" in finding for finding in packet.blocking_findings)


def test_recommend_next_cycle_requests_redesign_after_failed_assay() -> None:
    program = create_program_spec(
        program_id="prog-1",
        name="binder recovery",
        objective="recover binding and reduce aggregation",
        target_id="target-1",
        target_name="Target",
        sequence="ACDEFGHIKLMNPQRSTVWY",
        organism="human",
        mechanism="stabilize a binding competent state",
    )
    program.assay_panel.append(
        AssayRequirement(
            assay_id="primary-binding",
            purpose="confirm target engagement",
            readout="binding_score",
            sample_kind="biophysical",
            blocking=True,
        )
    )
    bundle = EvidenceBundle(
        bundle_id="bundle-1",
        target_id="target-1",
        records=[
            EvidenceRecord(
                evidence_id="lit-1",
                kind=EvidenceKind.LITERATURE,
                title="Paper",
                source="PMID:1",
                claim="Target is tractable.",
                confidence=0.9,
                strength=EvidenceStrength.SUPPORTING,
            ),
            EvidenceRecord(
                evidence_id="assay-1",
                kind=EvidenceKind.ASSAY,
                title="Assay",
                source="lab",
                claim="A first candidate retains activity.",
                confidence=0.8,
                strength=EvidenceStrength.DECISIVE,
            ),
            EvidenceRecord(
                evidence_id="structure-1",
                kind=EvidenceKind.STRUCTURE,
                title="Structure",
                source="model",
                claim="Fold remains plausible.",
                confidence=0.8,
                strength=EvidenceStrength.SUPPORTING,
            ),
        ],
    )

    plan = recommend_next_cycle(
        program,
        bundle,
        [
            AssayObservation(
                assay_id="primary-binding",
                metric="binding_score",
                value=0.42,
                passed=False,
            )
        ],
    )

    assert plan.decision is ProgressDecision.REDESIGN
    assert plan.assay_backlog == ["primary-binding"]


def test_recommend_next_cycle_redesigns_when_evidence_trust_is_too_low() -> None:
    program = create_program_spec(
        program_id="prog-2",
        name="trust weighted cycle",
        objective="hold weak evidence out of progression",
        target_id="target-2",
        target_name="Target",
        sequence="ACDEFGHIKLMNPQRSTVWY",
        organism="human",
        mechanism="use evidence trust in the loop",
    )
    bundle = EvidenceBundle(
        bundle_id="bundle-low-trust",
        target_id="target-2",
        records=[
            EvidenceRecord(
                evidence_id="note-1",
                kind=EvidenceKind.LITERATURE,
                title="Weak note",
                source="PMID:weak",
                claim="The target may matter.",
                confidence=0.2,
                strength=EvidenceStrength.EXPLORATORY,
            )
        ],
    )

    plan = recommend_next_cycle(program, bundle, [])

    assert plan.decision is ProgressDecision.REDESIGN
    assert plan.evidence_trust_score < 0.5


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


def test_schedule_experiment_plan_respects_batch_and_assay_capacity() -> None:
    plan = ExperimentPlan(
        program_id="prog-1",
        batches=[
            ExperimentBatch(
                batch_id="batch-1",
                objective="blocking",
                assay_ids=["a1", "a2", "a3"],
                priority=1,
            ),
            ExperimentBatch(
                batch_id="batch-2",
                objective="supporting",
                assay_ids=["b1"],
                priority=2,
            ),
        ],
    )

    scheduled = schedule_experiment_plan(
        plan,
        LabCapacity(cycle_id="cycle-1", max_batches=1, max_assays_per_batch=2),
        dependencies=[AssayDependency(assay_id="a2", requires_assay_id="a1")],
    )

    assert scheduled.scheduled_batches[0].assay_ids == ["a1", "a2"]
    assert scheduled.scheduled_batches[0].deferred_assay_ids == ["a3"]
    assert scheduled.unscheduled_batches == ["batch-2"]


def test_summarize_schedule_pressure_reports_utilization_and_deferred_assays() -> None:
    plan = ExperimentPlan(
        program_id="prog-pressure",
        batches=[
            ExperimentBatch(
                batch_id="batch-1",
                objective="blocking",
                assay_ids=["a1", "a2", "a3"],
                priority=1,
            )
        ],
    )
    capacity = LabCapacity(
        cycle_id="cycle-pressure", max_batches=1, max_assays_per_batch=2
    )
    scheduled = schedule_experiment_plan(plan, capacity)
    report = summarize_schedule_pressure(scheduled, capacity)

    assert report.cycle_id == "cycle-pressure"
    assert report.assay_slot_utilization == 1.0
    assert report.deferred_assay_count == 1


def test_prioritize_batches_by_material_feasibility_promotes_ready_batches() -> None:
    plan = ExperimentPlan(
        program_id="prog-material",
        batches=[
            ExperimentBatch(
                batch_id="batch-ready",
                objective="ready",
                assay_ids=["a1"],
                priority=1,
                sample_requirements=["protein"],
            ),
            ExperimentBatch(
                batch_id="batch-blocked",
                objective="blocked",
                assay_ids=["a2"],
                priority=2,
                sample_requirements=["cells"],
            ),
        ],
    )
    ranked = prioritize_batches_by_material_feasibility(
        plan,
        requirements=[
            MaterialRequirement(
                material_id="protein-stock",
                sample_kind="protein",
                minimum_units=1,
                unit="mg",
            ),
            MaterialRequirement(
                material_id="cell-stock",
                sample_kind="cells",
                minimum_units=10,
                unit="ml",
            ),
        ],
        inventory=[
            MaterialInventory(material_id="protein-stock", available_units=5),
            MaterialInventory(material_id="cell-stock", available_units=2),
        ],
    )

    assert ranked[0].batch_id == "batch-ready"
    assert ranked[1].material_ready is False


def test_validate_experiment_plan_reports_duplicate_and_empty_batches() -> None:
    issues = validate_experiment_plan(
        ExperimentPlan(
            program_id="prog-validate",
            batches=[
                ExperimentBatch(
                    batch_id="b1", objective="o1", assay_ids=["a1"], priority=2
                ),
                ExperimentBatch(
                    batch_id="b1", objective="o2", assay_ids=[], priority=1
                ),
            ],
        )
    )

    assert any(issue.code == "duplicate-batch-id" for issue in issues)
    assert any(issue.code == "empty-assay-batch" for issue in issues)


def test_assess_dependency_integrity_reports_unknown_and_self_edges() -> None:
    report = assess_dependency_integrity(
        ["a1", "a2"],
        [
            AssayDependency(assay_id="a2", requires_assay_id="a1"),
            AssayDependency(assay_id="a3", requires_assay_id="a1"),
            AssayDependency(assay_id="a2", requires_assay_id="a9"),
            AssayDependency(assay_id="a1", requires_assay_id="a1"),
        ],
    )

    assert report.unknown_assay_ids == ["a3"]
    assert report.unknown_prerequisite_ids == ["a9"]
    assert report.self_dependency_assay_ids == ["a1"]
    assert report.cycle_report.has_cycle is False


def test_detect_dependency_cycle_reports_cycle_nodes() -> None:
    cycle_report = detect_dependency_cycle(
        ["a1", "a2", "a3"],
        [
            AssayDependency(assay_id="a1", requires_assay_id="a2"),
            AssayDependency(assay_id="a2", requires_assay_id="a3"),
            AssayDependency(assay_id="a3", requires_assay_id="a1"),
        ],
    )

    assert cycle_report.has_cycle is True
    assert cycle_report.cycle_assay_ids == ["a1", "a2", "a3"]


def test_dependency_order_ignores_invalid_edges_and_keeps_valid_prerequisites() -> None:
    ordered = dependency_order(
        ["a1", "a2", "a3"],
        [
            AssayDependency(assay_id="a2", requires_assay_id="a1"),
            AssayDependency(assay_id="a3", requires_assay_id="a9"),
            AssayDependency(assay_id="a1", requires_assay_id="a1"),
        ],
    )

    assert ordered.index("a1") < ordered.index("a2")


def test_dependency_critical_path_returns_longest_prerequisite_chain() -> None:
    critical = dependency_critical_path(
        ["a1", "a2", "a3", "a4"],
        [
            AssayDependency(assay_id="a2", requires_assay_id="a1"),
            AssayDependency(assay_id="a3", requires_assay_id="a2"),
            AssayDependency(assay_id="a4", requires_assay_id="a1"),
        ],
    )

    assert critical.path_length == 3
    assert critical.ordered_assay_ids == ["a1", "a2", "a3"]


def test_recommend_next_cycle_from_outcome_holds_on_technical_failures() -> None:
    program = create_program_spec(
        program_id="prog-outcome-hold",
        name="outcome hold",
        objective="hold when assay execution quality is poor",
        target_id="target-outcome-hold",
        target_name="Target Outcome Hold",
        sequence="ACDEFGHIKLMNPQRSTVWY",
        organism="human",
        mechanism="defer decisions until technical issues are resolved",
    )
    bundle = EvidenceBundle(
        bundle_id="bundle-outcome-hold", target_id="target-outcome-hold", records=[]
    )
    outcome = ExperimentOutcome(
        batch_id="batch-outcome-hold",
        assay_outcomes=[
            AssayOutcome(
                assay_id="binding-assay",
                passed=False,
                result_state=AssayResultState.FAILED_TECHNICAL,
                observation_summary="instrument drift",
            )
        ],
        rerun_policy=RerunPolicy.ON_TECHNICAL_FAILURE,
    )

    plan = recommend_next_cycle_from_outcome(program, bundle, outcome)

    assert plan.decision is ProgressDecision.HOLD
    assert plan.assay_backlog == ["binding-assay"]
    assert plan.technical_failure_count == 1


def test_recommend_next_cycle_from_outcome_redesigns_on_biological_failures() -> None:
    program = create_program_spec(
        program_id="prog-outcome-redesign",
        name="outcome redesign",
        objective="redesign when biology fails",
        target_id="target-outcome-redesign",
        target_name="Target Outcome Redesign",
        sequence="ACDEFGHIKLMNPQRSTVWY",
        organism="human",
        mechanism="use biological outcomes to drive redesign",
    )
    bundle = EvidenceBundle(
        bundle_id="bundle-outcome-redesign",
        target_id="target-outcome-redesign",
        records=[],
    )
    outcome = ExperimentOutcome(
        batch_id="batch-outcome-redesign",
        assay_outcomes=[
            AssayOutcome(
                assay_id="activity-assay",
                passed=False,
                result_state=AssayResultState.FAILED_BIOLOGICAL,
                observation_summary="activity gate missed",
            )
        ],
        rerun_policy=RerunPolicy.ON_BIOLOGICAL_FAILURE,
    )

    plan = recommend_next_cycle_from_outcome(program, bundle, outcome)

    assert plan.decision is ProgressDecision.REDESIGN
    assert plan.promotion_ready_count == 0


def test_assess_material_constraints_flags_missing_sample_inventory() -> None:
    plan = ExperimentPlan(
        program_id="prog-3",
        batches=[
            ExperimentBatch(
                batch_id="batch-1",
                objective="blocking",
                assay_ids=["a1"],
                priority=1,
                sample_requirements=["purified protein"],
            )
        ],
    )

    report = assess_material_constraints(
        plan,
        requirements=[
            MaterialRequirement(
                material_id="purified-protein",
                sample_kind="purified protein",
                minimum_units=5.0,
                unit="mg",
            )
        ],
        inventory=[
            MaterialInventory(
                material_id="purified-protein",
                available_units=2.0,
            )
        ],
    )

    assert report.blocking_material_ids == ["purified-protein"]


def test_schedule_with_family_capacity_respects_family_limits() -> None:
    plan = ExperimentPlan(
        program_id="prog-4",
        batches=[
            ExperimentBatch(
                batch_id="batch-1",
                objective="family capacity",
                assay_ids=["a1", "a2"],
                sample_requirements=["biophysical", "expression"],
                assay_sample_kinds={"a1": "biophysical", "a2": "expression"},
                priority=1,
            )
        ],
    )

    scheduled = schedule_with_family_capacity(
        plan,
        LabCapacity(cycle_id="cycle-1", max_batches=1, max_assays_per_batch=2),
        family_capacities=[
            FamilyCapacity(family=AssayFamily.BIOPHYSICAL, max_assays=1),
            FamilyCapacity(family=AssayFamily.EXPRESSION, max_assays=0),
        ],
    )

    assert scheduled.scheduled_batches[0].assay_ids == ["a1"]
    assert "a2" in scheduled.scheduled_batches[0].deferred_assay_ids


def test_schedule_with_family_capacity_uses_per_assay_mapping() -> None:
    plan = ExperimentPlan(
        program_id="prog-5",
        batches=[
            ExperimentBatch(
                batch_id="batch-1",
                objective="family mapped scheduling",
                assay_ids=["a1", "a2", "a3"],
                sample_requirements=["biophysical"],
                assay_sample_kinds={
                    "a1": "biophysical",
                    "a2": "biophysical",
                    "a3": "expression",
                },
                priority=1,
            )
        ],
    )

    scheduled = schedule_with_family_capacity(
        plan,
        LabCapacity(cycle_id="cycle-2", max_batches=1, max_assays_per_batch=3),
        family_capacities=[
            FamilyCapacity(family=AssayFamily.BIOPHYSICAL, max_assays=1),
            FamilyCapacity(family=AssayFamily.EXPRESSION, max_assays=1),
        ],
    )

    assert scheduled.scheduled_batches[0].assay_ids == ["a1", "a3"]
    assert scheduled.scheduled_batches[0].deferred_assay_ids == ["a2"]


def test_experiment_plan_round_trips_with_serialization_helpers(tmp_path: Path) -> None:
    plan = ExperimentPlan(program_id="prog-2")
    plan.document_schema.trace_id = "trace-lab-1"
    path = tmp_path / "plan.json"

    plan.save_json(path)
    restored = ExperimentPlan.load_json(path)

    assert restored.to_dict()["document_schema"]["trace_id"] == "trace-lab-1"


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


def test_assay_family_priority_uses_scientific_execution_order() -> None:
    assert assay_family_priority(AssayFamily.BIOPHYSICAL) < assay_family_priority(
        AssayFamily.CELLULAR
    )
    assert assay_family_priority(AssayFamily.CELLULAR) < assay_family_priority(
        AssayFamily.DEVELOPABILITY
    )


def test_recommend_orthogonal_confirmation_when_convergence_is_low() -> None:
    program = create_program_spec(
        program_id="prog-orth",
        name="orthogonal plan",
        objective="request orthogonal confirmation when evidence lacks convergence",
        target_id="target-orth",
        target_name="Target Orth",
        sequence="ACDEFGHIKLMNPQRSTVWY",
        organism="human",
        mechanism="enforce orthogonal evidence checks",
    )
    program.assay_panel.append(
        AssayRequirement(
            assay_id="assay-a",
            purpose="confirm with second modality",
            readout="signal",
            sample_kind="cellular",
            blocking=False,
        )
    )
    bundle = EvidenceBundle(
        bundle_id="bundle-orth",
        target_id="target-orth",
        records=[
            EvidenceRecord(
                evidence_id="lit-only",
                kind=EvidenceKind.LITERATURE,
                title="single modality",
                source="pmid",
                claim="support",
                decision_tags=["progression"],
                confidence=0.8,
                strength=EvidenceStrength.SUPPORTING,
            )
        ],
    )

    plan = recommend_orthogonal_confirmation(program, bundle)

    assert plan.required is True
    assert plan.suggested_assay_ids == ["assay-a"]


def test_recommend_orthogonal_confirmation_honors_required_modalities_policy() -> None:
    program = create_program_spec(
        program_id="prog-orth-policy",
        name="orthogonal policy",
        objective="enforce required modalities",
        target_id="target-orth-policy",
        target_name="Target",
        sequence="ACDEFGHIKLMNPQRSTVWY",
        organism="human",
        mechanism="require modality coverage",
    )
    program.assay_panel.append(
        AssayRequirement(
            assay_id="assay-b",
            purpose="orthogonal assay",
            readout="signal",
            sample_kind="cellular",
            blocking=False,
        )
    )
    bundle = EvidenceBundle(
        bundle_id="bundle-orth-policy",
        target_id="target-orth-policy",
        records=[
            EvidenceRecord(
                evidence_id="lit",
                kind=EvidenceKind.LITERATURE,
                title="lit",
                source="pmid",
                claim="support",
                decision_tags=["progression"],
                confidence=0.8,
                strength=EvidenceStrength.SUPPORTING,
            ),
            EvidenceRecord(
                evidence_id="assay",
                kind=EvidenceKind.ASSAY,
                title="assay",
                source="lab",
                claim="support",
                decision_tags=["progression"],
                confidence=0.8,
                strength=EvidenceStrength.SUPPORTING,
            ),
        ],
    )
    plan = recommend_orthogonal_confirmation(
        program,
        bundle,
        policy=OrthogonalPolicy(
            policy_id="strict-modalities",
            required_modalities=[
                EvidenceKind.LITERATURE.value,
                EvidenceKind.ASSAY.value,
                EvidenceKind.STRUCTURE.value,
            ],
        ),
    )

    assert plan.required is True


def test_plan_conflict_resolution_assays_suggests_followup_when_conflicts_exist() -> (
    None
):
    program = create_program_spec(
        program_id="prog-conflict",
        name="conflict plan",
        objective="generate assays that resolve conflicting evidence",
        target_id="target-conflict",
        target_name="Target Conflict",
        sequence="ACDEFGHIKLMNPQRSTVWY",
        organism="human",
        mechanism="resolve evidence contradictions before progression",
    )
    program.assay_panel.append(
        AssayRequirement(
            assay_id="assay-conflict",
            purpose="resolve contradictory signal",
            readout="activity",
            sample_kind="biophysical",
            blocking=True,
        )
    )
    bundle = EvidenceBundle(
        bundle_id="bundle-conflict",
        target_id="target-conflict",
        records=[
            EvidenceRecord(
                evidence_id="c1",
                kind=EvidenceKind.ASSAY,
                title="positive",
                source="lab",
                claim="Candidate meets gate.",
                decision_tags=["progression"],
                confidence=0.8,
                strength=EvidenceStrength.SUPPORTING,
            ),
            EvidenceRecord(
                evidence_id="c2",
                kind=EvidenceKind.ASSAY,
                title="negative",
                source="lab2",
                claim="Candidate fails gate.",
                decision_tags=["progression"],
                confidence=0.8,
                strength=EvidenceStrength.SUPPORTING,
            ),
        ],
    )

    plan = plan_conflict_resolution_assays(program, bundle)

    assert plan.conflict_count > 0
    assert plan.suggested_assay_ids == ["assay-conflict"]


def test_plan_conflict_resolution_assays_honors_policy_suggestion_limit() -> None:
    program = create_program_spec(
        program_id="prog-conflict-policy",
        name="conflict policy",
        objective="limit conflict suggestions",
        target_id="target-conflict-policy",
        target_name="Target",
        sequence="ACDEFGHIKLMNPQRSTVWY",
        organism="human",
        mechanism="resolve conflicts",
    )
    program.assay_panel.extend(
        [
            AssayRequirement(
                assay_id="a1",
                purpose="p1",
                readout="r1",
                sample_kind="cell",
                blocking=True,
            ),
            AssayRequirement(
                assay_id="a2",
                purpose="p2",
                readout="r2",
                sample_kind="cell",
                blocking=False,
            ),
        ]
    )
    bundle = EvidenceBundle(
        bundle_id="bundle-conflict-policy",
        target_id="target-conflict-policy",
        records=[
            EvidenceRecord(
                evidence_id="cp1",
                kind=EvidenceKind.ASSAY,
                title="pos",
                source="lab",
                claim="Candidate meets gate.",
                decision_tags=["progression"],
                confidence=0.8,
                strength=EvidenceStrength.SUPPORTING,
            ),
            EvidenceRecord(
                evidence_id="cp2",
                kind=EvidenceKind.ASSAY,
                title="neg",
                source="lab2",
                claim="Candidate fails gate.",
                decision_tags=["progression"],
                confidence=0.8,
                strength=EvidenceStrength.SUPPORTING,
            ),
        ],
    )
    plan = plan_conflict_resolution_assays(
        program,
        bundle,
        policy=ConflictAssayPolicy(policy_id="limit-1", max_suggestions=1),
    )

    assert len(plan.suggested_assay_ids) == 1


def test_plan_uncertainty_reduction_assays_returns_ranked_backlog() -> None:
    program = create_program_spec(
        program_id="prog-ur",
        name="uncertainty reduction",
        objective="reduce uncertainty before progression",
        target_id="target-ur",
        target_name="Target",
        sequence="ACDEFGHIKLMNPQRSTVWY",
        organism="human",
        mechanism="resolve uncertainty",
    )
    program.assay_panel.append(
        AssayRequirement(
            assay_id="assay-ur-1",
            purpose="reduce uncertainty",
            readout="activity_score",
            sample_kind="cellular",
            blocking=True,
        )
    )
    bundle = EvidenceBundle(bundle_id="bundle-ur", target_id="target-ur")
    plan = plan_uncertainty_reduction_assays(
        program, bundle, [], decision_tag="progression"
    )

    assert "assay-ur-1" in plan.prioritized_assay_ids
    assert 0.0 <= plan.residual_uncertainty <= 1.0


def test_recommend_next_best_experiment_respects_dependencies() -> None:
    program = create_program_spec(
        program_id="prog-nbe",
        name="next best experiment",
        objective="pick next assay",
        target_id="target-nbe",
        target_name="Target",
        sequence="ACDEFGHIKLMNPQRSTVWY",
        organism="human",
        mechanism="resolve uncertainty",
    )
    program.assay_panel.extend(
        [
            AssayRequirement(
                assay_id="assay-prereq",
                purpose="prerequisite",
                readout="quality",
                sample_kind="biophysical",
                blocking=False,
            ),
            AssayRequirement(
                assay_id="assay-main",
                purpose="main uncertainty reducer",
                readout="activity",
                sample_kind="cellular",
                blocking=True,
            ),
        ]
    )
    recommendation = recommend_next_best_experiment(
        program,
        EvidenceBundle(bundle_id="bundle-nbe", target_id="target-nbe"),
        [],
        dependencies=[
            AssayDependency(assay_id="assay-main", requires_assay_id="assay-prereq")
        ],
    )

    assert recommendation is not None
    assert recommendation.assay_id == "assay-main"
    assert recommendation.prerequisite_assay_ids == ["assay-prereq"]


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

# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import json
from pathlib import Path
from typing import cast

from bijux_proteomics.domain.assays import AssayRequirement
from bijux_proteomics.domain.program_spec import create_program_spec
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
    AssayDependency,
    AssayIntent,
    AssayObservation,
    ConflictAssayPolicy,
    ExperimentBatch,
    ExperimentPlan,
    MaterialInventory,
    MaterialRequirement,
    OrthogonalPolicy,
    ProgressDecision,
    assess_gate_coverage_gaps,
    assess_material_constraints,
    build_review_packet,
    build_review_risk_profile,
    derive_lab_execution_directive,
    map_assay_contradiction_pressure,
    plan_conflict_resolution_assays,
    plan_hypothesis_falsification_assays,
    plan_material_reservations,
    plan_uncertainty_reduction_assays,
    recommend_next_best_experiment,
    recommend_next_cycle,
    recommend_next_cycle_from_outcome,
    recommend_orthogonal_confirmation,
    summarize_assay_portfolio_balance,
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

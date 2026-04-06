# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

from bijux_proteomics import create_program_spec
from bijux_proteomics.programs import AssayRequirement, ReviewGate
from bijux_proteomics_knowledge import EvidenceBundle, EvidenceKind, EvidenceRecord, EvidenceStrength
from bijux_proteomics_lab import (
    AssayDependency,
    AssayFamily,
    AssayObservation,
    assess_dependency_integrity,
    assay_family_priority,
    dependency_order,
    detect_dependency_cycle,
    ExperimentBatch,
    ExperimentPlan,
    FamilyCapacity,
    LabCapacity,
    MaterialInventory,
    MaterialRequirement,
    ProgressDecision,
    assess_material_constraints,
    build_review_packet,
    plan_experiment_batches,
    prioritize_next_assays,
    plan_conflict_resolution_assays,
    recommend_orthogonal_confirmation,
    recommend_next_cycle,
    schedule_experiment_plan,
    schedule_with_family_capacity,
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
        dependencies=[AssayDependency(assay_id="expression-screen", requires_assay_id="primary-binding")],
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
        [AssayObservation(assay_id="a-support", metric="yield", value=1.0, passed=True)],
    )

    assert ranked[0].assay_id == "a-block"
    assert ranked[0].estimated_cost > 0


def test_assay_family_priority_uses_scientific_execution_order() -> None:
    assert assay_family_priority(AssayFamily.BIOPHYSICAL) < assay_family_priority(AssayFamily.CELLULAR)
    assert assay_family_priority(AssayFamily.CELLULAR) < assay_family_priority(AssayFamily.DEVELOPABILITY)


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


def test_plan_conflict_resolution_assays_suggests_followup_when_conflicts_exist() -> None:
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

# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

import json
from pathlib import Path
from typing import cast

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
    AssayObservation,
    AssayPlanKind,
    ExecutableAssayPlan,
    ExperimentBatch,
    ExperimentPlan,
    assay_family_priority,
    assess_dependency_integrity,
    build_advisory_assay_plan,
    build_executable_assay_plan,
    build_lab_execution_request,
    build_lab_review_packet_bundle,
    build_review_packet,
    build_workflow_batch_outline,
    dependency_critical_path,
    dependency_order,
    detect_dependency_cycle,
    plan_experiment_batches,
    report_execution_plan_uncertainty,
    validate_experiment_plan,
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


def test_lab_surfaces_keep_advice_request_instruction_and_outcome_separate() -> None:
    program = create_program_spec(
        program_id="prog-surface-line",
        name="surface line",
        objective="keep scientific advice separate from executable and observed lab state",
        target_id="target-surface-line",
        target_name="Target Surface Line",
        sequence="ACDEFGHIKLMNPQRSTVWY",
        organism="human",
        mechanism="stabilize a productive state",
    )
    program.evidence_needs = [
        EvidenceNeed.LITERATURE,
        EvidenceNeed.STRUCTURE,
        EvidenceNeed.ASSAY,
    ]
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
        bundle_id="bundle-surface-line",
        target_id="target-surface-line",
        records=[
            EvidenceRecord(
                evidence_id="lit-line-1",
                kind=EvidenceKind.LITERATURE,
                title="Paper",
                source="PMID:2",
                claim="literature supports tractability",
                confidence=0.9,
                strength=EvidenceStrength.SUPPORTING,
            ),
            EvidenceRecord(
                evidence_id="structure-line-1",
                kind=EvidenceKind.STRUCTURE,
                title="Model",
                source="AlphaFold",
                claim="structure supports a stable binding pose",
                confidence=0.84,
                strength=EvidenceStrength.SUPPORTING,
            ),
            EvidenceRecord(
                evidence_id="assay-line-1",
                kind=EvidenceKind.ASSAY,
                title="Assay",
                source="lab",
                claim="a prior assay supports the same direction",
                confidence=0.88,
                strength=EvidenceStrength.DECISIVE,
            ),
        ],
    )
    advisory_plan = build_advisory_assay_plan(program)
    executable_plan = build_executable_assay_plan(
        ExperimentPlan(
            program_id=program.program_id,
            batches=[
                ExperimentBatch(
                    batch_id="batch-surface-line",
                    objective="execute the gate assay once review stays clean",
                    assay_ids=["gate-binding"],
                    priority=1,
                    sample_requirements=["biophysical"],
                    assay_sample_kinds={"gate-binding": "biophysical"},
                )
            ],
        ),
        batch_id="batch-surface-line",
        available_sample_kinds=["biophysical"],
    )
    review_packet = build_review_packet(program, bundle, [])
    request = build_lab_execution_request(review_packet, executable_plan)
    outcome = ExperimentOutcome(
        batch_id="batch-surface-line",
        assay_outcomes=[
            AssayOutcome(
                assay_id="gate-binding",
                passed=True,
                result_state=AssayResultState.PASSED,
                observation_summary="the gate assay reproduced the expected signal",
                replicate_count=2,
                uncertainty=0.09,
            )
        ],
        rerun_policy=RerunPolicy.NEVER,
    )

    assert advisory_plan.plan_kind is AssayPlanKind.ADVISORY
    assert advisory_plan.executable is False
    assert advisory_plan.recommendations[0].assay_id == "gate-binding"
    assert executable_plan.plan_kind is AssayPlanKind.EXECUTABLE
    assert (
        executable_plan.instructions[0].instruction_id
        == "batch-surface-line:gate-binding"
    )
    assert request.requested_instruction_ids == ["batch-surface-line:gate-binding"]
    assert request.requested_assay_ids == ["gate-binding"]
    assert request.ready_for_lab_review is True
    assert outcome.assay_outcomes[0].assay_id == request.requested_assay_ids[0]


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


def test_experiment_plan_round_trips_with_serialization_helpers(tmp_path: Path) -> None:
    plan = ExperimentPlan(program_id="prog-2")
    plan.document_schema.trace_id = "trace-lab-1"
    path = tmp_path / "plan.json"

    plan.save_json(path)
    restored = ExperimentPlan.load_json(path)

    assert restored.to_dict()["document_schema"]["trace_id"] == "trace-lab-1"


def test_assay_family_priority_uses_scientific_execution_order() -> None:
    assert assay_family_priority(AssayFamily.BIOPHYSICAL) < assay_family_priority(
        AssayFamily.CELLULAR
    )
    assert assay_family_priority(AssayFamily.CELLULAR) < assay_family_priority(
        AssayFamily.DEVELOPABILITY
    )

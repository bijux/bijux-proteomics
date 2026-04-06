# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from datetime import timedelta
from pathlib import Path

import pytest

from bijux_proteomics import (
    ExecutionRequest,
    ProgramExecutionRequest,
    ProgramSpec,
    ReviewDecision,
    ReviewGateBlockedError,
    ReviewOutcome,
    ProgramValidationIssue,
    ProgramValidationError,
    ProgramContext,
    DecisionQuery,
    ProgramDeliveryContext,
    DuplicateReviewDecisionError,
    ProgramNotFoundError,
    ProgramRevisionConflictError,
    ProgramPortfolioContext,
    ReviewGateEvaluation,
    ReviewGateState,
    StageEligibility,
    decision_timeline,
    create_program_spec,
    evaluate_review_gates,
    ensure_review_clearance,
    latest_gate_decision,
    list_decisions_by_outcome,
    list_gate_decisions,
    query_decisions,
    program_summary,
    revise_program,
    assess_stage_eligibility,
    ensure_unique_gate_decision,
    ensure_program_revision,
    require_program,
    validate_review_decision,
    validate_assay_dependencies,
    validate_program,
    validate_program_readiness,
)
from bijux_proteomics.runtime_adapter import MissingExecutionBackendError
from bijux_proteomics.programs import (
    AssayRequirement,
    MeasurementDirection,
    ProgramStage,
    ReviewGate,
    ScientificConstraint,
    SuccessCriterion,
)


def test_create_program_spec_enforces_sequence_contract() -> None:
    with pytest.raises(ValueError):
        create_program_spec(
            program_id="prog-1",
            name="bad-sequence",
            objective="test invalid sequence handling",
            target_id="target-1",
            target_name="Target",
            sequence="ACDU",
            organism="human",
            mechanism="test",
        )


def test_program_summary_counts_scientific_parts() -> None:
    program = create_program_spec(
        program_id="prog-1",
        name="kinase rescue",
        objective="recover activity while constraining off-target toxicity",
        target_id="kinase-x",
        target_name="Kinase X",
        sequence="ACDEFGHIKLMNPQRSTVWY",
        organism="human",
        mechanism="stabilize the active conformation",
    )
    program.constraints.append(
        ScientificConstraint(
            constraint_id="surface-charge",
            category="developability",
            statement="do not add a strongly hydrophobic surface patch",
            rationale="reduce aggregation risk",
        )
    )
    program.success_criteria.append(
        SuccessCriterion(
            criterion_id="binding",
            metric="binding_score",
            direction=MeasurementDirection.MAXIMIZE,
            threshold=0.8,
        )
    )
    program.review_gates.append(
        ReviewGate(
            gate_id="pre-synthesis",
            name="Pre-synthesis review",
            required_roles=["scientist", "safety"],
            decision_inputs=["evidence_bundle", "ranked_candidates"],
        )
    )
    program.assay_panel.append(
        AssayRequirement(
            assay_id="thermal-shift",
            purpose="screen stabilization",
            readout="delta_tm",
            sample_kind="purified protein",
            blocking=True,
        )
    )

    summary = program_summary(program)

    assert summary["constraint_count"] == 1
    assert summary["assay_count"] == 1
    assert summary["review_gate_count"] == 1
    assert summary["schema_version"] == "1.0.0"


def test_program_execution_request_requires_workspace_path(tmp_path: Path) -> None:
    program = create_program_spec(
        program_id="prog-1",
        name="enzyme rescue",
        objective="improve catalytic rate while preserving folding",
        target_id="enz-1",
        target_name="Enzyme 1",
        sequence="ACDEFGHIKLMNPQRSTVWY",
        organism="yeast",
        mechanism="recover active-site geometry",
    )

    request = ProgramExecutionRequest(
        program=program,
        candidate_sequence=program.target.sequence.residues,
        base_dir=tmp_path,
    )

    assert request.base_dir == tmp_path


def test_program_summary_includes_operating_model_defaults() -> None:
    program = create_program_spec(
        program_id="prog-2",
        name="reviewable rescue",
        objective="improve activity with explicit lab follow-up",
        target_id="target-2",
        target_name="Target 2",
        sequence="ACDEFGHIKLMNPQRSTVWY",
        organism="human",
        mechanism="stabilize the productive conformation",
    )

    summary = program_summary(program)

    assert summary["stage"] == ProgramStage.SCOPING.value
    assert summary["human_review_required"] is True
    assert summary["lab_feedback_required"] is True


def test_program_summary_includes_structured_context_fields() -> None:
    program = create_program_spec(
        program_id="prog-2b",
        name="portfolio context",
        objective="carry durable portfolio and delivery context",
        target_id="target-2b",
        target_name="Target 2B",
        sequence="ACDEFGHIKLMNPQRSTVWY",
        organism="human",
        mechanism="make scoping intent visible to downstream systems",
    )
    program.context = ProgramContext(
        portfolio=ProgramPortfolioContext(
            therapeutic_area="immunology",
            disease_area="autoimmune disease",
            modality="bispecific protein",
        ),
        delivery=ProgramDeliveryContext(
            sponsor="protein design",
            decision_horizon="monthly",
            intended_output="candidate shortlist",
        ),
        tags=["immune", "shortlist"],
    )

    summary = program_summary(program)

    assert summary["therapeutic_area"] == "immunology"
    assert summary["decision_horizon"] == "monthly"


def test_program_spec_round_trips_with_serialization_helpers(tmp_path: Path) -> None:
    program = create_program_spec(
        program_id="prog-3",
        name="portable manifest",
        objective="exercise SDK-style serialization helpers",
        target_id="target-3",
        target_name="Target 3",
        sequence="ACDEFGHIKLMNPQRSTVWY",
        organism="human",
        mechanism="preserve active-site geometry",
    )
    program.document_schema.trace_id = "trace-123"
    path = tmp_path / "program.json"

    program.save_json(path)
    restored = ProgramSpec.load_json(path)

    assert restored.to_dict()["document_schema"]["trace_id"] == "trace-123"
    assert ProgramSpec.from_json(program.to_json()).program_id == "prog-3"


def test_ensure_review_clearance_lists_blocking_gates_without_approval() -> None:
    program = create_program_spec(
        program_id="prog-4",
        name="reviewable manifest",
        objective="exercise review clearance",
        target_id="target-4",
        target_name="Target 4",
        sequence="ACDEFGHIKLMNPQRSTVWY",
        organism="human",
        mechanism="hold execution until review is recorded",
    )
    program.review_gates.append(
        ReviewGate(
            gate_id="pre-synthesis",
            name="Pre-synthesis review",
            required_roles=["scientist"],
            decision_inputs=["evidence_bundle"],
            blocking=True,
        )
    )

    blocked = ensure_review_clearance(program, [])

    assert [gate.gate_id for gate in blocked] == ["pre-synthesis"]


def test_execute_program_request_rejects_missing_blocking_approval(tmp_path: Path) -> None:
    program = create_program_spec(
        program_id="prog-5",
        name="gated execution",
        objective="confirm blocking review enforcement",
        target_id="target-5",
        target_name="Target 5",
        sequence="ACDEFGHIKLMNPQRSTVWY",
        organism="human",
        mechanism="hold execution until review is approved",
    )
    program.review_gates.append(
        ReviewGate(
            gate_id="pre-synthesis",
            name="Pre-synthesis review",
            required_roles=["scientist"],
            decision_inputs=["evidence_bundle"],
            blocking=True,
        )
    )
    program.operating_model.lab_feedback_required = False
    request = ProgramExecutionRequest(
        program=program,
        candidate_sequence=program.target.sequence.residues,
        base_dir=tmp_path,
        review_decisions=[
            ReviewDecision(
                program_id=program.program_id,
                gate_id="pre-synthesis",
                outcome=ReviewOutcome.NEEDS_REVISION,
                decided_by="scientist",
                rationale="need stronger evidence",
                reviewed_evidence_ids=["ev-1"],
            )
        ],
    )

    with pytest.raises(ReviewGateBlockedError):
        from bijux_proteomics.runner import execute_program

        execute_program(request)


def test_execute_program_requires_injected_backend(tmp_path: Path) -> None:
    program = create_program_spec(
        program_id="prog-6",
        name="injected backend",
        objective="exercise backend protocol boundary",
        target_id="target-6",
        target_name="Target 6",
        sequence="ACDEFGHIKLMNPQRSTVWY",
        organism="human",
        mechanism="decouple core from concrete runtime imports",
    )
    program.operating_model.human_review_required = False
    program.operating_model.lab_feedback_required = False
    request = ProgramExecutionRequest(
        program=program,
        candidate_sequence=program.target.sequence.residues,
        base_dir=tmp_path,
    )

    with pytest.raises(MissingExecutionBackendError):
        from bijux_proteomics.runner import execute_program

        execute_program(request)


def test_execute_program_uses_injected_backend(tmp_path: Path) -> None:
    class StubBackend:
        def execute(self, request: ExecutionRequest) -> dict[str, object]:
            return {
                "sequence": request.candidate_sequence,
                "backend": "stub",
            }

    program = create_program_spec(
        program_id="prog-7",
        name="stub backend",
        objective="exercise backend protocol",
        target_id="target-7",
        target_name="Target 7",
        sequence="ACDEFGHIKLMNPQRSTVWY",
        organism="human",
        mechanism="return stub payload",
    )
    program.operating_model.human_review_required = False
    program.operating_model.lab_feedback_required = False
    request = ProgramExecutionRequest(
        program=program,
        candidate_sequence=program.target.sequence.residues,
        base_dir=tmp_path,
        backend=StubBackend(),
    )

    from bijux_proteomics.runner import execute_program

    result = execute_program(request)

    assert result["backend"] == "stub"
    assert result["program"]["program_id"] == "prog-7"


def test_validate_program_detects_missing_review_and_assay_modeling() -> None:
    program = create_program_spec(
        program_id="prog-8",
        name="invalid program",
        objective="exercise validation rules",
        target_id="target-8",
        target_name="Target 8",
        sequence="ACDEFGHIKLMNPQRSTVWY",
        organism="human",
        mechanism="intentionally leave required structures empty",
    )
    program.stage = program.stage.LAB_READY

    issues = validate_program(program)

    assert ProgramValidationIssue(
        code="review-gates-missing",
        message="review and lab-ready programs should define review gates",
    ) in issues
    assert ProgramValidationIssue(
        code="assay-panel-missing",
        message="lab-ready programs should define an assay panel",
    ) in issues


def test_validate_program_readiness_flags_unmapped_review_inputs() -> None:
    program = create_program_spec(
        program_id="prog-10",
        name="review coherence",
        objective="keep review gates tied to concrete artifacts",
        target_id="target-10",
        target_name="Target 10",
        sequence="ACDEFGHIKLMNPQRSTVWY",
        organism="human",
        mechanism="tie signoff to actual evidence and assay outputs",
    )
    program.stage = ProgramStage.REVIEW
    program.review_gates.append(
        ReviewGate(
            gate_id="progression-review",
            name="Progression review",
            required_roles=["scientist"],
            decision_inputs=["missing-packet"],
            blocking=True,
        )
    )

    issues = validate_program_readiness(program)

    assert ProgramValidationIssue(
        code="review-input-unmapped",
        message="review gate 'progression-review' references unmapped inputs: missing-packet",
    ) in issues


def test_validate_program_readiness_flags_duplicate_gate_inputs() -> None:
    program = create_program_spec(
        program_id="prog-10b",
        name="duplicate review inputs",
        objective="reject repeated review input definitions",
        target_id="target-10b",
        target_name="Target 10B",
        sequence="ACDEFGHIKLMNPQRSTVWY",
        organism="human",
        mechanism="keep review contracts explicit and unique",
    )
    program.review_gates.append(
        ReviewGate(
            gate_id="pre-review",
            name="Pre-review",
            required_roles=["scientist"],
            decision_inputs=["evidence_bundle", "evidence_bundle"],
            blocking=True,
        )
    )

    issues = validate_program_readiness(program)

    assert ProgramValidationIssue(
        code="review-inputs-duplicate",
        message="review gate 'pre-review' repeats one or more decision inputs",
    ) in issues


def test_validate_program_readiness_requires_blocking_assays_for_blocking_gates() -> None:
    program = create_program_spec(
        program_id="prog-10c",
        name="blocking assay alignment",
        objective="ensure blocking review inputs map to blocking assays",
        target_id="target-10c",
        target_name="Target 10C",
        sequence="ACDEFGHIKLMNPQRSTVWY",
        organism="human",
        mechanism="tie review risk to hard assay blockers",
    )
    program.stage = ProgramStage.LAB_READY
    program.assay_panel.append(
        AssayRequirement(
            assay_id="primary-binding",
            purpose="measure activity",
            readout="binding_score",
            sample_kind="biophysical",
            blocking=False,
        )
    )
    program.review_gates.append(
        ReviewGate(
            gate_id="lab-gate",
            name="Lab gate",
            required_roles=["scientist"],
            decision_inputs=["primary-binding"],
            blocking=True,
        )
    )

    issues = validate_program_readiness(program)

    assert ProgramValidationIssue(
        code="blocking-gate-needs-blocking-assays",
        message="blocking review gate 'lab-gate' references non-blocking assays: primary-binding",
    ) in issues


def test_validate_assay_dependencies_flags_unmapped_success_metrics() -> None:
    program = create_program_spec(
        program_id="prog-11",
        name="assay coherence",
        objective="map advancement metrics to assay outputs",
        target_id="target-11",
        target_name="Target 11",
        sequence="ACDEFGHIKLMNPQRSTVWY",
        organism="human",
        mechanism="require assay-backed progression criteria",
    )
    program.assay_panel.append(
        AssayRequirement(
            assay_id="thermal-shift",
            purpose="measure stabilization",
            readout="delta_tm",
            sample_kind="purified protein",
            blocking=True,
        )
    )
    program.success_criteria.append(
        SuccessCriterion(
            criterion_id="binding",
            metric="ic50",
            direction=MeasurementDirection.MINIMIZE,
            threshold=10.0,
        )
    )

    issues = validate_assay_dependencies(program)

    assert ProgramValidationIssue(
        code="criterion-without-assay",
        message=(
            "success criterion 'binding' does not map to any assay readout or assay identifier"
        ),
    ) in issues


def test_validate_program_flags_duplicate_criterion_ids() -> None:
    program = create_program_spec(
        program_id="prog-12",
        name="duplicate criteria",
        objective="keep criterion identifiers stable and unique",
        target_id="target-12",
        target_name="Target 12",
        sequence="ACDEFGHIKLMNPQRSTVWY",
        organism="human",
        mechanism="prevent ambiguous criterion references",
    )
    program.success_criteria.append(
        SuccessCriterion(
            criterion_id="binding",
            metric="binding_score",
            direction=MeasurementDirection.MAXIMIZE,
            threshold=0.8,
        )
    )
    program.success_criteria.append(
        SuccessCriterion(
            criterion_id="binding",
            metric="off_target_score",
            direction=MeasurementDirection.MINIMIZE,
            threshold=0.2,
        )
    )

    issues = validate_program(program)

    assert ProgramValidationIssue(
        code="criterion-ids-duplicate",
        message="success criteria should use unique identifiers",
    ) in issues


def test_validate_program_requires_assay_evidence_for_gated_review() -> None:
    program = create_program_spec(
        program_id="prog-13",
        name="review evidence coherence",
        objective="align review gates with evidence needs",
        target_id="target-13",
        target_name="Target 13",
        sequence="ACDEFGHIKLMNPQRSTVWY",
        organism="human",
        mechanism="ensure review contracts require assay evidence",
    )
    program.review_gates.append(
        ReviewGate(
            gate_id="pre-synthesis",
            name="Pre-synthesis",
            required_roles=["scientist"],
            decision_inputs=["review_packet"],
            blocking=True,
        )
    )
    program.evidence_needs = [program.evidence_needs[0]]

    issues = validate_program(program)

    assert ProgramValidationIssue(
        code="review-needs-assay-evidence",
        message="programs with review gates should include assay evidence needs",
    ) in issues


def test_execute_program_rejects_invalid_program_before_backend_use(tmp_path: Path) -> None:
    class StubBackend:
        def execute(self, request: ExecutionRequest) -> dict[str, object]:
            return {"backend": "stub"}

    program = create_program_spec(
        program_id="prog-9",
        name="invalid execution",
        objective="validation should block execution before backend use",
        target_id="target-9",
        target_name="Target 9",
        sequence="ACDEFGHIKLMNPQRSTVWY",
        organism="human",
        mechanism="set stage without matching review gates",
    )
    program.stage = program.stage.REVIEW
    request = ProgramExecutionRequest(
        program=program,
        candidate_sequence=program.target.sequence.residues,
        base_dir=tmp_path,
        backend=StubBackend(),
    )

    with pytest.raises(ProgramValidationError) as excinfo:
        from bijux_proteomics.runner import execute_program

        execute_program(request)

    assert "review-gates-missing" in str(excinfo.value)


def test_evaluate_review_gates_reports_missing_inputs_and_roles() -> None:
    program = create_program_spec(
        program_id="prog-12",
        name="review engine",
        objective="make gate state explainable",
        target_id="target-12",
        target_name="Target 12",
        sequence="ACDEFGHIKLMNPQRSTVWY",
        organism="human",
        mechanism="trace who signed off and what they reviewed",
    )
    program.review_gates.append(
        ReviewGate(
            gate_id="progression-review",
            name="Progression review",
            required_roles=["scientist", "safety"],
            decision_inputs=["review_packet", "binding_score"],
            blocking=True,
        )
    )

    evaluations = evaluate_review_gates(
        program,
        [
            ReviewDecision(
                program_id=program.program_id,
                gate_id="progression-review",
                outcome=ReviewOutcome.APPROVED,
                decided_by="scientist",
                rationale="scientific case is strong",
                reviewed_inputs=["review_packet"],
                reviewed_evidence_ids=["ev-1"],
            )
        ],
    )

    assert evaluations == [
        ReviewGateEvaluation(
            gate_id="progression-review",
            state=ReviewGateState.NEEDS_OWNER,
            missing_roles=["safety"],
            missing_inputs=["binding_score"],
            rationale="required decision owners have not all signed off yet",
        )
    ]


def test_evaluate_review_gates_reports_fully_approved_gate() -> None:
    program = create_program_spec(
        program_id="prog-13",
        name="approved review engine",
        objective="mark fully covered gates as approved",
        target_id="target-13",
        target_name="Target 13",
        sequence="ACDEFGHIKLMNPQRSTVWY",
        organism="human",
        mechanism="require all owners and inputs before progression",
    )
    program.review_gates.append(
        ReviewGate(
            gate_id="pre-synthesis",
            name="Pre-synthesis review",
            required_roles=["scientist"],
            decision_inputs=["review_packet"],
            blocking=True,
        )
    )

    evaluations = evaluate_review_gates(
        program,
        [
            ReviewDecision(
                program_id=program.program_id,
                gate_id="pre-synthesis",
                outcome=ReviewOutcome.APPROVED,
                decided_by="scientist",
                rationale="packet is complete",
                reviewed_inputs=["review_packet"],
                reviewed_evidence_ids=["ev-2"],
            )
        ],
    )

    assert evaluations[0].state is ReviewGateState.APPROVED


def test_validate_review_decision_requires_evidence_refs_for_approval() -> None:
    issues = validate_review_decision(
        ReviewDecision(
            program_id="prog-14",
            gate_id="pre-synthesis",
            outcome=ReviewOutcome.APPROVED,
            decided_by="scientist",
            rationale="packet is complete",
            reviewed_inputs=["review_packet"],
        )
    )

    assert issues == ["approved review decisions should reference supporting evidence ids"]


def test_latest_gate_decision_and_timeline_are_time_ordered() -> None:
    older = ReviewDecision(
        program_id="prog-15",
        gate_id="pre-synthesis",
        outcome=ReviewOutcome.NEEDS_REVISION,
        decided_by="scientist",
        rationale="needs stronger assay corroboration",
        reviewed_inputs=["review_packet"],
        reviewed_evidence_ids=["ev-1"],
    )
    newer = older.model_copy(
        update={
            "outcome": ReviewOutcome.APPROVED,
            "rationale": "evidence is now sufficient",
            "decided_at": older.decided_at + timedelta(seconds=1),
        }
    )
    decisions = [newer, older]

    latest = latest_gate_decision("prog-15", "pre-synthesis", decisions)

    assert latest is not None
    assert latest.outcome is ReviewOutcome.APPROVED
    assert decision_timeline("prog-15", decisions) == [older, newer]


def test_assess_stage_eligibility_flags_missing_lab_ready_prerequisites() -> None:
    program = create_program_spec(
        program_id="prog-16",
        name="stage eligibility",
        objective="make stage blockers explicit",
        target_id="target-16",
        target_name="Target 16",
        sequence="ACDEFGHIKLMNPQRSTVWY",
        organism="human",
        mechanism="check stage-level prerequisites",
    )

    eligibility = assess_stage_eligibility(program, ProgramStage.LAB_READY)

    assert eligibility == StageEligibility(
        program_id="prog-16",
        stage=ProgramStage.LAB_READY,
        eligible=False,
        blockers=[
            "lab-ready stage requires at least one blocking assay",
            "lab-ready stage requires at least one blocking review gate",
        ],
    )


def test_require_program_raises_typed_not_found_error() -> None:
    with pytest.raises(ProgramNotFoundError):
        require_program(None, "prog-17")


def test_ensure_unique_gate_decision_rejects_duplicate_timestamp() -> None:
    decision = ReviewDecision(
        program_id="prog-18",
        gate_id="pre-synthesis",
        outcome=ReviewOutcome.APPROVED,
        decided_by="scientist",
        rationale="ready",
        reviewed_inputs=["review_packet"],
        reviewed_evidence_ids=["ev-1"],
    )

    with pytest.raises(DuplicateReviewDecisionError):
        ensure_unique_gate_decision(decision, [decision])


def test_ensure_program_revision_detects_stale_writes() -> None:
    program = create_program_spec(
        program_id="prog-13",
        name="revision-check",
        objective="guard against stale concurrent writes",
        target_id="target-13",
        target_name="Target 13",
        sequence="ACDEFGHIKLMNPQRSTVWY",
        organism="human",
        mechanism="maintain revision-aware persistence boundaries",
    )
    program.document_schema.revision = 3

    with pytest.raises(ProgramRevisionConflictError):
        ensure_program_revision(program, expected_revision=2)


def test_revise_program_increments_revision_and_sets_content_hash() -> None:
    program = create_program_spec(
        program_id="prog-19",
        name="revision test",
        objective="check revision metadata behavior",
        target_id="target-19",
        target_name="Target 19",
        sequence="ACDEFGHIKLMNPQRSTVWY",
        organism="human",
        mechanism="test revision bumping",
    )

    revised = revise_program(program, actor="scientist", tag="updated")

    assert revised.document_schema.revision == program.document_schema.revision + 1
    assert revised.document_schema.updated_by == "scientist"
    assert revised.document_schema.content_hash is not None


def test_decision_query_helpers_filter_by_outcome_and_gate() -> None:
    d1 = ReviewDecision(
        program_id="prog-20",
        gate_id="g1",
        outcome=ReviewOutcome.APPROVED,
        decided_by="scientist",
        rationale="ok",
        reviewed_inputs=["p"],
        reviewed_evidence_ids=["ev-1"],
    )
    d2 = d1.model_copy(
        update={
            "gate_id": "g2",
            "outcome": ReviewOutcome.NEEDS_REVISION,
            "decided_at": d1.decided_at + timedelta(seconds=1),
        }
    )
    d3 = d1.model_copy(
        update={
            "gate_id": "g1",
            "outcome": ReviewOutcome.APPROVED,
            "decided_at": d1.decided_at + timedelta(seconds=2),
        }
    )
    decisions = [d2, d3, d1]

    approved = list_decisions_by_outcome("prog-20", ReviewOutcome.APPROVED, decisions)
    gate = list_gate_decisions("prog-20", "g1", decisions)
    scientist_approved_gate = query_decisions(
        decisions,
        DecisionQuery(
            program_id="prog-20",
            gate_id="g1",
            decided_by="scientist",
            outcome=ReviewOutcome.APPROVED,
        ),
    )

    assert approved == [d1, d3]
    assert gate == [d1, d3]
    assert scientist_approved_gate == [d1, d3]

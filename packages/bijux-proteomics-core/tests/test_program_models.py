# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

import pytest

from bijux_proteomics import (
    ProgramExecutionRequest,
    ProgramSpec,
    ReviewDecision,
    ReviewGateBlockedError,
    ReviewOutcome,
    create_program_spec,
    ensure_review_clearance,
    program_summary,
)
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
        candidate_sequence=program.target.sequence,
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
    request = ProgramExecutionRequest(
        program=program,
        candidate_sequence=program.target.sequence,
        base_dir=tmp_path,
        review_decisions=[
            ReviewDecision(
                program_id=program.program_id,
                gate_id="pre-synthesis",
                outcome=ReviewOutcome.NEEDS_REVISION,
                decided_by="scientist",
                rationale="need stronger evidence",
            )
        ],
    )

    with pytest.raises(ReviewGateBlockedError):
        from bijux_proteomics.runner import execute_program

        execute_program(request)

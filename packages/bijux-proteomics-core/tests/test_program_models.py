# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from pathlib import Path

import pytest

from bijux_proteomics import (
    ProgramExecutionRequest,
    ProgramSpec,
    create_program_spec,
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

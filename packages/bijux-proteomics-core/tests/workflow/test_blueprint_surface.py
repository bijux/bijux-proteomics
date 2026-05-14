# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.domain.assays import AssayRequirement
from bijux_proteomics.domain.program_spec import (
    EvidenceNeed,
    ProgramStage,
    create_program_spec,
)
from bijux_proteomics.domain.reviews import ReviewGate
from bijux_proteomics.workflow.blueprint import (
    ScientificWorkflowBlueprint,
    WorkflowStageKind,
    WorkflowStepBlueprint,
    workflow_blueprint_for_program,
    workflow_blueprint_summary,
)


def test_workflow_blueprint_summary_surfaces_blocking_components() -> None:
    blueprint = ScientificWorkflowBlueprint(
        program_id="prog-1",
        current_stage=ProgramStage.REVIEW,
        steps=[
            WorkflowStepBlueprint(
                step_id="prog-1-evidence-review",
                stage_kind=WorkflowStageKind.EVIDENCE_REVIEW,
                objective="confirm the evidence base before assay spend",
                evidence_needs=[EvidenceNeed.LITERATURE, EvidenceNeed.STRUCTURE],
                review_gate_ids=["pre-assay-review"],
                blocking=True,
            ),
            WorkflowStepBlueprint(
                step_id="prog-1-assay-execution",
                stage_kind=WorkflowStageKind.ASSAY_EXECUTION,
                objective="run blocking assays for decision support",
                evidence_needs=[EvidenceNeed.ASSAY],
                assay_ids=["assay-primary-binding"],
                blocking=True,
            ),
        ],
        open_evidence_needs=[EvidenceNeed.ASSAY],
        blocking_assay_ids=["assay-primary-binding"],
        blocking_review_gate_ids=["pre-assay-review"],
    )

    summary = workflow_blueprint_summary(blueprint)

    assert summary["current_stage"] == "review"
    assert summary["step_count"] == 2
    assert summary["step_ids"] == [
        "prog-1-evidence-review",
        "prog-1-assay-execution",
    ]
    assert summary["open_evidence_needs"] == ["assay"]
    assert summary["blocking_assay_ids"] == ["assay-primary-binding"]
    assert summary["blocking_review_gate_ids"] == ["pre-assay-review"]


def test_workflow_blueprint_for_program_routes_assays_and_reviews() -> None:
    program = create_program_spec(
        program_id="prog-2",
        name="reviewable progression",
        objective="connect scientific stages to owned package contracts",
        target_id="target-2",
        target_name="Target 2",
        sequence="ACDEFGHIKLMNPQRSTVWY",
        organism="human",
        mechanism="stabilize productive state",
    )
    program.stage = ProgramStage.REVIEW
    program.assay_panel.append(
        AssayRequirement(
            assay_id="assay-primary-binding",
            purpose="confirm target engagement",
            readout="binding_score",
            sample_kind="biophysical",
            blocking=True,
        )
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

    blueprint = workflow_blueprint_for_program(program)

    assert blueprint.program_id == "prog-2"
    assert [step.stage_kind for step in blueprint.steps] == [
        WorkflowStageKind.INTAKE,
        WorkflowStageKind.EVIDENCE_REVIEW,
        WorkflowStageKind.ASSAY_EXECUTION,
        WorkflowStageKind.DECISION_REVIEW,
        WorkflowStageKind.LEARNING_LOOP,
    ]
    assert blueprint.blocking_assay_ids == ["assay-primary-binding"]
    assert blueprint.blocking_review_gate_ids == ["review-pre-synthesis"]

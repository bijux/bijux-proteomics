# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Scientific workflow blueprints for reviewable proteomics programs."""

from __future__ import annotations

from enum import StrEnum

from pydantic import ConfigDict, Field

from bijux_proteomics.program_spec import EvidenceNeed, ProgramStage
from bijux_proteomics.programs import ProgramSpec
from bijux_proteomics_foundation import AssayId, JsonModel, ProgramId


class WorkflowStageKind(StrEnum):
    """High-level scientific workflow stages for one program."""

    INTAKE = "intake"
    EVIDENCE_REVIEW = "evidence_review"
    ASSAY_EXECUTION = "assay_execution"
    DECISION_REVIEW = "decision_review"
    LEARNING_LOOP = "learning_loop"


class WorkflowStepBlueprint(JsonModel):
    """One explicit workflow step in a scientific program."""

    model_config = ConfigDict(extra="forbid")

    step_id: str = Field(..., min_length=1, description="Stable workflow step id.")
    stage_kind: WorkflowStageKind = Field(
        ..., description="Coarse scientific workflow stage."
    )
    objective: str = Field(..., min_length=1, description="Why the step exists.")
    evidence_needs: list[EvidenceNeed] = Field(
        default_factory=list,
        description="Evidence families required for this step.",
    )
    assay_ids: list[AssayId] = Field(
        default_factory=list,
        description="Assays consumed or executed in this step.",
    )
    review_gate_ids: list[str] = Field(
        default_factory=list,
        description="Review gates that must evaluate this step.",
    )
    blocking: bool = Field(
        default=False,
        description="Whether downstream workflow progress depends on this step.",
    )


class ScientificWorkflowBlueprint(JsonModel):
    """Reviewable workflow outline for one proteomics program."""

    model_config = ConfigDict(extra="forbid")

    program_id: ProgramId = Field(..., description="Program identifier.")
    current_stage: ProgramStage = Field(
        ..., description="Current lifecycle stage of the program."
    )
    steps: list[WorkflowStepBlueprint] = Field(
        default_factory=list,
        description="Ordered scientific workflow steps.",
    )
    open_evidence_needs: list[EvidenceNeed] = Field(
        default_factory=list,
        description="Evidence needs that remain unresolved in this blueprint.",
    )
    blocking_assay_ids: list[AssayId] = Field(
        default_factory=list,
        description="Blocking assays that still anchor downstream progress.",
    )
    blocking_review_gate_ids: list[str] = Field(
        default_factory=list,
        description="Blocking review gates that still anchor downstream progress.",
    )


def build_program_workflow_blueprint(
    program_id: ProgramId,
    *,
    current_stage: ProgramStage,
    evidence_needs: list[EvidenceNeed],
    assay_ids: list[AssayId],
    blocking_assay_ids: list[AssayId],
    review_gate_ids: list[str],
    blocking_review_gate_ids: list[str],
    lab_feedback_required: bool,
) -> ScientificWorkflowBlueprint:
    """Build a stable workflow outline from program-facing inputs."""
    steps: list[WorkflowStepBlueprint] = [
        WorkflowStepBlueprint(
            step_id=f"{program_id}-intake",
            stage_kind=WorkflowStageKind.INTAKE,
            objective="capture target framing, objective, and operating context",
            blocking=True,
        )
    ]

    if evidence_needs:
        steps.append(
            WorkflowStepBlueprint(
                step_id=f"{program_id}-evidence-review",
                stage_kind=WorkflowStageKind.EVIDENCE_REVIEW,
                objective="review whether the required evidence base is decision-ready",
                evidence_needs=list(evidence_needs),
                review_gate_ids=list(review_gate_ids),
                blocking=True,
            )
        )
    if assay_ids:
        steps.append(
            WorkflowStepBlueprint(
                step_id=f"{program_id}-assay-execution",
                stage_kind=WorkflowStageKind.ASSAY_EXECUTION,
                objective="run or interpret planned assays before downstream advancement",
                evidence_needs=[EvidenceNeed.ASSAY],
                assay_ids=list(assay_ids),
                blocking=bool(blocking_assay_ids),
            )
        )
    if review_gate_ids:
        steps.append(
            WorkflowStepBlueprint(
                step_id=f"{program_id}-decision-review",
                stage_kind=WorkflowStageKind.DECISION_REVIEW,
                objective="route scientific progression through explicit review gates",
                review_gate_ids=list(review_gate_ids),
                blocking=bool(blocking_review_gate_ids),
            )
        )
    if current_stage is ProgramStage.LEARNING or lab_feedback_required:
        steps.append(
            WorkflowStepBlueprint(
                step_id=f"{program_id}-learning-loop",
                stage_kind=WorkflowStageKind.LEARNING_LOOP,
                objective="capture assay feedback and convert it into the next program revision",
                assay_ids=list(assay_ids),
                blocking=False,
            )
        )

    return ScientificWorkflowBlueprint(
        program_id=program_id,
        current_stage=current_stage,
        steps=steps,
        open_evidence_needs=list(evidence_needs),
        blocking_assay_ids=list(blocking_assay_ids),
        blocking_review_gate_ids=list(blocking_review_gate_ids),
    )


def workflow_blueprint_for_program(program: ProgramSpec) -> ScientificWorkflowBlueprint:
    """Build a scientific workflow blueprint directly from a program spec."""
    return build_program_workflow_blueprint(
        program.program_id,
        current_stage=program.stage,
        evidence_needs=list(program.evidence_needs),
        assay_ids=[assay.assay_id for assay in program.assay_panel],
        blocking_assay_ids=[
            assay.assay_id for assay in program.assay_panel if assay.blocking
        ],
        review_gate_ids=[gate.gate_id for gate in program.review_gates],
        blocking_review_gate_ids=[
            gate.gate_id for gate in program.review_gates if gate.blocking
        ],
        lab_feedback_required=program.operating_model.lab_feedback_required,
    )


def workflow_blueprint_summary(
    blueprint: ScientificWorkflowBlueprint,
) -> dict[str, object]:
    """Return a compact workflow summary for docs, CLIs, and dashboards."""
    return {
        "program_id": blueprint.program_id,
        "current_stage": blueprint.current_stage.value,
        "step_count": len(blueprint.steps),
        "step_ids": [step.step_id for step in blueprint.steps],
        "open_evidence_needs": [need.value for need in blueprint.open_evidence_needs],
        "blocking_assay_ids": list(blueprint.blocking_assay_ids),
        "blocking_review_gate_ids": list(blueprint.blocking_review_gate_ids),
    }

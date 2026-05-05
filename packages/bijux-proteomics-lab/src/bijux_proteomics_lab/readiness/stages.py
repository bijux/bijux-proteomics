# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Workflow-stage readiness summaries for lab-facing program execution."""

from __future__ import annotations

from pydantic import ConfigDict, Field

from bijux_proteomics.domain.program_spec import ProgramSpec
from bijux_proteomics.workflow.blueprint import (
    WorkflowStageKind,
    workflow_blueprint_for_program,
)
from bijux_proteomics_foundation import JsonModel, ProgramId
from bijux_proteomics_knowledge.memory.evidence import EvidenceBundle, evidence_gaps


class WorkflowReadinessStep(JsonModel):
    """Readiness status for one workflow step."""

    model_config = ConfigDict(extra="forbid")

    step_id: str = Field(..., min_length=1, description="Workflow step id.")
    stage_kind: WorkflowStageKind = Field(..., description="Workflow stage kind.")
    ready: bool = Field(..., description="Whether the step is currently ready.")
    blockers: list[str] = Field(
        default_factory=list,
        description="Concrete blockers that still stop this step.",
    )


class WorkflowReadinessSummary(JsonModel):
    """Decision-facing view of which workflow stages are blocked."""

    model_config = ConfigDict(extra="forbid")

    program_id: ProgramId = Field(..., description="Program identifier.")
    ready_step_count: int = Field(..., ge=0, description="Ready workflow steps.")
    blocked_step_count: int = Field(..., ge=0, description="Blocked workflow steps.")
    missing_evidence_needs: list[str] = Field(
        default_factory=list,
        description="Evidence needs still missing from the bundle.",
    )
    blocking_assay_ids: list[str] = Field(
        default_factory=list,
        description="Blocking assays still attached to the workflow.",
    )
    blocking_review_gate_ids: list[str] = Field(
        default_factory=list,
        description="Blocking review gates still attached to the workflow.",
    )
    step_statuses: list[WorkflowReadinessStep] = Field(
        default_factory=list,
        description="Readiness status for each workflow step.",
    )


def summarize_workflow_readiness(
    program: ProgramSpec, bundle: EvidenceBundle
) -> WorkflowReadinessSummary:
    """Summarize workflow readiness from current evidence and workflow shape."""
    blueprint = workflow_blueprint_for_program(program)
    missing = set(
        evidence_gaps(bundle, [need.value for need in program.evidence_needs])
    )
    step_statuses: list[WorkflowReadinessStep] = []

    for step in blueprint.steps:
        blockers = [
            f"missing_evidence:{need.value}"
            for need in step.evidence_needs
            if need.value in missing
        ]
        if (
            step.stage_kind is WorkflowStageKind.ASSAY_EXECUTION
            and blueprint.blocking_assay_ids
            and "assay" in missing
        ):
            blockers.extend(
                f"blocking_assay:{assay_id}"
                for assay_id in blueprint.blocking_assay_ids
            )
        if (
            step.stage_kind is WorkflowStageKind.DECISION_REVIEW
            and blueprint.blocking_review_gate_ids
        ):
            blockers.extend(
                f"blocking_review_gate:{gate_id}"
                for gate_id in blueprint.blocking_review_gate_ids
            )
        step_statuses.append(
            WorkflowReadinessStep(
                step_id=step.step_id,
                stage_kind=step.stage_kind,
                ready=not blockers,
                blockers=blockers,
            )
        )

    return WorkflowReadinessSummary(
        program_id=program.program_id,
        ready_step_count=sum(1 for step in step_statuses if step.ready),
        blocked_step_count=sum(1 for step in step_statuses if not step.ready),
        missing_evidence_needs=sorted(missing),
        blocking_assay_ids=list(blueprint.blocking_assay_ids),
        blocking_review_gate_ids=list(blueprint.blocking_review_gate_ids),
        step_statuses=step_statuses,
    )


__all__ = [
    "WorkflowReadinessStep",
    "WorkflowReadinessSummary",
    "summarize_workflow_readiness",
]

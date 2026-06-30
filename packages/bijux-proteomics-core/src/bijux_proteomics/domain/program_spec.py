# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Top-level program specification models and helpers."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import ConfigDict, Field

from bijux_proteomics.domain.assays import AssayRequirement
from bijux_proteomics.domain.constraints import ScientificConstraint
from bijux_proteomics.domain.context import ProgramContext
from bijux_proteomics.domain.criteria import SuccessCriterion
from bijux_proteomics.domain.liabilities import ProgramLiability
from bijux_proteomics.domain.operating_model import OperatingModel
from bijux_proteomics.domain.reviews import ReviewGate
from bijux_proteomics.domain.targets import ProteinTarget
from bijux_proteomics.sequences.fasta import ProteinSequence
from bijux_proteomics_foundation import DocumentSchema, JsonModel, ProgramId


class EvidenceNeed(StrEnum):
    """Evidence families that make a program decision-ready."""

    LITERATURE = "literature"
    STRUCTURE = "structure"
    ASSAY = "assay"
    PATHWAY = "pathway"
    SAFETY = "safety"


class ProgramStage(StrEnum):
    """Lifecycle stages for a protein program."""

    SCOPING = "scoping"
    DESIGN = "design"
    REVIEW = "review"
    LAB_READY = "lab_ready"
    LEARNING = "learning"


class ProgramSpec(JsonModel):
    """Top-level program document for a protein effort."""

    model_config = ConfigDict(extra="forbid")

    program_id: ProgramId = Field(..., description="Stable program identifier.")
    name: str = Field(..., min_length=1, description="Program name.")
    objective: str = Field(..., min_length=1, description="Scientific objective.")
    mechanism_hypothesis: str | None = Field(
        default=None,
        description="Explicit mechanistic hypothesis under test.",
    )
    intervention_goal: str | None = Field(
        default=None,
        description="Desired intervention outcome such as inhibit, stabilize, or degrade.",
    )
    modality_context: str | None = Field(
        default=None,
        description="Modality context such as degrader, antibody, or enzyme modulator.",
    )
    success_mode: str | None = Field(
        default=None,
        description="Primary success mode such as inhibitor, binder, or stability rescue.",
    )
    translational_assumptions: list[str] = Field(
        default_factory=list,
        description="Major translational assumptions that should be validated experimentally.",
    )
    key_unknowns: list[str] = Field(
        default_factory=list,
        description="Key scientific unknowns that must be reduced for progression.",
    )
    critical_failure_modes: list[str] = Field(
        default_factory=list,
        description="Failure modes that would terminate or significantly reset the program.",
    )
    stage: ProgramStage = Field(
        default=ProgramStage.SCOPING,
        description="Current lifecycle stage.",
    )
    target: ProteinTarget = Field(..., description="Protein target definition.")
    constraints: list[ScientificConstraint] = Field(
        default_factory=list,
        description="Scientific and operational constraints.",
    )
    liabilities: list[ProgramLiability] = Field(
        default_factory=list,
        description="Known liabilities tracked at the program level.",
    )
    success_criteria: list[SuccessCriterion] = Field(
        default_factory=list,
        description="Program success criteria.",
    )
    assay_panel: list[AssayRequirement] = Field(
        default_factory=list,
        description="Assays required for the program.",
    )
    review_gates: list[ReviewGate] = Field(
        default_factory=list,
        description="Human approval gates.",
    )
    evidence_needs: list[EvidenceNeed] = Field(
        default_factory=list,
        description="Evidence types that must be covered.",
    )
    operating_model: OperatingModel = Field(
        default_factory=OperatingModel,
        description="How the program is governed across compute, review, and lab work.",
    )
    document_schema: DocumentSchema = Field(
        default_factory=lambda: DocumentSchema(created_by="bijux-proteomics-core"),
        description="Schema and provenance metadata.",
    )
    context: ProgramContext = Field(
        default_factory=ProgramContext,
        description="Structured program context for portfolio and delivery framing.",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Creation timestamp.",
    )


class StageEligibility(JsonModel):
    """Eligibility view for entering or operating in a lifecycle stage."""

    model_config = ConfigDict(extra="forbid")

    program_id: ProgramId = Field(..., description="Program identifier.")
    stage: ProgramStage = Field(..., description="Stage evaluated for readiness.")
    eligible: bool = Field(
        ..., description="Whether required prerequisites are satisfied."
    )
    blockers: list[str] = Field(
        default_factory=list,
        description="Concrete blockers that prevent this stage from being eligible.",
    )


def create_program_spec(
    *,
    program_id: str,
    name: str,
    objective: str,
    target_id: str,
    target_name: str,
    sequence: str,
    organism: str,
    mechanism: str,
) -> ProgramSpec:
    """Create a minimal but valid protein program document."""
    return ProgramSpec(
        program_id=program_id,
        name=name,
        objective=objective,
        mechanism_hypothesis=mechanism,
        intervention_goal="modulate_target_state",
        modality_context="protein_engineering",
        success_mode="binder",
        key_unknowns=["target engagement durability in biological system"],
        critical_failure_modes=["loss of target selectivity"],
        target=ProteinTarget(
            target_id=target_id,
            name=target_name,
            sequence=ProteinSequence(target_id=target_id, residues=sequence),
            organism=organism,
            mechanism=mechanism,
        ),
        evidence_needs=[
            EvidenceNeed.LITERATURE,
            EvidenceNeed.STRUCTURE,
            EvidenceNeed.ASSAY,
        ],
    )


def program_summary(program: ProgramSpec) -> dict[str, object]:
    """Return a compact summary for CLI and dashboards."""
    return {
        "program_id": program.program_id,
        "target_id": program.target.target_id,
        "target_class": program.target.target_class,
        "target_localization": program.target.subcellular_localization,
        "stage": program.stage.value,
        "mechanism_hypothesis": program.mechanism_hypothesis,
        "intervention_goal": program.intervention_goal,
        "modality_context": program.modality_context,
        "success_mode": program.success_mode,
        "key_unknown_count": len(program.key_unknowns),
        "critical_failure_mode_count": len(program.critical_failure_modes),
        "schema_version": program.document_schema.schema_version,
        "constraint_count": len(program.constraints),
        "liability_count": len(program.liabilities),
        "assay_count": len(program.assay_panel),
        "review_gate_count": len(program.review_gates),
        "evidence_needs": [need.value for need in program.evidence_needs],
        "human_review_required": program.operating_model.human_review_required,
        "lab_feedback_required": program.operating_model.lab_feedback_required,
        "therapeutic_area": program.context.portfolio.therapeutic_area,
        "decision_horizon": program.context.delivery.decision_horizon,
    }


def assess_stage_eligibility(
    program: ProgramSpec,
    stage: ProgramStage | None = None,
) -> StageEligibility:
    """Assess whether a program satisfies prerequisites for a target stage."""
    stage = stage or program.stage
    blockers: list[str] = []
    if stage is ProgramStage.REVIEW and not program.review_gates:
        blockers.append("review stage requires at least one review gate")
    if stage is ProgramStage.LAB_READY:
        if not any(assay.blocking for assay in program.assay_panel):
            blockers.append("lab-ready stage requires at least one blocking assay")
        if not any(gate.blocking for gate in program.review_gates):
            blockers.append(
                "lab-ready stage requires at least one blocking review gate"
            )
    if stage is ProgramStage.LEARNING and not program.assay_panel:
        blockers.append("learning stage requires retained assay definitions")
    return StageEligibility(
        program_id=program.program_id,
        stage=stage,
        eligible=not blockers,
        blockers=blockers,
    )


def revise_program(
    program: ProgramSpec,
    *,
    actor: str,
    tag: str | None = None,
) -> ProgramSpec:
    """Return a revised program with incremented schema revision and content hash."""
    touched = program.document_schema.touch(actor, tag=tag)
    hashed = touched.with_content_hash(program_summary(program))
    return program.model_copy(update={"document_schema": hashed})

# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Top-level program specification models and helpers."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import ConfigDict, Field

from bijux_proteomics.assays import AssayRequirement
from bijux_proteomics.constraints import ScientificConstraint
from bijux_proteomics.criteria import SuccessCriterion
from bijux_proteomics.operating_model import OperatingModel
from bijux_proteomics.reviews import ReviewGate
from bijux_proteomics_foundation import DocumentSchema, JsonModel, ProgramId
from bijux_proteomics.targets import ProteinTarget


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
    stage: ProgramStage = Field(
        default=ProgramStage.SCOPING,
        description="Current lifecycle stage.",
    )
    target: ProteinTarget = Field(..., description="Protein target definition.")
    constraints: list[ScientificConstraint] = Field(
        default_factory=list,
        description="Scientific and operational constraints.",
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
    metadata: dict[str, str] = Field(
        default_factory=dict,
        description="Free-form metadata for program setup.",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Creation timestamp.",
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
        target=ProteinTarget(
            target_id=target_id,
            name=target_name,
            sequence=sequence,
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
        "stage": program.stage.value,
        "schema_version": program.document_schema.schema_version,
        "constraint_count": len(program.constraints),
        "assay_count": len(program.assay_panel),
        "review_gate_count": len(program.review_gates),
        "evidence_needs": [need.value for need in program.evidence_needs],
        "human_review_required": program.operating_model.human_review_required,
        "lab_feedback_required": program.operating_model.lab_feedback_required,
    }

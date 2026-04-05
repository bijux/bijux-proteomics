# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Program definitions for scientific protein work."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
import re

from pydantic import BaseModel, ConfigDict, Field, field_validator

_SEQUENCE_RE = re.compile(r"^[ACDEFGHIKLMNPQRSTVWY]+$")


class MeasurementDirection(StrEnum):
    """Target direction for a success criterion."""

    MAXIMIZE = "maximize"
    MINIMIZE = "minimize"
    BOUND = "bound"


class EvidenceNeed(StrEnum):
    """Evidence families that make a program decision-ready."""

    LITERATURE = "literature"
    STRUCTURE = "structure"
    ASSAY = "assay"
    PATHWAY = "pathway"
    SAFETY = "safety"


class ProteinTarget(BaseModel):
    """Target definition for a discovery or engineering program."""

    model_config = ConfigDict(extra="forbid")

    target_id: str = Field(..., min_length=1, description="Stable target identifier.")
    name: str = Field(..., min_length=1, description="Human-readable target name.")
    sequence: str = Field(
        ..., min_length=1, description="Reference amino-acid sequence."
    )
    organism: str = Field(..., min_length=1, description="Source organism.")
    mechanism: str = Field(
        ..., min_length=1, description="Working biological hypothesis."
    )
    desired_outcomes: list[str] = Field(
        default_factory=list,
        description="Desired biological or engineering outcomes.",
    )
    blocked_outcomes: list[str] = Field(
        default_factory=list,
        description="Known failure modes or safety concerns.",
    )

    @field_validator("sequence")
    @classmethod
    def _validate_sequence(cls, value: str) -> str:
        sequence = value.strip().upper()
        if not _SEQUENCE_RE.fullmatch(sequence):
            raise ValueError("sequence must contain only canonical amino-acid symbols")
        return sequence


class ScientificConstraint(BaseModel):
    """Constraint that narrows the search space."""

    model_config = ConfigDict(extra="forbid")

    constraint_id: str = Field(
        ..., min_length=1, description="Stable constraint identifier."
    )
    category: str = Field(..., min_length=1, description="Constraint family.")
    statement: str = Field(..., min_length=1, description="Constraint text.")
    rationale: str = Field(..., min_length=1, description="Why this constraint exists.")
    threshold: float | None = Field(
        default=None,
        description="Optional numeric threshold for the constraint.",
    )


class SuccessCriterion(BaseModel):
    """Condition required for a program to advance."""

    model_config = ConfigDict(extra="forbid")

    criterion_id: str = Field(
        ..., min_length=1, description="Stable criterion identifier."
    )
    metric: str = Field(..., min_length=1, description="Metric to evaluate.")
    direction: MeasurementDirection = Field(..., description="Optimization direction.")
    threshold: float = Field(..., description="Threshold for the metric.")
    unit: str | None = Field(default=None, description="Optional measurement unit.")


class ReviewGate(BaseModel):
    """Human oversight checkpoint before expensive actions."""

    model_config = ConfigDict(extra="forbid")

    gate_id: str = Field(
        ..., min_length=1, description="Stable review gate identifier."
    )
    name: str = Field(..., min_length=1, description="Review gate name.")
    required_roles: list[str] = Field(
        default_factory=list,
        description="Roles that must sign off.",
    )
    decision_inputs: list[str] = Field(
        default_factory=list,
        description="Evidence and artifacts needed for signoff.",
    )
    blocking: bool = Field(
        default=True,
        description="Whether execution must stop until approval is recorded.",
    )


class AssayRequirement(BaseModel):
    """Assay needed to validate a program."""

    model_config = ConfigDict(extra="forbid")

    assay_id: str = Field(..., min_length=1, description="Stable assay identifier.")
    purpose: str = Field(..., min_length=1, description="Why the assay exists.")
    readout: str = Field(
        ..., min_length=1, description="Primary output or measurement."
    )
    sample_kind: str = Field(..., min_length=1, description="Sample or system type.")
    replicates: int = Field(default=3, ge=1, description="Recommended replicate count.")
    blocking: bool = Field(
        default=False,
        description="Whether the assay must be run before the program advances.",
    )


class ProgramSpec(BaseModel):
    """Top-level program document for a protein effort."""

    model_config = ConfigDict(extra="forbid")

    program_id: str = Field(..., min_length=1, description="Stable program identifier.")
    name: str = Field(..., min_length=1, description="Program name.")
    objective: str = Field(..., min_length=1, description="Scientific objective.")
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
        "constraint_count": len(program.constraints),
        "assay_count": len(program.assay_panel),
        "review_gate_count": len(program.review_gates),
        "evidence_needs": [need.value for need in program.evidence_needs],
    }

# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Target models for protein programs."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field
from bijux_proteomics_foundation import TargetId
from bijux_proteomics.sequences import ProteinSequence


class OutcomeSeverity(StrEnum):
    """Severity level for desired or blocked outcomes."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class TargetOutcome(BaseModel):
    """Typed target outcome with severity and rationale."""

    model_config = ConfigDict(extra="forbid")

    code: str = Field(..., min_length=1, description="Stable outcome code.")
    summary: str = Field(..., min_length=1, description="Human-readable outcome summary.")
    severity: OutcomeSeverity = Field(
        default=OutcomeSeverity.MEDIUM,
        description="Severity for blocked outcomes or importance for desired outcomes.",
    )
    rationale: str | None = Field(
        default=None,
        description="Optional reasoning that explains the outcome classification.",
    )


class TargetAnnotation(BaseModel):
    """Evidence-backed annotation on the target definition."""

    model_config = ConfigDict(extra="forbid")

    annotation_id: str = Field(..., min_length=1, description="Stable annotation identifier.")
    statement: str = Field(..., min_length=1, description="Annotation text.")
    evidence_ids: list[str] = Field(
        default_factory=list,
        description="Evidence identifiers supporting this annotation.",
    )


class ProteinTarget(BaseModel):
    """Target definition for a discovery or engineering program."""

    model_config = ConfigDict(extra="forbid")

    target_id: TargetId = Field(..., description="Stable target identifier.")
    name: str = Field(..., min_length=1, description="Human-readable target name.")
    sequence: ProteinSequence = Field(..., description="Reference amino-acid sequence.")
    organism: str = Field(..., min_length=1, description="Source organism.")
    mechanism: str = Field(
        ..., min_length=1, description="Working biological hypothesis."
    )
    target_class: str | None = Field(
        default=None,
        description="Target class such as enzyme, receptor, or scaffold.",
    )
    subcellular_localization: str | None = Field(
        default=None,
        description="Expected subcellular localization context.",
    )
    isoforms: list[str] = Field(
        default_factory=list,
        description="Known isoform identifiers relevant to this program.",
    )
    pathway_roles: list[str] = Field(
        default_factory=list,
        description="Pathway roles relevant to the target mechanism.",
    )
    desired_outcomes: list[str] = Field(
        default_factory=list,
        description="Desired biological or engineering outcomes.",
    )
    blocked_outcomes: list[str] = Field(
        default_factory=list,
        description="Known failure modes or safety concerns.",
    )
    desired_outcome_records: list[TargetOutcome] = Field(
        default_factory=list,
        description="Structured desired outcomes with explicit severity and rationale.",
    )
    blocked_outcome_records: list[TargetOutcome] = Field(
        default_factory=list,
        description="Structured blocked outcomes with explicit severity and rationale.",
    )
    annotations: list[TargetAnnotation] = Field(
        default_factory=list,
        description="Evidence-backed target annotations.",
    )


def target_summary(target: ProteinTarget) -> dict[str, object]:
    """Return a compact target summary suitable for planning and ranking."""
    high_risk_blocks = [
        outcome.code
        for outcome in target.blocked_outcome_records
        if outcome.severity is OutcomeSeverity.HIGH
    ]
    annotation_evidence_ids = sorted(
        {
            evidence_id
            for annotation in target.annotations
            for evidence_id in annotation.evidence_ids
        }
    )
    return {
        "target_id": target.target_id,
        "organism": target.organism,
        "target_class": target.target_class,
        "subcellular_localization": target.subcellular_localization,
        "isoform_count": len(target.isoforms),
        "pathway_role_count": len(target.pathway_roles),
        "blocked_outcomes": len(target.blocked_outcomes)
        + len(target.blocked_outcome_records),
        "high_risk_block_codes": high_risk_blocks,
        "annotation_count": len(target.annotations),
        "annotation_evidence_ids": annotation_evidence_ids,
    }

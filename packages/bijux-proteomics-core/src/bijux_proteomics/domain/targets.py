# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Target models for protein programs."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from bijux_proteomics.sequences.fasta import ProteinSequence
from bijux_proteomics_foundation import TargetId


class OutcomeSeverity(StrEnum):
    """Severity level for desired or blocked outcomes."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class TargetOutcome(BaseModel):
    """Typed target outcome with severity and rationale."""

    model_config = ConfigDict(extra="forbid")

    code: str = Field(..., min_length=1, description="Stable outcome code.")
    summary: str = Field(
        ..., min_length=1, description="Human-readable outcome summary."
    )
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

    annotation_id: str = Field(
        ..., min_length=1, description="Stable annotation identifier."
    )
    statement: str = Field(..., min_length=1, description="Annotation text.")
    evidence_ids: list[str] = Field(
        default_factory=list,
        description="Evidence identifiers supporting this annotation.",
    )


class ProteinDomain(BaseModel):
    """Structured domain annotation for the target."""

    model_config = ConfigDict(extra="forbid")

    domain_id: str = Field(..., min_length=1, description="Stable domain identifier.")
    name: str = Field(..., min_length=1, description="Domain name.")
    start: int = Field(..., ge=1, description="Start residue (1-based).")
    end: int = Field(..., ge=1, description="End residue (1-based).")


class ProteinMotif(BaseModel):
    """Motif annotation for the target sequence."""

    model_config = ConfigDict(extra="forbid")

    motif_id: str = Field(..., min_length=1, description="Stable motif identifier.")
    name: str = Field(..., min_length=1, description="Motif name.")
    pattern: str = Field(..., min_length=1, description="Motif sequence pattern.")
    start: int | None = Field(
        default=None, ge=1, description="Optional motif start residue."
    )


class PtmHotspot(BaseModel):
    """Post-translational modification hotspot metadata."""

    model_config = ConfigDict(extra="forbid")

    site: str = Field(..., min_length=1, description="PTM site label such as S123.")
    modification: str = Field(..., min_length=1, description="Modification type.")
    evidence_ids: list[str] = Field(
        default_factory=list,
        description="Evidence identifiers supporting the hotspot.",
    )


class ComplexMembership(BaseModel):
    """Complex membership annotation for the target."""

    model_config = ConfigDict(extra="forbid")

    complex_id: str = Field(..., min_length=1, description="Complex identifier.")
    role: str = Field(
        ..., min_length=1, description="Role of the target in the complex."
    )


class TractabilityFlag(BaseModel):
    """Tractability signals for the target."""

    model_config = ConfigDict(extra="forbid")

    code: str = Field(..., min_length=1, description="Stable tractability flag code.")
    summary: str = Field(..., min_length=1, description="Tractability summary.")
    severity: OutcomeSeverity = Field(
        default=OutcomeSeverity.MEDIUM,
        description="How strongly the flag impacts tractability.",
    )


class MechanismLiability(BaseModel):
    """Mechanism-specific liability attached to the target."""

    model_config = ConfigDict(extra="forbid")

    liability_id: str = Field(
        ..., min_length=1, description="Stable liability identifier."
    )
    summary: str = Field(..., min_length=1, description="Liability summary.")
    severity: OutcomeSeverity = Field(
        default=OutcomeSeverity.MEDIUM,
        description="Severity of the liability.",
    )
    evidence_ids: list[str] = Field(
        default_factory=list,
        description="Evidence identifiers supporting the liability.",
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
    domains: list[ProteinDomain] = Field(
        default_factory=list,
        description="Structured domain annotations.",
    )
    motifs: list[ProteinMotif] = Field(
        default_factory=list,
        description="Motif annotations on the target sequence.",
    )
    ptm_hotspots: list[PtmHotspot] = Field(
        default_factory=list,
        description="PTM hotspot annotations.",
    )
    paralog_family: str | None = Field(
        default=None,
        description="Paralog or family context for the target.",
    )
    complex_memberships: list[ComplexMembership] = Field(
        default_factory=list,
        description="Known complex memberships for the target.",
    )
    tractability_flags: list[TractabilityFlag] = Field(
        default_factory=list,
        description="Tractability flags that affect program risk.",
    )
    mechanism_liabilities: list[MechanismLiability] = Field(
        default_factory=list,
        description="Mechanism-specific liabilities for the target.",
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
        "domain_count": len(target.domains),
        "motif_count": len(target.motifs),
        "ptm_hotspot_count": len(target.ptm_hotspots),
        "complex_membership_count": len(target.complex_memberships),
        "tractability_flag_count": len(target.tractability_flags),
        "mechanism_liability_count": len(target.mechanism_liabilities),
        "pathway_role_count": len(target.pathway_roles),
        "blocked_outcomes": len(target.blocked_outcomes)
        + len(target.blocked_outcome_records),
        "high_risk_block_codes": high_risk_blocks,
        "annotation_count": len(target.annotations),
        "annotation_evidence_ids": annotation_evidence_ids,
    }


def summarize_tractability(target: ProteinTarget) -> dict[str, object]:
    """Summarize tractability posture for a target."""
    high_severity_flags = [
        flag.code
        for flag in target.tractability_flags
        if flag.severity is OutcomeSeverity.HIGH
    ]
    high_severity_liabilities = [
        liability.liability_id
        for liability in target.mechanism_liabilities
        if liability.severity is OutcomeSeverity.HIGH
    ]
    return {
        "tractability_flag_count": len(target.tractability_flags),
        "mechanism_liability_count": len(target.mechanism_liabilities),
        "high_severity_flags": high_severity_flags,
        "high_severity_liabilities": high_severity_liabilities,
    }

# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Constraint models for protein programs."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field
from bijux_proteomics_foundation import EvidenceId


class ConstraintCategory(StrEnum):
    """Proteomics-aware constraint categories."""

    CATALYTIC_RESIDUE = "catalytic_residue"
    INTERFACE_CONSERVATION = "interface_conservation"
    PTM_PRESERVATION = "ptm_preservation"
    DOMAIN_MUTABILITY = "domain_mutability"
    CONSERVATION_LIMIT = "conservation_limit"
    STABILITY_FLOOR = "stability_floor"
    EXPRESSION_FLOOR = "expression_floor"
    AGGREGATION_CEILING = "aggregation_ceiling"
    IMMUNOGENICITY_CEILING = "immunogenicity_ceiling"
    DEVELOPABILITY = "developability"


class ScientificConstraint(BaseModel):
    """Constraint that narrows the search space."""

    model_config = ConfigDict(extra="forbid")

    constraint_id: EvidenceId = Field(..., description="Stable constraint identifier.")
    category: ConstraintCategory = Field(..., description="Constraint family.")
    statement: str = Field(..., min_length=1, description="Constraint text.")
    rationale: str = Field(..., min_length=1, description="Why this constraint exists.")
    affected_region: str | None = Field(
        default=None,
        description="Optional protein region or motif affected by the constraint.",
    )
    assay_context: str | None = Field(
        default=None,
        description="Assay or modality context where the constraint applies.",
    )
    blocker: bool = Field(
        default=False,
        description="Whether violating this constraint should block progression.",
    )
    mitigation_plan: str | None = Field(
        default=None,
        description="Mitigation plan when this constraint is at risk.",
    )
    threshold: float | None = Field(
        default=None,
        description="Optional numeric threshold for the constraint.",
    )


class ConstraintRiskReport(BaseModel):
    """Risk summary for a set of scientific constraints."""

    model_config = ConfigDict(extra="forbid")

    total_constraints: int = Field(..., ge=0, description="Total number of constraints evaluated.")
    blocker_count: int = Field(..., ge=0, description="Number of blocker constraints.")
    high_risk_constraints: list[str] = Field(
        default_factory=list,
        description="Constraint identifiers considered high risk.",
    )
    notes: list[str] = Field(default_factory=list, description="Risk interpretation notes.")


def build_protein_native_constraints(
    *,
    target_id: str,
    catalytic_region: str | None = None,
    interface_region: str | None = None,
) -> list[ScientificConstraint]:
    """Build a baseline protein-native constraint set for a program target."""
    constraints: list[ScientificConstraint] = [
        ScientificConstraint(
            constraint_id=f"{target_id}-stability-floor",
            category=ConstraintCategory.STABILITY_FLOOR,
            statement="maintain thermal stability above minimum gate",
            rationale="avoid unstable candidates that collapse in lab workflows",
            threshold=0.0,
            blocker=True,
            mitigation_plan="run thermal shift assay and redesign destabilizing substitutions",
        ),
        ScientificConstraint(
            constraint_id=f"{target_id}-aggregation-ceiling",
            category=ConstraintCategory.AGGREGATION_CEILING,
            statement="keep aggregation propensity below risk ceiling",
            rationale="high aggregation blocks expression and purification",
            threshold=0.0,
            blocker=True,
            mitigation_plan="screen sequence variants with reduced hydrophobic patching",
        ),
        ScientificConstraint(
            constraint_id=f"{target_id}-conservation-limit",
            category=ConstraintCategory.CONSERVATION_LIMIT,
            statement="limit edits at highly conserved positions",
            rationale="conserved sites often encode core function and selectivity",
            blocker=True,
            mitigation_plan="restrict mutational search around highly conserved residues",
        ),
    ]
    if catalytic_region:
        constraints.append(
            ScientificConstraint(
                constraint_id=f"{target_id}-catalytic-preservation",
                category=ConstraintCategory.CATALYTIC_RESIDUE,
                statement="preserve catalytic residues and local geometry",
                rationale="catalytic disruption can eliminate desired mechanism",
                affected_region=catalytic_region,
                blocker=True,
                mitigation_plan="require catalytic activity assay coverage before progression",
            )
        )
    if interface_region:
        constraints.append(
            ScientificConstraint(
                constraint_id=f"{target_id}-interface-mutability",
                category=ConstraintCategory.DOMAIN_MUTABILITY,
                statement="constrain mutational load at critical interaction interface",
                rationale="interface disruption can break target engagement or specificity",
                affected_region=interface_region,
                blocker=True,
                mitigation_plan="run selectivity and binding panel for interface-adjacent edits",
            )
        )
    return constraints


def assess_constraint_risk(constraints: list[ScientificConstraint]) -> ConstraintRiskReport:
    """Assess constraint risk based on blocker flags and missing mitigation plans."""
    blockers = [constraint for constraint in constraints if constraint.blocker]
    high_risk = [
        constraint.constraint_id
        for constraint in constraints
        if constraint.blocker and not constraint.mitigation_plan
    ]
    notes: list[str] = []
    if high_risk:
        notes.append("blocker constraints lack mitigation plans and require action")
    if not notes:
        notes.append("constraints have acceptable mitigation posture")
    return ConstraintRiskReport(
        total_constraints=len(constraints),
        blocker_count=len(blockers),
        high_risk_constraints=high_risk,
        notes=notes,
    )

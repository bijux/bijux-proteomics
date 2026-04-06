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
    threshold: float | None = Field(
        default=None,
        description="Optional numeric threshold for the constraint.",
    )

# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Constraint models for protein programs."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field
from bijux_proteomics_foundation import EvidenceId


class ScientificConstraint(BaseModel):
    """Constraint that narrows the search space."""

    model_config = ConfigDict(extra="forbid")

    constraint_id: EvidenceId = Field(..., description="Stable constraint identifier.")
    category: str = Field(..., min_length=1, description="Constraint family.")
    statement: str = Field(..., min_length=1, description="Constraint text.")
    rationale: str = Field(..., min_length=1, description="Why this constraint exists.")
    threshold: float | None = Field(
        default=None,
        description="Optional numeric threshold for the constraint.",
    )

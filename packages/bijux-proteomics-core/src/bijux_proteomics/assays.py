# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Assay requirements for protein programs."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field
from bijux_proteomics_foundation import AssayId


class AssayRequirement(BaseModel):
    """Assay needed to validate a program."""

    model_config = ConfigDict(extra="forbid")

    assay_id: AssayId = Field(..., description="Stable assay identifier.")
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

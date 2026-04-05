# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Candidate schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from agentic_proteins.domain.metrics.quality import ConfidenceVector


class CandidateStructure(BaseModel):
    """CandidateStructure."""

    model_config = ConfigDict(extra="forbid")

    structure_id: str = Field(..., min_length=1, description="Structure identifier.")
    provider: str = Field(..., min_length=1, description="Provider name.")
    pdb_text: str | None = Field(
        default=None, description="Optional PDB text for the structure."
    )
    metrics: dict[str, float] = Field(
        default_factory=dict, description="Structure-level metrics."
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Structure metadata."
    )


class Candidate(BaseModel):
    """Candidate."""

    model_config = ConfigDict(extra="forbid")

    candidate_id: str = Field(..., min_length=1, description="Candidate identifier.")
    sequence: str = Field(..., min_length=1, description="Amino-acid sequence.")
    structures: list[CandidateStructure] = Field(
        default_factory=list, description="Predicted structures."
    )
    metrics: dict[str, float] = Field(
        default_factory=dict, description="Candidate-level metrics."
    )
    flags: list[str] = Field(default_factory=list, description="Candidate flags.")
    provenance: dict[str, Any] = Field(
        default_factory=dict, description="Provenance metadata."
    )
    confidence: ConfidenceVector = Field(
        default_factory=ConfidenceVector,
        description="Confidence vector.",
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Candidate creation timestamp."
    )

# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""State snapshot schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, PrivateAttr

from agentic_proteins.core.decisions import Decision
from agentic_proteins.domain.metrics.quality import MetricValue


class ArtifactMetadata(BaseModel):
    """ArtifactMetadata."""

    model_config = ConfigDict(extra="forbid")

    artifact_id: str = Field(..., min_length=1, description="Artifact identifier.")
    kind: str = Field(..., min_length=1, description="Artifact kind.")
    description: str = Field(..., min_length=1, description="Artifact description.")
    tags: list[str] = Field(default_factory=list, description="Artifact tags.")


class ConfidenceItem(BaseModel):
    """ConfidenceItem."""

    model_config = ConfigDict(extra="forbid")

    subject: str = Field(
        ..., min_length=1, description="Confidence subject identifier."
    )
    score: float = Field(0.0, ge=0.0, le=1.0, description="Confidence score.")


class StateSnapshot(BaseModel):
    """StateSnapshot."""

    model_config = ConfigDict(extra="forbid")

    _frozen: bool = PrivateAttr(default=False)

    state_id: str = Field(..., description="State identifier.")
    parent_state_id: str | None = Field(default=None, description="Parent state id.")
    plan_fingerprint: str = Field(..., description="Plan fingerprint.")
    timestamp: datetime = Field(..., description="Snapshot timestamp.")
    agent_decisions: list[Decision] = Field(
        default_factory=list, description="Decisions."
    )
    artifacts: list[ArtifactMetadata] = Field(
        default_factory=list,
        description="Artifact metadata only.",
    )
    metrics: list[MetricValue] = Field(default_factory=list, description="Metrics.")
    confidence_summary: list[ConfidenceItem] = Field(
        default_factory=list,
        description="Confidence summary items.",
    )

    def __init__(self, **data: object) -> None:
        """__init__."""
        super().__init__(**data)
        object.__setattr__(self, "_frozen", True)

    def __setattr__(self, name: str, value: object) -> None:
        """__setattr__."""
        if name == "_frozen":
            object.__setattr__(self, name, value)
            return
        if not getattr(self, "_frozen", False):
            object.__setattr__(self, name, value)
            return
        raise TypeError("StateSnapshot is immutable")

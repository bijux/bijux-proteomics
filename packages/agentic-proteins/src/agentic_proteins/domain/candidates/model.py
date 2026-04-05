# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Candidate domain models."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from agentic_proteins.domain.metrics.quality import ConfidenceVector


@dataclass(frozen=True)
class Candidate:
    """Candidate."""

    candidate_id: str
    sequence: str
    metrics: dict[str, float] = field(default_factory=dict)
    confidence: ConfidenceVector = field(default_factory=ConfidenceVector)
    flags: list[str] = field(default_factory=list)
    provenance: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CandidateScore:
    """CandidateScore."""

    candidate_id: str
    score: float
    rank: int
    reasons: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class CandidateSelection:
    """CandidateSelection."""

    candidates: list[Candidate]
    scores: list[CandidateScore]
    pareto_front: list[str]
    frozen_ids: list[str]
    human_required: bool
    metadata: dict[str, Any] = field(default_factory=dict)

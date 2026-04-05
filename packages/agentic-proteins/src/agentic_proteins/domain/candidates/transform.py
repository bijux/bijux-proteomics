# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Candidate transformations."""

from __future__ import annotations

from agentic_proteins.domain.candidates.model import Candidate as DomainCandidate
from agentic_proteins.domain.candidates.schema import Candidate


def candidate_to_domain(candidate: Candidate) -> DomainCandidate:
    """candidate_to_domain."""
    return DomainCandidate(
        candidate_id=candidate.candidate_id,
        sequence=candidate.sequence,
        metrics=candidate.metrics,
        confidence=candidate.confidence,
        flags=candidate.flags,
        provenance=candidate.provenance,
    )

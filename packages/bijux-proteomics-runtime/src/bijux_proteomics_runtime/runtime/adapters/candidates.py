"""Runtime adapters for intelligence candidate domain models."""

from __future__ import annotations

from bijux_proteomics_intelligence.domain.candidates import (
    CandidateStore,
    candidate_to_domain,
    rank_candidates,
    select_candidates,
    update_candidate_from_result,
)
from bijux_proteomics_intelligence.domain.candidates.model import (
    Candidate as DomainCandidate,
)
from bijux_proteomics_intelligence.domain.candidates.model import (
    CandidateSelection,
)
from bijux_proteomics_intelligence.domain.candidates.schema import Candidate


def candidate_payload(candidate: Candidate) -> dict[str, object]:
    """Map candidate model to a runtime-safe artifact payload."""
    return {
        "candidate_id": candidate.candidate_id,
        "sequence": candidate.sequence,
        "metrics": dict(candidate.metrics),
        "flags": list(candidate.flags),
        "provenance": dict(candidate.provenance),
    }


__all__ = [
    "Candidate",
    "CandidateStore",
    "CandidateSelection",
    "DomainCandidate",
    "candidate_payload",
    "candidate_to_domain",
    "rank_candidates",
    "select_candidates",
    "update_candidate_from_result",
]

from __future__ import annotations

from bijux_proteomics_intelligence.domain.candidates.model import Candidate
from bijux_proteomics_intelligence.domain.metrics.quality import ConfidenceVector


def test_legacy_domain_candidate_model_smoke() -> None:
    candidate = Candidate(
        candidate_id="cand-1", sequence="ACDE", confidence=ConfidenceVector()
    )
    assert candidate.candidate_id == "cand-1"
    assert candidate.sequence == "ACDE"

from __future__ import annotations

from bijux_proteomics_intelligence.domain.candidates.schema import Candidate
from bijux_proteomics_runtime.runtime.adapters.candidates import candidate_payload


def test_candidate_payload_adapter_smoke() -> None:
    candidate = Candidate(candidate_id="cand-1", sequence="ACDE")
    payload = candidate_payload(candidate)
    assert payload["candidate_id"] == "cand-1"
    assert payload["sequence"] == "ACDE"

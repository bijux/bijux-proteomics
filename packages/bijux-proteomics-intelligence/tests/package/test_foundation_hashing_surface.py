# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_foundation import hash_payload as foundation_hash_payload
from bijux_proteomics_foundation import hash_text as foundation_hash_text
from bijux_proteomics_intelligence.candidates.fingerprints import (
    hash_payload,
    sha256_hex,
)


def test_intelligence_candidate_fingerprints_reuse_foundation_helpers() -> None:
    payload = {"program": "alpha", "weights": {"evidence": 3, "novelty": 1}}

    assert hash_payload(payload) == foundation_hash_payload(payload)
    assert sha256_hex("intelligence") == foundation_hash_text("intelligence")

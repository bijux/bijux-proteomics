# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_foundation import (
    fingerprint_model as foundation_fingerprint_model,
    to_canonical_json as foundation_to_canonical_json,
)
from bijux_proteomics_knowledge import (
    EvidenceBundle,
    fingerprint_model,
    to_canonical_json,
)


def test_canonical_serialization_and_fingerprint_are_stable() -> None:
    bundle = EvidenceBundle(bundle_id="bundle-s1", target_id="target-s1")
    serialized = to_canonical_json(bundle)
    digest_a = fingerprint_model(bundle)
    digest_b = fingerprint_model(bundle)

    assert serialized.startswith("{")
    assert digest_a == digest_b


def test_knowledge_serialization_reuses_foundation_helpers() -> None:
    assert to_canonical_json is foundation_to_canonical_json
    assert fingerprint_model is foundation_fingerprint_model

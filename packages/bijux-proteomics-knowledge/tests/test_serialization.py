# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_foundation import (
    fingerprint_model as foundation_fingerprint_model,
)
from bijux_proteomics_foundation import (
    to_canonical_json as foundation_to_canonical_json,
)
from bijux_proteomics_knowledge import EvidenceBundle


def test_canonical_serialization_and_fingerprint_are_stable() -> None:
    bundle = EvidenceBundle(bundle_id="bundle-s1", target_id="target-s1")
    serialized = foundation_to_canonical_json(bundle)
    digest_a = foundation_fingerprint_model(bundle)
    digest_b = foundation_fingerprint_model(bundle)

    assert serialized.startswith("{")
    assert digest_a == digest_b


def test_knowledge_root_does_not_reexport_foundation_helpers() -> None:
    import bijux_proteomics_knowledge

    assert "to_canonical_json" not in bijux_proteomics_knowledge.__all__
    assert "fingerprint_model" not in bijux_proteomics_knowledge.__all__

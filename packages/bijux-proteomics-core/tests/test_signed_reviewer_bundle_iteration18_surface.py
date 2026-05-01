# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.collaboration_iteration18 import (
    SignedReviewerBundleInput,
    build_signed_reviewer_bundle,
    verify_signed_reviewer_bundle,
)


def test_signed_reviewer_bundle_build_and_verify_roundtrip() -> None:
    bundle = build_signed_reviewer_bundle(
        SignedReviewerBundleInput(
            bundle_id="signed-review-1",
            manifest_entries=("manifest:claims", "manifest:review"),
            schema_refs=("schema.bundle.v1",),
            evidence_pointer_ids=("ev-9", "ev-1"),
            review_packet_ids=("rp-2", "rp-1"),
            hash_ledger_entries=("sha256:abc", "sha256:def"),
            signing_key_id="review-key-01",
            signing_secret="supersecret-signing-key",
        )
    )

    assert bundle.signature_algorithm == "sha256-secret-v1"
    assert bundle.review_packet_ids == ("rp-1", "rp-2")
    assert verify_signed_reviewer_bundle(bundle, "supersecret-signing-key") is True
    assert verify_signed_reviewer_bundle(bundle, "wrong-secret") is False

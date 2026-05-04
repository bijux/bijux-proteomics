# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics.collaboration import (
    ExternalReviewerBundleInput,
    build_external_reviewer_bundle,
)


def test_build_external_reviewer_bundle_keeps_required_review_fields() -> None:
    bundle = build_external_reviewer_bundle(
        ExternalReviewerBundleInput(
            bundle_id="review-bundle-1",
            schema_refs=("schema.review.v1", "schema.evidence.v1"),
            evidence_pointer_ids=("ev-1", "ev-2"),
            summary_lines=("candidate reasoning summary",),
            hash_ledger_entries=("sha256:abc",),
            reviewer_instructions="Review claims and linked evidence pointers.",
        )
    )

    assert bundle.schema_refs[0] == "schema.evidence.v1"
    assert not bundle.completeness_notes

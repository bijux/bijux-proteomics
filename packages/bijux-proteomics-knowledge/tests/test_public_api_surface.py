# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_foundation import DocumentSchema
from bijux_proteomics_knowledge import (
    EvidenceBundle,
    EvidenceClaim,
    EvidenceRecord,
    KnowledgeReviewPacket,
    evaluate_schema_compatibility,
)


def test_knowledge_public_root_exposes_curated_memory_anchors() -> None:
    record = EvidenceRecord(
        evidence_id="public-root-record",
        kind="literature",
        title="public root record",
        source="PMID:1",
        claim="public root evidence stays typed",
        confidence=0.8,
        strength="supporting",
    )
    bundle = EvidenceBundle(
        bundle_id="public-root-bundle",
        target_id="public-root-target",
        records=[record],
    )
    claim = EvidenceClaim(
        claim_id="public-root-claim",
        target_id="public-root-target",
        statement="public root claims stay typed",
        evidence_ids=[record.evidence_id],
        status="supported",
    )

    report = evaluate_schema_compatibility(
        DocumentSchema(schema_version="1.0.0", created_by="public-root-test")
    )

    assert bundle.records[0].evidence_id == "public-root-record"
    assert claim.evidence_ids == ["public-root-record"]
    assert KnowledgeReviewPacket.__name__ == "KnowledgeReviewPacket"
    assert report.compatible is True

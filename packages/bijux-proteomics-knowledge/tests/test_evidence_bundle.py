# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_knowledge import (
    EvidenceBundle,
    EvidenceKind,
    EvidenceRecord,
    EvidenceStrength,
    evidence_gaps,
    summarize_bundle,
)


def test_summarize_bundle_counts_records_by_kind() -> None:
    bundle = EvidenceBundle(
        bundle_id="bundle-1",
        target_id="target-1",
        records=[
            EvidenceRecord(
                evidence_id="lit-1",
                kind=EvidenceKind.LITERATURE,
                title="Paper",
                source="PMID:1",
                claim="Target is disease-relevant.",
                confidence=0.9,
                strength=EvidenceStrength.SUPPORTING,
            ),
            EvidenceRecord(
                evidence_id="assay-1",
                kind=EvidenceKind.ASSAY,
                title="Assay",
                source="lab",
                claim="Variant keeps activity in vitro.",
                confidence=0.8,
                strength=EvidenceStrength.DECISIVE,
            ),
        ],
    )

    summary = summarize_bundle(bundle)

    assert summary["record_count"] == 2
    assert summary["decisive_records"] == 1
    assert summary["by_kind"]["literature"] == 1
    assert summary["by_kind"]["assay"] == 1


def test_evidence_gaps_reports_missing_kinds() -> None:
    bundle = EvidenceBundle(
        bundle_id="bundle-1",
        target_id="target-1",
        records=[
            EvidenceRecord(
                evidence_id="lit-1",
                kind=EvidenceKind.LITERATURE,
                title="Paper",
                source="PMID:1",
                claim="Target is disease-relevant.",
                confidence=0.9,
                strength=EvidenceStrength.SUPPORTING,
            )
        ],
    )

    gaps = evidence_gaps(bundle, ["literature", "structure", "assay"])

    assert gaps == ["structure", "assay"]

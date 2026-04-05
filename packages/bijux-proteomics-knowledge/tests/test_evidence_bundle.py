# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_knowledge import (
    assess_decision_readiness,
    coverage_report,
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
    assert summary["schema_version"] == "1.0.0"
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


def test_coverage_report_tracks_missing_kinds_and_confidence() -> None:
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
                confidence=0.7,
                strength=EvidenceStrength.DECISIVE,
            ),
        ],
    )

    coverage = coverage_report(bundle, ["literature", "structure", "assay"])

    assert coverage.missing_kinds == ["structure"]
    assert coverage.decisive_records == 1
    assert coverage.mean_confidence == 0.8


def test_assess_decision_readiness_reports_blockers() -> None:
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
                confidence=0.55,
                strength=EvidenceStrength.EXPLORATORY,
            )
        ],
    )

    readiness = assess_decision_readiness(
        bundle,
        ["literature", "structure", "assay"],
        minimum_mean_confidence=0.7,
        minimum_decisive_records=1,
    )

    assert readiness.ready is False
    assert "missing required evidence kinds: structure, assay" in readiness.blockers
    assert "not enough decisive evidence for an irreversible decision" in readiness.blockers


def test_evidence_bundle_round_trips_with_serialization_helpers(tmp_path) -> None:
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
    bundle.document_schema.trace_id = "trace-knowledge-1"
    path = tmp_path / "bundle.json"

    bundle.save_json(path)
    restored = EvidenceBundle.load_json(path)

    assert restored.to_dict()["document_schema"]["trace_id"] == "trace-knowledge-1"
    assert EvidenceBundle.from_json(bundle.to_json()).bundle_id == "bundle-1"

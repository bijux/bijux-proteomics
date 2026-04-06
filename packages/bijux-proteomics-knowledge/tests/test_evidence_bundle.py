# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from bijux_proteomics_knowledge import (
    assess_decision_readiness,
    compute_bundle_trust,
    coverage_report,
    deduplicate_records,
    EvidenceBundle,
    EvidenceConflict,
    EvidenceExtractionMethod,
    EvidenceKind,
    EvidenceOrigin,
    EvidenceRecord,
    EvidenceSourceType,
    EvidenceStrength,
    evidence_gaps,
    flag_conflicting_evidence,
    score_evidence_record,
    stale_records,
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
                source_uri="https://pubmed.ncbi.nlm.nih.gov/1/",
                origin=EvidenceOrigin.IMPORTED,
                extraction_method=EvidenceExtractionMethod.AUTOMATED_IMPORT,
                curator="literature-loader",
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
                source_type=EvidenceSourceType.LITERATURE,
                source_uri="https://pubmed.ncbi.nlm.nih.gov/1/",
                origin=EvidenceOrigin.IMPORTED,
                extraction_method=EvidenceExtractionMethod.AUTOMATED_IMPORT,
                curator="literature-loader",
                claim="Target is disease-relevant.",
                confidence=0.9,
                strength=EvidenceStrength.SUPPORTING,
            ),
            EvidenceRecord(
                evidence_id="assay-1",
                kind=EvidenceKind.ASSAY,
                title="Assay",
                source="lab",
                source_type=EvidenceSourceType.LAB_ASSAY,
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
                source_type=EvidenceSourceType.LITERATURE,
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
                source_type=EvidenceSourceType.LITERATURE,
                source_uri="https://pubmed.ncbi.nlm.nih.gov/1/",
                origin=EvidenceOrigin.IMPORTED,
                extraction_method=EvidenceExtractionMethod.AUTOMATED_IMPORT,
                curator="literature-loader",
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
    assert restored.records[0].curator == "literature-loader"


def test_compute_bundle_trust_accounts_for_staleness_conflicts_and_duplicates() -> None:
    now = datetime(2026, 1, 10, tzinfo=UTC)
    bundle = EvidenceBundle(
        bundle_id="bundle-2",
        target_id="target-2",
        records=[
            EvidenceRecord(
                evidence_id="assay-1",
                kind=EvidenceKind.ASSAY,
                title="Assay positive",
                source="lab",
                source_type=EvidenceSourceType.LAB_ASSAY,
                claim="Candidate meets the activity gate.",
                decision_tags=["progression"],
                confidence=0.9,
                strength=EvidenceStrength.DECISIVE,
                expires_at=now + timedelta(days=7),
            ),
            EvidenceRecord(
                evidence_id="assay-2",
                kind=EvidenceKind.ASSAY,
                title="Assay caution",
                source="lab-2",
                source_type=EvidenceSourceType.LAB_ASSAY,
                claim="Candidate may miss the activity gate.",
                decision_tags=["progression"],
                confidence=0.8,
                strength=EvidenceStrength.EXPLORATORY,
                expires_at=now + timedelta(days=7),
            ),
            EvidenceRecord(
                evidence_id="lit-1",
                kind=EvidenceKind.LITERATURE,
                title="Paper",
                source="PMID:1",
                source_type=EvidenceSourceType.LITERATURE,
                claim="Target is disease-relevant.",
                confidence=0.8,
                strength=EvidenceStrength.SUPPORTING,
                expires_at=now - timedelta(days=1),
            ),
            EvidenceRecord(
                evidence_id="lit-2",
                kind=EvidenceKind.LITERATURE,
                title="Paper duplicate",
                source="PMID:1",
                source_type=EvidenceSourceType.LITERATURE,
                claim="Target is disease-relevant.",
                confidence=0.8,
                strength=EvidenceStrength.SUPPORTING,
                expires_at=now + timedelta(days=20),
            ),
        ],
    )

    trust = compute_bundle_trust(bundle, now=now)

    assert trust.stale_records == ["lit-1"]
    assert trust.duplicate_groups == [["lit-1", "lit-2"]]
    assert trust.conflicts == [
        EvidenceConflict(
            left_evidence_id="assay-1",
            right_evidence_id="assay-2",
            reason="same decision tag but materially different claim strength",
        )
    ]
    assert trust.trust_score < 1.0


def test_record_scoring_and_helpers_are_exposed_for_policy_use() -> None:
    now = datetime(2026, 1, 10, tzinfo=UTC)
    record = EvidenceRecord(
        evidence_id="lit-1",
        kind=EvidenceKind.LITERATURE,
        title="Paper",
        source="PMID:1",
        source_type=EvidenceSourceType.LITERATURE,
        claim="Target is disease-relevant.",
        confidence=0.9,
        strength=EvidenceStrength.SUPPORTING,
        expires_at=now + timedelta(days=30),
    )
    bundle = EvidenceBundle(bundle_id="bundle-3", target_id="target-3", records=[record, record.model_copy(update={"evidence_id": "lit-2"})])

    assert score_evidence_record(record, now=now) > 0.0
    assert stale_records(bundle, now=now) == []
    assert deduplicate_records(bundle) == [["lit-1", "lit-2"]]
    assert flag_conflicting_evidence(bundle) == []

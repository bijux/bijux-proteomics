# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from bijux_proteomics_knowledge import (
    aging_records,
    assess_decision_readiness,
    attach_manual_notes,
    BundleFreshnessReport,
    ConflictPolicy,
    compute_bundle_trust,
    coverage_report,
    deduplicate_records,
    EvidenceBundle,
    EvidenceConflict,
    EvidenceExtractionMethod,
    EvidenceRefreshNeed,
    EvidenceRefreshPriority,
    EvidenceKind,
    EvidenceOrigin,
    EvidenceRecord,
    EvidenceSourceType,
    EvidenceStrength,
    ManualEvidenceNote,
    QuantitativeSupport,
    TrustPolicy,
    default_trust_policy,
    default_conflict_policy,
    evidence_gaps,
    flag_conflicting_evidence,
    plan_evidence_refresh,
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


def test_evidence_gaps_supports_proteomics_specific_kinds() -> None:
    bundle = EvidenceBundle(
        bundle_id="bundle-omics",
        target_id="target-omics",
        records=[
            EvidenceRecord(
                evidence_id="dp-1",
                kind=EvidenceKind.DIFFERENTIAL_PROTEOMICS,
                title="Proteomics panel",
                source="lab",
                claim="Target pathway proteins show desired directional shift.",
                confidence=0.78,
                strength=EvidenceStrength.SUPPORTING,
            )
        ],
    )

    gaps = evidence_gaps(
        bundle,
        [EvidenceKind.DIFFERENTIAL_PROTEOMICS.value, EvidenceKind.PHOSPHOPROTEOMICS.value],
    )

    assert gaps == [EvidenceKind.PHOSPHOPROTEOMICS.value]


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
            conflict_type="claim_strength_mismatch",
            severity="medium",
            left_evidence_id="assay-1",
            right_evidence_id="assay-2",
            reason="same decision tag but materially different claim strength",
        )
    ]
    assert trust.trust_score < 1.0


def test_compute_bundle_trust_uses_explicit_trust_policy() -> None:
    now = datetime(2026, 1, 10, tzinfo=UTC)
    record = EvidenceRecord(
        evidence_id="note-1",
        kind=EvidenceKind.STRUCTURE,
        title="Curated note",
        source="notebook",
        source_type=EvidenceSourceType.CURATED_NOTE,
        claim="Fold looks rescuable.",
        confidence=0.8,
        strength=EvidenceStrength.SUPPORTING,
        expires_at=now + timedelta(days=10),
    )
    bundle = EvidenceBundle(bundle_id="bundle-policy", target_id="target-policy", records=[record])

    default_score = compute_bundle_trust(bundle, now=now).trust_score
    strict_policy = default_trust_policy().model_copy(
        update={
            "policy_id": "strict-curation",
            "source_type_weights": {
                **default_trust_policy().source_type_weights,
                EvidenceSourceType.CURATED_NOTE: 0.3,
            },
        }
    )

    strict_score = compute_bundle_trust(bundle, now=now, policy=strict_policy).trust_score

    assert isinstance(strict_policy, TrustPolicy)
    assert strict_score < default_score


def test_conflict_policy_detects_same_assay_source_disagreement() -> None:
    bundle = EvidenceBundle(
        bundle_id="bundle-conflict",
        target_id="target-conflict",
        records=[
            EvidenceRecord(
                evidence_id="assay-1",
                kind=EvidenceKind.ASSAY,
                title="Assay positive",
                source="lab",
                source_uri="lab://run-1",
                decision_tags=["progression"],
                claim="Candidate meets the assay gate.",
                confidence=0.9,
                strength=EvidenceStrength.SUPPORTING,
            ),
            EvidenceRecord(
                evidence_id="assay-2",
                kind=EvidenceKind.ASSAY,
                title="Assay negative",
                source="lab",
                source_uri="lab://run-1",
                decision_tags=["progression"],
                claim="Candidate misses the assay gate.",
                confidence=0.8,
                strength=EvidenceStrength.SUPPORTING,
            ),
        ],
    )

    conflicts = flag_conflicting_evidence(
        bundle,
        policy=default_conflict_policy().model_copy(
            update={"policy_id": "assay-aware"}
        ),
    )

    assert conflicts == [
        EvidenceConflict(
            conflict_type="assay_readout_disagreement",
            severity="high",
            left_evidence_id="assay-1",
            right_evidence_id="assay-2",
            reason="same assay source but inconsistent assay interpretation",
        )
    ]


def test_conflict_detection_captures_opposite_claim_polarity() -> None:
    bundle = EvidenceBundle(
        bundle_id="bundle-polarity",
        target_id="target-polarity",
        records=[
            EvidenceRecord(
                evidence_id="assay-1",
                kind=EvidenceKind.ASSAY,
                title="assay positive",
                source="lab",
                decision_tags=["progression"],
                claim="Candidate meets the progression gate.",
                confidence=0.8,
                strength=EvidenceStrength.SUPPORTING,
            ),
            EvidenceRecord(
                evidence_id="assay-2",
                kind=EvidenceKind.ASSAY,
                title="assay negative",
                source="lab-2",
                decision_tags=["progression"],
                claim="Candidate fails the progression gate.",
                confidence=0.8,
                strength=EvidenceStrength.SUPPORTING,
            ),
        ],
    )

    conflicts = flag_conflicting_evidence(bundle)

    assert conflicts == [
        EvidenceConflict(
            conflict_type="opposite_claim_polarity",
            severity="high",
            left_evidence_id="assay-1",
            right_evidence_id="assay-2",
            reason="evidence claims suggest opposite progression polarity",
        )
    ]


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


def test_evidence_record_supports_quantitative_context_payload() -> None:
    record = EvidenceRecord(
        evidence_id="assay-quant-1",
        kind=EvidenceKind.ASSAY,
        title="Dose response",
        source="lab",
        claim="Candidate improves activity in cellular assay.",
        confidence=0.82,
        strength=EvidenceStrength.SUPPORTING,
        assay_modality="cellular",
        biological_system="HEK293",
        species="human",
        sample_type="cell lysate",
        endpoint="activity_ratio",
        quantitative_support=QuantitativeSupport(
            effect_size=1.8,
            p_value=0.004,
            q_value=0.02,
            replicate_count=4,
            unit="fold-change",
        ),
    )

    assert record.quantitative_support is not None
    assert record.quantitative_support.replicate_count == 4


def test_attach_manual_notes_creates_curated_evidence_records() -> None:
    bundle = EvidenceBundle(bundle_id="bundle-4", target_id="target-4")

    updated = attach_manual_notes(
        bundle,
        [
            ManualEvidenceNote(
                note_id="note-1",
                target_id="target-4",
                title="Scientist review note",
                claim="The fold rescue hypothesis still looks plausible.",
                curator="review-scientist",
                kind=EvidenceKind.STRUCTURE,
                decision_tags=["progression", "design"],
                confidence=0.72,
                strength=EvidenceStrength.SUPPORTING,
                source_uri="notebook://target-4/review-1",
            )
        ],
    )

    assert updated.records[0].source_type is EvidenceSourceType.CURATED_NOTE
    assert updated.records[0].curator == "review-scientist"
    assert updated.records[0].extraction_method is EvidenceExtractionMethod.MANUAL_CURATION


def test_plan_evidence_refresh_prioritizes_stale_and_aging_records() -> None:
    now = datetime(2026, 1, 10, tzinfo=UTC)
    bundle = EvidenceBundle(
        bundle_id="bundle-5",
        target_id="target-5",
        records=[
            EvidenceRecord(
                evidence_id="assay-urgent",
                kind=EvidenceKind.ASSAY,
                title="Aging assay",
                source="lab",
                source_type=EvidenceSourceType.LAB_ASSAY,
                claim="Activity remains above the gate.",
                confidence=0.88,
                strength=EvidenceStrength.DECISIVE,
                expires_at=now + timedelta(days=4),
            ),
            EvidenceRecord(
                evidence_id="lit-stale",
                kind=EvidenceKind.LITERATURE,
                title="Stale paper review",
                source="PMID:4",
                source_type=EvidenceSourceType.LITERATURE,
                claim="The target remains disease relevant.",
                confidence=0.76,
                strength=EvidenceStrength.SUPPORTING,
                expires_at=now - timedelta(days=1),
            ),
        ],
    )

    freshness = plan_evidence_refresh(bundle, now=now, horizon_days=7)

    assert aging_records(bundle, now=now, horizon_days=7)[0].evidence_id == "assay-urgent"
    assert freshness == BundleFreshnessReport(
        bundle_id="bundle-5",
        target_id="target-5",
        stale_records=["lit-stale"],
        aging_records=["assay-urgent"],
        refresh_needs=[
            EvidenceRefreshNeed(
                evidence_id="lit-stale",
                priority=EvidenceRefreshPriority.HIGH,
                reason="the evidence record is already past its validity window",
                suggested_action="search for newer literature and re-evaluate the claim",
            ),
            EvidenceRefreshNeed(
                evidence_id="assay-urgent",
                priority=EvidenceRefreshPriority.HIGH,
                reason="the evidence record will expire soon and should be refreshed proactively",
                suggested_action="repeat or reconfirm the assay readout in the lab system",
            ),
        ],
    )

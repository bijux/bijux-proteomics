# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from bijux_proteomics_knowledge import (
    aging_records,
    assess_decision_readiness,
    assess_context_completeness,
    assess_scientific_context_completeness,
    assess_context_compatibility,
    audit_knowledge_quality,
    summarize_quantitative_coverage,
    rank_evidence_for_decision,
    evaluate_modality_coverage,
    summarize_evidence_provenance,
    ContextScoringProfile,
    query_evidence_records,
    EvidenceRecordQuery,
    plan_evidence_collection,
    validate_quantitative_support_payload,
    validate_bundle_integrity,
    normalize_bundle_decision_tags,
    assess_artifact_risk,
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
    ProteomicsArtifactFlags,
    EvidenceSourceType,
    EvidenceStrength,
    ManualEvidenceNote,
    QuantitativeSupport,
    TrustPolicy,
    default_trust_policy,
    default_conflict_policy,
    decompose_evidence_quality,
    evidence_gaps,
    evaluate_quantitative_support,
    flag_conflicting_evidence,
    plan_evidence_refresh,
    score_evidence_record,
    stale_records,
    summarize_bundle,
    triangulate_evidence,
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


def test_evidence_kind_taxonomy_covers_biological_and_developability_domains() -> None:
    expected = {
        "sequence_homology",
        "conservation",
        "binding",
        "enzymatic",
        "cellular",
        "phenotype",
        "developability",
        "manufacturability",
    }
    observed = {kind.value for kind in EvidenceKind}

    assert expected.issubset(observed)


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


def test_conflict_detection_flags_quantitative_direction_conflict() -> None:
    bundle = EvidenceBundle(
        bundle_id="bundle-quant-direction",
        target_id="target-quant-direction",
        records=[
            EvidenceRecord(
                evidence_id="q1",
                kind=EvidenceKind.ASSAY,
                title="effect positive",
                source="lab-1",
                decision_tags=["progression"],
                endpoint="activity_ratio",
                claim="Activity increases.",
                confidence=0.82,
                strength=EvidenceStrength.SUPPORTING,
                quantitative_support=QuantitativeSupport(effect_size=1.2),
            ),
            EvidenceRecord(
                evidence_id="q2",
                kind=EvidenceKind.ASSAY,
                title="effect negative",
                source="lab-2",
                decision_tags=["progression"],
                endpoint="activity_ratio",
                claim="Activity decreases.",
                confidence=0.81,
                strength=EvidenceStrength.SUPPORTING,
                quantitative_support=QuantitativeSupport(effect_size=-0.7),
            ),
        ],
    )

    conflicts = flag_conflicting_evidence(bundle)

    assert conflicts[0].conflict_type == "quantitative_direction_conflict"


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


def test_summarize_quantitative_coverage_counts_records() -> None:
    bundle = EvidenceBundle(
        bundle_id="bundle-quant",
        target_id="target-quant",
        records=[
            EvidenceRecord(
                evidence_id="e1",
                kind=EvidenceKind.ASSAY,
                title="quant",
                source="lab",
                claim="quant",
                confidence=0.8,
                strength=EvidenceStrength.SUPPORTING,
                quantitative_support=QuantitativeSupport(replicate_count=3),
            ),
            EvidenceRecord(
                evidence_id="e2",
                kind=EvidenceKind.LITERATURE,
                title="lit",
                source="PMID:1",
                claim="lit",
                confidence=0.7,
                strength=EvidenceStrength.SUPPORTING,
            ),
        ],
    )

    report = summarize_quantitative_coverage(bundle)

    assert report.total_records == 2
    assert report.quantitative_records == 1


def test_decompose_evidence_quality_derives_confidence_components() -> None:
    record = EvidenceRecord(
        evidence_id="assay-qual-1",
        kind=EvidenceKind.ASSAY,
        title="quality record",
        source="lab",
        source_type=EvidenceSourceType.LAB_ASSAY,
        claim="Candidate improves endpoint.",
        decision_tags=["progression", "synthesis"],
        confidence=0.7,
        strength=EvidenceStrength.SUPPORTING,
        biological_system="HEK293",
        quantitative_support=QuantitativeSupport(replicate_count=4),
    )

    quality = decompose_evidence_quality(record)

    assert quality.reproducibility >= 0.9
    assert quality.statistical_support > 0.0
    assert quality.context_match >= 0.7
    assert quality.context_relevance == 0.9
    assert 0.0 <= quality.derived_confidence <= 1.0


def test_assess_context_compatibility_flags_species_and_system_mismatch() -> None:
    record = EvidenceRecord(
        evidence_id="ctx-1",
        kind=EvidenceKind.ASSAY,
        title="context test",
        source="lab",
        claim="Context mismatch candidate signal.",
        confidence=0.7,
        strength=EvidenceStrength.SUPPORTING,
        species="mouse",
        biological_system="NIH3T3",
        sample_type="plasma",
    )

    report = assess_context_compatibility(
        record,
        expected_species="human",
        expected_system="HEK293",
        expected_sample_type="cell lysate",
    )

    assert report.score < 1.0
    assert any("species context" in note for note in report.notes)


def test_assess_context_compatibility_supports_custom_scoring_profile() -> None:
    record = EvidenceRecord(
        evidence_id="ctx-profile-1",
        kind=EvidenceKind.ASSAY,
        title="context profile",
        source="lab",
        claim="signal",
        confidence=0.7,
        strength=EvidenceStrength.SUPPORTING,
        species="mouse",
        biological_system="NIH3T3",
        sample_type="plasma",
    )
    report = assess_context_compatibility(
        record,
        expected_species="human",
        expected_system="HEK293",
        expected_sample_type="cell lysate",
        profile=ContextScoringProfile(
            profile_id="strict-profile",
            species_mismatch_penalty=0.4,
            system_mismatch_penalty=0.4,
            sample_type_mismatch_penalty=0.1,
        ),
    )

    assert report.score == 0.1


def test_triangulate_evidence_scores_modality_convergence() -> None:
    bundle = EvidenceBundle(
        bundle_id="bundle-tri",
        target_id="target-tri",
        records=[
            EvidenceRecord(
                evidence_id="e1",
                kind=EvidenceKind.LITERATURE,
                title="lit",
                source="pmid",
                claim="lit support",
                decision_tags=["progression"],
                confidence=0.8,
                strength=EvidenceStrength.SUPPORTING,
            ),
            EvidenceRecord(
                evidence_id="e2",
                kind=EvidenceKind.ASSAY,
                title="assay",
                source="lab",
                claim="assay support",
                decision_tags=["progression"],
                confidence=0.8,
                strength=EvidenceStrength.DECISIVE,
            ),
        ],
    )
    report = triangulate_evidence(
        bundle,
        decision_tag="progression",
        required_modalities=[EvidenceKind.LITERATURE.value, EvidenceKind.ASSAY.value, EvidenceKind.STRUCTURE.value],
    )

    assert report.modality_diversity == 2
    assert report.decisive_share == 0.5
    assert report.missing_required_modalities == [EvidenceKind.STRUCTURE.value]
    assert report.convergence_score > 0


def test_conflict_detection_flags_species_context_mismatch() -> None:
    bundle = EvidenceBundle(
        bundle_id="bundle-species",
        target_id="target-species",
        records=[
            EvidenceRecord(
                evidence_id="s1",
                kind=EvidenceKind.ASSAY,
                title="human assay",
                source="lab-h",
                claim="Candidate meets activity gate.",
                decision_tags=["progression"],
                species="human",
                confidence=0.8,
                strength=EvidenceStrength.SUPPORTING,
            ),
            EvidenceRecord(
                evidence_id="s2",
                kind=EvidenceKind.ASSAY,
                title="mouse assay",
                source="lab-m",
                claim="Candidate meets activity gate.",
                decision_tags=["progression"],
                species="mouse",
                confidence=0.8,
                strength=EvidenceStrength.SUPPORTING,
            ),
        ],
    )

    conflicts = flag_conflicting_evidence(bundle)

    assert conflicts == [
        EvidenceConflict(
            conflict_type="species_context_mismatch",
            severity="medium",
            left_evidence_id="s1",
            right_evidence_id="s2",
            reason="records inform the same decision tag under different species contexts",
        )
    ]


def test_assess_artifact_risk_scores_proteomics_uncertainty_flags() -> None:
    record = EvidenceRecord(
        evidence_id="art-1",
        kind=EvidenceKind.PHOSPHOPROTEOMICS,
        title="phospho readout",
        source="lab",
        claim="site phosphorylation increases",
        confidence=0.7,
        strength=EvidenceStrength.SUPPORTING,
        artifact_flags=ProteomicsArtifactFlags(
            ion_interference=True,
            ptm_site_localization_uncertain=True,
        ),
    )
    report = assess_artifact_risk(record)

    assert report.risk_score > 0.0
    assert any("ion interference" in note for note in report.notes)


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
                biological_system="HEK293",
                species="human",
            )
        ],
    )

    assert updated.records[0].source_type is EvidenceSourceType.CURATED_NOTE
    assert updated.records[0].curator == "review-scientist"
    assert updated.records[0].biological_system == "HEK293"
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


def test_stale_records_flags_old_records_without_explicit_expiry() -> None:
    now = datetime(2026, 1, 10, tzinfo=UTC)
    bundle = EvidenceBundle(
        bundle_id="bundle-old-observed",
        target_id="target-old-observed",
        records=[
            EvidenceRecord(
                evidence_id="note-old",
                kind=EvidenceKind.LITERATURE,
                title="old note",
                source="pmid",
                source_type=EvidenceSourceType.CURATED_NOTE,
                claim="legacy interpretation",
                confidence=0.6,
                strength=EvidenceStrength.SUPPORTING,
                observed_at=now - timedelta(days=120),
            )
        ],
    )

    stale = stale_records(bundle, now=now)
    assert [record.evidence_id for record in stale] == ["note-old"]


def test_evaluate_quantitative_support_scores_high_quality_payload() -> None:
    report = evaluate_quantitative_support(
        QuantitativeSupport(
            effect_size=1.8,
            confidence_interval_low=1.3,
            confidence_interval_high=2.2,
            confidence_interval_level=0.95,
            variance=0.12,
            coefficient_of_variation=0.18,
            p_value=0.01,
            q_value=0.04,
            replicate_count=4,
            peptide_count=6,
            protein_coverage=0.42,
            site_localization_probability=0.86,
            absolute_scale=True,
            scale_type="fold-change",
        )
    )

    assert report.support_score > 0.7
    assert "replicate count supports reproducibility" in report.notes
    assert "confidence interval bounds are available" in report.notes


def test_evaluate_quantitative_support_penalizes_censored_signal() -> None:
    report = evaluate_quantitative_support(
        QuantitativeSupport(
            replicate_count=2,
            coefficient_of_variation=0.52,
            peptide_count=1,
            protein_coverage=0.12,
            censored_by_detection_limit=True,
            detection_limit_value=0.03,
            censoring_direction="left-censored",
        )
    )

    assert report.support_score < 0.5
    assert "quantitative estimate is censored by detection limit" in report.notes
    assert "detection limit value is reported for censoring context" in report.notes


def test_assess_context_completeness_reports_missing_context_fields() -> None:
    report = assess_context_completeness(
        EvidenceRecord(
            evidence_id="assay-context-1",
            kind=EvidenceKind.ASSAY,
            title="Context-light assay",
            source="lab",
            claim="Candidate appears active.",
            confidence=0.8,
            strength=EvidenceStrength.SUPPORTING,
            species="human",
        )
    )

    assert report.completeness_score == 0.2
    assert sorted(report.missing_fields) == [
        "assay_modality",
        "biological_system",
        "endpoint",
        "sample_type",
    ]


def test_assess_context_completeness_scores_full_context_record() -> None:
    report = assess_context_completeness(
        EvidenceRecord(
            evidence_id="assay-context-2",
            kind=EvidenceKind.ASSAY,
            title="Context-rich assay",
            source="lab",
            claim="Candidate remains active.",
            confidence=0.9,
            strength=EvidenceStrength.DECISIVE,
            assay_modality="cellular",
            biological_system="HEK293",
            species="human",
            sample_type="whole-cell lysate",
            endpoint="viability rescue",
        )
    )

    assert report.completeness_score == 1.0
    assert report.missing_fields == []


def test_assess_scientific_context_completeness_requires_extended_fields() -> None:
    report = assess_scientific_context_completeness(
        EvidenceRecord(
            evidence_id="assay-science-1",
            kind=EvidenceKind.CELLULAR,
            title="Context-rich cellular assay",
            source="lab",
            claim="Candidate rescues pathway activity.",
            confidence=0.86,
            strength=EvidenceStrength.DECISIVE,
            assay_modality="cellular",
            biological_system="HEK293",
            species="human",
            sample_type="cell lysate",
            endpoint="pathway rescue",
            dose="1 uM",
            timepoint="24 h",
            perturbation="compound treatment",
            control_design="vehicle control",
            replicate_design="3 biological replicates",
            normalization_method="median normalization",
            sample_preparation="tryptic digest",
            tissue_context="liver",
            cell_line_context="HEK293",
        )
    )

    assert report.completeness_score == 1.0
    assert report.missing_fields == []


def test_audit_knowledge_quality_surfaces_bundle_level_recommendations() -> None:
    bundle = EvidenceBundle(
        bundle_id="bundle-audit",
        target_id="target-audit",
        records=[
            EvidenceRecord(
                evidence_id="audit-1",
                kind=EvidenceKind.ASSAY,
                title="assay result",
                source="lab",
                claim="signal supports progression",
                decision_tags=["progression"],
                endpoint="activity_ratio",
                confidence=0.82,
                strength=EvidenceStrength.SUPPORTING,
                quantitative_support=QuantitativeSupport(replicate_count=2, coefficient_of_variation=0.55),
            )
        ],
    )

    audit = audit_knowledge_quality(
        bundle,
        decision_tag="progression",
        required_modalities=[EvidenceKind.ASSAY.value, EvidenceKind.STRUCTURE.value],
    )

    assert audit.triangulation_score >= 0.0
    assert "audit-1" in audit.low_context_records
    assert "audit-1" in audit.weak_quantitative_records
    assert any("collect missing modalities" in note for note in audit.recommendations)


def test_rank_evidence_for_decision_prioritizes_context_and_quality() -> None:
    bundle = EvidenceBundle(
        bundle_id="bundle-rank",
        target_id="target-rank",
        records=[
            EvidenceRecord(
                evidence_id="rank-high",
                kind=EvidenceKind.CELLULAR,
                title="high context fit",
                source="lab",
                claim="supports progression",
                decision_tags=["progression"],
                species="human",
                biological_system="HEK293",
                sample_type="cell lysate",
                confidence=0.85,
                strength=EvidenceStrength.DECISIVE,
                quantitative_support=QuantitativeSupport(replicate_count=4, coefficient_of_variation=0.2, p_value=0.01),
            ),
            EvidenceRecord(
                evidence_id="rank-low",
                kind=EvidenceKind.ASSAY,
                title="low context fit",
                source="lab",
                claim="supports progression",
                decision_tags=["progression"],
                species="mouse",
                biological_system="NIH3T3",
                sample_type="plasma",
                confidence=0.85,
                strength=EvidenceStrength.SUPPORTING,
            ),
        ],
    )
    ranked = rank_evidence_for_decision(
        bundle,
        decision_tag="progression",
        expected_species="human",
        expected_system="HEK293",
        expected_sample_type="cell lysate",
    )

    assert ranked[0].evidence_id == "rank-high"
    assert ranked[0].relevance_score >= ranked[1].relevance_score


def test_evaluate_modality_coverage_reports_missing_required_modalities() -> None:
    bundle = EvidenceBundle(
        bundle_id="bundle-modality-coverage",
        target_id="target-modality-coverage",
        records=[
            EvidenceRecord(
                evidence_id="m1",
                kind=EvidenceKind.LITERATURE,
                title="literature",
                source="pmid",
                claim="support",
                decision_tags=["progression"],
                confidence=0.8,
                strength=EvidenceStrength.SUPPORTING,
            )
        ],
    )

    report = evaluate_modality_coverage(
        bundle,
        decision_tag="progression",
        required_modalities=[EvidenceKind.LITERATURE.value, EvidenceKind.ASSAY.value],
    )

    assert report.observed_modalities[EvidenceKind.LITERATURE.value] == 1
    assert report.missing_modalities == [EvidenceKind.ASSAY.value]


def test_summarize_evidence_provenance_reports_transitive_ancestors() -> None:
    bundle = EvidenceBundle(
        bundle_id="bundle-prov",
        target_id="target-prov",
        records=[
            EvidenceRecord(
                evidence_id="prov-root",
                kind=EvidenceKind.LITERATURE,
                title="root",
                source="pmid",
                claim="root",
                confidence=0.7,
                strength=EvidenceStrength.SUPPORTING,
            ),
            EvidenceRecord(
                evidence_id="prov-mid",
                kind=EvidenceKind.STRUCTURE,
                title="mid",
                source="model",
                claim="mid",
                derived_from=["prov-root"],
                confidence=0.7,
                strength=EvidenceStrength.SUPPORTING,
            ),
            EvidenceRecord(
                evidence_id="prov-leaf",
                kind=EvidenceKind.ASSAY,
                title="leaf",
                source="lab",
                claim="leaf",
                derived_from=["prov-mid"],
                confidence=0.7,
                strength=EvidenceStrength.SUPPORTING,
            ),
        ],
    )
    report = summarize_evidence_provenance(bundle, evidence_id="prov-leaf")

    assert report.ancestor_ids == ["prov-mid", "prov-root"]
    assert report.lineage_depth == 2


def test_query_evidence_records_filters_by_decision_kind_and_confidence() -> None:
    records = [
        EvidenceRecord(
            evidence_id="qr-1",
            kind=EvidenceKind.ASSAY,
            title="assay",
            source="lab",
            claim="support",
            decision_tags=["progression"],
            confidence=0.9,
            strength=EvidenceStrength.SUPPORTING,
        ),
        EvidenceRecord(
            evidence_id="qr-2",
            kind=EvidenceKind.LITERATURE,
            title="lit",
            source="pmid",
            claim="context",
            decision_tags=["design"],
            confidence=0.5,
            strength=EvidenceStrength.EXPLORATORY,
        ),
    ]
    filtered = query_evidence_records(
        records,
        EvidenceRecordQuery(
            decision_tag="progression",
            kind=EvidenceKind.ASSAY,
            minimum_confidence=0.8,
        ),
    )

    assert [record.evidence_id for record in filtered] == ["qr-1"]


def test_query_evidence_records_supports_confidence_sorting() -> None:
    records = [
        EvidenceRecord(
            evidence_id="sort-1",
            kind=EvidenceKind.ASSAY,
            title="a",
            source="lab",
            claim="a",
            decision_tags=["progression"],
            confidence=0.6,
            strength=EvidenceStrength.SUPPORTING,
        ),
        EvidenceRecord(
            evidence_id="sort-2",
            kind=EvidenceKind.ASSAY,
            title="b",
            source="lab",
            claim="b",
            decision_tags=["progression"],
            confidence=0.9,
            strength=EvidenceStrength.SUPPORTING,
        ),
    ]
    sorted_records = query_evidence_records(
        records,
        EvidenceRecordQuery(
            decision_tag="progression",
            sort_by="confidence",
            descending=True,
        ),
    )

    assert [record.evidence_id for record in sorted_records] == ["sort-2", "sort-1"]


def test_plan_evidence_collection_prioritizes_missing_modalities() -> None:
    bundle = EvidenceBundle(
        bundle_id="bundle-collection",
        target_id="target-collection",
        records=[
            EvidenceRecord(
                evidence_id="ec-1",
                kind=EvidenceKind.LITERATURE,
                title="literature",
                source="pmid",
                claim="support",
                decision_tags=["progression"],
                confidence=0.8,
                strength=EvidenceStrength.SUPPORTING,
            )
        ],
    )
    actions = plan_evidence_collection(
        bundle,
        decision_tag="progression",
        required_modalities=[EvidenceKind.LITERATURE.value, EvidenceKind.ASSAY.value],
    )

    assert any(action.priority == "high" for action in actions)
    assert any("collect assay evidence" in action.action for action in actions)


def test_validate_quantitative_support_payload_reports_coherence_issues() -> None:
    issues = validate_quantitative_support_payload(
        QuantitativeSupport(
            confidence_interval_low=2.0,
            confidence_interval_high=1.0,
            p_value=0.2,
            q_value=0.1,
            censored_by_detection_limit=True,
            absolute_scale=True,
        )
    )

    assert {issue.code for issue in issues} == {
        "interval-bounds-inverted",
        "censoring-limit-missing",
        "q-value-less-than-p-value",
        "absolute-scale-unit-missing",
    }


def test_validate_bundle_integrity_reports_duplicate_and_missing_lineage() -> None:
    bundle = EvidenceBundle(
        bundle_id="bundle-integrity",
        target_id="target-integrity",
        records=[
            EvidenceRecord(
                evidence_id="dup-1",
                kind=EvidenceKind.LITERATURE,
                title="one",
                source="pmid",
                claim="one",
                decision_tags=["progression"],
                confidence=0.7,
                strength=EvidenceStrength.SUPPORTING,
            ),
            EvidenceRecord(
                evidence_id="dup-1",
                kind=EvidenceKind.ASSAY,
                title="two",
                source="lab",
                claim="two",
                derived_from=["missing-upstream"],
                decision_tags=[],
                confidence=0.7,
                strength=EvidenceStrength.SUPPORTING,
            ),
        ],
    )
    issues = validate_bundle_integrity(bundle)

    assert any(issue.code == "duplicate-evidence-ids" for issue in issues)
    assert any(issue.code == "derived-from-missing" for issue in issues)


def test_normalize_bundle_decision_tags_standardizes_format() -> None:
    bundle = EvidenceBundle(
        bundle_id="bundle-tags",
        target_id="target-tags",
        records=[
            EvidenceRecord(
                evidence_id="tag-1",
                kind=EvidenceKind.LITERATURE,
                title="tag",
                source="pmid",
                claim="tag",
                decision_tags=[" Progression ", "Cell Design", "progression"],
                confidence=0.7,
                strength=EvidenceStrength.SUPPORTING,
            )
        ],
    )
    normalized, report = normalize_bundle_decision_tags(bundle)

    assert normalized.records[0].decision_tags == ["cell-design", "progression"]
    assert report.changed_records == 1

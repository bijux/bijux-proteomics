# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from datetime import UTC, datetime

from bijux_proteomics_knowledge.memory.claims import ClaimStatus, build_claim
from bijux_proteomics_knowledge.memory.evidence import (
    EvidenceBundle,
    EvidenceKind,
    EvidenceRecord,
    EvidenceSourceType,
    EvidenceStrength,
    QuantitativeSupport,
)
from bijux_proteomics_knowledge.memory.resolution import (
    ClaimStatus,
    ContradictoryInterpretationCase,
    ContradictoryInterpretationComparison,
    ResolutionAction,
    ResolutionPolicy,
    apply_resolution_updates,
    build_resolution_escalation_queue,
    cluster_conflicts,
    compare_contradictory_interpretations,
    compare_resolution_policies,
    preview_resolution_impact,
    resolve_conflicts,
    summarize_resolutions,
)
from bijux_proteomics_knowledge.reviews.queries import (
    ClaimResolutionRecord,
    ResolutionRecordQuery,
    query_resolution_records,
)


def _multi_source_disagreement_bundle() -> EvidenceBundle:
    return EvidenceBundle(
        bundle_id="bundle-multi-source-disagreement",
        target_id="target-multi-source-disagreement",
        records=[
            EvidenceRecord(
                evidence_id="lit-human-support",
                kind=EvidenceKind.LITERATURE,
                title="Human cohort support",
                source="PMID:100",
                source_type=EvidenceSourceType.LITERATURE,
                claim="Target engagement supports the progression gate in human disease tissue.",
                decision_tags=["progression"],
                species="human",
                biological_system="disease_tissue",
                confidence=0.82,
                strength=EvidenceStrength.SUPPORTING,
            ),
            EvidenceRecord(
                evidence_id="assay-human-support",
                kind=EvidenceKind.ASSAY,
                title="Human assay support",
                source="lab-human",
                source_type=EvidenceSourceType.LAB_ASSAY,
                source_uri="lab://shared-human-run",
                claim="Target engagement supports the progression gate in the same context.",
                decision_tags=["progression"],
                species="human",
                biological_system="disease_tissue",
                confidence=0.81,
                strength=EvidenceStrength.SUPPORTING,
            ),
            EvidenceRecord(
                evidence_id="assay-human-contradict",
                kind=EvidenceKind.ASSAY,
                title="Human assay contradiction",
                source="lab-human",
                source_type=EvidenceSourceType.LAB_ASSAY,
                source_uri="lab://shared-human-run",
                claim="Target engagement misses the progression gate in the same context.",
                decision_tags=["progression"],
                species="human",
                biological_system="disease_tissue",
                confidence=0.79,
                strength=EvidenceStrength.SUPPORTING,
            ),
            EvidenceRecord(
                evidence_id="assay-mouse-support",
                kind=EvidenceKind.ASSAY,
                title="Mouse assay support",
                source="lab-mouse",
                source_type=EvidenceSourceType.LAB_ASSAY,
                claim="Target engagement supports the progression gate in mouse tissue.",
                decision_tags=["progression"],
                species="mouse",
                biological_system="mouse_tissue",
                confidence=0.77,
                strength=EvidenceStrength.SUPPORTING,
            ),
            EvidenceRecord(
                evidence_id="structure-caution",
                kind=EvidenceKind.STRUCTURE,
                title="Structure caution",
                source="model-1",
                source_type=EvidenceSourceType.STRUCTURE_MODEL,
                claim="Structure model misses the progression gate.",
                decision_tags=["progression"],
                species="human",
                biological_system="disease_tissue",
                confidence=0.74,
                strength=EvidenceStrength.SUPPORTING,
            ),
        ],
    )


def test_resolve_conflicts_prefers_higher_confidence_record() -> None:
    bundle = EvidenceBundle(
        bundle_id="bundle-1",
        target_id="target-1",
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
            ),
            EvidenceRecord(
                evidence_id="assay-2",
                kind=EvidenceKind.ASSAY,
                title="Assay caution",
                source="lab-2",
                source_type=EvidenceSourceType.LAB_ASSAY,
                claim="Candidate may miss the activity gate.",
                decision_tags=["progression"],
                confidence=0.6,
                strength=EvidenceStrength.EXPLORATORY,
            ),
        ],
    )

    _, resolutions = resolve_conflicts(bundle)

    assert resolutions[0].action is ResolutionAction.ACCEPT_HIGHER_TRUST


def test_resolve_conflicts_requires_curation_when_confidence_gap_is_small() -> None:
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
                confidence=0.76,
                strength=EvidenceStrength.DECISIVE,
            ),
            EvidenceRecord(
                evidence_id="assay-2",
                kind=EvidenceKind.ASSAY,
                title="Assay caution",
                source="lab-2",
                source_type=EvidenceSourceType.LAB_ASSAY,
                claim="Candidate may miss the activity gate.",
                decision_tags=["progression"],
                confidence=0.71,
                strength=EvidenceStrength.EXPLORATORY,
            ),
        ],
    )

    _, resolutions = resolve_conflicts(
        bundle,
        policy=ResolutionPolicy(
            policy_id="strict-resolution",
            minimum_confidence_delta_for_auto_accept=0.1,
        ),
    )

    assert resolutions[0].action is ResolutionAction.REQUIRE_CURATION


def test_resolve_conflicts_holds_high_severity_conflicts() -> None:
    bundle = EvidenceBundle(
        bundle_id="bundle-hold",
        target_id="target-hold",
        records=[
            EvidenceRecord(
                evidence_id="assay-1",
                kind=EvidenceKind.ASSAY,
                title="Assay positive",
                source="lab",
                source_type=EvidenceSourceType.LAB_ASSAY,
                source_uri="lab://run-1",
                claim="Candidate meets the activity gate.",
                decision_tags=["progression"],
                confidence=0.9,
                strength=EvidenceStrength.SUPPORTING,
            ),
            EvidenceRecord(
                evidence_id="assay-2",
                kind=EvidenceKind.ASSAY,
                title="Assay negative",
                source="lab",
                source_type=EvidenceSourceType.LAB_ASSAY,
                source_uri="lab://run-1",
                claim="Candidate misses the activity gate.",
                decision_tags=["progression"],
                confidence=0.8,
                strength=EvidenceStrength.SUPPORTING,
            ),
        ],
    )

    _, resolutions = resolve_conflicts(bundle)

    assert resolutions[0].action is ResolutionAction.HOLD_DECISION


def test_resolution_fixture_captures_multi_source_disagreement_patterns() -> None:
    policy = ResolutionPolicy(policy_id="multi-source-policy")
    trust, resolutions = resolve_conflicts(
        _multi_source_disagreement_bundle(),
        policy=policy,
    )
    summary = summarize_resolutions(resolutions, policy=policy)

    assert len(trust.conflicts) >= 3
    assert {resolution.action for resolution in resolutions} >= {
        ResolutionAction.HOLD_DECISION,
        ResolutionAction.SPLIT_BY_CONTEXT,
        ResolutionAction.SPLIT_BY_MODALITY,
    }
    assert summary.hold_required is True


def test_compare_contradictory_interpretations_reports_case_level_resolution() -> None:
    bundle = EvidenceBundle(
        bundle_id="bundle-interpretation-compare",
        target_id="target-interpretation-compare",
        records=[
            EvidenceRecord(
                evidence_id="dataset-a-support",
                kind=EvidenceKind.ASSAY,
                title="dataset a support",
                source="dataset-a",
                source_type=EvidenceSourceType.LAB_ASSAY,
                source_uri="dataset://a",
                claim="candidate supports progression",
                decision_tags=["progression"],
                confidence=0.82,
                strength=EvidenceStrength.SUPPORTING,
            ),
            EvidenceRecord(
                evidence_id="dataset-a-contradict",
                kind=EvidenceKind.ASSAY,
                title="dataset a contradiction",
                source="dataset-a",
                source_type=EvidenceSourceType.LAB_ASSAY,
                source_uri="dataset://a",
                claim="candidate misses progression",
                decision_tags=["progression"],
                confidence=0.79,
                strength=EvidenceStrength.SUPPORTING,
            ),
            EvidenceRecord(
                evidence_id="search-b-support",
                kind=EvidenceKind.ASSAY,
                title="search interpretation support",
                source="search-b",
                source_type=EvidenceSourceType.LAB_ASSAY,
                source_uri="search://b",
                claim="peptide evidence supports progression",
                decision_tags=["progression"],
                confidence=0.74,
                strength=EvidenceStrength.SUPPORTING,
            ),
            EvidenceRecord(
                evidence_id="search-b-contradict",
                kind=EvidenceKind.ASSAY,
                title="search interpretation contradiction",
                source="search-b",
                source_type=EvidenceSourceType.LAB_ASSAY,
                source_uri="search://b",
                claim="peptide evidence contradicts progression",
                decision_tags=["progression"],
                confidence=0.7,
                strength=EvidenceStrength.SUPPORTING,
            ),
        ],
    )

    comparison = compare_contradictory_interpretations(
        bundle,
        cases=[
            ContradictoryInterpretationCase(
                case_id="dataset-a",
                dataset_label="cohort-a",
                interpretation_label="manual-curation",
                evidence_ids=["dataset-a-support", "dataset-a-contradict"],
            ),
            ContradictoryInterpretationCase(
                case_id="search-b",
                dataset_label="cohort-a",
                interpretation_label="search-engine-merge",
                evidence_ids=["search-b-support", "search-b-contradict"],
            ),
        ],
    )

    assert isinstance(comparison, ContradictoryInterpretationComparison)
    assert comparison.policy_id == "default-resolution-policy"
    assert comparison.contradictory_case_pairs == ["dataset-a<>search-b"]
    assert [outcome.case_id for outcome in comparison.outcomes] == [
        "dataset-a",
        "search-b",
    ]
    assert all(outcome.conflict_count >= 1 for outcome in comparison.outcomes)
    assert any(
        outcome.resolution_summary.hold_required for outcome in comparison.outcomes
    )


def test_resolve_conflicts_can_split_species_context_conflicts() -> None:
    bundle = EvidenceBundle(
        bundle_id="bundle-context-split",
        target_id="target-context-split",
        records=[
            EvidenceRecord(
                evidence_id="assay-human",
                kind=EvidenceKind.ASSAY,
                title="human assay",
                source="lab-human",
                source_type=EvidenceSourceType.LAB_ASSAY,
                claim="Candidate meets the activity gate.",
                decision_tags=["progression"],
                species="human",
                confidence=0.8,
                strength=EvidenceStrength.SUPPORTING,
            ),
            EvidenceRecord(
                evidence_id="assay-mouse",
                kind=EvidenceKind.ASSAY,
                title="mouse assay",
                source="lab-mouse",
                source_type=EvidenceSourceType.LAB_ASSAY,
                claim="Candidate meets the activity gate.",
                decision_tags=["progression"],
                species="mouse",
                confidence=0.8,
                strength=EvidenceStrength.SUPPORTING,
            ),
        ],
    )

    _, resolutions = resolve_conflicts(bundle)

    assert resolutions[0].action is ResolutionAction.SPLIT_BY_CONTEXT


def test_resolve_conflicts_can_split_cross_modality_conflicts() -> None:
    bundle = EvidenceBundle(
        bundle_id="bundle-modality-split",
        target_id="target-modality-split",
        records=[
            EvidenceRecord(
                evidence_id="assay-1",
                kind=EvidenceKind.ASSAY,
                title="assay positive",
                source="lab-1",
                source_type=EvidenceSourceType.LAB_ASSAY,
                claim="Candidate meets the activity gate.",
                decision_tags=["progression"],
                confidence=0.8,
                strength=EvidenceStrength.SUPPORTING,
            ),
            EvidenceRecord(
                evidence_id="structure-1",
                kind=EvidenceKind.STRUCTURE,
                title="structure caution",
                source="model-1",
                source_type=EvidenceSourceType.STRUCTURE_MODEL,
                claim="Candidate misses the activity gate.",
                decision_tags=["progression"],
                confidence=0.8,
                strength=EvidenceStrength.SUPPORTING,
            ),
        ],
    )

    _, resolutions = resolve_conflicts(bundle)

    assert resolutions[0].action is ResolutionAction.SPLIT_BY_MODALITY


def test_resolve_conflicts_holds_quantitative_direction_conflicts() -> None:
    bundle = EvidenceBundle(
        bundle_id="bundle-quant-hold",
        target_id="target-quant-hold",
        records=[
            EvidenceRecord(
                evidence_id="q-up",
                kind=EvidenceKind.ASSAY,
                title="up signal",
                source="lab-1",
                source_type=EvidenceSourceType.LAB_ASSAY,
                claim="Signal increases.",
                decision_tags=["progression"],
                endpoint="activity_ratio",
                quantitative_support=QuantitativeSupport(effect_size=1.1),
                confidence=0.8,
                strength=EvidenceStrength.SUPPORTING,
            ),
            EvidenceRecord(
                evidence_id="q-down",
                kind=EvidenceKind.ASSAY,
                title="down signal",
                source="lab-2",
                source_type=EvidenceSourceType.LAB_ASSAY,
                claim="Signal decreases.",
                decision_tags=["progression"],
                endpoint="activity_ratio",
                quantitative_support=QuantitativeSupport(effect_size=-0.9),
                confidence=0.8,
                strength=EvidenceStrength.SUPPORTING,
            ),
        ],
    )

    _, resolutions = resolve_conflicts(bundle)

    assert resolutions[0].action is ResolutionAction.HOLD_DECISION


def test_claim_resolution_record_captures_resolution_history() -> None:
    _, resolutions = resolve_conflicts(
        EvidenceBundle(
            bundle_id="bundle-3",
            target_id="target-3",
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
                ),
                EvidenceRecord(
                    evidence_id="assay-2",
                    kind=EvidenceKind.ASSAY,
                    title="Assay caution",
                    source="lab-2",
                    source_type=EvidenceSourceType.LAB_ASSAY,
                    claim="Candidate may miss the activity gate.",
                    decision_tags=["progression"],
                    confidence=0.6,
                    strength=EvidenceStrength.EXPLORATORY,
                ),
            ],
        )
    )

    record = ClaimResolutionRecord(
        record_id="resolution-1",
        target_id="target-3",
        decision_tag="progression",
        resolution=resolutions[0],
        recorded_by="scientist",
    )

    assert record.resolution.action is ResolutionAction.ACCEPT_HIGHER_TRUST


def test_summarize_resolutions_reports_action_counts() -> None:
    bundle = EvidenceBundle(
        bundle_id="bundle-summary",
        target_id="target-summary",
        records=[
            EvidenceRecord(
                evidence_id="assay-1",
                kind=EvidenceKind.ASSAY,
                title="Assay positive",
                source="lab",
                source_type=EvidenceSourceType.LAB_ASSAY,
                source_uri="lab://run-1",
                claim="Candidate meets the activity gate.",
                decision_tags=["progression"],
                confidence=0.9,
                strength=EvidenceStrength.SUPPORTING,
            ),
            EvidenceRecord(
                evidence_id="assay-2",
                kind=EvidenceKind.ASSAY,
                title="Assay negative",
                source="lab",
                source_type=EvidenceSourceType.LAB_ASSAY,
                source_uri="lab://run-1",
                claim="Candidate misses the activity gate.",
                decision_tags=["progression"],
                confidence=0.8,
                strength=EvidenceStrength.SUPPORTING,
            ),
        ],
    )
    policy = ResolutionPolicy(policy_id="summary-policy")
    _, resolutions = resolve_conflicts(bundle, policy=policy)
    summary = summarize_resolutions(resolutions, policy=policy)

    assert summary.policy_id == "summary-policy"
    assert summary.hold_required is True


def test_apply_resolution_updates_strengthens_claim_on_preferred_evidence() -> None:
    bundle = EvidenceBundle(
        bundle_id="bundle-update",
        target_id="target-update",
        records=[
            EvidenceRecord(
                evidence_id="assay-strong",
                kind=EvidenceKind.ASSAY,
                title="Assay strong",
                source="lab",
                source_type=EvidenceSourceType.LAB_ASSAY,
                claim="Candidate meets the activity gate.",
                decision_tags=["progression"],
                confidence=0.9,
                strength=EvidenceStrength.DECISIVE,
            ),
            EvidenceRecord(
                evidence_id="assay-weak",
                kind=EvidenceKind.ASSAY,
                title="Assay weak",
                source="lab",
                source_type=EvidenceSourceType.LAB_ASSAY,
                claim="Candidate may miss the activity gate.",
                decision_tags=["progression"],
                confidence=0.6,
                strength=EvidenceStrength.EXPLORATORY,
            ),
        ],
    )
    _, resolutions = resolve_conflicts(bundle)
    claim = build_claim(
        claim_id="claim-support",
        target_id="target-update",
        statement="activity is sufficient",
        evidence_ids=["assay-strong"],
        status=ClaimStatus.SUPPORTED,
        confidence=0.6,
    )

    updated_claims, updates = apply_resolution_updates([claim], resolutions)

    assert updated_claims[0].confidence > claim.confidence
    assert updates[0].updated_status is ClaimStatus.SUPPORTED


def test_cluster_conflicts_groups_by_decision_tag_and_type() -> None:
    bundle = EvidenceBundle(
        bundle_id="bundle-cluster",
        target_id="target-cluster",
        records=[
            EvidenceRecord(
                evidence_id="c1",
                kind=EvidenceKind.ASSAY,
                title="positive",
                source="lab-1",
                source_type=EvidenceSourceType.LAB_ASSAY,
                claim="Candidate meets progression gate.",
                decision_tags=["progression"],
                confidence=0.9,
                strength=EvidenceStrength.SUPPORTING,
            ),
            EvidenceRecord(
                evidence_id="c2",
                kind=EvidenceKind.ASSAY,
                title="negative",
                source="lab-2",
                source_type=EvidenceSourceType.LAB_ASSAY,
                claim="Candidate fails progression gate.",
                decision_tags=["progression"],
                confidence=0.8,
                strength=EvidenceStrength.SUPPORTING,
            ),
        ],
    )
    trust, _ = resolve_conflicts(bundle)
    clusters = cluster_conflicts(bundle, trust)

    assert len(clusters) == 1
    assert clusters[0].decision_tag == "progression"
    assert clusters[0].recommended_hold is True


def test_preview_resolution_impact_estimates_confidence_shift() -> None:
    claim = build_claim(
        claim_id="claim-impact",
        target_id="target-1",
        statement="impact preview claim",
        evidence_ids=["assay-strong", "assay-weak"],
        status=ClaimStatus.SUPPORTED,
        confidence=0.7,
        resolution_assays=["assay"],
    )
    resolutions = [
        ClaimResolutionRecord(
            record_id="r1",
            target_id="target-1",
            decision_tag="progression",
            resolution=resolve_conflicts(
                EvidenceBundle(
                    bundle_id="bundle-impact",
                    target_id="target-1",
                    records=[
                        EvidenceRecord(
                            evidence_id="assay-strong",
                            kind=EvidenceKind.ASSAY,
                            title="strong",
                            source="lab",
                            source_type=EvidenceSourceType.LAB_ASSAY,
                            claim="meets gate",
                            decision_tags=["progression"],
                            confidence=0.9,
                            strength=EvidenceStrength.DECISIVE,
                        ),
                        EvidenceRecord(
                            evidence_id="assay-weak",
                            kind=EvidenceKind.ASSAY,
                            title="weak",
                            source="lab",
                            source_type=EvidenceSourceType.LAB_ASSAY,
                            claim="fails gate",
                            decision_tags=["progression"],
                            confidence=0.5,
                            strength=EvidenceStrength.EXPLORATORY,
                        ),
                    ],
                )
            )[1][0],
            recorded_by="tester",
        ).resolution
    ]
    preview = preview_resolution_impact([claim], resolutions)

    assert preview.claim_count == 1
    assert preview.changed_claim_count >= 1


def test_query_resolution_records_filters_by_tag_actor_and_time() -> None:
    record = ClaimResolutionRecord(
        record_id="rr-1",
        target_id="target-rr",
        decision_tag="progression",
        resolution=resolve_conflicts(
            EvidenceBundle(
                bundle_id="bundle-rr",
                target_id="target-rr",
                records=[
                    EvidenceRecord(
                        evidence_id="rr-a",
                        kind=EvidenceKind.ASSAY,
                        title="a",
                        source="lab",
                        source_type=EvidenceSourceType.LAB_ASSAY,
                        claim="meets gate",
                        decision_tags=["progression"],
                        confidence=0.8,
                        strength=EvidenceStrength.SUPPORTING,
                    ),
                    EvidenceRecord(
                        evidence_id="rr-b",
                        kind=EvidenceKind.ASSAY,
                        title="b",
                        source="lab",
                        source_type=EvidenceSourceType.LAB_ASSAY,
                        claim="fails gate",
                        decision_tags=["progression"],
                        confidence=0.7,
                        strength=EvidenceStrength.SUPPORTING,
                    ),
                ],
            )
        )[1][0],
        recorded_at=datetime(2026, 1, 10, tzinfo=UTC),
        recorded_by="reviewer-a",
    )
    filtered = query_resolution_records(
        [record],
        ResolutionRecordQuery(
            target_id="target-rr",
            decision_tag="progression",
            recorded_by="reviewer-a",
            recorded_after=datetime(2026, 1, 1, tzinfo=UTC),
        ),
    )

    assert [item.record_id for item in filtered] == ["rr-1"]


def test_compare_resolution_policies_reports_action_profiles() -> None:
    bundle = EvidenceBundle(
        bundle_id="bundle-policy-compare",
        target_id="target-policy-compare",
        records=[
            EvidenceRecord(
                evidence_id="pc-1",
                kind=EvidenceKind.ASSAY,
                title="positive",
                source="lab",
                source_type=EvidenceSourceType.LAB_ASSAY,
                claim="Candidate meets activity gate.",
                decision_tags=["progression"],
                confidence=0.9,
                strength=EvidenceStrength.SUPPORTING,
            ),
            EvidenceRecord(
                evidence_id="pc-2",
                kind=EvidenceKind.ASSAY,
                title="negative",
                source="lab",
                source_type=EvidenceSourceType.LAB_ASSAY,
                claim="Candidate fails activity gate.",
                decision_tags=["progression"],
                confidence=0.8,
                strength=EvidenceStrength.SUPPORTING,
            ),
        ],
    )
    comparison = compare_resolution_policies(
        bundle,
        policies=[
            ResolutionPolicy(policy_id="default-a"),
            ResolutionPolicy(policy_id="strict-b", high_severity_requires_hold=True),
        ],
    )

    assert set(comparison.policy_action_counts) == {"default-a", "strict-b"}


def test_build_resolution_escalation_queue_prioritizes_hold_conflicts() -> None:
    bundle = EvidenceBundle(
        bundle_id="bundle-escalation",
        target_id="target-escalation",
        records=[
            EvidenceRecord(
                evidence_id="e1",
                kind=EvidenceKind.ASSAY,
                title="positive",
                source="lab",
                source_uri="lab://run-1",
                source_type=EvidenceSourceType.LAB_ASSAY,
                claim="Candidate meets gate.",
                decision_tags=["progression"],
                confidence=0.9,
                strength=EvidenceStrength.SUPPORTING,
            ),
            EvidenceRecord(
                evidence_id="e2",
                kind=EvidenceKind.ASSAY,
                title="negative",
                source="lab",
                source_uri="lab://run-1",
                source_type=EvidenceSourceType.LAB_ASSAY,
                claim="Candidate fails gate.",
                decision_tags=["progression"],
                confidence=0.8,
                strength=EvidenceStrength.SUPPORTING,
            ),
        ],
    )
    trust, resolutions = resolve_conflicts(bundle)
    queue = build_resolution_escalation_queue(trust, resolutions)

    assert len(queue.items) == 1
    assert queue.items[0].priority == "high"


def test_apply_resolution_updates_disputes_claim_when_hold_is_required() -> None:
    bundle = EvidenceBundle(
        bundle_id="bundle-update-hold",
        target_id="target-update-hold",
        records=[
            EvidenceRecord(
                evidence_id="assay-1",
                kind=EvidenceKind.ASSAY,
                title="Assay 1",
                source="lab",
                source_type=EvidenceSourceType.LAB_ASSAY,
                source_uri="lab://run-1",
                claim="Candidate meets the activity gate.",
                decision_tags=["progression"],
                confidence=0.9,
                strength=EvidenceStrength.SUPPORTING,
            ),
            EvidenceRecord(
                evidence_id="assay-2",
                kind=EvidenceKind.ASSAY,
                title="Assay 2",
                source="lab",
                source_type=EvidenceSourceType.LAB_ASSAY,
                source_uri="lab://run-1",
                claim="Candidate misses the activity gate.",
                decision_tags=["progression"],
                confidence=0.8,
                strength=EvidenceStrength.SUPPORTING,
            ),
        ],
    )
    _, resolutions = resolve_conflicts(bundle)
    claim = build_claim(
        claim_id="claim-hold",
        target_id="target-update-hold",
        statement="activity remains acceptable",
        evidence_ids=["assay-1", "assay-2"],
        status=ClaimStatus.SUPPORTED,
        confidence=0.7,
    )

    updated_claims, updates = apply_resolution_updates([claim], resolutions)

    assert updated_claims[0].status is ClaimStatus.DISPUTED
    assert updates[0].updated_confidence < claim.confidence

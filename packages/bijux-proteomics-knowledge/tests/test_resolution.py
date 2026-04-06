# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_knowledge import (
    ClaimStatus,
    ClaimResolutionRecord,
    EvidenceBundle,
    EvidenceKind,
    EvidenceRecord,
    EvidenceSourceType,
    EvidenceStrength,
    ResolutionAction,
    ResolutionPolicy,
    QuantitativeSupport,
    apply_resolution_updates,
    cluster_conflicts,
    preview_resolution_impact,
    build_claim,
    resolve_conflicts,
    summarize_resolutions,
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

# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_knowledge import (
    ClaimResolutionRecord,
    EvidenceBundle,
    EvidenceKind,
    EvidenceRecord,
    EvidenceSourceType,
    EvidenceStrength,
    ResolutionAction,
    ResolutionPolicy,
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

# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_knowledge import (
    EvidenceBundle,
    EvidenceKind,
    EvidenceRecord,
    EvidenceSourceType,
    EvidenceStrength,
    ResolutionAction,
    ResolutionPolicy,
    resolve_conflicts,
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

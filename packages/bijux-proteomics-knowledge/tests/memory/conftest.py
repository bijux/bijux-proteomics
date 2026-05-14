# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import pytest

from bijux_proteomics_knowledge.memory.models.evidence import (
    EvidenceBundle,
    EvidenceKind,
    EvidenceRecord,
    EvidenceSourceType,
    EvidenceStrength,
)


@pytest.fixture
def multi_source_disagreement_bundle() -> EvidenceBundle:
    """Representative memory conflict case owned by the resolution family."""

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

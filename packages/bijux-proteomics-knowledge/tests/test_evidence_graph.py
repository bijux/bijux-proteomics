# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_knowledge import (
    ClaimStatus,
    EvidenceBundle,
    EvidenceClaim,
    EvidenceKind,
    EvidenceRecord,
    EvidenceSourceType,
    EvidenceStrength,
    NormalizedEvidenceInput,
    attach_evidence_inputs,
    ingest_inputs_with_report,
    build_evidence_graph,
)


def test_build_evidence_graph_links_target_evidence_and_decisions() -> None:
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
                decision_tags=["progression"],
                confidence=0.8,
                strength=EvidenceStrength.SUPPORTING,
            ),
            EvidenceRecord(
                evidence_id="assay-1",
                kind=EvidenceKind.ASSAY,
                title="Assay",
                source="lab",
                source_type=EvidenceSourceType.LAB_ASSAY,
                claim="Candidate retained activity.",
                decision_tags=["progression"],
                derived_from=["lit-1"],
                confidence=0.9,
                strength=EvidenceStrength.DECISIVE,
            ),
        ],
    )

    graph = build_evidence_graph(
        bundle,
        claims=[
            EvidenceClaim(
                claim_id="claim-1",
                target_id="target-1",
                statement="Target should progress.",
                evidence_ids=["lit-1", "assay-1"],
                status=ClaimStatus.SUPPORTED,
            )
        ],
    )

    assert graph.target_id == "target-1"
    assert any(node.node_type.value == "claim" for node in graph.nodes)
    assert any(edge.relation == "supported_by" for edge in graph.edges)
    assert any(edge.relation == "informs" for edge in graph.edges)
    assert any(edge.relation == "derived_into" for edge in graph.edges)
    assert any(edge.relation == "supported_by_evidence" for edge in graph.edges)


def test_attach_evidence_inputs_converts_adapter_payloads_to_records() -> None:
    bundle = EvidenceBundle(bundle_id="bundle-2", target_id="target-2")

    updated = attach_evidence_inputs(
        bundle,
        [
            NormalizedEvidenceInput(
                evidence_id="ext-1",
                kind=EvidenceKind.STRUCTURE,
                title="Fold annotation",
                source="fold-service",
                source_type=EvidenceSourceType.STRUCTURE_MODEL,
                claim="Predicted fold remains plausible.",
                related_targets=["target-2"],
                decision_tags=["synthesis"],
                confidence=0.7,
                strength=EvidenceStrength.SUPPORTING,
            )
        ],
    )

    assert len(updated.records) == 1
    assert updated.records[0].source_type is EvidenceSourceType.STRUCTURE_MODEL


def test_ingest_inputs_with_report_tracks_duplicates() -> None:
    bundle = EvidenceBundle(
        bundle_id="bundle-3",
        target_id="target-3",
        records=[
            EvidenceRecord(
                evidence_id="existing-1",
                kind=EvidenceKind.LITERATURE,
                title="Paper",
                source="PMID:1",
                source_type=EvidenceSourceType.LITERATURE,
                claim="Existing claim.",
                confidence=0.7,
                strength=EvidenceStrength.SUPPORTING,
            )
        ],
    )
    updated, report = ingest_inputs_with_report(
        bundle,
        [
            NormalizedEvidenceInput(
                evidence_id="existing-1",
                kind=EvidenceKind.STRUCTURE,
                title="Duplicate",
                source="model",
                source_type=EvidenceSourceType.STRUCTURE_MODEL,
                claim="duplicate",
                confidence=0.6,
                strength=EvidenceStrength.EXPLORATORY,
            ),
            NormalizedEvidenceInput(
                evidence_id="new-1",
                kind=EvidenceKind.STRUCTURE,
                title="New",
                source="model",
                source_type=EvidenceSourceType.STRUCTURE_MODEL,
                claim="new",
                confidence=0.8,
                strength=EvidenceStrength.SUPPORTING,
            ),
        ],
    )

    assert len(updated.records) == 2
    assert report.added_records == 1
    assert report.duplicate_ids == ["existing-1"]

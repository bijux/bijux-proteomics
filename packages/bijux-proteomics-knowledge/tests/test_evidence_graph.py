# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_knowledge.memory.claims import ClaimStatus, EvidenceClaim
from bijux_proteomics_knowledge.memory.evidence import (
    EvidenceBundle,
    EvidenceKind,
    EvidenceRecord,
    EvidenceSourceType,
    EvidenceStrength,
    QuantitativeSupport,
)
from bijux_proteomics_knowledge.memory.graph import (
    LiabilityNodeInput,
    UnresolvedQuestion,
    build_evidence_graph,
    extract_decision_subgraph,
    trace_decision_paths,
    validate_evidence_graph,
)
from bijux_proteomics_knowledge.memory.ingestion import (
    NormalizedEvidenceInput,
    attach_evidence_inputs,
    ingest_inputs_with_report,
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
                contradicting_evidence_ids=["lit-1"],
                assumptions=["assay signal maps to disease-relevant biology"],
                status=ClaimStatus.SUPPORTED,
            )
        ],
        unresolved_questions=[
            UnresolvedQuestion(
                question_id="q1",
                text="Does orthogonal assay confirm the activity signal?",
                related_decision_tags=["progression"],
            )
        ],
        liabilities=[
            LiabilityNodeInput(
                liability_id="liability-1",
                summary="aggregation risk",
                related_decision_tags=["progression"],
            )
        ],
    )

    assert graph.target_id == "target-1"
    assert any(node.node_type.value == "claim" for node in graph.nodes)
    assert any(edge.relation == "supported_by" for edge in graph.edges)
    assert any(edge.relation == "informs" for edge in graph.edges)
    assert any(edge.relation == "derived_into" for edge in graph.edges)
    assert any(edge.relation == "supported_by_evidence" for edge in graph.edges)
    assert any(edge.relation == "contradicted_by_evidence" for edge in graph.edges)
    assert any(edge.relation == "assumes" for edge in graph.edges)
    assert any(node.node_type.value == "assumption" for node in graph.nodes)
    assert any(node.node_type.value == "question" for node in graph.nodes)
    assert any(node.node_type.value == "liability" for node in graph.nodes)
    assert any(edge.relation == "blocks" for edge in graph.edges)
    assert any(edge.relation == "risks" for edge in graph.edges)


def test_extract_decision_subgraph_keeps_decision_scoped_nodes() -> None:
    bundle = EvidenceBundle(
        bundle_id="bundle-subgraph",
        target_id="target-subgraph",
        records=[
            EvidenceRecord(
                evidence_id="ev-sub-1",
                kind=EvidenceKind.ASSAY,
                title="assay",
                source="lab",
                claim="supports progression",
                decision_tags=["progression"],
                confidence=0.8,
                strength=EvidenceStrength.SUPPORTING,
            )
        ],
    )
    graph = build_evidence_graph(bundle)
    subgraph = extract_decision_subgraph(graph, decision_tag="progression")

    assert any(node.node_id == "decision:progression" for node in subgraph.nodes)
    assert len(subgraph.nodes) <= len(graph.nodes)


def test_trace_decision_paths_returns_terminal_paths() -> None:
    bundle = EvidenceBundle(
        bundle_id="bundle-trace",
        target_id="target-trace",
        records=[
            EvidenceRecord(
                evidence_id="trace-1",
                kind=EvidenceKind.ASSAY,
                title="assay",
                source="lab",
                claim="supports progression",
                decision_tags=["progression"],
                confidence=0.8,
                strength=EvidenceStrength.SUPPORTING,
            )
        ],
    )
    graph = build_evidence_graph(bundle)
    traces = trace_decision_paths(graph, decision_tag="progression")

    assert len(traces) >= 1
    assert traces[0].path[0] == "decision:progression"


def test_validate_evidence_graph_reports_dangling_edges() -> None:
    graph = build_evidence_graph(
        EvidenceBundle(bundle_id="bundle-gv", target_id="target-gv")
    )
    broken = graph.model_copy(
        update={
            "edges": graph.edges
            + [
                {
                    "source_node_id": "target:target-gv",
                    "target_node_id": "evidence:missing",
                    "relation": "supported_by",
                }
            ]
        }
    )
    issues = validate_evidence_graph(broken)

    assert any(issue.code == "dangling-edge" for issue in issues)


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
                assay_modality="proteomics",
                biological_system="HEK293",
                species="human",
                sample_type="cell lysate",
                endpoint="fold_confidence",
                dose="0.5 uM",
                timepoint="6 h",
                perturbation="compound treatment",
                control_design="vehicle control",
                replicate_design="3 biological replicates",
                normalization_method="median normalization",
                sample_preparation="S-trap digestion",
                tissue_context="liver",
                cell_line_context="HEK293",
                quantitative_support=QuantitativeSupport(
                    effect_size=1.4,
                    p_value=0.01,
                    q_value=0.04,
                    replicate_count=3,
                    unit="fold-change",
                ),
            )
        ],
    )

    assert len(updated.records) == 1
    assert updated.records[0].source_type is EvidenceSourceType.STRUCTURE_MODEL
    assert updated.records[0].quantitative_support is not None
    assert updated.records[0].timepoint == "6 h"
    assert updated.records[0].normalization_method == "median normalization"


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
    assert "new-1" in report.accepted_fingerprints


def test_ingest_inputs_with_report_rejects_invalid_inputs_with_reasons() -> None:
    bundle = EvidenceBundle(bundle_id="bundle-4", target_id="target-4")
    updated, report = ingest_inputs_with_report(
        bundle,
        [
            NormalizedEvidenceInput(
                evidence_id="invalid-assay",
                kind=EvidenceKind.ASSAY,
                title="Invalid assay",
                source="lab",
                source_type=EvidenceSourceType.LAB_ASSAY,
                claim="Signal changed.",
                related_targets=["off-target"],
                confidence=0.6,
                strength=EvidenceStrength.EXPLORATORY,
            )
        ],
    )

    assert len(updated.records) == 0
    assert report.rejected_records >= 1
    assert any("endpoint is required" in reason for reason in report.rejection_reasons)

# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_intelligence.claims.support import (
    ClaimSupportStatus,
    ClaimSupportValidationEntry,
    render_claim_support_validation_tsv,
    validate_claim_support,
)
from bijux_proteomics_knowledge.memory.integrity.graph import (
    EvidenceEdge,
    EvidenceGraph,
    EvidenceNode,
    EvidenceNodeType,
)
from bijux_proteomics_knowledge.memory.models.claims import ClaimStatus, EvidenceClaim


def test_validate_claim_support_marks_claim_without_graph_evidence_invalid() -> None:
    report = validate_claim_support(
        (
            EvidenceClaim(
                claim_id="claim-supported",
                target_id="target:1",
                statement="supported claim",
                evidence_ids=["evidence-1"],
                status=ClaimStatus.SUPPORTED,
            ),
            EvidenceClaim(
                claim_id="claim-invalid",
                target_id="target:1",
                statement="invalid claim",
                evidence_ids=["evidence-missing"],
                status=ClaimStatus.INSUFFICIENT,
            ),
        ),
        _graph_for_support_checks(),
    )

    assert report.entries == (
        ClaimSupportValidationEntry(
            claim_id="claim-supported",
            support_status=ClaimSupportStatus.SUPPORTED,
            missing_support=(),
            contradicting_evidence=(),
        ),
        ClaimSupportValidationEntry(
            claim_id="claim-invalid",
            support_status=ClaimSupportStatus.INVALID,
            missing_support=(
                "claim node missing from evidence graph",
                "missing graph evidence node evidence:evidence-missing",
            ),
            contradicting_evidence=(),
        ),
    )
    assert report.summary.invalid_claim_count == 1


def test_validate_claim_support_keeps_contradicting_graph_evidence_explicit() -> None:
    report = validate_claim_support(
        (
            EvidenceClaim(
                claim_id="claim-conflicted",
                target_id="target:1",
                statement="conflicted claim",
                evidence_ids=["evidence-2"],
                contradicting_evidence_ids=["evidence-3"],
                status=ClaimStatus.DISPUTED,
            ),
        ),
        _graph_for_support_checks(),
    )

    assert report.entries == (
        ClaimSupportValidationEntry(
            claim_id="claim-conflicted",
            support_status=ClaimSupportStatus.CONFLICTED,
            missing_support=(),
            contradicting_evidence=("evidence-3",),
        ),
    )
    assert render_claim_support_validation_tsv(report.entries).splitlines()[0] == (
        "claim_id\tsupport_status\tmissing_support\tcontradicting_evidence"
    )


def _graph_for_support_checks() -> EvidenceGraph:
    return EvidenceGraph(
        bundle_id="bundle-1",
        target_id="target:1",
        nodes=[
            EvidenceNode(
                node_id="claim:claim-supported",
                node_type=EvidenceNodeType.CLAIM,
                label="supported claim",
            ),
            EvidenceNode(
                node_id="claim:claim-conflicted",
                node_type=EvidenceNodeType.CLAIM,
                label="conflicted claim",
            ),
            EvidenceNode(
                node_id="evidence:evidence-1",
                node_type=EvidenceNodeType.EVIDENCE,
                label="support row",
            ),
            EvidenceNode(
                node_id="evidence:evidence-2",
                node_type=EvidenceNodeType.EVIDENCE,
                label="support row two",
            ),
            EvidenceNode(
                node_id="evidence:evidence-3",
                node_type=EvidenceNodeType.EVIDENCE,
                label="contradiction row",
            ),
        ],
        edges=[
            EvidenceEdge(
                source_node_id="claim:claim-supported",
                target_node_id="evidence:evidence-1",
                relation="supported_by_evidence",
            ),
            EvidenceEdge(
                source_node_id="claim:claim-conflicted",
                target_node_id="evidence:evidence-2",
                relation="supported_by_evidence",
            ),
            EvidenceEdge(
                source_node_id="claim:claim-conflicted",
                target_node_id="evidence:evidence-3",
                relation="contradicted_by_evidence",
            ),
        ],
    )

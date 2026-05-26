# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

import pytest

from bijux_proteomics_intelligence.reviews import (
    build_intelligence_report_contract,
    validate_intelligence_report_contract,
)
from bijux_proteomics_knowledge.memory.integrity.graph import (
    EvidenceEdge,
    EvidenceGraph,
    EvidenceNode,
    EvidenceNodeType,
)
from bijux_proteomics_knowledge.memory.models.claims import ClaimStatus, EvidenceClaim


def test_build_intelligence_report_contract_keeps_claim_review_state_typed() -> None:
    contract = build_intelligence_report_contract(_claims(), _graph())

    entry_by_claim_id = {
        entry.claim.claim_id: entry for entry in contract.claim_entries
    }

    assert contract.summary.claim_count == 3
    assert contract.summary.supported_claim_count == 3
    assert contract.summary.refused_claim_count == 1
    assert contract.summary.top_claim_count == 3
    assert contract.summary.belief_audited_claim_count == 3
    assert contract.summary.contradiction_pair_count == 1

    top_supported = entry_by_claim_id["claim-top-supported"]
    assert top_supported.support_validation.claim_id == "claim-top-supported"
    assert top_supported.refusal.refused is False
    assert top_supported.falsifier.claim_id == "claim-top-supported"
    assert top_supported.belief_audit is not None

    top_refused = entry_by_claim_id["claim-top-refused"]
    assert top_refused.refusal.refused is True
    assert top_refused.refusal.refusal_reason is not None
    assert top_refused.contradictions
    assert {
        contradiction.claim_a for contradiction in top_refused.contradictions
    } | {
        contradiction.claim_b for contradiction in top_refused.contradictions
    } >= {"claim-top-refused", "claim-opposed"}


def test_validate_intelligence_report_contract_rejects_missing_top_claim_belief_audit() -> (
    None
):
    contract = build_intelligence_report_contract(_claims(), _graph())
    top_claim_id = contract.belief_audit_report.summary.top_claim_ids[0]
    damaged_entries = tuple(
        entry.model_copy(update={"belief_audit": None})
        if entry.claim.claim_id == top_claim_id
        else entry
        for entry in contract.claim_entries
    )
    damaged_contract = contract.model_copy(update={"claim_entries": damaged_entries})

    with pytest.raises(
        ValueError,
        match=f"missing belief audit for top claim {top_claim_id}",
    ):
        validate_intelligence_report_contract(damaged_contract)


def _claims() -> tuple[EvidenceClaim, ...]:
    return (
        EvidenceClaim(
            claim_id="claim-top-supported",
            target_id="protein:p11111",
            statement="protein P11111 increases in treatment",
            evidence_ids=["evidence-1"],
            assumptions=[
                "design_valid=true",
                "qc_status=passed",
                "peptide_support_count=3",
            ],
            resolution_assays=["targeted rerun"],
            status=ClaimStatus.SUPPORTED,
            confidence=0.95,
            condition="control_vs_treated",
            direction="up",
        ),
        EvidenceClaim(
            claim_id="claim-top-refused",
            target_id="protein:p22222",
            statement="protein P22222 increases despite invalid design",
            evidence_ids=["evidence-2"],
            assumptions=[
                "design_valid=false",
                "qc_status=passed",
                "peptide_support_count=3",
            ],
            resolution_assays=["design repair rerun"],
            status=ClaimStatus.SUPPORTED,
            confidence=0.93,
            condition="control_vs_treated",
            direction="up",
        ),
        EvidenceClaim(
            claim_id="claim-opposed",
            target_id="protein:p22222",
            statement="protein P22222 decreases in treatment",
            evidence_ids=["evidence-3"],
            assumptions=[
                "design_valid=true",
                "qc_status=passed",
                "peptide_support_count=3",
            ],
            resolution_assays=["orthogonal protein rerun"],
            status=ClaimStatus.SUPPORTED,
            confidence=0.91,
            condition="control_vs_treated",
            direction="down",
        ),
    )


def _graph() -> EvidenceGraph:
    return EvidenceGraph(
        bundle_id="bundle-1",
        target_id="target-1",
        nodes=[
            EvidenceNode(
                node_id="claim:claim-top-supported",
                node_type=EvidenceNodeType.CLAIM,
                label="protein P11111 increases in treatment",
            ),
            EvidenceNode(
                node_id="claim:claim-top-refused",
                node_type=EvidenceNodeType.CLAIM,
                label="protein P22222 increases despite invalid design",
            ),
            EvidenceNode(
                node_id="claim:claim-opposed",
                node_type=EvidenceNodeType.CLAIM,
                label="protein P22222 decreases in treatment",
            ),
            EvidenceNode(
                node_id="evidence:evidence-1",
                node_type=EvidenceNodeType.EVIDENCE,
                label="support row 1",
            ),
            EvidenceNode(
                node_id="evidence:evidence-2",
                node_type=EvidenceNodeType.EVIDENCE,
                label="support row 2",
            ),
            EvidenceNode(
                node_id="evidence:evidence-3",
                node_type=EvidenceNodeType.EVIDENCE,
                label="support row 3",
            ),
        ],
        edges=[
            EvidenceEdge(
                source_node_id="claim:claim-top-supported",
                target_node_id="evidence:evidence-1",
                relation="supported_by_evidence",
            ),
            EvidenceEdge(
                source_node_id="claim:claim-top-refused",
                target_node_id="evidence:evidence-2",
                relation="supported_by_evidence",
            ),
            EvidenceEdge(
                source_node_id="claim:claim-opposed",
                target_node_id="evidence:evidence-3",
                relation="supported_by_evidence",
            ),
        ],
    )

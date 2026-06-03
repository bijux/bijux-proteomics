# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_intelligence.belief_audit import (
    build_belief_audit,
    render_belief_audit_tsv,
)
from bijux_proteomics_knowledge.memory.integrity.graph import (
    EvidenceEdge,
    EvidenceGraph,
    EvidenceNode,
    EvidenceNodeType,
)
from bijux_proteomics_knowledge.memory.models.claims import (
    ClaimStatus,
    ClaimType,
    EvidenceClaim,
)


def test_build_belief_audit_keeps_top_claim_rows_and_balanced_evidence_visible() -> (
    None
):
    report = build_belief_audit(
        (
            EvidenceClaim(
                claim_id="claim-top-protein",
                target_id="protein:p11111",
                statement="protein abundance increases",
                evidence_ids=["evidence-1"],
                resolution_assays=["targeted validation assay"],
                status=ClaimStatus.SUPPORTED,
                confidence=0.95,
            ),
            EvidenceClaim(
                claim_id="claim-top-ptm",
                target_id="ptm_site:p11111:s5:phospho",
                statement="site-specific phosphorylation increases",
                evidence_ids=["evidence-2"],
                contradicting_evidence_ids=["evidence-3"],
                assumptions=[
                    "protein_correction_status=high_confidence_corrected",
                    "mechanism_class=site_specific",
                ],
                resolution_assays=["site localization rerun"],
                status=ClaimStatus.DISPUTED,
                confidence=0.9,
            ),
            EvidenceClaim(
                claim_id="claim-top-pathway",
                target_id="pathway:stress_response",
                statement="stress response pathway is activated",
                evidence_ids=["evidence-missing"],
                claim_type=ClaimType.MECHANISTIC,
                status=ClaimStatus.INSUFFICIENT,
                confidence=0.85,
            ),
        ),
        _belief_audit_graph(),
    )

    entry_by_claim_id = {entry.claim_id: entry for entry in report.entries}

    assert report.summary.top_claim_ids == (
        "claim-top-protein",
        "claim-top-ptm",
        "claim-top-pathway",
    )
    assert set(entry_by_claim_id) == {
        "claim-top-protein",
        "claim-top-ptm",
        "claim-top-pathway",
    }

    protein_entry = entry_by_claim_id["claim-top-protein"]
    assert protein_entry.evidence_for == ("evidence-1",)
    assert protein_entry.evidence_against == ()
    assert protein_entry.falsifier == "orthogonal_protein_quant_failure"
    assert protein_entry.next_check == "targeted validation assay"

    ptm_entry = entry_by_claim_id["claim-top-ptm"]
    assert ptm_entry.evidence_for == ("evidence-2",)
    assert ptm_entry.evidence_against == ("evidence-3",)
    assert "contradicting_evidence_present" in ptm_entry.uncertainty
    assert "assumption_dependent" in ptm_entry.uncertainty
    assert ptm_entry.falsifier == "site_localization_or_correction_failure"
    assert ptm_entry.next_check == "site localization rerun"

    invalid_entry = entry_by_claim_id["claim-top-pathway"]
    assert invalid_entry.evidence_for == ("evidence-missing",)
    assert invalid_entry.evidence_against == ()
    assert any(
        item.startswith("missing_support:") for item in invalid_entry.uncertainty
    )
    assert invalid_entry.falsifier == "pathway_member_support_collapse"
    assert invalid_entry.next_check == "claim node missing from evidence graph"


def test_render_belief_audit_tsv_preserves_required_columns() -> None:
    report = build_belief_audit(
        (
            EvidenceClaim(
                claim_id="claim-top-protein",
                target_id="protein:p11111",
                statement="protein abundance increases",
                evidence_ids=["evidence-1"],
                resolution_assays=["targeted validation assay"],
                status=ClaimStatus.SUPPORTED,
                confidence=0.95,
            ),
        ),
        _belief_audit_graph(),
    )

    assert render_belief_audit_tsv(report.entries).splitlines()[0] == (
        "claim_id\tevidence_for\tevidence_against\tuncertainty\tfalsifier\tconfidence\tnext_check"
    )


def _belief_audit_graph() -> EvidenceGraph:
    return EvidenceGraph(
        bundle_id="bundle-1",
        target_id="target:1",
        nodes=[
            EvidenceNode(
                node_id="claim:claim-top-protein",
                node_type=EvidenceNodeType.CLAIM,
                label="protein abundance increases",
            ),
            EvidenceNode(
                node_id="claim:claim-top-ptm",
                node_type=EvidenceNodeType.CLAIM,
                label="site-specific phosphorylation increases",
            ),
            EvidenceNode(
                node_id="evidence:evidence-1",
                node_type=EvidenceNodeType.EVIDENCE,
                label="protein support row",
            ),
            EvidenceNode(
                node_id="evidence:evidence-2",
                node_type=EvidenceNodeType.EVIDENCE,
                label="ptm support row",
            ),
            EvidenceNode(
                node_id="evidence:evidence-3",
                node_type=EvidenceNodeType.EVIDENCE,
                label="ptm contradiction row",
            ),
        ],
        edges=[
            EvidenceEdge(
                source_node_id="claim:claim-top-protein",
                target_node_id="evidence:evidence-1",
                relation="supported_by_evidence",
            ),
            EvidenceEdge(
                source_node_id="claim:claim-top-ptm",
                target_node_id="evidence:evidence-2",
                relation="supported_by_evidence",
            ),
            EvidenceEdge(
                source_node_id="claim:claim-top-ptm",
                target_node_id="evidence:evidence-3",
                relation="contradicted_by_evidence",
            ),
        ],
    )

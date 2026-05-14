# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

from __future__ import annotations

from bijux_proteomics_knowledge.references.workflows.benchmarks import (
    KnowledgeWorkflowFamily,
)
from bijux_proteomics_knowledge.references.workflows.claim_grounding import (
    ClaimNarrativeSurface,
    ClaimSupportState,
    ScientificClaimSeverity,
    build_workflow_claim_citation_table,
    build_workflow_unsupported_claim_ledger,
    list_workflow_claim_citation_tables,
)


def test_workflow_claim_citation_tables_cover_each_family() -> None:
    tables = list_workflow_claim_citation_tables()

    assert {table.workflow_family for table in tables} == set(KnowledgeWorkflowFamily)


def test_workflow_claim_citation_table_keeps_doc_and_packet_surfaces_explicit() -> None:
    targeted = build_workflow_claim_citation_table(KnowledgeWorkflowFamily.TARGETED)
    multiplex = build_workflow_claim_citation_table(KnowledgeWorkflowFamily.MULTIPLEX)

    assert targeted.outsider_packet_id == "outsider_review:targeted"
    assert any(
        entry.surface is ClaimNarrativeSurface.TRUST_PAGE for entry in targeted.entries
    )
    assert any(
        entry.surface is ClaimNarrativeSurface.OUTSIDER_PACKET
        for entry in targeted.entries
    )
    assert multiplex.outsider_packet_id is None
    assert all(
        entry.surface is ClaimNarrativeSurface.AUTHORITY_BOUNDARY
        for entry in multiplex.entries
    )
    assert "claim-bearing narrative sentences" in targeted.coverage_scope_note


def test_workflow_unsupported_claim_ledger_tracks_only_low_severity_current_overreach() -> (
    None
):
    ledger = build_workflow_unsupported_claim_ledger(KnowledgeWorkflowFamily.DIA)

    assert ledger.threshold_blocking_severities == (
        ScientificClaimSeverity.MEDIUM,
        ScientificClaimSeverity.HIGH,
    )
    assert ledger.entries
    assert all(
        entry.scientific_severity is ScientificClaimSeverity.LOW
        for entry in ledger.entries
    )
    assert "independent rerun dossier" in ledger.entries[0].why_still_thin


def test_claim_grounding_entries_keep_supported_and_thin_claims_distinguishable() -> (
    None
):
    dda = build_workflow_claim_citation_table(KnowledgeWorkflowFamily.DDA)

    assert any(
        entry.support_state is ClaimSupportState.SUPPORTED for entry in dda.entries
    )
    assert any(
        entry.support_state is ClaimSupportState.THINNER_THAN_WORDING
        for entry in dda.entries
    )
    assert any("target-decoy semantics" in entry.claim_text for entry in dda.entries)

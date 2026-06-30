# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Card facade ledgers for workflow evidence surfaces."""

from __future__ import annotations

from bijux_proteomics.workflow.facade_catalog import (
    WorkflowFacadeOwner,
    copy_facade_owners,
)


CARD_FACADE_OWNERS = (
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.cards.cross_study_evidence_cards",
        rationale="cross-study evidence card ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.cards.mechanisms",
        rationale="mechanism card workflow ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.cards.pathway_evidence_cards",
        rationale="pathway evidence card ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.cards.protein_evidence_cards",
        rationale="protein evidence card ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.cards.protein_mechanism_cards",
        rationale="protein mechanism card ownership",
    ),
    WorkflowFacadeOwner(
        owner_module="bijux_proteomics.workflow.cards.sample_evidence_cards",
        rationale="sample evidence card ownership",
    ),
)

WORKFLOW_ROOT_CARD_HELPER_EXPORTS = (
    "render_cross_study_evidence_card_summary_tsv",
    "render_cross_study_evidence_card_tsv",
    "render_cross_study_evidence_dataset_tsv",
    "render_mechanism_card_summary_tsv",
    "render_mechanism_cards_tsv",
    "export_pathway_evidence_card_tsv",
    "render_pathway_evidence_card_tsv",
    "export_protein_evidence_card_summary_tsv",
    "export_protein_evidence_card_tsv",
    "render_protein_evidence_card_summary_tsv",
    "render_protein_evidence_card_tsv",
    "export_protein_mechanism_card_summary_tsv",
    "export_protein_mechanism_card_tsv",
    "render_protein_mechanism_card_summary_tsv",
    "render_protein_mechanism_card_tsv",
    "export_sample_evidence_card_tsv",
    "render_sample_evidence_card_tsv",
)

WORKFLOW_ROOT_CARD_OWNERS = copy_facade_owners(CARD_FACADE_OWNERS)


__all__ = [
    "CARD_FACADE_OWNERS",
    "WORKFLOW_ROOT_CARD_HELPER_EXPORTS",
    "WORKFLOW_ROOT_CARD_OWNERS",
    "WorkflowFacadeOwner",
]

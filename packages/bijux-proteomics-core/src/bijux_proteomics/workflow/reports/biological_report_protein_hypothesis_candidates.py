# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi
"""Protein biological hypothesis candidate builders."""

from __future__ import annotations

from bijux_proteomics.review.claims.biological_claim_validation import (
    BiologicalClaimKind,
    BiologicalClaimValidationReport,
)
from bijux_proteomics.review.claims.biological_hypotheses import (
    BiologicalHypothesisCandidate,
    BiologicalHypothesisKind,
)
from bijux_proteomics.workflow.cards.protein_mechanism_cards import (
    ProteinMechanismCardReport,
)
from bijux_proteomics.workflow.reports.biological_report_hypothesis_evidence import (
    _graph_node_ids_from_cards,
    _protein_hypothesis_opposing_evidence,
)
from bijux_proteomics.workflow.reports.biological_report_hypothesis_scoring import (
    _protein_hypothesis_base_confidence,
)


def _build_biological_protein_hypothesis_candidates(
    claim_validation_report: BiologicalClaimValidationReport,
    *,
    protein_mechanism_cards: ProteinMechanismCardReport,
) -> tuple[BiologicalHypothesisCandidate, ...]:
    cards_by_group_id = {
        card.protein_group_id: card for card in protein_mechanism_cards.cards
    }
    candidates: list[BiologicalHypothesisCandidate] = []
    for claim in claim_validation_report.supported_claims:
        if claim.claim_kind is not BiologicalClaimKind.PROTEIN_ABUNDANCE_CHANGE:
            continue
        card = cards_by_group_id.get(claim.subject_id)
        supporting_site_keys = (
            tuple(ptm.site_key for ptm in card.ptms) if card is not None else ()
        )
        supporting_pathway_ids = (
            tuple(pathway.entry_id for pathway in card.pathways)
            if card is not None
            else ()
        )
        candidates.append(
            BiologicalHypothesisCandidate(
                hypothesis_id=f"protein-hypothesis:{claim.subject_id}",
                hypothesis_kind=BiologicalHypothesisKind.PROTEIN_MECHANISM,
                subject_id=claim.subject_id,
                subject_label=claim.subject_label,
                claim=claim.claim_text,
                supporting_protein_refs=(
                    (card.representative_protein_ref,) if card is not None else ()
                ),
                supporting_site_keys=supporting_site_keys,
                supporting_pathway_ids=supporting_pathway_ids,
                opposing_evidence=(
                    _protein_hypothesis_opposing_evidence(card)
                    if card is not None
                    else ()
                ),
                evidence_node_ids=_graph_node_ids_from_cards(
                    () if card is None else (card,)
                ),
                base_confidence_score=_protein_hypothesis_base_confidence(
                    claim,
                    card=card,
                ),
                source_ids=claim.source_ids
                + (() if card is None else (card.card_id, card.protein_card_id)),
                note=(
                    "validated protein claims become biological hypotheses only when a "
                    "graph-backed protein mechanism card preserves the supporting claim "
                    "and subject node ids"
                ),
            )
        )
    return tuple(candidates)


__all__ = ["_build_biological_protein_hypothesis_candidates"]

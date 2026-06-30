# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi
"""Pathway biological hypothesis candidate builders."""

from __future__ import annotations

from bijux_proteomics.interpretation import PathwayActivityReport
from bijux_proteomics.review.claims.biological_claim_validation import (
    BiologicalClaimKind,
    BiologicalClaimValidationReport,
)
from bijux_proteomics.review.claims.biological_hypotheses import (
    BiologicalHypothesisCandidate,
    BiologicalHypothesisKind,
)
from bijux_proteomics.workflow.cards.protein_mechanism_cards import (
    ProteinMechanismCard,
    ProteinMechanismCardReport,
)
from bijux_proteomics.workflow.reports.biological_report_hypothesis_evidence import (
    _graph_node_ids_from_cards,
    _pathway_hypothesis_opposing_evidence,
    _pathway_hypothesis_supporting_protein_refs,
)
from bijux_proteomics.workflow.reports.biological_report_hypothesis_scoring import (
    _pathway_hypothesis_base_confidence,
)


def _build_biological_pathway_hypothesis_candidates(
    claim_validation_report: BiologicalClaimValidationReport,
    *,
    protein_mechanism_cards: ProteinMechanismCardReport,
    pathway_activity_report: PathwayActivityReport | None,
) -> tuple[BiologicalHypothesisCandidate, ...]:
    if pathway_activity_report is None:
        return ()
    cards_by_ref: dict[str, ProteinMechanismCard] = {
        card.representative_protein_ref: card for card in protein_mechanism_cards.cards
    }
    comparisons = {
        (entry.pathway_id, entry.condition_a, entry.condition_b): entry
        for entry in pathway_activity_report.condition_comparisons
    }
    candidates: list[BiologicalHypothesisCandidate] = []
    for claim in claim_validation_report.supported_claims:
        if claim.claim_kind is not BiologicalClaimKind.PATHWAY_ACTIVITY_CHANGE:
            continue
        comparison = comparisons.get(
            (claim.subject_id, claim.condition_a, claim.condition_b)
        )
        supporting_protein_refs = (
            ()
            if comparison is None
            else _pathway_hypothesis_supporting_protein_refs(
                pathway_activity_report,
                pathway_id=comparison.pathway_id,
                condition_a=comparison.condition_a,
                condition_b=comparison.condition_b,
                cards_by_ref=cards_by_ref,
            )
        )
        supporting_cards = tuple(
            cards_by_ref[protein_ref]
            for protein_ref in supporting_protein_refs
            if protein_ref in cards_by_ref
        )
        candidates.append(
            BiologicalHypothesisCandidate(
                hypothesis_id=(
                    "pathway-hypothesis:"
                    f"{claim.subject_id}:{claim.condition_a}:{claim.condition_b}"
                ),
                hypothesis_kind=BiologicalHypothesisKind.PATHWAY_ACTIVITY,
                subject_id=claim.subject_id,
                subject_label=claim.subject_label,
                claim=claim.claim_text,
                supporting_protein_refs=supporting_protein_refs,
                supporting_pathway_ids=(claim.subject_id,),
                opposing_evidence=(
                    _pathway_hypothesis_opposing_evidence(
                        pathway_activity_report,
                        comparison=comparison,
                    )
                    if comparison is not None
                    else ()
                ),
                evidence_node_ids=_graph_node_ids_from_cards(supporting_cards),
                base_confidence_score=_pathway_hypothesis_base_confidence(
                    claim,
                    comparison=comparison,
                ),
                source_ids=claim.source_ids
                + tuple(card.card_id for card in supporting_cards),
                note=(
                    "pathway hypotheses inherit directional activity support from the "
                    "owned pathway activity report and anchor onto graph-backed member "
                    "protein evidence nodes"
                ),
            )
        )
    return tuple(candidates)


__all__ = ["_build_biological_pathway_hypothesis_candidates"]

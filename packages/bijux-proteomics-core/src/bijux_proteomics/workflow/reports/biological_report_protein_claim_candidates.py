# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Protein claim candidate builders for governed biological reports."""

from __future__ import annotations

from bijux_proteomics.domain.semantic_ids import build_protein_claim_id
from bijux_proteomics.quantification.contracts import DifferentialAbundanceReport
from bijux_proteomics.review.claims.biological_claim_validation import (
    BiologicalClaimCandidate,
    BiologicalClaimDirection,
    BiologicalClaimKind,
)
from bijux_proteomics.workflow.cards.protein_mechanism_cards import (
    ProteinMechanismCardReport,
)


def _build_biological_protein_claim_candidates(
    differential_report: DifferentialAbundanceReport,
    *,
    protein_mechanism_cards: ProteinMechanismCardReport,
) -> tuple[BiologicalClaimCandidate, ...]:
    differential_by_entity = {
        entry.entity_id: entry for entry in differential_report.entries
    }
    candidates: list[BiologicalClaimCandidate] = []
    for card in protein_mechanism_cards.cards:
        if card.abundance_change.direction.value == "unchanged":
            continue
        differential_entry = differential_by_entity.get(card.protein_group_id)
        if differential_entry is None:
            raise ValueError(
                "biological claim validation requires one differential entry per protein mechanism card"
            )
        direction = (
            BiologicalClaimDirection.UP
            if card.abundance_change.direction.value == "increased"
            else BiologicalClaimDirection.DOWN
        )
        direction_label = (
            "increased" if direction is BiologicalClaimDirection.UP else "decreased"
        )
        candidates.append(
            BiologicalClaimCandidate(
                claim_id=build_protein_claim_id(card.protein_group_id),
                claim_kind=BiologicalClaimKind.PROTEIN_ABUNDANCE_CHANGE,
                subject_id=card.protein_group_id,
                subject_label=card.gene_symbol or card.representative_protein_ref,
                claim_text=(
                    f"Protein {card.gene_symbol or card.representative_protein_ref} "
                    f"{direction_label} in {card.abundance_change.condition_b} vs "
                    f"{card.abundance_change.condition_a}"
                ),
                condition_a=card.abundance_change.condition_a,
                condition_b=card.abundance_change.condition_b,
                asserted_direction=direction,
                significant=card.abundance_change.significant,
                adjusted_p_value=card.abundance_change.adjusted_p_value,
                effect_size=abs(card.abundance_change.log2_fold_change),
                robustness_score=differential_entry.robustness_score,
                imputation_dependent=differential_entry.imputation_dependent_hit,
                evidence_tier=card.evidence_tier,
                confidence_tier=card.confidence_tier,
                source_ids=(
                    card.card_id,
                    card.graph_claim_node_id,
                    card.protein_card_id,
                ),
                source_row_refs=card.source_row_refs,
                derived_no_source_reason=card.derived_no_source_reason,
                note=(
                    "protein abundance claims require robust quantitative support, "
                    "not just nominal differential direction"
                ),
            )
        )
    return tuple(candidates)

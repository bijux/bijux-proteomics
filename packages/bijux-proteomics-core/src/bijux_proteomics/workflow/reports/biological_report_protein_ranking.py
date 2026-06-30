# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Protein ranking candidate construction for biological reports."""

from __future__ import annotations

from bijux_proteomics.quantification.contracts import DifferentialAbundanceReport
from bijux_proteomics.review.belief.evidence_aware_ranking import (
    EvidenceAwareRankingCandidate,
    EvidenceAwareRankingEntityKind,
    normalize_linear_range,
    score_adjusted_p_value,
    score_effect_size,
)
from bijux_proteomics.study import ExperimentConfidenceReport
from bijux_proteomics.workflow.cards.protein_evidence_cards import (
    ProteinEvidenceCardReport,
)
from bijux_proteomics.workflow.cards.protein_mechanism_cards import (
    ProteinMechanismCardReport,
)
from bijux_proteomics.workflow.reports.biological_report_protein_ranking_scoring import (
    _build_protein_annotation_score,
    _build_protein_confidence_score,
    _build_protein_ranking_penalties,
    _build_protein_reproducibility_score,
    _build_protein_support_score,
)
from bijux_proteomics.workflow.reports.biological_report_ranking_support import (
    _biological_result_uncertainty,
)


def _build_biological_protein_ranking_candidates(
    differential_report: DifferentialAbundanceReport,
    *,
    protein_cards: ProteinEvidenceCardReport,
    protein_mechanism_cards: ProteinMechanismCardReport,
    experiment_confidence_report: ExperimentConfidenceReport,
) -> tuple[EvidenceAwareRankingCandidate, ...]:
    differential_by_entity = {
        entry.entity_id: entry for entry in differential_report.entries
    }
    mechanism_by_protein_group = {
        card.protein_group_id: card for card in protein_mechanism_cards.cards
    }
    abundance_by_entity = {
        card.protein_group_id: max(
            card.differential_result.mean_log2_abundance_a,
            card.differential_result.mean_log2_abundance_b,
        )
        for card in protein_cards.cards
    }
    abundance_scores = normalize_linear_range(abundance_by_entity)

    candidates: list[EvidenceAwareRankingCandidate] = []
    for protein_card in protein_cards.cards:
        mechanism_card = mechanism_by_protein_group.get(protein_card.protein_group_id)
        if mechanism_card is None:
            raise ValueError(
                "biological evidence-aware ranking requires one protein mechanism card per protein card"
            )
        differential_entry = differential_by_entity.get(protein_card.protein_group_id)
        if differential_entry is None:
            raise ValueError(
                "biological evidence-aware ranking requires one differential entry per protein card"
            )
        abundance_value = abundance_by_entity[protein_card.protein_group_id]
        unique_support = mechanism_card.peptide_support.unique_peptide_count
        abundance_score = abundance_scores[protein_card.protein_group_id]
        support_score = _build_protein_support_score(mechanism_card)
        annotation_score = _build_protein_annotation_score(protein_card)
        confidence_score = _build_protein_confidence_score(mechanism_card)
        reproducibility_score = _build_protein_reproducibility_score(
            differential_entry
        )
        qc_score = max(
            0.0,
            experiment_confidence_report.summary.overall_score
            - (0.04 * len(protein_card.warnings)),
        )
        penalties = _build_protein_ranking_penalties(
            protein_card=protein_card,
            differential_entry=differential_entry,
            abundance_score=abundance_score,
            unique_support=unique_support,
        )
        candidates.append(
            EvidenceAwareRankingCandidate(
                candidate_id=protein_card.protein_group_id,
                entity_kind=EvidenceAwareRankingEntityKind.PROTEIN,
                display_label=protein_card.representative_protein_ref,
                effect_size=abs(protein_card.differential_result.log2_fold_change),
                adjusted_p_value=protein_card.differential_result.adjusted_p_value,
                abundance_value=abundance_value,
                support_count=unique_support,
                annotation_label=protein_card.annotation.gene_symbol
                or protein_card.annotation.description,
                effect_score=score_effect_size(
                    abs(protein_card.differential_result.log2_fold_change),
                    saturation=2.0,
                ),
                significance_score=score_adjusted_p_value(
                    protein_card.differential_result.adjusted_p_value
                ),
                abundance_score=abundance_score,
                support_score=support_score,
                qc_score=qc_score,
                annotation_score=annotation_score,
                reproducibility_score=reproducibility_score,
                confidence_score=confidence_score,
                penalties=penalties,
                uncertainty=_biological_result_uncertainty(protein_card),
                source_ids=(
                    protein_card.card_id,
                    mechanism_card.card_id,
                    protein_card.graph_claim_node_id,
                ),
                note=(
                    "protein ranking combines differential strength, abundance, peptide "
                    "support, experiment confidence, annotation, and graph confidence"
                ),
            )
        )
    return tuple(candidates)

# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Pathway ranking candidate construction for biological reports."""

from __future__ import annotations

from bijux_proteomics.interpretation import PathwayEnrichmentReport
from bijux_proteomics.review.belief.evidence_aware_ranking import (
    EvidenceAwareRankingCandidate,
    EvidenceAwareRankingEntityKind,
    normalize_linear_range,
    score_adjusted_p_value,
    score_effect_size,
    score_support_count,
)
from bijux_proteomics.study import ExperimentConfidenceReport
from bijux_proteomics.workflow.cards.protein_mechanism_cards import (
    ProteinMechanismCardReport,
)
from bijux_proteomics.workflow.reports.biological_report_ranking_support import (
    _mean,
    _tier_score,
)


def _build_biological_pathway_ranking_candidates(
    pathway_enrichment_report: PathwayEnrichmentReport | None,
    *,
    protein_mechanism_cards: ProteinMechanismCardReport,
    experiment_confidence_report: ExperimentConfidenceReport,
) -> tuple[EvidenceAwareRankingCandidate, ...]:
    if pathway_enrichment_report is None:
        return ()
    support_by_member_id: dict[str, list[float]] = {}
    abundance_by_member_id: dict[str, list[float]] = {}
    reproducibility_by_member_id: dict[str, list[float]] = {}
    for card in protein_mechanism_cards.cards:
        support_by_member_id.setdefault(card.protein_group_id, []).append(
            _tier_score(card.confidence_tier.value)
        )
        support_by_member_id.setdefault(card.representative_protein_ref, []).append(
            _tier_score(card.confidence_tier.value)
        )
        if card.gene_symbol:
            support_by_member_id.setdefault(card.gene_symbol, []).append(
                _tier_score(card.confidence_tier.value)
            )
        abundance = abs(card.abundance_change.log2_fold_change)
        abundance_by_member_id.setdefault(card.protein_group_id, []).append(abundance)
        abundance_by_member_id.setdefault(card.representative_protein_ref, []).append(
            abundance
        )
        if card.gene_symbol:
            abundance_by_member_id.setdefault(card.gene_symbol, []).append(abundance)
        reproducibility = min(
            1.0,
            (
                0.5
                * score_support_count(
                    card.peptide_support.unique_peptide_count,
                    saturation=4,
                )
            )
            + (0.5 * _tier_score(card.evidence_tier.value)),
        )
        reproducibility_by_member_id.setdefault(card.protein_group_id, []).append(
            reproducibility
        )
        reproducibility_by_member_id.setdefault(
            card.representative_protein_ref,
            [],
        ).append(reproducibility)
        if card.gene_symbol:
            reproducibility_by_member_id.setdefault(card.gene_symbol, []).append(
                reproducibility
            )

    pathway_abundance = {
        entry.pathway_id: _mean(
            abundance_by_member_id.get(member_id, ())
            for member_id in entry.foreground_member_ids
        )
        for entry in pathway_enrichment_report.entries
    }
    abundance_scores = normalize_linear_range(pathway_abundance)

    candidates: list[EvidenceAwareRankingCandidate] = []
    for entry in pathway_enrichment_report.entries:
        support_strength = _mean(
            support_by_member_id.get(member_id, ())
            for member_id in entry.foreground_member_ids
        )
        reproducibility = _mean(
            reproducibility_by_member_id.get(member_id, ())
            for member_id in entry.foreground_member_ids
        )
        penalties: dict[str, float] = {}
        if entry.foreground_overlap_count <= 1:
            penalties["weak_member_support"] = 0.14
        if support_strength == 0.0:
            penalties["unresolved_supporting_members"] = 0.1
        if support_strength < 0.5:
            penalties["weak_supporting_proteins"] = 0.08
        candidates.append(
            EvidenceAwareRankingCandidate(
                candidate_id=entry.pathway_id,
                entity_kind=EvidenceAwareRankingEntityKind.PATHWAY,
                display_label=entry.pathway_name or entry.pathway_id,
                effect_size=entry.enrichment_ratio,
                adjusted_p_value=entry.adjusted_p_value,
                abundance_value=pathway_abundance[entry.pathway_id],
                support_count=entry.foreground_overlap_count,
                annotation_label=entry.source_name,
                effect_score=score_effect_size(
                    None
                    if entry.enrichment_ratio is None
                    else max(0.0, entry.enrichment_ratio - 1.0),
                    saturation=2.0,
                ),
                significance_score=score_adjusted_p_value(entry.adjusted_p_value),
                abundance_score=abundance_scores[entry.pathway_id],
                support_score=min(
                    1.0,
                    (
                        0.6
                        * score_support_count(
                            entry.foreground_overlap_count, saturation=5
                        )
                    )
                    + (0.4 * support_strength),
                ),
                qc_score=experiment_confidence_report.summary.overall_score,
                annotation_score=1.0
                if entry.pathway_name and entry.source_name
                else (0.75 if entry.pathway_name else 0.4),
                reproducibility_score=max(
                    0.4 * experiment_confidence_report.summary.overall_score,
                    reproducibility,
                ),
                confidence_score=support_strength,
                penalties=penalties,
                uncertainty=0.1 if support_strength == 0.0 else 0.05,
                source_ids=(entry.pathway_id,),
                note=(
                    "pathway ranking combines enrichment strength with supporting protein "
                    "confidence so one-member pathways do not outrank broader supported biology"
                ),
            )
        )
    return tuple(candidates)

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
from bijux_proteomics.workflow.reports.biological_report_pathway_member_metrics import (
    _build_biological_pathway_abundance,
    _build_biological_pathway_member_metrics,
    _build_biological_pathway_ranking_penalties,
    _build_biological_pathway_reproducibility,
    _build_biological_pathway_support_strength,
)


def _build_biological_pathway_ranking_candidates(
    pathway_enrichment_report: PathwayEnrichmentReport | None,
    *,
    protein_mechanism_cards: ProteinMechanismCardReport,
    experiment_confidence_report: ExperimentConfidenceReport,
) -> tuple[EvidenceAwareRankingCandidate, ...]:
    if pathway_enrichment_report is None:
        return ()
    member_metrics = _build_biological_pathway_member_metrics(protein_mechanism_cards)

    pathway_abundance = {
        entry.pathway_id: _build_biological_pathway_abundance(entry, member_metrics)
        for entry in pathway_enrichment_report.entries
    }
    abundance_scores = normalize_linear_range(pathway_abundance)

    candidates: list[EvidenceAwareRankingCandidate] = []
    for entry in pathway_enrichment_report.entries:
        support_strength = _build_biological_pathway_support_strength(
            entry,
            member_metrics,
        )
        reproducibility = _build_biological_pathway_reproducibility(
            entry,
            member_metrics,
        )
        penalties = _build_biological_pathway_ranking_penalties(
            entry,
            support_strength=support_strength,
        )
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

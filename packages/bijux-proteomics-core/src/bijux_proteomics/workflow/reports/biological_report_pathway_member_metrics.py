# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Pathway member-derived metrics for biological ranking candidates."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from bijux_proteomics.review.belief.evidence_aware_ranking import score_support_count
from bijux_proteomics.workflow.reports.biological_report_ranking_support import (
    _mean,
    _tier_score,
)

if TYPE_CHECKING:
    from bijux_proteomics.interpretation.pathway_enrichment import (
        PathwayEnrichmentEntry,
    )
    from bijux_proteomics.workflow.cards.protein_mechanism_cards import (
        ProteinMechanismCardReport,
    )


@dataclass(frozen=True)
class BiologicalPathwayMemberMetrics:
    """Member-level evidence views reused across pathway ranking candidates."""

    support_by_member_id: dict[str, list[float]]
    abundance_by_member_id: dict[str, list[float]]
    reproducibility_by_member_id: dict[str, list[float]]


def _build_biological_pathway_member_metrics(
    protein_mechanism_cards: ProteinMechanismCardReport,
) -> BiologicalPathwayMemberMetrics:
    support_by_member_id: dict[str, list[float]] = {}
    abundance_by_member_id: dict[str, list[float]] = {}
    reproducibility_by_member_id: dict[str, list[float]] = {}
    for card in protein_mechanism_cards.cards:
        support_strength = _tier_score(card.confidence_tier.value)
        abundance = abs(card.abundance_change.log2_fold_change)
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
        member_ids = [card.protein_group_id, card.representative_protein_ref]
        if card.gene_symbol:
            member_ids.append(card.gene_symbol)
        for member_id in member_ids:
            support_by_member_id.setdefault(member_id, []).append(support_strength)
            abundance_by_member_id.setdefault(member_id, []).append(abundance)
            reproducibility_by_member_id.setdefault(member_id, []).append(
                reproducibility
            )
    return BiologicalPathwayMemberMetrics(
        support_by_member_id=support_by_member_id,
        abundance_by_member_id=abundance_by_member_id,
        reproducibility_by_member_id=reproducibility_by_member_id,
    )


def _build_biological_pathway_abundance(
    entry: PathwayEnrichmentEntry,
    member_metrics: BiologicalPathwayMemberMetrics,
) -> float:
    return _mean(
        member_metrics.abundance_by_member_id.get(member_id, ())
        for member_id in entry.foreground_member_ids
    )


def _build_biological_pathway_support_strength(
    entry: PathwayEnrichmentEntry,
    member_metrics: BiologicalPathwayMemberMetrics,
) -> float:
    return _mean(
        member_metrics.support_by_member_id.get(member_id, ())
        for member_id in entry.foreground_member_ids
    )


def _build_biological_pathway_reproducibility(
    entry: PathwayEnrichmentEntry,
    member_metrics: BiologicalPathwayMemberMetrics,
) -> float:
    return _mean(
        member_metrics.reproducibility_by_member_id.get(member_id, ())
        for member_id in entry.foreground_member_ids
    )


def _build_biological_pathway_ranking_penalties(
    entry: PathwayEnrichmentEntry,
    *,
    support_strength: float,
) -> dict[str, float]:
    penalties: dict[str, float] = {}
    if entry.foreground_overlap_count <= 1:
        penalties["weak_member_support"] = 0.14
    if support_strength == 0.0:
        penalties["unresolved_supporting_members"] = 0.1
    if support_strength < 0.5:
        penalties["weak_supporting_proteins"] = 0.08
    return penalties


__all__ = [
    "BiologicalPathwayMemberMetrics",
    "_build_biological_pathway_abundance",
    "_build_biological_pathway_member_metrics",
    "_build_biological_pathway_ranking_penalties",
    "_build_biological_pathway_reproducibility",
    "_build_biological_pathway_support_strength",
]

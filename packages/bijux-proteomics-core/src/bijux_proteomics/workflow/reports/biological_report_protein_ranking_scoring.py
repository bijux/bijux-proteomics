# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Protein ranking score components for biological report candidates."""

from __future__ import annotations

from typing import TYPE_CHECKING

from bijux_proteomics.review.belief.evidence_aware_ranking import score_support_count
from bijux_proteomics.workflow.reports.biological_report_ranking_support import (
    _tier_score,
)

if TYPE_CHECKING:
    from bijux_proteomics.quantification.contracts.differential import (
        DifferentialAbundanceEntry,
    )
    from bijux_proteomics.workflow.cards.protein_evidence.models import (
        ProteinEvidenceCard,
    )
    from bijux_proteomics.workflow.cards.protein_mechanism_cards import (
        ProteinMechanismCard,
    )


def _build_protein_support_score(mechanism_card: ProteinMechanismCard) -> float:
    return min(
        1.0,
        (
            0.7
            * score_support_count(
                mechanism_card.peptide_support.unique_peptide_count,
                saturation=4,
            )
        )
        + (
            0.3
            * score_support_count(
                mechanism_card.peptide_support.quantifying_peptide_count,
                saturation=6,
            )
        ),
    )


def _build_protein_annotation_score(protein_card: ProteinEvidenceCard) -> float:
    return min(
        1.0,
        (0.45 if protein_card.annotation.annotation_status.value != "unmapped" else 0.0)
        + (0.15 if protein_card.functional_regions else 0.0)
        + (0.15 if protein_card.pathways else 0.0)
        + (0.15 if protein_card.ptm_sites else 0.0)
        + (0.10 if protein_card.context_terms else 0.0),
    )


def _build_protein_confidence_score(mechanism_card: ProteinMechanismCard) -> float:
    return min(
        1.0,
        (
            0.45 * _tier_score(mechanism_card.confidence_tier.value)
            + 0.35 * _tier_score(mechanism_card.evidence_tier.value)
            + max(0.0, 0.2 - (0.04 * len(mechanism_card.downgrade_reasons)))
        ),
    )


def _build_protein_reproducibility_score(
    differential_entry: DifferentialAbundanceEntry,
) -> float:
    if differential_entry.robustness_score is not None:
        return differential_entry.robustness_score
    return min(
        1.0,
        (
            0.5
            * score_support_count(
                min(
                    differential_entry.observations_a,
                    differential_entry.observations_b,
                ),
                saturation=3,
            )
        )
        + (
            0.5
            * score_support_count(
                differential_entry.complete_pair_count,
                saturation=3,
            )
        ),
    )


def _build_protein_ranking_penalties(
    *,
    protein_card: ProteinEvidenceCard,
    differential_entry: DifferentialAbundanceEntry,
    abundance_score: float,
    unique_support: int,
) -> dict[str, float]:
    penalties: dict[str, float] = {}
    if unique_support <= 1:
        penalties["single_peptide_support"] = 0.18
    if abundance_score < 0.25:
        penalties["low_abundance_signal"] = 0.12
    if protein_card.warnings:
        penalties["warning_burden"] = min(0.15, 0.03 * len(protein_card.warnings))
    if not protein_card.significant:
        penalties["not_significant"] = 0.1
    if differential_entry.imputation_dependent_hit:
        penalties["imputation_dependent_hit"] = 0.08
    if (
        differential_entry.robustness_score is not None
        and differential_entry.robustness_score < 0.5
    ):
        penalties["limited_robustness"] = 0.08
    return penalties


__all__ = [
    "_build_protein_annotation_score",
    "_build_protein_confidence_score",
    "_build_protein_ranking_penalties",
    "_build_protein_reproducibility_score",
    "_build_protein_support_score",
]

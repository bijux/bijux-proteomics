# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Biological ranking candidate orchestration."""

from __future__ import annotations

from bijux_proteomics.interpretation import PathwayEnrichmentReport
from bijux_proteomics.quantification.contracts import DifferentialAbundanceReport
from bijux_proteomics.review.belief.evidence_aware_ranking import (
    EvidenceAwareRankingCandidate,
)
from bijux_proteomics.study import ExperimentConfidenceReport
from bijux_proteomics.workflow.cards.protein_evidence_cards import (
    ProteinEvidenceCardReport,
)
from bijux_proteomics.workflow.cards.protein_mechanism_cards import (
    ProteinMechanismCardReport,
)
from bijux_proteomics.workflow.reports.biological_report_pathway_ranking import (
    _build_biological_pathway_ranking_candidates as _build_pathway_candidates,
)
from bijux_proteomics.workflow.reports.biological_report_protein_ranking import (
    _build_biological_protein_ranking_candidates as _build_protein_candidates,
)


def _build_biological_protein_ranking_candidates(
    differential_report: DifferentialAbundanceReport,
    *,
    protein_cards: ProteinEvidenceCardReport,
    protein_mechanism_cards: ProteinMechanismCardReport,
    experiment_confidence_report: ExperimentConfidenceReport,
) -> tuple[EvidenceAwareRankingCandidate, ...]:
    return _build_protein_candidates(
        differential_report,
        protein_cards=protein_cards,
        protein_mechanism_cards=protein_mechanism_cards,
        experiment_confidence_report=experiment_confidence_report,
    )


def _build_biological_pathway_ranking_candidates(
    pathway_enrichment_report: PathwayEnrichmentReport | None,
    *,
    protein_mechanism_cards: ProteinMechanismCardReport,
    experiment_confidence_report: ExperimentConfidenceReport,
) -> tuple[EvidenceAwareRankingCandidate, ...]:
    return _build_pathway_candidates(
        pathway_enrichment_report,
        protein_mechanism_cards=protein_mechanism_cards,
        experiment_confidence_report=experiment_confidence_report,
    )

__all__ = [
    "_build_biological_pathway_ranking_candidates",
    "_build_biological_protein_ranking_candidates",
]

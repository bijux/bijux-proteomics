# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi
"""Evidence-aware ranking report assembly for biological report workflows."""

from __future__ import annotations

from bijux_proteomics.interpretation import PathwayEnrichmentReport
from bijux_proteomics.quantification.contracts import (
    DifferentialAbundanceReport,
)
from bijux_proteomics.review.belief.evidence_aware_ranking import (
    EvidenceAwareRankingReport,
    build_evidence_aware_ranking_report,
)
from bijux_proteomics.study import (
    ExperimentConfidenceReport,
)
from bijux_proteomics.workflow.cards.protein_evidence_cards import ProteinEvidenceCardReport
from bijux_proteomics.workflow.cards.protein_mechanism_cards import (
    ProteinMechanismCardReport,
)
from bijux_proteomics.workflow.reports.biological_report_ranking import (
    _build_biological_pathway_ranking_candidates,
    _build_biological_protein_ranking_candidates,
)


def _build_biological_evidence_aware_ranking_report(
    differential_report: DifferentialAbundanceReport,
    *,
    protein_cards: ProteinEvidenceCardReport,
    protein_mechanism_cards: ProteinMechanismCardReport,
    experiment_confidence_report: ExperimentConfidenceReport,
    pathway_enrichment_report: PathwayEnrichmentReport | None,
) -> EvidenceAwareRankingReport:
    protein_candidates = _build_biological_protein_ranking_candidates(
        differential_report,
        protein_cards=protein_cards,
        protein_mechanism_cards=protein_mechanism_cards,
        experiment_confidence_report=experiment_confidence_report,
    )
    pathway_candidates = _build_biological_pathway_ranking_candidates(
        pathway_enrichment_report,
        protein_mechanism_cards=protein_mechanism_cards,
        experiment_confidence_report=experiment_confidence_report,
    )
    return build_evidence_aware_ranking_report(protein_candidates + pathway_candidates)


__all__ = ["_build_biological_evidence_aware_ranking_report"]

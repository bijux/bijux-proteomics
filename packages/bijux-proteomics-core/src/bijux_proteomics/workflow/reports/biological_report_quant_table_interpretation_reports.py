# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi
"""Interpretation-layer review assembly for biological quant-table workflows."""

from __future__ import annotations

from typing import NamedTuple

from bijux_proteomics.workflow.reports.biological_report_claims import (
    _build_biological_claim_validation_report,
    _build_biological_evidence_aware_ranking_report,
    _build_biological_hypothesis_report,
)
from bijux_proteomics.workflow.reports.biological_report_experiment_review import (
    BiologicalExperimentReviewReports,
)


class BiologicalQuantTableInterpretationReports(NamedTuple):
    """Interpretation reports layered over experiment review outputs."""

    evidence_aware_ranking_report: object | None
    claim_validation_report: object
    biological_hypothesis_report: object


def _build_biological_quant_table_interpretation_reports(
    *,
    differential_report: object,
    active_selection_policy: object,
    protein_cards: object,
    protein_mechanism_cards: object,
    pathway_activity_report: object | None,
    pathway_enrichment_report: object | None,
    regulator_inference_report: object | None,
    experiment_review_reports: BiologicalExperimentReviewReports,
) -> BiologicalQuantTableInterpretationReports:
    experiment_confidence_report = (
        experiment_review_reports.experiment_confidence_report
    )
    evidence_aware_ranking_report = _build_biological_evidence_aware_ranking_report(
        differential_report,
        protein_cards=protein_cards,
        protein_mechanism_cards=protein_mechanism_cards,
        experiment_confidence_report=experiment_confidence_report,
        pathway_enrichment_report=pathway_enrichment_report,
    )
    claim_validation_report = _build_biological_claim_validation_report(
        differential_report,
        protein_mechanism_cards=protein_mechanism_cards,
        pathway_activity_report=pathway_activity_report,
        regulator_inference_report=regulator_inference_report,
        selection_policy=active_selection_policy,
    )
    biological_hypothesis_report = _build_biological_hypothesis_report(
        claim_validation_report,
        protein_mechanism_cards=protein_mechanism_cards,
        pathway_activity_report=pathway_activity_report,
        regulator_inference_report=regulator_inference_report,
    )
    return BiologicalQuantTableInterpretationReports(
        evidence_aware_ranking_report=evidence_aware_ranking_report,
        claim_validation_report=claim_validation_report,
        biological_hypothesis_report=biological_hypothesis_report,
    )


__all__ = [
    "BiologicalQuantTableInterpretationReports",
    "_build_biological_quant_table_interpretation_reports",
]

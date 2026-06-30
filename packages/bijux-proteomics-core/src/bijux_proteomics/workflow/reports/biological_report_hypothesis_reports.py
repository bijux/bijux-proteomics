# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi
"""Hypothesis report assembly for biological report workflows."""

from __future__ import annotations

from bijux_proteomics.interpretation import (
    PathwayActivityReport,
    RegulatorInferenceReport,
)
from bijux_proteomics.review.claims.biological_claim_validation import (
    BiologicalClaimValidationReport,
)
from bijux_proteomics.review.claims.biological_hypotheses import (
    BiologicalHypothesisReport,
    build_biological_hypothesis_report,
)
from bijux_proteomics.workflow.cards.protein_mechanism_cards import (
    ProteinMechanismCardReport,
)
from bijux_proteomics.workflow.reports.biological_report_pathway_hypothesis_candidates import (
    _build_biological_pathway_hypothesis_candidates,
)
from bijux_proteomics.workflow.reports.biological_report_protein_hypothesis_candidates import (
    _build_biological_protein_hypothesis_candidates,
)
from bijux_proteomics.workflow.reports.biological_report_regulator_hypothesis_candidates import (
    _build_biological_regulator_hypothesis_candidates,
)


def _build_biological_hypothesis_report(
    claim_validation_report: BiologicalClaimValidationReport,
    *,
    protein_mechanism_cards: ProteinMechanismCardReport,
    pathway_activity_report: PathwayActivityReport | None,
    regulator_inference_report: RegulatorInferenceReport | None,
) -> BiologicalHypothesisReport:
    candidates = (
        _build_biological_protein_hypothesis_candidates(
            claim_validation_report,
            protein_mechanism_cards=protein_mechanism_cards,
        )
        + _build_biological_pathway_hypothesis_candidates(
            claim_validation_report,
            protein_mechanism_cards=protein_mechanism_cards,
            pathway_activity_report=pathway_activity_report,
        )
        + _build_biological_regulator_hypothesis_candidates(
            claim_validation_report,
            protein_mechanism_cards=protein_mechanism_cards,
            regulator_inference_report=regulator_inference_report,
        )
    )
    return build_biological_hypothesis_report(candidates)


__all__ = ["_build_biological_hypothesis_report"]

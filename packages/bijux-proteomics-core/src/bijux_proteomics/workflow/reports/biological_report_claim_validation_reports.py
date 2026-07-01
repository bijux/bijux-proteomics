# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi
"""Claim-validation report assembly for biological report workflows."""

from __future__ import annotations

from bijux_proteomics.interpretation import (
    PathwayActivityReport,
    RegulatorInferenceReport,
)
from bijux_proteomics.quantification.contracts import (
    DifferentialAbundanceReport,
)
from bijux_proteomics.review.claims.biological_claim_validation import (
    BiologicalClaimValidationPolicy,
    BiologicalClaimValidationReport,
    build_biological_claim_validation_report,
)
from bijux_proteomics.workflow.cards.protein_mechanism_cards import (
    ProteinMechanismCardReport,
)
from bijux_proteomics.workflow.reports.biological_report_pathway_claim_candidates import (
    _build_biological_pathway_claim_candidates,
)
from bijux_proteomics.workflow.reports.biological_report_protein_claim_candidates import (
    _build_biological_protein_claim_candidates,
)
from bijux_proteomics.workflow.reports.biological_report_regulator_claim_candidates import (
    _build_biological_regulator_claim_candidates,
)
from bijux_proteomics.workflow.reports.biological_report_selection_policy import (
    BiologicalResultSelectionPolicy,
)


def _build_biological_claim_validation_report(
    differential_report: DifferentialAbundanceReport,
    *,
    protein_mechanism_cards: ProteinMechanismCardReport,
    pathway_activity_report: PathwayActivityReport | None,
    regulator_inference_report: RegulatorInferenceReport | None,
    selection_policy: BiologicalResultSelectionPolicy,
) -> BiologicalClaimValidationReport:
    candidates = (
        _build_biological_protein_claim_candidates(
            differential_report,
            protein_mechanism_cards=protein_mechanism_cards,
        )
        + _build_biological_pathway_claim_candidates(pathway_activity_report)
        + _build_biological_regulator_claim_candidates(regulator_inference_report)
    )
    return build_biological_claim_validation_report(
        candidates,
        policy=BiologicalClaimValidationPolicy(
            max_adjusted_p_value=selection_policy.max_adjusted_p_value,
            min_robustness_score=0.55,
            min_pathway_activity_delta=0.2,
            min_regulator_score=0.55,
        ),
    )


__all__ = ["_build_biological_claim_validation_report"]

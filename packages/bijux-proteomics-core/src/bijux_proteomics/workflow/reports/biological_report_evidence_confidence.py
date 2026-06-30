# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Evidence-derived confidence rules for biological report sections."""

from __future__ import annotations

from bijux_proteomics.interpretation import (
    BiologicalForegroundBackgroundModel,
    RegulatorInferenceReport,
)
from bijux_proteomics.study import ExperimentConfidenceReport
from bijux_proteomics.workflow.cards.protein_mechanism_cards import (
    ProteinMechanismCardReport,
)
from bijux_proteomics.workflow.reports.biological_report_evidence_finding_confidence import (
    _build_claim_validation_entry,
    _build_evidence_ranking_entry,
    _build_hypothesis_entry,
)
from bijux_proteomics.workflow.reports.biological_report_experiment_confidence import (
    _build_experiment_confidence_entry,
)
from bijux_proteomics.workflow.reports.biological_report_mechanistic_confidence import (
    _build_foreground_background_entry,
    _build_protein_mechanism_entry,
    _build_regulator_inference_entry,
)
from bijux_proteomics.workflow.reports.biological_report_section_metadata import (
    BiologicalReportSectionConfidenceEntry,
)
from bijux_proteomics.review.belief.evidence_aware_ranking import (
    EvidenceAwareRankingReport,
)
from bijux_proteomics.review.claims.biological_claim_validation import (
    BiologicalClaimValidationReport,
)
from bijux_proteomics.review.claims.biological_hypotheses import (
    BiologicalHypothesisReport,
)


def _build_evidence_section_confidence_entries(
    *,
    experiment_confidence_report: ExperimentConfidenceReport,
    evidence_aware_ranking_report: EvidenceAwareRankingReport | None,
    claim_validation_report: BiologicalClaimValidationReport | None,
    biological_hypothesis_report: BiologicalHypothesisReport | None,
    foreground_background_model: BiologicalForegroundBackgroundModel,
    regulator_inference_report: RegulatorInferenceReport | None,
    protein_mechanism_cards: ProteinMechanismCardReport,
) -> tuple[BiologicalReportSectionConfidenceEntry, ...]:
    """Build confidence entries for evidence-anchored report sections."""

    return (
        _build_experiment_confidence_entry(experiment_confidence_report),
        _build_evidence_ranking_entry(evidence_aware_ranking_report),
        _build_claim_validation_entry(claim_validation_report),
        _build_hypothesis_entry(biological_hypothesis_report),
        _build_foreground_background_entry(foreground_background_model),
        _build_regulator_inference_entry(regulator_inference_report),
        _build_protein_mechanism_entry(protein_mechanism_cards),
    )

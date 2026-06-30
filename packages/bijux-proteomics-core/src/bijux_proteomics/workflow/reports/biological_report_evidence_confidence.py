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
from bijux_proteomics.workflow.reports.biological_report_models import (
    BiologicalReportSectionConfidenceEntry,
    BiologicalReportSectionConfidenceLabel,
    BiologicalReportSectionKey,
)
from bijux_proteomics.workflow.reports.biological_report_section_confidence_entry_building import (
    _build_biological_report_section_confidence_entry,
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


def _build_foreground_background_entry(
    model: BiologicalForegroundBackgroundModel,
) -> BiologicalReportSectionConfidenceEntry:
    if not model.summary.valid_for_enrichment:
        return _build_biological_report_section_confidence_entry(
            BiologicalReportSectionKey.ENRICHMENT_FOREGROUND_BACKGROUND,
            BiologicalReportSectionConfidenceLabel.INVALID,
            "foreground/background construction failed the enrichment validity checks",
        )
    issue_count = model.summary.issue_count
    if issue_count == 0:
        label = BiologicalReportSectionConfidenceLabel.HIGH
    elif issue_count == 1:
        label = BiologicalReportSectionConfidenceLabel.MODERATE
    else:
        label = BiologicalReportSectionConfidenceLabel.WEAK
    return _build_biological_report_section_confidence_entry(
        BiologicalReportSectionKey.ENRICHMENT_FOREGROUND_BACKGROUND,
        label,
        (
            "foreground/background confidence derives from enrichment validity and "
            f"{issue_count} modeled issue(s)"
        ),
    )


def _build_regulator_inference_entry(
    report: RegulatorInferenceReport | None,
) -> BiologicalReportSectionConfidenceEntry:
    if report is None or report.summary.entry_count == 0:
        return _build_biological_report_section_confidence_entry(
            BiologicalReportSectionKey.REGULATOR_INFERENCE,
            BiologicalReportSectionConfidenceLabel.INVALID,
            "no regulator entries were supported by the supplied evidence tables",
        )
    high_scoring = report.summary.high_scoring_entry_count
    unresolved_targets = report.summary.unresolved_target_count
    if high_scoring > 0 and unresolved_targets == 0:
        label = BiologicalReportSectionConfidenceLabel.HIGH
    elif high_scoring > 0:
        label = BiologicalReportSectionConfidenceLabel.MODERATE
    else:
        label = BiologicalReportSectionConfidenceLabel.WEAK
    return _build_biological_report_section_confidence_entry(
        BiologicalReportSectionKey.REGULATOR_INFERENCE,
        label,
        (
            "regulator confidence derives from high-scoring inferred regulators and "
            f"{unresolved_targets} unresolved target set(s)"
        ),
    )


def _build_protein_mechanism_entry(
    report: ProteinMechanismCardReport,
) -> BiologicalReportSectionConfidenceEntry:
    if report.summary.card_count == 0:
        return _build_biological_report_section_confidence_entry(
            BiologicalReportSectionKey.PROTEIN_MECHANISM_CARDS,
            BiologicalReportSectionConfidenceLabel.INVALID,
            "no protein mechanism cards were generated",
        )
    high_card_count = sum(
        1 for card in report.cards if card.confidence_tier.value == "high"
    )
    moderate_card_count = sum(
        1 for card in report.cards if card.confidence_tier.value == "moderate"
    )
    if (
        high_card_count == report.summary.card_count
        and report.summary.weak_evidence_card_count == 0
    ):
        label = BiologicalReportSectionConfidenceLabel.HIGH
    elif high_card_count + moderate_card_count > 0:
        label = BiologicalReportSectionConfidenceLabel.MODERATE
    else:
        label = BiologicalReportSectionConfidenceLabel.WEAK
    return _build_biological_report_section_confidence_entry(
        BiologicalReportSectionKey.PROTEIN_MECHANISM_CARDS,
        label,
        (
            "protein mechanism card confidence derives from per-card propagated confidence tiers and "
            f"{report.summary.weak_evidence_card_count} weak-evidence card(s)"
        ),
    )

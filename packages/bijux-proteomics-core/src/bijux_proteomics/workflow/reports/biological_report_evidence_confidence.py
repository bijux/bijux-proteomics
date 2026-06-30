# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Evidence-derived confidence rules for biological report sections."""

from __future__ import annotations

from bijux_proteomics.domain.confidence import ConfidenceTier
from bijux_proteomics.interpretation import (
    BiologicalForegroundBackgroundModel,
    RegulatorInferenceReport,
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
from bijux_proteomics.study import ExperimentConfidenceReport
from bijux_proteomics.workflow.cards.protein_mechanism_cards import (
    ProteinMechanismCardReport,
)
from bijux_proteomics.workflow.reports.biological_report_models import (
    _BIOLOGICAL_REPORT_SECTION_TITLES,
    BiologicalReportSectionConfidenceEntry,
    BiologicalReportSectionConfidenceLabel,
    BiologicalReportSectionKey,
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


def _build_experiment_confidence_entry(
    report: ExperimentConfidenceReport,
) -> BiologicalReportSectionConfidenceEntry:
    summary = report.summary
    if summary.overall_tier is ConfidenceTier.HIGH:
        if summary.low_confidence_component_count == 0:
            return _build_section_confidence_entry(
                BiologicalReportSectionKey.EXPERIMENT_CONFIDENCE,
                BiologicalReportSectionConfidenceLabel.HIGH,
                "overall experimental confidence is high and no components were downgraded",
            )
        return _build_section_confidence_entry(
            BiologicalReportSectionKey.EXPERIMENT_CONFIDENCE,
            BiologicalReportSectionConfidenceLabel.MODERATE,
            "overall experimental confidence is high but at least one component remained low-confidence",
        )
    if summary.overall_tier is ConfidenceTier.MODERATE:
        return _build_section_confidence_entry(
            BiologicalReportSectionKey.EXPERIMENT_CONFIDENCE,
            BiologicalReportSectionConfidenceLabel.MODERATE,
            "overall experimental confidence is moderate after aggregating metadata, missingness, power, and QC checks",
        )
    return _build_section_confidence_entry(
        BiologicalReportSectionKey.EXPERIMENT_CONFIDENCE,
        BiologicalReportSectionConfidenceLabel.WEAK,
        "overall experimental confidence is low because multiple design or QC components were downgraded",
    )


def _build_evidence_ranking_entry(
    report: EvidenceAwareRankingReport | None,
) -> BiologicalReportSectionConfidenceEntry:
    if report is None or not report.entries:
        return _build_section_confidence_entry(
            BiologicalReportSectionKey.EVIDENCE_AWARE_RANKING,
            BiologicalReportSectionConfidenceLabel.INVALID,
            "no evidence-aware ranking entries were produced",
        )
    top_score = report.entries[0].decomposition.final_score
    if top_score >= 0.8:
        label = BiologicalReportSectionConfidenceLabel.HIGH
    elif top_score >= 0.55:
        label = BiologicalReportSectionConfidenceLabel.MODERATE
    else:
        label = BiologicalReportSectionConfidenceLabel.WEAK
    return _build_section_confidence_entry(
        BiologicalReportSectionKey.EVIDENCE_AWARE_RANKING,
        label,
        f"ranking confidence derives from the top evidence-aware final score ({top_score:.3f}) across governed findings",
    )


def _build_claim_validation_entry(
    report: BiologicalClaimValidationReport | None,
) -> BiologicalReportSectionConfidenceEntry:
    if report is None or report.summary.candidate_count == 0:
        return _build_section_confidence_entry(
            BiologicalReportSectionKey.VALIDATED_BIOLOGICAL_CLAIMS,
            BiologicalReportSectionConfidenceLabel.INVALID,
            "no biological claim candidates were available for validation",
        )
    supported_count = report.summary.supported_claim_count
    candidate_count = report.summary.candidate_count
    support_fraction = supported_count / candidate_count
    if supported_count == 0:
        label = BiologicalReportSectionConfidenceLabel.INVALID
        rationale = (
            "all candidate biological claims were rejected by directional or evidence checks"
        )
    elif support_fraction >= 0.75 and report.summary.rejected_claim_count == 0:
        label = BiologicalReportSectionConfidenceLabel.HIGH
        rationale = "most candidate biological claims remained supported and none were rejected"
    elif support_fraction >= 0.4:
        label = BiologicalReportSectionConfidenceLabel.MODERATE
        rationale = (
            "supported biological claims remain after validation, but a material fraction were rejected"
        )
    else:
        label = BiologicalReportSectionConfidenceLabel.WEAK
        rationale = "validated biological claims are sparse relative to the candidate claim set"
    return _build_section_confidence_entry(
        BiologicalReportSectionKey.VALIDATED_BIOLOGICAL_CLAIMS,
        label,
        rationale,
    )


def _build_hypothesis_entry(
    report: BiologicalHypothesisReport | None,
) -> BiologicalReportSectionConfidenceEntry:
    if (
        report is None
        or report.summary.candidate_count == 0
        or report.summary.hypothesis_count == 0
    ):
        return _build_section_confidence_entry(
            BiologicalReportSectionKey.BIOLOGICAL_HYPOTHESES,
            BiologicalReportSectionConfidenceLabel.INVALID,
            "no graph-backed biological hypotheses were produced",
        )
    return _build_section_confidence_entry(
        BiologicalReportSectionKey.BIOLOGICAL_HYPOTHESES,
        BiologicalReportSectionConfidenceLabel.EXPLORATORY,
        (
            "hypotheses are intentionally exploratory follow-up statements, "
            f"with {report.summary.high_confidence_hypothesis_count} high-confidence hypotheses retained"
        ),
    )


def _build_foreground_background_entry(
    model: BiologicalForegroundBackgroundModel,
) -> BiologicalReportSectionConfidenceEntry:
    if not model.summary.valid_for_enrichment:
        return _build_section_confidence_entry(
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
    return _build_section_confidence_entry(
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
        return _build_section_confidence_entry(
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
    return _build_section_confidence_entry(
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
        return _build_section_confidence_entry(
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
    return _build_section_confidence_entry(
        BiologicalReportSectionKey.PROTEIN_MECHANISM_CARDS,
        label,
        (
            "protein mechanism card confidence derives from per-card propagated confidence tiers and "
            f"{report.summary.weak_evidence_card_count} weak-evidence card(s)"
        ),
    )


def _build_section_confidence_entry(
    section_key: BiologicalReportSectionKey,
    confidence_label: BiologicalReportSectionConfidenceLabel,
    rationale: str,
) -> BiologicalReportSectionConfidenceEntry:
    return BiologicalReportSectionConfidenceEntry(
        section_key=section_key,
        section_title=_BIOLOGICAL_REPORT_SECTION_TITLES[section_key],
        confidence_label=confidence_label,
        rationale=rationale,
    )

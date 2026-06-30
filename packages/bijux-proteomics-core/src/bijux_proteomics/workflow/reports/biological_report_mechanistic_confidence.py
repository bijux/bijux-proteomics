# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Mechanistic-support section confidence for biological reports."""

from __future__ import annotations

from bijux_proteomics.interpretation import (
    BiologicalForegroundBackgroundModel,
    RegulatorInferenceReport,
)
from bijux_proteomics.workflow.cards.protein_mechanism_cards import (
    ProteinMechanismCardReport,
)
from bijux_proteomics.workflow.reports.biological_report_models import (
    BiologicalReportSectionConfidenceEntry,
    BiologicalReportSectionConfidenceLabel,
    BiologicalReportSectionKey,
)
from bijux_proteomics.workflow.reports.biological_report_section_confidence_entry_building import (
    _build_biological_report_section_confidence_entry,
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

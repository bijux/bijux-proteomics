# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Evidence-finding section confidence for biological reports."""

from __future__ import annotations

from bijux_proteomics.review.belief.evidence_aware_ranking import (
    EvidenceAwareRankingReport,
)
from bijux_proteomics.review.claims.biological_claim_validation import (
    BiologicalClaimValidationReport,
)
from bijux_proteomics.review.claims.biological_hypotheses import (
    BiologicalHypothesisReport,
)
from bijux_proteomics.workflow.reports.biological_report_section_metadata import (
    BiologicalReportSectionConfidenceEntry,
    BiologicalReportSectionConfidenceLabel,
    BiologicalReportSectionKey,
)
from bijux_proteomics.workflow.reports.biological_report_section_confidence_entry_building import (
    _build_biological_report_section_confidence_entry,
)


def _build_evidence_ranking_entry(
    report: EvidenceAwareRankingReport | None,
) -> BiologicalReportSectionConfidenceEntry:
    if report is None or not report.entries:
        return _build_biological_report_section_confidence_entry(
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
    return _build_biological_report_section_confidence_entry(
        BiologicalReportSectionKey.EVIDENCE_AWARE_RANKING,
        label,
        f"ranking confidence derives from the top evidence-aware final score ({top_score:.3f}) across governed findings",
    )


def _build_claim_validation_entry(
    report: BiologicalClaimValidationReport | None,
) -> BiologicalReportSectionConfidenceEntry:
    if report is None or report.summary.candidate_count == 0:
        return _build_biological_report_section_confidence_entry(
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
    return _build_biological_report_section_confidence_entry(
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
        return _build_biological_report_section_confidence_entry(
            BiologicalReportSectionKey.BIOLOGICAL_HYPOTHESES,
            BiologicalReportSectionConfidenceLabel.INVALID,
            "no graph-backed biological hypotheses were produced",
        )
    return _build_biological_report_section_confidence_entry(
        BiologicalReportSectionKey.BIOLOGICAL_HYPOTHESES,
        BiologicalReportSectionConfidenceLabel.EXPLORATORY,
        (
            "hypotheses are intentionally exploratory follow-up statements, "
            f"with {report.summary.high_confidence_hypothesis_count} high-confidence hypotheses retained"
        ),
    )

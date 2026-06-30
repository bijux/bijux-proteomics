# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Sample-context confidence rules for biological report sections."""

from __future__ import annotations

from bijux_proteomics.interpretation import TissueCellTypeContextReport
from bijux_proteomics.workflow.reports.biological_report_section_metadata import (
    BiologicalReportSectionConfidenceEntry,
    BiologicalReportSectionConfidenceLabel,
    BiologicalReportSectionKey,
)
from bijux_proteomics.workflow.reports.biological_report_section_confidence_entry_building import (
    _build_biological_report_section_confidence_entry,
)
from bijux_proteomics.workflow.studies.cohort_stratification import (
    CohortStratificationReport,
)


def _build_cohort_entry(
    report: CohortStratificationReport | None,
) -> BiologicalReportSectionConfidenceEntry:
    if report is None or report.summary.supported_stratum_count == 0:
        return _build_biological_report_section_confidence_entry(
            BiologicalReportSectionKey.COHORT_STRATIFICATION,
            BiologicalReportSectionConfidenceLabel.INVALID,
            "no supported subgroup strata passed the cohort stratification feasibility checks",
        )
    summary = report.summary
    if summary.subgroup_effect_count > 0 or summary.interaction_candidate_count > 0:
        label = BiologicalReportSectionConfidenceLabel.EXPLORATORY
    else:
        label = BiologicalReportSectionConfidenceLabel.WEAK
    return _build_biological_report_section_confidence_entry(
        BiologicalReportSectionKey.COHORT_STRATIFICATION,
        label,
        (
            "cohort stratification confidence derives from supported subgroup strata and "
            f"{summary.interaction_candidate_count} interaction candidate(s)"
        ),
    )


def _build_tissue_context_entry(
    report: TissueCellTypeContextReport | None,
) -> BiologicalReportSectionConfidenceEntry:
    if report is None or report.summary.sample_with_marker_definition_count == 0:
        return _build_biological_report_section_confidence_entry(
            BiologicalReportSectionKey.TISSUE_CELL_TYPE_CONTEXT,
            BiologicalReportSectionConfidenceLabel.INVALID,
            "no samples carried marker definitions for tissue or cell-type validation",
        )
    summary = report.summary
    if summary.mismatch_warning_count > 0:
        label = BiologicalReportSectionConfidenceLabel.WEAK
    elif summary.insufficient_marker_support_count > 0:
        label = BiologicalReportSectionConfidenceLabel.MODERATE
    else:
        label = BiologicalReportSectionConfidenceLabel.HIGH
    return _build_biological_report_section_confidence_entry(
        BiologicalReportSectionKey.TISSUE_CELL_TYPE_CONTEXT,
        label,
        (
            "tissue and cell-type context confidence derives from sample marker agreement, "
            f"{summary.mismatch_warning_count} mismatch warning(s), and "
            f"{summary.insufficient_marker_support_count} insufficient-support sample(s)"
        ),
    )


__all__ = [
    "_build_cohort_entry",
    "_build_tissue_context_entry",
]

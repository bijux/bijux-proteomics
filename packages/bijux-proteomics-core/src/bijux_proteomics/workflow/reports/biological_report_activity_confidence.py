# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Activity-derived confidence rules for biological report sections."""

from __future__ import annotations

from bijux_proteomics.interpretation import (
    ComplexActivityReport,
    PathwayActivityReport,
)
from bijux_proteomics.workflow.reports.biological_report_section_metadata import (
    BiologicalReportSectionConfidenceEntry,
    BiologicalReportSectionConfidenceLabel,
    BiologicalReportSectionKey,
)
from bijux_proteomics.workflow.reports.biological_report_section_confidence_entry_building import (
    _build_biological_report_section_confidence_entry,
)


def _build_activity_section_confidence_entries(
    *,
    pathway_activity_report: PathwayActivityReport | None,
    complex_activity_report: ComplexActivityReport | None,
) -> tuple[BiologicalReportSectionConfidenceEntry, ...]:
    """Build confidence entries for activity-scored report sections."""

    return (
        _build_pathway_activity_entry(pathway_activity_report),
        _build_complex_activity_entry(complex_activity_report),
    )


def _build_pathway_activity_entry(
    report: PathwayActivityReport | None,
) -> BiologicalReportSectionConfidenceEntry:
    if report is None or report.summary.pathway_count == 0:
        return _build_biological_report_section_confidence_entry(
            BiologicalReportSectionKey.PATHWAY_ACTIVITY,
            BiologicalReportSectionConfidenceLabel.INVALID,
            "no pathways were evaluable for activity scoring",
        )
    summary = report.summary
    if (
        summary.condition_comparison_count > 0
        and summary.low_confidence_sample_score_count == 0
        and summary.unresolved_member_count == 0
    ):
        label = BiologicalReportSectionConfidenceLabel.HIGH
    elif summary.condition_comparison_count > 0:
        label = BiologicalReportSectionConfidenceLabel.MODERATE
    else:
        label = BiologicalReportSectionConfidenceLabel.WEAK
    return _build_biological_report_section_confidence_entry(
        BiologicalReportSectionKey.PATHWAY_ACTIVITY,
        label,
        (
            "pathway activity confidence derives from pathway comparisons, "
            f"{summary.low_confidence_sample_score_count} low-confidence sample score(s), "
            f"and {summary.unresolved_member_count} unresolved member(s)"
        ),
    )


def _build_complex_activity_entry(
    report: ComplexActivityReport | None,
) -> BiologicalReportSectionConfidenceEntry:
    if report is None or report.summary.complex_count == 0:
        return _build_biological_report_section_confidence_entry(
            BiologicalReportSectionKey.COMPLEX_ACTIVITY,
            BiologicalReportSectionConfidenceLabel.INVALID,
            "no complexes were evaluable for activity scoring",
        )
    summary = report.summary
    if (
        summary.condition_comparison_count > 0
        and summary.low_confidence_sample_score_count == 0
        and summary.unresolved_member_count == 0
    ):
        label = BiologicalReportSectionConfidenceLabel.HIGH
    elif summary.condition_comparison_count > 0:
        label = BiologicalReportSectionConfidenceLabel.MODERATE
    else:
        label = BiologicalReportSectionConfidenceLabel.WEAK
    return _build_biological_report_section_confidence_entry(
        BiologicalReportSectionKey.COMPLEX_ACTIVITY,
        label,
        (
            "complex activity confidence derives from complex comparisons, "
            f"{summary.low_confidence_sample_score_count} low-confidence sample score(s), "
            f"and {summary.unresolved_member_count} unresolved member(s)"
        ),
    )

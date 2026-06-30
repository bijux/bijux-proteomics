# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Compartment-biology confidence rules for biological report sections."""

from __future__ import annotations

from bijux_proteomics.interpretation.compartment_biology import (
    CompartmentBiologyReport,
)
from bijux_proteomics.workflow.reports.biological_report_models import (
    BiologicalReportSectionConfidenceEntry,
    BiologicalReportSectionConfidenceLabel,
    BiologicalReportSectionKey,
)
from bijux_proteomics.workflow.reports.biological_report_section_confidence_entry_building import (
    _build_biological_report_section_confidence_entry,
)


def _build_compartment_entry(
    report: CompartmentBiologyReport | None,
) -> BiologicalReportSectionConfidenceEntry:
    if report is None or report.summary.compartment_count == 0:
        return _build_biological_report_section_confidence_entry(
            BiologicalReportSectionKey.COMPARTMENT_BIOLOGY,
            BiologicalReportSectionConfidenceLabel.INVALID,
            "no compartments were evaluable from the supplied localization context",
        )
    summary = report.summary
    if (
        summary.condition_comparison_count > 0
        and summary.low_confidence_sample_score_count == 0
        and summary.unresolved_member_count == 0
        and summary.unknown_foreground_protein_count == 0
    ):
        label = BiologicalReportSectionConfidenceLabel.HIGH
    elif summary.condition_comparison_count > 0:
        label = BiologicalReportSectionConfidenceLabel.MODERATE
    else:
        label = BiologicalReportSectionConfidenceLabel.WEAK
    return _build_biological_report_section_confidence_entry(
        BiologicalReportSectionKey.COMPARTMENT_BIOLOGY,
        label,
        (
            "compartment confidence derives from condition comparisons, unresolved members, "
            "and unknown-localization counts"
        ),
    )


__all__ = ["_build_compartment_entry"]

# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Experiment-confidence section entry building for biological reports."""

from __future__ import annotations

from bijux_proteomics.domain.confidence import ConfidenceTier
from bijux_proteomics.study import ExperimentConfidenceReport
from bijux_proteomics.workflow.reports.biological_report_section_confidence_entry_building import (
    _build_biological_report_section_confidence_entry,
)
from bijux_proteomics.workflow.reports.biological_report_section_metadata import (
    BiologicalReportSectionConfidenceEntry,
    BiologicalReportSectionConfidenceLabel,
    BiologicalReportSectionKey,
)


def _build_experiment_confidence_entry(
    report: ExperimentConfidenceReport,
) -> BiologicalReportSectionConfidenceEntry:
    summary = report.summary
    if summary.overall_tier is ConfidenceTier.HIGH:
        if summary.low_confidence_component_count == 0:
            return _build_biological_report_section_confidence_entry(
                BiologicalReportSectionKey.EXPERIMENT_CONFIDENCE,
                BiologicalReportSectionConfidenceLabel.HIGH,
                "overall experimental confidence is high and no components were downgraded",
            )
        return _build_biological_report_section_confidence_entry(
            BiologicalReportSectionKey.EXPERIMENT_CONFIDENCE,
            BiologicalReportSectionConfidenceLabel.MODERATE,
            "overall experimental confidence is high but at least one component remained low-confidence",
        )
    if summary.overall_tier is ConfidenceTier.MODERATE:
        return _build_biological_report_section_confidence_entry(
            BiologicalReportSectionKey.EXPERIMENT_CONFIDENCE,
            BiologicalReportSectionConfidenceLabel.MODERATE,
            "overall experimental confidence is moderate after aggregating metadata, missingness, power, and QC checks",
        )
    return _build_biological_report_section_confidence_entry(
        BiologicalReportSectionKey.EXPERIMENT_CONFIDENCE,
        BiologicalReportSectionConfidenceLabel.WEAK,
        "overall experimental confidence is low because multiple design or QC components were downgraded",
    )

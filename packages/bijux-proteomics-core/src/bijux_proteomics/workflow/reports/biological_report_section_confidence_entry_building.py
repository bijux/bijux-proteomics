# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Shared builders for biological report section-confidence entries."""

from __future__ import annotations

from bijux_proteomics.workflow.reports.biological_report_models import (
    _BIOLOGICAL_REPORT_SECTION_TITLES,
    BiologicalReportSectionConfidenceEntry,
    BiologicalReportSectionConfidenceLabel,
    BiologicalReportSectionKey,
)


def _build_biological_report_section_confidence_entry(
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

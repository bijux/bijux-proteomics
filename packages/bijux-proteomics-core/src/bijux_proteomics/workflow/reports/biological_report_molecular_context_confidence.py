# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Molecular-context confidence rules for biological report sections."""

from __future__ import annotations

from bijux_proteomics.interpretation import (
    DiseasePhenotypeInterpretationReport,
    DrugTargetInterpretationReport,
)
from bijux_proteomics.workflow.reports.biological_report_section_metadata import (
    BiologicalReportSectionConfidenceEntry,
    BiologicalReportSectionConfidenceLabel,
    BiologicalReportSectionKey,
)
from bijux_proteomics.workflow.reports.biological_report_section_confidence_entry_building import (
    _build_biological_report_section_confidence_entry,
)


def _build_drug_target_entry(
    report: DrugTargetInterpretationReport | None,
) -> BiologicalReportSectionConfidenceEntry:
    if report is None or report.summary.entry_count == 0:
        return _build_biological_report_section_confidence_entry(
            BiologicalReportSectionKey.DRUG_TARGET_INTERPRETATION,
            BiologicalReportSectionConfidenceLabel.INVALID,
            "no drug-target relationships were supported by explicit target annotations",
        )
    summary = report.summary
    if summary.high_evidence_entry_count > 0 and summary.direct_target_entry_count > 0:
        label = BiologicalReportSectionConfidenceLabel.HIGH
    elif summary.high_evidence_entry_count + summary.moderate_evidence_entry_count > 0:
        label = BiologicalReportSectionConfidenceLabel.MODERATE
    else:
        label = BiologicalReportSectionConfidenceLabel.WEAK
    return _build_biological_report_section_confidence_entry(
        BiologicalReportSectionKey.DRUG_TARGET_INTERPRETATION,
        label,
        (
            "drug-target confidence derives from explicit target evidence tiers and "
            f"{summary.direct_target_entry_count} direct target entries"
        ),
    )


def _build_disease_phenotype_entry(
    report: DiseasePhenotypeInterpretationReport | None,
) -> BiologicalReportSectionConfidenceEntry:
    if report is None or report.summary.evaluated_term_count == 0:
        return _build_biological_report_section_confidence_entry(
            BiologicalReportSectionKey.DISEASE_PHENOTYPE_INTERPRETATION,
            BiologicalReportSectionConfidenceLabel.INVALID,
            "no disease or phenotype terms were evaluable from the supplied annotations",
        )
    summary = report.summary
    if (
        summary.high_confidence_term_count > 0
        and summary.unknown_foreground_protein_count == 0
    ):
        label = BiologicalReportSectionConfidenceLabel.HIGH
    elif summary.filter_passing_term_count > 0:
        label = BiologicalReportSectionConfidenceLabel.MODERATE
    else:
        label = BiologicalReportSectionConfidenceLabel.WEAK
    return _build_biological_report_section_confidence_entry(
        BiologicalReportSectionKey.DISEASE_PHENOTYPE_INTERPRETATION,
        label,
        (
            "disease and phenotype confidence derives from passing-term counts and "
            f"{summary.unknown_foreground_protein_count} unknown foreground proteins"
        ),
    )


__all__ = [
    "_build_disease_phenotype_entry",
    "_build_drug_target_entry",
]

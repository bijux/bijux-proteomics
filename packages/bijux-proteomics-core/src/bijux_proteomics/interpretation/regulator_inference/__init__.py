# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Upstream regulator inference ownership and governed export surface."""

from __future__ import annotations

from bijux_proteomics.interpretation.regulator_inference.inference import (
    build_regulator_inference_report,
    build_regulator_site_signal_entries_from_ptm_evidence_cards,
    parse_regulator_evidence_table,
    parse_regulator_site_signal_table,
    render_rejected_regulator_evidence_tsv,
    render_rejected_regulator_site_signal_tsv,
    render_regulator_inference_summary_tsv,
    render_regulator_inference_tsv,
    render_unresolved_regulator_target_tsv,
)
from bijux_proteomics.interpretation.regulator_inference.models import (
    RegulatorEvidenceColumnMapping,
    RegulatorEvidenceImportReport,
    RegulatorEvidenceImportSummary,
    RegulatorEvidenceRecord,
    RegulatorEvidenceTargetField,
    RegulatorEvidenceType,
    RegulatorInferenceDirection,
    RegulatorInferenceEntry,
    RegulatorInferencePolicy,
    RegulatorInferenceReport,
    RegulatorInferenceSummary,
    RegulatorSignalSurface,
    RegulatorSiteSignalColumnMapping,
    RegulatorSiteSignalEntry,
    RegulatorSiteSignalImportReport,
    RegulatorSiteSignalImportSummary,
    RejectedRegulatorEvidenceRow,
    RejectedRegulatorSiteSignalRow,
    UnresolvedRegulatorTargetEntry,
)

__all__ = [
    "RegulatorEvidenceColumnMapping",
    "RegulatorEvidenceImportReport",
    "RegulatorEvidenceImportSummary",
    "RegulatorEvidenceRecord",
    "RegulatorEvidenceTargetField",
    "RegulatorEvidenceType",
    "RegulatorInferenceDirection",
    "RegulatorInferenceEntry",
    "RegulatorInferencePolicy",
    "RegulatorInferenceReport",
    "RegulatorInferenceSummary",
    "RegulatorSignalSurface",
    "RegulatorSiteSignalColumnMapping",
    "RegulatorSiteSignalEntry",
    "RegulatorSiteSignalImportReport",
    "RegulatorSiteSignalImportSummary",
    "RejectedRegulatorEvidenceRow",
    "RejectedRegulatorSiteSignalRow",
    "UnresolvedRegulatorTargetEntry",
    "build_regulator_inference_report",
    "build_regulator_site_signal_entries_from_ptm_evidence_cards",
    "parse_regulator_evidence_table",
    "parse_regulator_site_signal_table",
    "render_rejected_regulator_evidence_tsv",
    "render_rejected_regulator_site_signal_tsv",
    "render_regulator_inference_summary_tsv",
    "render_regulator_inference_tsv",
    "render_unresolved_regulator_target_tsv",
]

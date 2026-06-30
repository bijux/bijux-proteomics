# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi
"""Owned regulator evidence import and inference assembly for biological reports."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bijux_proteomics.interpretation import (
        PathwayActivityReport,
        ProteinAnnotationMappingReport,
        RegulatorEvidenceImportReport,
        RegulatorInferenceReport,
    )
    from bijux_proteomics.ptm import PtmEvidenceCardReport
    from bijux_proteomics.quantification.contracts import DifferentialAbundanceReport


@dataclass(frozen=True, slots=True)
class BiologicalRegulatorAnalysisReports:
    """Optional regulator evidence import and downstream inference outputs."""

    regulator_evidence_import_report: RegulatorEvidenceImportReport | None
    regulator_inference_report: RegulatorInferenceReport | None


def _build_biological_regulator_analysis_reports(
    *,
    regulator_evidence_tsv_path: Path | None,
    regulator_site_signal_tsv_path: Path | None,
    ptm_evidence_card_report: PtmEvidenceCardReport | None,
    differential_report: DifferentialAbundanceReport,
    protein_refs_by_entity: Mapping[str, tuple[str, ...]],
    annotation_report: ProteinAnnotationMappingReport,
    pathway_activity_report: PathwayActivityReport | None,
) -> BiologicalRegulatorAnalysisReports:
    from bijux_proteomics.interpretation import (
        build_regulator_inference_report,
        build_regulator_site_signal_entries_from_ptm_evidence_cards,
        parse_regulator_evidence_table,
        parse_regulator_site_signal_table,
    )

    regulator_evidence_import_report = (
        None
        if regulator_evidence_tsv_path is None
        else parse_regulator_evidence_table(regulator_evidence_tsv_path)
    )
    regulator_inference_report = None
    if regulator_evidence_import_report is not None:
        if regulator_site_signal_tsv_path is not None:
            site_signal_entries = parse_regulator_site_signal_table(
                regulator_site_signal_tsv_path
            ).accepted_entries
        elif ptm_evidence_card_report is not None:
            site_signal_entries = (
                build_regulator_site_signal_entries_from_ptm_evidence_cards(
                    ptm_evidence_card_report
                )
            )
        else:
            site_signal_entries = ()
        regulator_inference_report = build_regulator_inference_report(
            regulator_evidence_import_report.accepted_records,
            differential_report,
            protein_refs_by_entity=protein_refs_by_entity,
            annotation_report=annotation_report,
            pathway_activity_report=pathway_activity_report,
            site_signal_entries=site_signal_entries,
        )

    return BiologicalRegulatorAnalysisReports(
        regulator_evidence_import_report=regulator_evidence_import_report,
        regulator_inference_report=regulator_inference_report,
    )

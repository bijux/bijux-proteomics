# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi
"""Required scientific artifact export for biological report bundles."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from bijux_proteomics.workflow.reports.biological_report_bundle_contracts import (
    BiologicalResultReportBundle,
)
from bijux_proteomics.workflow.reports.biological_report_scientific_analysis_exports import (
    _write_biological_analysis_scientific_exports,
)
from bijux_proteomics.workflow.reports.biological_report_scientific_interpretation_exports import (
    _write_biological_interpretation_scientific_exports,
)


@dataclass(frozen=True)
class BiologicalScientificRequiredExportNames:
    """Artifact names emitted for always-on scientific report outputs."""

    summary_name: str
    differential_name: str
    protein_card_summary_name: str
    protein_card_name: str
    protein_mechanism_card_summary_name: str
    protein_mechanism_card_name: str
    evidence_graph_nodes_name: str
    evidence_graph_edges_name: str
    experiment_confidence_summary_name: str
    experiment_confidence_components_name: str
    section_confidence_name: str
    foreground_background_summary_name: str
    foreground_background_entry_name: str
    foreground_background_issue_name: str
    annotation_summary_name: str
    annotation_name: str
    annotation_unmapped_name: str


def _write_biological_required_scientific_exports(
    report: BiologicalResultReportBundle,
    output_dir: Path,
    *,
    report_summary_tsv: str,
    section_confidence_tsv: str,
) -> BiologicalScientificRequiredExportNames:
    analysis_export_names = _write_biological_analysis_scientific_exports(
        report,
        output_dir,
        report_summary_tsv=report_summary_tsv,
        section_confidence_tsv=section_confidence_tsv,
    )
    interpretation_export_names = _write_biological_interpretation_scientific_exports(
        report,
        output_dir,
    )

    return BiologicalScientificRequiredExportNames(
        summary_name=analysis_export_names.summary_name,
        differential_name=analysis_export_names.differential_name,
        protein_card_summary_name=analysis_export_names.protein_card_summary_name,
        protein_card_name=analysis_export_names.protein_card_name,
        protein_mechanism_card_summary_name=(
            analysis_export_names.protein_mechanism_card_summary_name
        ),
        protein_mechanism_card_name=analysis_export_names.protein_mechanism_card_name,
        evidence_graph_nodes_name=analysis_export_names.evidence_graph_nodes_name,
        evidence_graph_edges_name=analysis_export_names.evidence_graph_edges_name,
        experiment_confidence_summary_name=(
            analysis_export_names.experiment_confidence_summary_name
        ),
        experiment_confidence_components_name=(
            analysis_export_names.experiment_confidence_components_name
        ),
        section_confidence_name=analysis_export_names.section_confidence_name,
        foreground_background_summary_name=(
            interpretation_export_names.foreground_background_summary_name
        ),
        foreground_background_entry_name=(
            interpretation_export_names.foreground_background_entry_name
        ),
        foreground_background_issue_name=(
            interpretation_export_names.foreground_background_issue_name
        ),
        annotation_summary_name=interpretation_export_names.annotation_summary_name,
        annotation_name=interpretation_export_names.annotation_name,
        annotation_unmapped_name=interpretation_export_names.annotation_unmapped_name,
    )


__all__ = [
    "BiologicalScientificRequiredExportNames",
    "_write_biological_required_scientific_exports",
]

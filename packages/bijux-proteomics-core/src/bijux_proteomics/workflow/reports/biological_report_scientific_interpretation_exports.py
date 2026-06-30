# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi
"""Interpretation-owned scientific artifact export for biological report bundles."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from bijux_proteomics._output_tables import write_output_table_tsv
from bijux_proteomics.interpretation import (
    render_biological_foreground_background_entry_tsv,
    render_biological_foreground_background_issue_tsv,
    render_biological_foreground_background_summary_tsv,
    render_protein_annotation_summary_tsv,
    render_protein_annotation_tsv,
    render_unmapped_protein_annotation_tsv,
)
from bijux_proteomics.workflow.reports.biological_report_bundle_contracts import (
    BiologicalResultReportBundle,
)


@dataclass(frozen=True)
class BiologicalScientificInterpretationExportNames:
    """Artifact names emitted for interpretation-owned scientific outputs."""

    foreground_background_summary_name: str
    foreground_background_entry_name: str
    foreground_background_issue_name: str
    annotation_summary_name: str
    annotation_name: str
    annotation_unmapped_name: str


def _write_biological_interpretation_scientific_exports(
    report: BiologicalResultReportBundle,
    output_dir: Path,
) -> BiologicalScientificInterpretationExportNames:
    foreground_background_summary_name = (
        "biological_enrichment_foreground_background_summary.tsv"
    )
    foreground_background_entry_name = (
        "biological_enrichment_foreground_background_entries.tsv"
    )
    foreground_background_issue_name = (
        "biological_enrichment_foreground_background_issues.tsv"
    )
    annotation_summary_name = "biological_annotation_summary.tsv"
    annotation_name = "biological_annotations.tsv"
    annotation_unmapped_name = "biological_annotation_unmapped.tsv"

    write_output_table_tsv(
        output_dir / foreground_background_summary_name,
        render_biological_foreground_background_summary_tsv(
            report.foreground_background_model
        ),
    )
    write_output_table_tsv(
        output_dir / foreground_background_entry_name,
        render_biological_foreground_background_entry_tsv(
            report.foreground_background_model
        ),
    )
    write_output_table_tsv(
        output_dir / foreground_background_issue_name,
        render_biological_foreground_background_issue_tsv(
            report.foreground_background_model
        ),
    )
    write_output_table_tsv(
        output_dir / annotation_summary_name,
        render_protein_annotation_summary_tsv(report.annotation_report),
    )
    write_output_table_tsv(
        output_dir / annotation_name,
        render_protein_annotation_tsv(report.annotation_report),
    )
    write_output_table_tsv(
        output_dir / annotation_unmapped_name,
        render_unmapped_protein_annotation_tsv(report.annotation_report),
    )

    return BiologicalScientificInterpretationExportNames(
        foreground_background_summary_name=foreground_background_summary_name,
        foreground_background_entry_name=foreground_background_entry_name,
        foreground_background_issue_name=foreground_background_issue_name,
        annotation_summary_name=annotation_summary_name,
        annotation_name=annotation_name,
        annotation_unmapped_name=annotation_unmapped_name,
    )


__all__ = [
    "BiologicalScientificInterpretationExportNames",
    "_write_biological_interpretation_scientific_exports",
]

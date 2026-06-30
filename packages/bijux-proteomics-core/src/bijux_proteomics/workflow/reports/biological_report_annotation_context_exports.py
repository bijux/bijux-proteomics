# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Annotation-context artifact export for biological report bundles."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from bijux_proteomics._output_tables import write_output_table_tsv
from bijux_proteomics.interpretation import (
    render_biological_context_mapping_summary_tsv,
    render_biological_context_mapping_tsv,
    render_biological_context_term_tsv,
    render_rejected_biological_context_tsv,
    render_unmapped_biological_context_tsv,
)
from bijux_proteomics.workflow.reports.biological_report_bundle_contracts import (
    BiologicalContextualReportBundle,
)


@dataclass(frozen=True)
class BiologicalAnnotationContextExportNames:
    """Artifact names emitted for annotation-context exports."""

    summary_name: str | None
    mapping_name: str | None
    term_name: str | None
    unmapped_name: str | None
    rejected_name: str | None


def _write_biological_annotation_context_exports(
    report: BiologicalContextualReportBundle,
    output_dir: Path,
) -> BiologicalAnnotationContextExportNames:
    if (
        report.context_import_report is None
        or report.context_mapping_report is None
    ):
        return BiologicalAnnotationContextExportNames(
            summary_name=None,
            mapping_name=None,
            term_name=None,
            unmapped_name=None,
            rejected_name=None,
        )

    summary_name = "biological_context_summary.tsv"
    mapping_name = "biological_context_mappings.tsv"
    term_name = "biological_context_terms.tsv"
    unmapped_name = "biological_context_unmapped.tsv"
    rejected_name = "biological_context_rejected.tsv"
    write_output_table_tsv(
        output_dir / summary_name,
        render_biological_context_mapping_summary_tsv(report.context_mapping_report),
    )
    write_output_table_tsv(
        output_dir / mapping_name,
        render_biological_context_mapping_tsv(report.context_mapping_report),
    )
    write_output_table_tsv(
        output_dir / term_name,
        render_biological_context_term_tsv(report.context_mapping_report),
    )
    write_output_table_tsv(
        output_dir / unmapped_name,
        render_unmapped_biological_context_tsv(report.context_mapping_report),
    )
    write_output_table_tsv(
        output_dir / rejected_name,
        render_rejected_biological_context_tsv(report.context_import_report),
    )
    return BiologicalAnnotationContextExportNames(
        summary_name=summary_name,
        mapping_name=mapping_name,
        term_name=term_name,
        unmapped_name=unmapped_name,
        rejected_name=rejected_name,
    )


__all__ = [
    "BiologicalAnnotationContextExportNames",
    "_write_biological_annotation_context_exports",
]

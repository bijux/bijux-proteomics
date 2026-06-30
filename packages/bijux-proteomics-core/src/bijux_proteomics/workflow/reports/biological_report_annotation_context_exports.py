# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Annotation-context artifact export for biological report bundles."""

from __future__ import annotations

from pathlib import Path

from bijux_proteomics._output_tables import write_output_table_tsv
from bijux_proteomics.interpretation import (
    render_biological_context_mapping_summary_tsv,
    render_biological_context_mapping_tsv,
    render_biological_context_term_tsv,
    render_rejected_biological_context_tsv,
    render_unmapped_biological_context_tsv,
)
from bijux_proteomics.workflow.reports.biological_report_models import (
    BiologicalResultReportBundle,
)


def _write_biological_annotation_context_exports(
    report: BiologicalResultReportBundle,
    output_dir: Path,
) -> tuple[str | None, str | None, str | None, str | None, str | None]:
    if (
        report.context_import_report is None
        or report.context_mapping_report is None
    ):
        return (None, None, None, None, None)

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
    return (
        summary_name,
        mapping_name,
        term_name,
        unmapped_name,
        rejected_name,
    )

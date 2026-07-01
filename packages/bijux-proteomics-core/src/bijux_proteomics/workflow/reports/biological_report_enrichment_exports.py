# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Optional enrichment artifact export for biological report bundles."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from bijux_proteomics._output_tables import write_output_table_tsv
from bijux_proteomics.interpretation import (
    render_complex_enrichment_entry_tsv,
    render_complex_enrichment_summary_tsv,
    render_complex_unresolved_member_tsv,
    render_go_enrichment_summary_tsv,
    render_go_enrichment_term_tsv,
    render_go_enrichment_unannotated_tsv,
    render_pathway_enrichment_entry_tsv,
    render_pathway_enrichment_summary_tsv,
    render_pathway_unresolved_member_tsv,
)
from bijux_proteomics.workflow.reports.biological_report_bundle_contracts import (
    BiologicalEnrichmentReportBundle,
)


@dataclass(frozen=True)
class BiologicalEnrichmentExportNames:
    """Artifact names emitted for optional enrichment sections."""

    go_summary_name: str | None
    go_term_name: str | None
    go_unannotated_name: str | None
    pathway_summary_name: str | None
    pathway_entry_name: str | None
    pathway_unresolved_name: str | None
    complex_summary_name: str | None
    complex_entry_name: str | None
    complex_unresolved_name: str | None


def write_biological_enrichment_exports(
    report: BiologicalEnrichmentReportBundle,
    output_dir: Path,
) -> BiologicalEnrichmentExportNames:
    """Write optional GO, pathway, and complex enrichment artifacts."""

    go_summary_name = None
    go_term_name = None
    go_unannotated_name = None
    if report.go_enrichment_report is not None:
        go_summary_name = "biological_go_summary.tsv"
        go_term_name = "biological_go_terms.tsv"
        go_unannotated_name = "biological_go_unannotated.tsv"
        write_output_table_tsv(
            output_dir / go_summary_name,
            render_go_enrichment_summary_tsv(report.go_enrichment_report),
        )
        write_output_table_tsv(
            output_dir / go_term_name,
            render_go_enrichment_term_tsv(report.go_enrichment_report),
        )
        write_output_table_tsv(
            output_dir / go_unannotated_name,
            render_go_enrichment_unannotated_tsv(report.go_enrichment_report),
        )

    pathway_summary_name = None
    pathway_entry_name = None
    pathway_unresolved_name = None
    if report.pathway_enrichment_report is not None:
        pathway_summary_name = "biological_pathway_summary.tsv"
        pathway_entry_name = "biological_pathway_entries.tsv"
        pathway_unresolved_name = "biological_pathway_unresolved.tsv"
        write_output_table_tsv(
            output_dir / pathway_summary_name,
            render_pathway_enrichment_summary_tsv(report.pathway_enrichment_report),
        )
        write_output_table_tsv(
            output_dir / pathway_entry_name,
            render_pathway_enrichment_entry_tsv(report.pathway_enrichment_report),
        )
        write_output_table_tsv(
            output_dir / pathway_unresolved_name,
            render_pathway_unresolved_member_tsv(report.pathway_enrichment_report),
        )

    complex_summary_name = None
    complex_entry_name = None
    complex_unresolved_name = None
    if report.complex_enrichment_report is not None:
        complex_summary_name = "biological_complex_summary.tsv"
        complex_entry_name = "biological_complex_entries.tsv"
        complex_unresolved_name = "biological_complex_unresolved.tsv"
        write_output_table_tsv(
            output_dir / complex_summary_name,
            render_complex_enrichment_summary_tsv(report.complex_enrichment_report),
        )
        write_output_table_tsv(
            output_dir / complex_entry_name,
            render_complex_enrichment_entry_tsv(report.complex_enrichment_report),
        )
        write_output_table_tsv(
            output_dir / complex_unresolved_name,
            render_complex_unresolved_member_tsv(report.complex_enrichment_report),
        )

    return BiologicalEnrichmentExportNames(
        go_summary_name=go_summary_name,
        go_term_name=go_term_name,
        go_unannotated_name=go_unannotated_name,
        pathway_summary_name=pathway_summary_name,
        pathway_entry_name=pathway_entry_name,
        pathway_unresolved_name=pathway_unresolved_name,
        complex_summary_name=complex_summary_name,
        complex_entry_name=complex_entry_name,
        complex_unresolved_name=complex_unresolved_name,
    )

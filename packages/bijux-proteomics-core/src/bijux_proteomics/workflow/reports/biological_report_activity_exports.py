# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Optional activity artifact export for biological report bundles."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from bijux_proteomics._output_tables import write_output_table_tsv
from bijux_proteomics.interpretation import (
    render_complex_activity_condition_comparison_tsv,
    render_complex_activity_condition_score_tsv,
    render_complex_activity_matrix_tsv,
    render_complex_activity_sample_score_tsv,
    render_complex_activity_summary_tsv,
    render_complex_activity_unresolved_member_tsv,
    render_pathway_activity_condition_comparison_tsv,
    render_pathway_activity_condition_score_tsv,
    render_pathway_activity_matrix_tsv,
    render_pathway_activity_sample_score_tsv,
    render_pathway_activity_summary_tsv,
    render_pathway_activity_unresolved_member_tsv,
    render_pathway_member_contribution_tsv,
    render_complex_member_contribution_tsv,
)
from bijux_proteomics.interpretation.compartment_biology import (
    render_compartment_activity_condition_comparison_tsv,
    render_compartment_activity_condition_score_tsv,
    render_compartment_activity_matrix_tsv,
    render_compartment_activity_sample_score_tsv,
    render_compartment_activity_unresolved_member_tsv,
    render_compartment_biology_summary_tsv,
    render_compartment_enrichment_tsv,
    render_unknown_compartment_localization_tsv,
)
from bijux_proteomics.workflow.cards.pathway_evidence_cards import (
    render_pathway_evidence_card_tsv,
)
from bijux_proteomics.workflow.reports.biological_report_models import (
    BiologicalResultReportBundle,
)


@dataclass(frozen=True)
class BiologicalActivityExportNames:
    """Artifact names emitted for optional biological activity sections."""

    compartment_summary_name: str | None
    compartment_enrichment_name: str | None
    compartment_activity_matrix_name: str | None
    compartment_activity_sample_name: str | None
    compartment_activity_condition_name: str | None
    compartment_activity_comparison_name: str | None
    compartment_activity_unresolved_name: str | None
    compartment_unknown_name: str | None
    pathway_card_name: str | None
    pathway_activity_summary_name: str | None
    pathway_activity_matrix_name: str | None
    pathway_activity_sample_name: str | None
    pathway_activity_condition_name: str | None
    pathway_activity_comparison_name: str | None
    pathway_activity_member_name: str | None
    pathway_activity_unresolved_name: str | None
    complex_activity_summary_name: str | None
    complex_activity_matrix_name: str | None
    complex_activity_sample_name: str | None
    complex_activity_condition_name: str | None
    complex_activity_comparison_name: str | None
    complex_activity_member_name: str | None
    complex_activity_unresolved_name: str | None


def write_biological_activity_exports(
    report: BiologicalResultReportBundle,
    output_dir: Path,
) -> BiologicalActivityExportNames:
    """Write optional compartment, pathway, and complex activity artifacts."""

    compartment_summary_name = None
    compartment_enrichment_name = None
    compartment_activity_matrix_name = None
    compartment_activity_sample_name = None
    compartment_activity_condition_name = None
    compartment_activity_comparison_name = None
    compartment_activity_unresolved_name = None
    compartment_unknown_name = None
    if report.compartment_biology_report is not None:
        compartment_summary_name = "biological_compartment_biology_summary.tsv"
        compartment_enrichment_name = "biological_compartment_enrichment.tsv"
        compartment_activity_matrix_name = "biological_compartment_activity_matrix.tsv"
        compartment_activity_sample_name = "biological_compartment_activity_samples.tsv"
        compartment_activity_condition_name = (
            "biological_compartment_activity_conditions.tsv"
        )
        compartment_activity_comparison_name = (
            "biological_compartment_activity_condition_comparisons.tsv"
        )
        compartment_activity_unresolved_name = (
            "biological_compartment_activity_unresolved.tsv"
        )
        compartment_unknown_name = "biological_compartment_unknown_localization.tsv"
        write_output_table_tsv(
            output_dir / compartment_summary_name,
            render_compartment_biology_summary_tsv(report.compartment_biology_report),
        )
        write_output_table_tsv(
            output_dir / compartment_enrichment_name,
            render_compartment_enrichment_tsv(report.compartment_biology_report),
        )
        write_output_table_tsv(
            output_dir / compartment_activity_matrix_name,
            render_compartment_activity_matrix_tsv(report.compartment_biology_report),
        )
        write_output_table_tsv(
            output_dir / compartment_activity_sample_name,
            render_compartment_activity_sample_score_tsv(
                report.compartment_biology_report
            ),
        )
        write_output_table_tsv(
            output_dir / compartment_activity_condition_name,
            render_compartment_activity_condition_score_tsv(
                report.compartment_biology_report
            ),
        )
        write_output_table_tsv(
            output_dir / compartment_activity_comparison_name,
            render_compartment_activity_condition_comparison_tsv(
                report.compartment_biology_report
            ),
        )
        write_output_table_tsv(
            output_dir / compartment_activity_unresolved_name,
            render_compartment_activity_unresolved_member_tsv(
                report.compartment_biology_report
            ),
        )
        write_output_table_tsv(
            output_dir / compartment_unknown_name,
            render_unknown_compartment_localization_tsv(
                report.compartment_biology_report
            ),
        )

    pathway_card_name = None
    pathway_activity_summary_name = None
    pathway_activity_matrix_name = None
    pathway_activity_sample_name = None
    pathway_activity_condition_name = None
    pathway_activity_comparison_name = None
    pathway_activity_member_name = None
    pathway_activity_unresolved_name = None
    if report.pathway_activity_report is not None:
        pathway_card_name = "biological_pathway_cards.tsv"
        pathway_activity_summary_name = "biological_pathway_activity_summary.tsv"
        pathway_activity_matrix_name = "biological_pathway_activity_matrix.tsv"
        pathway_activity_sample_name = "biological_pathway_activity_samples.tsv"
        pathway_activity_condition_name = "biological_pathway_activity_conditions.tsv"
        pathway_activity_comparison_name = (
            "biological_pathway_activity_condition_comparisons.tsv"
        )
        pathway_activity_member_name = "biological_pathway_activity_members.tsv"
        pathway_activity_unresolved_name = "biological_pathway_activity_unresolved.tsv"
        write_output_table_tsv(
            output_dir / pathway_activity_summary_name,
            render_pathway_activity_summary_tsv(report.pathway_activity_report),
        )
        write_output_table_tsv(
            output_dir / pathway_card_name,
            render_pathway_evidence_card_tsv(report.pathway_activity_report),
        )
        write_output_table_tsv(
            output_dir / pathway_activity_matrix_name,
            render_pathway_activity_matrix_tsv(report.pathway_activity_report),
        )
        write_output_table_tsv(
            output_dir / pathway_activity_sample_name,
            render_pathway_activity_sample_score_tsv(report.pathway_activity_report),
        )
        write_output_table_tsv(
            output_dir / pathway_activity_condition_name,
            render_pathway_activity_condition_score_tsv(report.pathway_activity_report),
        )
        write_output_table_tsv(
            output_dir / pathway_activity_comparison_name,
            render_pathway_activity_condition_comparison_tsv(
                report.pathway_activity_report
            ),
        )
        write_output_table_tsv(
            output_dir / pathway_activity_member_name,
            render_pathway_member_contribution_tsv(report.pathway_activity_report),
        )
        write_output_table_tsv(
            output_dir / pathway_activity_unresolved_name,
            render_pathway_activity_unresolved_member_tsv(
                report.pathway_activity_report
            ),
        )

    complex_activity_summary_name = None
    complex_activity_matrix_name = None
    complex_activity_sample_name = None
    complex_activity_condition_name = None
    complex_activity_comparison_name = None
    complex_activity_member_name = None
    complex_activity_unresolved_name = None
    if report.complex_activity_report is not None:
        complex_activity_summary_name = "biological_complex_activity_summary.tsv"
        complex_activity_matrix_name = "biological_complex_activity_matrix.tsv"
        complex_activity_sample_name = "biological_complex_activity_samples.tsv"
        complex_activity_condition_name = "biological_complex_activity_conditions.tsv"
        complex_activity_comparison_name = (
            "biological_complex_activity_condition_comparisons.tsv"
        )
        complex_activity_member_name = "biological_complex_activity_members.tsv"
        complex_activity_unresolved_name = "biological_complex_activity_unresolved.tsv"
        write_output_table_tsv(
            output_dir / complex_activity_summary_name,
            render_complex_activity_summary_tsv(report.complex_activity_report),
        )
        write_output_table_tsv(
            output_dir / complex_activity_matrix_name,
            render_complex_activity_matrix_tsv(report.complex_activity_report),
        )
        write_output_table_tsv(
            output_dir / complex_activity_sample_name,
            render_complex_activity_sample_score_tsv(report.complex_activity_report),
        )
        write_output_table_tsv(
            output_dir / complex_activity_condition_name,
            render_complex_activity_condition_score_tsv(report.complex_activity_report),
        )
        write_output_table_tsv(
            output_dir / complex_activity_comparison_name,
            render_complex_activity_condition_comparison_tsv(
                report.complex_activity_report
            ),
        )
        write_output_table_tsv(
            output_dir / complex_activity_member_name,
            render_complex_member_contribution_tsv(report.complex_activity_report),
        )
        write_output_table_tsv(
            output_dir / complex_activity_unresolved_name,
            render_complex_activity_unresolved_member_tsv(
                report.complex_activity_report
            ),
        )

    return BiologicalActivityExportNames(
        compartment_summary_name=compartment_summary_name,
        compartment_enrichment_name=compartment_enrichment_name,
        compartment_activity_matrix_name=compartment_activity_matrix_name,
        compartment_activity_sample_name=compartment_activity_sample_name,
        compartment_activity_condition_name=compartment_activity_condition_name,
        compartment_activity_comparison_name=compartment_activity_comparison_name,
        compartment_activity_unresolved_name=compartment_activity_unresolved_name,
        compartment_unknown_name=compartment_unknown_name,
        pathway_card_name=pathway_card_name,
        pathway_activity_summary_name=pathway_activity_summary_name,
        pathway_activity_matrix_name=pathway_activity_matrix_name,
        pathway_activity_sample_name=pathway_activity_sample_name,
        pathway_activity_condition_name=pathway_activity_condition_name,
        pathway_activity_comparison_name=pathway_activity_comparison_name,
        pathway_activity_member_name=pathway_activity_member_name,
        pathway_activity_unresolved_name=pathway_activity_unresolved_name,
        complex_activity_summary_name=complex_activity_summary_name,
        complex_activity_matrix_name=complex_activity_matrix_name,
        complex_activity_sample_name=complex_activity_sample_name,
        complex_activity_condition_name=complex_activity_condition_name,
        complex_activity_comparison_name=complex_activity_comparison_name,
        complex_activity_member_name=complex_activity_member_name,
        complex_activity_unresolved_name=complex_activity_unresolved_name,
    )

# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Compartment activity artifact export for biological report bundles."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from bijux_proteomics._output_tables import write_output_table_tsv
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
from bijux_proteomics.workflow.reports.biological_report_bundle_contracts import (
    BiologicalResultReportBundle,
)


@dataclass(frozen=True)
class BiologicalCompartmentActivityExportNames:
    """Artifact names emitted for compartment activity exports."""

    summary_name: str | None
    enrichment_name: str | None
    activity_matrix_name: str | None
    activity_sample_name: str | None
    activity_condition_name: str | None
    activity_comparison_name: str | None
    activity_unresolved_name: str | None
    unknown_name: str | None


def _write_biological_compartment_activity_exports(
    report: BiologicalResultReportBundle,
    output_dir: Path,
) -> BiologicalCompartmentActivityExportNames:
    if report.compartment_biology_report is None:
        return BiologicalCompartmentActivityExportNames(
            summary_name=None,
            enrichment_name=None,
            activity_matrix_name=None,
            activity_sample_name=None,
            activity_condition_name=None,
            activity_comparison_name=None,
            activity_unresolved_name=None,
            unknown_name=None,
        )

    summary_name = "biological_compartment_biology_summary.tsv"
    enrichment_name = "biological_compartment_enrichment.tsv"
    activity_matrix_name = "biological_compartment_activity_matrix.tsv"
    activity_sample_name = "biological_compartment_activity_samples.tsv"
    activity_condition_name = "biological_compartment_activity_conditions.tsv"
    activity_comparison_name = (
        "biological_compartment_activity_condition_comparisons.tsv"
    )
    activity_unresolved_name = "biological_compartment_activity_unresolved.tsv"
    unknown_name = "biological_compartment_unknown_localization.tsv"
    write_output_table_tsv(
        output_dir / summary_name,
        render_compartment_biology_summary_tsv(report.compartment_biology_report),
    )
    write_output_table_tsv(
        output_dir / enrichment_name,
        render_compartment_enrichment_tsv(report.compartment_biology_report),
    )
    write_output_table_tsv(
        output_dir / activity_matrix_name,
        render_compartment_activity_matrix_tsv(report.compartment_biology_report),
    )
    write_output_table_tsv(
        output_dir / activity_sample_name,
        render_compartment_activity_sample_score_tsv(report.compartment_biology_report),
    )
    write_output_table_tsv(
        output_dir / activity_condition_name,
        render_compartment_activity_condition_score_tsv(
            report.compartment_biology_report
        ),
    )
    write_output_table_tsv(
        output_dir / activity_comparison_name,
        render_compartment_activity_condition_comparison_tsv(
            report.compartment_biology_report
        ),
    )
    write_output_table_tsv(
        output_dir / activity_unresolved_name,
        render_compartment_activity_unresolved_member_tsv(
            report.compartment_biology_report
        ),
    )
    write_output_table_tsv(
        output_dir / unknown_name,
        render_unknown_compartment_localization_tsv(report.compartment_biology_report),
    )
    return BiologicalCompartmentActivityExportNames(
        summary_name=summary_name,
        enrichment_name=enrichment_name,
        activity_matrix_name=activity_matrix_name,
        activity_sample_name=activity_sample_name,
        activity_condition_name=activity_condition_name,
        activity_comparison_name=activity_comparison_name,
        activity_unresolved_name=activity_unresolved_name,
        unknown_name=unknown_name,
    )


__all__ = [
    "BiologicalCompartmentActivityExportNames",
    "_write_biological_compartment_activity_exports",
]

# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Complex activity artifact export for biological report bundles."""

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
    render_complex_member_contribution_tsv,
)
from bijux_proteomics.workflow.reports.biological_report_bundle_contracts import (
    BiologicalActivityReportBundle,
)


@dataclass(frozen=True)
class BiologicalComplexActivityExportNames:
    """Artifact names emitted for complex activity exports."""

    activity_summary_name: str | None
    activity_matrix_name: str | None
    activity_sample_name: str | None
    activity_condition_name: str | None
    activity_comparison_name: str | None
    activity_member_name: str | None
    activity_unresolved_name: str | None


def _write_biological_complex_activity_exports(
    report: BiologicalActivityReportBundle,
    output_dir: Path,
) -> BiologicalComplexActivityExportNames:
    if report.complex_activity_report is None:
        return BiologicalComplexActivityExportNames(
            activity_summary_name=None,
            activity_matrix_name=None,
            activity_sample_name=None,
            activity_condition_name=None,
            activity_comparison_name=None,
            activity_member_name=None,
            activity_unresolved_name=None,
        )

    activity_summary_name = "biological_complex_activity_summary.tsv"
    activity_matrix_name = "biological_complex_activity_matrix.tsv"
    activity_sample_name = "biological_complex_activity_samples.tsv"
    activity_condition_name = "biological_complex_activity_conditions.tsv"
    activity_comparison_name = (
        "biological_complex_activity_condition_comparisons.tsv"
    )
    activity_member_name = "biological_complex_activity_members.tsv"
    activity_unresolved_name = "biological_complex_activity_unresolved.tsv"
    write_output_table_tsv(
        output_dir / activity_summary_name,
        render_complex_activity_summary_tsv(report.complex_activity_report),
    )
    write_output_table_tsv(
        output_dir / activity_matrix_name,
        render_complex_activity_matrix_tsv(report.complex_activity_report),
    )
    write_output_table_tsv(
        output_dir / activity_sample_name,
        render_complex_activity_sample_score_tsv(report.complex_activity_report),
    )
    write_output_table_tsv(
        output_dir / activity_condition_name,
        render_complex_activity_condition_score_tsv(report.complex_activity_report),
    )
    write_output_table_tsv(
        output_dir / activity_comparison_name,
        render_complex_activity_condition_comparison_tsv(
            report.complex_activity_report
        ),
    )
    write_output_table_tsv(
        output_dir / activity_member_name,
        render_complex_member_contribution_tsv(report.complex_activity_report),
    )
    write_output_table_tsv(
        output_dir / activity_unresolved_name,
        render_complex_activity_unresolved_member_tsv(report.complex_activity_report),
    )
    return BiologicalComplexActivityExportNames(
        activity_summary_name=activity_summary_name,
        activity_matrix_name=activity_matrix_name,
        activity_sample_name=activity_sample_name,
        activity_condition_name=activity_condition_name,
        activity_comparison_name=activity_comparison_name,
        activity_member_name=activity_member_name,
        activity_unresolved_name=activity_unresolved_name,
    )


__all__ = [
    "BiologicalComplexActivityExportNames",
    "_write_biological_complex_activity_exports",
]

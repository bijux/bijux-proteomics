# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""HTML tables for sample-context report sections."""

from __future__ import annotations

from html import escape

from bijux_proteomics.workflow.reports.biological_report_html_support import (
    _format_optional_float,
)
from bijux_proteomics.workflow.reports.biological_report_bundle_contracts import (
    BiologicalResultReportBundle,
)


def _render_tissue_cell_type_context_table_html(
    report: BiologicalResultReportBundle,
) -> str:
    tissue_context_report = report.tissue_cell_type_context_report
    if tissue_context_report is None:
        return "<p>No tissue or cell-type context report was generated.</p>"
    headers = (
        "Sample",
        "Label",
        "Expected score",
        "Unexpected context",
        "Unexpected score",
        "QC warning",
        "Status",
    )
    header_html = "".join(f"<th>{escape(header)}</th>" for header in headers)
    row_html = "".join(
        (
            "<tr>"
            f"<td>{escape(entry.sample_id)}</td>"
            f"<td>{escape(entry.tissue_or_cell_type or '-')}</td>"
            f"<td>{_format_optional_float(entry.expected_marker_score)}</td>"
            f"<td>{escape(entry.highest_unexpected_context_name or entry.highest_unexpected_context_id or '-')}</td>"
            f"<td>{_format_optional_float(entry.highest_unexpected_marker_score)}</td>"
            f"<td>{escape(str(entry.qc_warning).lower())}</td>"
            f"<td>{escape(entry.status.value)}</td>"
            "</tr>"
        )
        for entry in tissue_context_report.sample_consistency_entries[:10]
    )
    summary = tissue_context_report.summary
    return (
        "<p>"
        f"<strong>Samples</strong>: {summary.sample_count} | "
        f"<strong>Labeled</strong>: {summary.labeled_sample_count} | "
        f"<strong>Marker contexts</strong>: {summary.marker_context_count} | "
        f"<strong>QC warnings</strong>: {summary.mismatch_warning_count} | "
        f"<strong>Unexpected signals</strong>: {summary.unexpected_signal_count}"
        "</p>"
        "<table>"
        f"<thead><tr>{header_html}</tr></thead>"
        f"<tbody>{row_html}</tbody>"
        "</table>"
    )


def _render_cohort_stratification_table_html(
    report: BiologicalResultReportBundle,
) -> str:
    cohort_report = report.cohort_stratification_report
    if cohort_report is None:
        return "<p>No cohort stratification report was generated.</p>"
    headers = (
        "Field",
        "Left subgroup",
        "Right subgroup",
        "Entity",
        "Kind",
        "Delta",
    )
    header_html = "".join(f"<th>{escape(header)}</th>" for header in headers)
    row_html = "".join(
        (
            "<tr>"
            f"<td>{escape(entry.field_name.value)}</td>"
            f"<td>{escape(entry.left_subgroup_value)}</td>"
            f"<td>{escape(entry.right_subgroup_value)}</td>"
            f"<td>{escape(entry.entity_id)}</td>"
            f"<td>{escape(entry.candidate_kind.value)}</td>"
            f"<td>{entry.interaction_delta:.4f}</td>"
            "</tr>"
        )
        for entry in cohort_report.interaction_candidates[:10]
    )
    summary = cohort_report.summary
    return (
        "<p>"
        f"<strong>Fields</strong>: {summary.field_count} | "
        f"<strong>Supported strata</strong>: {summary.supported_stratum_count} | "
        f"<strong>Blocked strata</strong>: {summary.blocked_stratum_count} | "
        f"<strong>Subgroup effects</strong>: {summary.subgroup_effect_count} | "
        f"<strong>Interaction candidates</strong>: {summary.interaction_candidate_count}"
        "</p>"
        "<table>"
        f"<thead><tr>{header_html}</tr></thead>"
        f"<tbody>{row_html}</tbody>"
        "</table>"
    )

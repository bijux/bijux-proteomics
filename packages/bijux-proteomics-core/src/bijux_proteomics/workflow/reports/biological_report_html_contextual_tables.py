# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Compatibility wrappers for split contextual biological report tables."""

from __future__ import annotations

from html import escape

from bijux_proteomics.workflow.reports.biological_report_html_interpretation_tables import (
    _render_cohort_stratification_table_html as _render_html_cohort_stratification_table,
    _render_disease_phenotype_table_html as _render_html_disease_phenotype_table,
    _render_drug_target_table_html as _render_html_drug_target_table,
    _render_regulator_inference_table_html as _render_html_regulator_inference_table,
    _render_tissue_cell_type_context_table_html as _render_html_tissue_context_table,
)
from bijux_proteomics.workflow.reports.biological_report_html_support import (
    _format_optional_float,
)
from bijux_proteomics.workflow.reports.biological_report_models import (
    BiologicalResultReportBundle,
)


def _render_regulator_inference_table_html(
    report: BiologicalResultReportBundle,
) -> str:
    return _render_html_regulator_inference_table(report)


def _render_drug_target_table_html(report: BiologicalResultReportBundle) -> str:
    return _render_html_drug_target_table(report)


def _render_disease_phenotype_table_html(report: BiologicalResultReportBundle) -> str:
    return _render_html_disease_phenotype_table(report)


def _render_tissue_cell_type_context_table_html(
    report: BiologicalResultReportBundle,
) -> str:
    return _render_html_tissue_context_table(report)


def _render_cohort_stratification_table_html(
    report: BiologicalResultReportBundle,
) -> str:
    return _render_html_cohort_stratification_table(report)


def _render_compartment_biology_table_html(
    report: BiologicalResultReportBundle,
) -> str:
    compartment_biology_report = report.compartment_biology_report
    if compartment_biology_report is None:
        return "<p>No compartment biology report was generated.</p>"
    headers = (
        "Compartment",
        "Condition A",
        "Condition B",
        "Delta",
        "Comparison confidence",
    )
    header_html = "".join(f"<th>{escape(header)}</th>" for header in headers)
    row_html = "".join(
        (
            "<tr>"
            f"<td>{escape(entry.set_name or entry.set_id)}</td>"
            f"<td>{escape(entry.condition_a)}</td>"
            f"<td>{escape(entry.condition_b)}</td>"
            f"<td>{_format_optional_float(entry.activity_score_delta)}</td>"
            f"<td>{escape(entry.comparison_confidence_status.value)}</td>"
            "</tr>"
        )
        for entry in compartment_biology_report.activity_report.condition_comparisons[
            :10
        ]
    )
    return (
        "<p>"
        f"<strong>Compartments</strong>: {compartment_biology_report.summary.compartment_count} | "
        f"<strong>Enriched compartments</strong>: "
        f"{compartment_biology_report.summary.enriched_compartment_count} | "
        f"<strong>Low-confidence sample scores</strong>: "
        f"{compartment_biology_report.summary.low_confidence_sample_score_count} | "
        f"<strong>Unresolved members</strong>: "
        f"{compartment_biology_report.summary.unresolved_member_count} | "
        f"<strong>Unknown foreground proteins</strong>: "
        f"{compartment_biology_report.summary.unknown_foreground_protein_count} | "
        f"<strong>Unknown background proteins</strong>: "
        f"{compartment_biology_report.summary.unknown_background_protein_count}"
        "</p>"
        "<table>"
        f"<thead><tr>{header_html}</tr></thead>"
        f"<tbody>{row_html}</tbody>"
        "</table>"
    )


def _render_pathway_activity_table_html(report: BiologicalResultReportBundle) -> str:
    pathway_activity_report = report.pathway_activity_report
    if pathway_activity_report is None:
        return "<p>No pathway activity report was generated.</p>"
    headers = (
        "Pathway",
        "Condition A",
        "Condition B",
        "Delta",
        "Comparison confidence",
    )
    header_html = "".join(f"<th>{escape(header)}</th>" for header in headers)
    row_html = "".join(
        (
            "<tr>"
            f"<td>{escape(entry.pathway_name or entry.pathway_id)}</td>"
            f"<td>{escape(entry.condition_a)}</td>"
            f"<td>{escape(entry.condition_b)}</td>"
            f"<td>{_format_optional_float(entry.activity_score_delta)}</td>"
            f"<td>{escape(entry.comparison_confidence_status.value)}</td>"
            "</tr>"
        )
        for entry in pathway_activity_report.condition_comparisons[:10]
    )
    return (
        "<p>"
        f"<strong>Pathways</strong>: {pathway_activity_report.summary.pathway_count} | "
        f"<strong>Low-confidence sample scores</strong>: "
        f"{pathway_activity_report.summary.low_confidence_sample_score_count} | "
        f"<strong>Unresolved members</strong>: "
        f"{pathway_activity_report.summary.unresolved_member_count}"
        "</p>"
        "<table>"
        f"<thead><tr>{header_html}</tr></thead>"
        f"<tbody>{row_html}</tbody>"
        "</table>"
    )


def _render_complex_activity_table_html(report: BiologicalResultReportBundle) -> str:
    complex_activity_report = report.complex_activity_report
    if complex_activity_report is None:
        return "<p>No complex activity report was generated.</p>"
    headers = (
        "Complex",
        "Condition A",
        "Condition B",
        "Delta",
        "Limiting members",
        "Comparison confidence",
    )
    header_html = "".join(f"<th>{escape(header)}</th>" for header in headers)
    row_html = "".join(
        (
            "<tr>"
            f"<td>{escape(entry.complex_name or entry.complex_id)}</td>"
            f"<td>{escape(entry.condition_a)}</td>"
            f"<td>{escape(entry.condition_b)}</td>"
            f"<td>{_format_optional_float(entry.activity_score_delta)}</td>"
            f"<td>{escape('; '.join(entry.condition_b_limiting_member_ids))}</td>"
            f"<td>{escape(entry.comparison_confidence_status.value)}</td>"
            "</tr>"
        )
        for entry in complex_activity_report.condition_comparisons[:10]
    )
    return (
        "<p>"
        f"<strong>Complexes</strong>: {complex_activity_report.summary.complex_count} | "
        f"<strong>Low-confidence sample scores</strong>: "
        f"{complex_activity_report.summary.low_confidence_sample_score_count} | "
        f"<strong>Unresolved members</strong>: "
        f"{complex_activity_report.summary.unresolved_member_count}"
        "</p>"
        "<table>"
        f"<thead><tr>{header_html}</tr></thead>"
        f"<tbody>{row_html}</tbody>"
        "</table>"
    )

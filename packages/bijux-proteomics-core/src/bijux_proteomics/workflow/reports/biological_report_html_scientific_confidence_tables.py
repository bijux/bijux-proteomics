# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""HTML tables for scientific confidence and selection report sections."""

from __future__ import annotations

from html import escape

from bijux_proteomics.workflow.reports.biological_report_models import (
    BiologicalResultReportBundle,
)


def _render_experiment_confidence_table_html(
    report: BiologicalResultReportBundle,
) -> str:
    headers = ("Component", "Score", "Tier", "Reason codes", "Message")
    header_html = "".join(f"<th>{escape(header)}</th>" for header in headers)
    row_html = "".join(
        (
            "<tr>"
            f"<td>{escape(component.component.value)}</td>"
            f"<td>{component.score:.3f}</td>"
            f"<td>{escape(component.tier.value)}</td>"
            f"<td>{escape('; '.join(component.reason_codes))}</td>"
            f"<td>{escape(component.message)}</td>"
            "</tr>"
        )
        for component in report.experiment_confidence_report.components
    )
    summary = report.experiment_confidence_report.summary
    return (
        "<p>"
        f"<strong>Overall score</strong>: {summary.overall_score:.3f} | "
        f"<strong>Tier</strong>: {escape(summary.overall_tier.value)} | "
        f"<strong>Low-confidence components</strong>: "
        f"{summary.low_confidence_component_count}"
        "</p>"
        "<table>"
        f"<thead><tr>{header_html}</tr></thead>"
        f"<tbody>{row_html}</tbody>"
        "</table>"
    )


def _render_foreground_background_model_table_html(
    report: BiologicalResultReportBundle,
) -> str:
    model = report.foreground_background_model
    issue_summary = (
        "none"
        if not model.issues
        else "; ".join(f"{issue.severity.value}:{issue.code}" for issue in model.issues)
    )
    headers = ("Role", "Source kind", "Policy", "Protein count")
    header_html = "".join(f"<th>{escape(header)}</th>" for header in headers)
    row_html = "".join(
        (
            "<tr>"
            f"<td>{escape(role)}</td>"
            f"<td>{escape(source_kind)}</td>"
            f"<td>{escape(policy_name)}</td>"
            f"<td>{count}</td>"
            "</tr>"
        )
        for role, source_kind, policy_name, count in (
            (
                "foreground",
                model.foreground_source_kind.value,
                model.foreground_policy.policy_name,
                model.summary.foreground_size,
            ),
            (
                "background",
                model.background_source_kind.value,
                model.background_policy.policy_name,
                model.summary.background_size,
            ),
        )
    )
    return (
        "<p>"
        f"<strong>Valid for enrichment</strong>: "
        f"{str(model.summary.valid_for_enrichment).lower()} | "
        f"<strong>Issues</strong>: {model.summary.issue_count} | "
        f"<strong>Issue summary</strong>: {escape(issue_summary)}"
        "</p>"
        "<table>"
        f"<thead><tr>{header_html}</tr></thead>"
        f"<tbody>{row_html}</tbody>"
        "</table>"
    )

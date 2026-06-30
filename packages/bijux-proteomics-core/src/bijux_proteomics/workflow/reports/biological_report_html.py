# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi
"""Biological report page orchestration and artifact inventory HTML."""

from __future__ import annotations

from bijux_proteomics.workflow.reports.biological_report_html_report_sections import (
    _render_biological_report_section_blocks_html,
)
from bijux_proteomics.workflow.reports.biological_report_html_report_summary import (
    _render_biological_report_summary_html,
)
from bijux_proteomics.workflow.reports.biological_report_models import (
    BiologicalResultReportArtifactPaths,
    BiologicalResultReportBundle,
)


def _render_biological_result_report_html(
    report: BiologicalResultReportBundle,
    artifacts: BiologicalResultReportArtifactPaths,
) -> str:
    report_summary_html = _render_biological_report_summary_html(report, artifacts)
    section_blocks_html = _render_biological_report_section_blocks_html(report)
    return (
        "<html><head><title>Bijux Proteomics Biological Report</title></head><body>"
        f"{report_summary_html}"
        f"{section_blocks_html}"
        "</body></html>\n"
    )


__all__ = ["_render_biological_result_report_html"]

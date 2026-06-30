# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Compatibility wrappers for biological activity HTML tables."""

from __future__ import annotations

from bijux_proteomics.workflow.reports.biological_report_html_compartment_tables import (
    _render_compartment_biology_table_html as _render_html_compartment_biology_table,
)
from bijux_proteomics.workflow.reports.biological_report_html_complex_activity_tables import (
    _render_complex_activity_table_html as _render_html_complex_activity_table,
)
from bijux_proteomics.workflow.reports.biological_report_html_pathway_activity_tables import (
    _render_pathway_activity_table_html as _render_html_pathway_activity_table,
)
from bijux_proteomics.workflow.reports.biological_report_models import (
    BiologicalResultReportBundle,
)


def _render_compartment_biology_table_html(
    report: BiologicalResultReportBundle,
) -> str:
    return _render_html_compartment_biology_table(report)


def _render_pathway_activity_table_html(report: BiologicalResultReportBundle) -> str:
    return _render_html_pathway_activity_table(report)


def _render_complex_activity_table_html(report: BiologicalResultReportBundle) -> str:
    return _render_html_complex_activity_table(report)


__all__ = [
    "_render_compartment_biology_table_html",
    "_render_complex_activity_table_html",
    "_render_pathway_activity_table_html",
]

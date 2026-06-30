# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Compatibility wrappers for molecular interpretation HTML tables."""

from __future__ import annotations

from bijux_proteomics.workflow.reports.biological_report_html_disease_phenotype_tables import (
    _render_disease_phenotype_table_html as _render_html_disease_phenotype_table,
)
from bijux_proteomics.workflow.reports.biological_report_html_drug_target_tables import (
    _render_drug_target_table_html as _render_html_drug_target_table,
)
from bijux_proteomics.workflow.reports.biological_report_html_regulator_tables import (
    _render_regulator_inference_table_html as _render_html_regulator_inference_table,
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


__all__ = [
    "_render_disease_phenotype_table_html",
    "_render_drug_target_table_html",
    "_render_regulator_inference_table_html",
]

# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Compatibility surface for interpretation and cohort-context HTML tables."""

from __future__ import annotations

from .molecular_interpretation_tables import (
    _render_disease_phenotype_table_html as _render_html_disease_phenotype_table,
    _render_drug_target_table_html as _render_html_drug_target_table,
    _render_regulator_inference_table_html as _render_html_regulator_inference_table,
)
from .sample_context_tables import (
    _render_cohort_stratification_table_html as _render_html_cohort_stratification_table,
    _render_tissue_cell_type_context_table_html as _render_html_tissue_context_table,
)
from ..biological_report_bundle_contracts import BiologicalResultReportBundle


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

__all__ = [
    "_render_cohort_stratification_table_html",
    "_render_disease_phenotype_table_html",
    "_render_drug_target_table_html",
    "_render_regulator_inference_table_html",
    "_render_tissue_cell_type_context_table_html",
]

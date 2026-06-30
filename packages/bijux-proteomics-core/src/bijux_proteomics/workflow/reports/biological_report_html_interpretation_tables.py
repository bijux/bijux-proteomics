# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Compatibility surface for interpretation and cohort-context HTML tables."""

from __future__ import annotations

from bijux_proteomics.workflow.reports.biological_report_html_molecular_interpretation_tables import (
    _render_disease_phenotype_table_html,
    _render_drug_target_table_html,
    _render_regulator_inference_table_html,
)
from bijux_proteomics.workflow.reports.biological_report_html_sample_context_tables import (
    _render_cohort_stratification_table_html,
    _render_tissue_cell_type_context_table_html,
)

__all__ = [
    "_render_cohort_stratification_table_html",
    "_render_disease_phenotype_table_html",
    "_render_drug_target_table_html",
    "_render_regulator_inference_table_html",
    "_render_tissue_cell_type_context_table_html",
]

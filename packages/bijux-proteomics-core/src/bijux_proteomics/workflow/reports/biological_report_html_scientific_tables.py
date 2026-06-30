# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Compatibility surface for scientific biological report HTML tables."""

from __future__ import annotations

from bijux_proteomics.workflow.reports.biological_report_html_scientific_claim_tables import (
    _render_biological_claim_validation_table_html,
    _render_biological_hypothesis_table_html,
)
from bijux_proteomics.workflow.reports.biological_report_html_scientific_confidence_tables import (
    _render_experiment_confidence_table_html,
    _render_foreground_background_model_table_html,
)
from bijux_proteomics.workflow.reports.biological_report_html_scientific_ranking_tables import (
    _render_evidence_aware_ranking_table_html,
    _render_protein_mechanism_card_table_html,
)

__all__ = [
    "_render_biological_claim_validation_table_html",
    "_render_biological_hypothesis_table_html",
    "_render_evidence_aware_ranking_table_html",
    "_render_experiment_confidence_table_html",
    "_render_foreground_background_model_table_html",
    "_render_protein_mechanism_card_table_html",
]

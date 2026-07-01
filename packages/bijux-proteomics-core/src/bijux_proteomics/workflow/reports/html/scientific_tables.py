# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Compatibility surface for scientific biological report HTML tables."""

from __future__ import annotations

from ..biological_report_bundle_contracts import BiologicalResultReportBundle
from .scientific_claim_tables import (
    _render_biological_claim_validation_table_html as _render_html_claim_validation_table,
)
from .scientific_claim_tables import (
    _render_biological_hypothesis_table_html as _render_html_hypothesis_table,
)
from .scientific_confidence_tables import (
    _render_experiment_confidence_table_html as _render_html_experiment_confidence_table,
)
from .scientific_confidence_tables import (
    _render_foreground_background_model_table_html as _render_html_foreground_background_table,
)
from .scientific_ranking_tables import (
    _render_evidence_aware_ranking_table_html as _render_html_ranking_table,
)
from .scientific_ranking_tables import (
    _render_protein_mechanism_card_table_html as _render_html_protein_mechanism_table,
)


def _render_biological_claim_validation_table_html(
    report: BiologicalResultReportBundle,
) -> str:
    return _render_html_claim_validation_table(report)


def _render_biological_hypothesis_table_html(
    report: BiologicalResultReportBundle,
) -> str:
    return _render_html_hypothesis_table(report)


def _render_evidence_aware_ranking_table_html(
    report: BiologicalResultReportBundle,
) -> str:
    return _render_html_ranking_table(report)


def _render_experiment_confidence_table_html(
    report: BiologicalResultReportBundle,
) -> str:
    return _render_html_experiment_confidence_table(report)


def _render_foreground_background_model_table_html(
    report: BiologicalResultReportBundle,
) -> str:
    return _render_html_foreground_background_table(report)


def _render_protein_mechanism_card_table_html(
    report: BiologicalResultReportBundle,
) -> str:
    return _render_html_protein_mechanism_table(report)


__all__ = [
    "_render_biological_claim_validation_table_html",
    "_render_biological_hypothesis_table_html",
    "_render_evidence_aware_ranking_table_html",
    "_render_experiment_confidence_table_html",
    "_render_foreground_background_model_table_html",
    "_render_protein_mechanism_card_table_html",
]

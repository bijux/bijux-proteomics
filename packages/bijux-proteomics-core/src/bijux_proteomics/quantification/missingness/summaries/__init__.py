# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Governed facade for sample, entity, and condition missingness summaries."""

from __future__ import annotations

from bijux_proteomics.quantification.missingness.summaries.condition_summary import (
    _build_missingness_condition_summary_report_pure,
    _build_missingness_condition_summary_report_vectorized,
    build_missingness_condition_summary_report,
)
from bijux_proteomics.quantification.missingness.summaries.entity_summary import (
    _build_missingness_entity_summary_report_pure,
    _build_missingness_entity_summary_report_vectorized,
    build_missingness_entity_summary_report,
)
from bijux_proteomics.quantification.missingness.summaries.sample_summary import (
    _summarize_missing_values_pure,
    _summarize_missing_values_vectorized,
    summarize_missing_values,
)

__all__ = [
    "_build_missingness_condition_summary_report_pure",
    "_build_missingness_condition_summary_report_vectorized",
    "_build_missingness_entity_summary_report_pure",
    "_build_missingness_entity_summary_report_vectorized",
    "_summarize_missing_values_pure",
    "_summarize_missing_values_vectorized",
    "build_missingness_condition_summary_report",
    "build_missingness_entity_summary_report",
    "summarize_missing_values",
]

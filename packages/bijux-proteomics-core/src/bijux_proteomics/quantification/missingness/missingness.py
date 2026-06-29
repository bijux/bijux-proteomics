# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Compatibility facade for quantification missingness ownership."""

from __future__ import annotations

from bijux_proteomics.quantification.missingness.classification import (
    build_missingness_classifier_report,
    classify_missingness,
)
from bijux_proteomics.quantification.missingness.intensity_dependence import (
    build_missingness_intensity_dependence_report,
)
from bijux_proteomics.quantification.missingness.mechanism_report import (
    build_missing_data_mechanism_report,
)
from bijux_proteomics.quantification.missingness.models import (
    MissingnessClassificationEntry,
    MissingnessClassificationReport,
    MissingnessLabel,
)
from bijux_proteomics.quantification.missingness.rendering import (
    render_missingness_classification_tsv,
)
from bijux_proteomics.quantification.missingness.summaries import (
    build_missingness_condition_summary_report,
    build_missingness_entity_summary_report,
    summarize_missing_values,
)

__all__ = [
    "MissingnessClassificationEntry",
    "MissingnessClassificationReport",
    "MissingnessLabel",
    "build_missingness_condition_summary_report",
    "build_missingness_classifier_report",
    "build_missing_data_mechanism_report",
    "build_missingness_entity_summary_report",
    "build_missingness_intensity_dependence_report",
    "classify_missingness",
    "render_missingness_classification_tsv",
    "summarize_missing_values",
]

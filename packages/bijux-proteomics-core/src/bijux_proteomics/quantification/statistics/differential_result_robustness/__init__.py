# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Governed public facade for differential-result robustness."""

from __future__ import annotations

from bijux_proteomics.quantification.statistics.differential_result_robustness.analysis import (
    annotate_differential_abundance_report_robustness,
    annotate_time_course_differential_report_robustness,
    build_differential_abundance_robustness_report,
    build_time_course_differential_robustness_report,
)
from bijux_proteomics.quantification.statistics.differential_result_robustness.bootstrap import (
    bootstrap_effect_stability,
    render_bootstrap_effect_stability_tsv,
)
from bijux_proteomics.quantification.statistics.differential_result_robustness.models import (
    BootstrapEffectRobustnessTier,
    BootstrapEffectStabilityEntry,
    BootstrapEffectStabilityReport,
    DifferentialResultRobustnessAnalysisKind,
    DifferentialResultRobustnessEntry,
    DifferentialResultRobustnessReport,
)

__all__ = [
    "BootstrapEffectRobustnessTier",
    "BootstrapEffectStabilityEntry",
    "BootstrapEffectStabilityReport",
    "DifferentialResultRobustnessAnalysisKind",
    "DifferentialResultRobustnessEntry",
    "DifferentialResultRobustnessReport",
    "annotate_differential_abundance_report_robustness",
    "annotate_time_course_differential_report_robustness",
    "bootstrap_effect_stability",
    "build_differential_abundance_robustness_report",
    "build_time_course_differential_robustness_report",
    "render_bootstrap_effect_stability_tsv",
]

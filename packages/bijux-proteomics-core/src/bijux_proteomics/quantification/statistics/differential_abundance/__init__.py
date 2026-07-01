# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Governed public facade for differential-abundance analysis."""

from __future__ import annotations

from bijux_proteomics.quantification.statistics.differential_abundance.analysis import (
    apply_benjamini_hochberg,
    build_differential_abundance_report,
    build_multi_condition_differential_abundance_report,
)
from bijux_proteomics.quantification.statistics.differential_abundance.observation_vectors import (
    collect_condition_values,
    collect_condition_values_vectorized,
)
from bijux_proteomics.quantification.statistics.differential_abundance.rendering import (
    export_differential_abundance_tsv,
    export_differential_broken_pairs_tsv,
    export_multi_condition_differential_abundance_tsv,
    render_differential_abundance_tsv,
    render_differential_broken_pairs_tsv,
    render_multi_condition_differential_abundance_tsv,
)

_collect_condition_values = collect_condition_values
_collect_condition_values_vectorized = collect_condition_values_vectorized


__all__ = [
    "apply_benjamini_hochberg",
    "build_differential_abundance_report",
    "build_multi_condition_differential_abundance_report",
    "export_differential_abundance_tsv",
    "export_differential_broken_pairs_tsv",
    "export_multi_condition_differential_abundance_tsv",
    "render_differential_abundance_tsv",
    "render_differential_broken_pairs_tsv",
    "render_multi_condition_differential_abundance_tsv",
]

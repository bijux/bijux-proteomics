# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Governed facade for MaxLFQ-like protein quantification."""

from __future__ import annotations

from bijux_proteomics.quantification.rollup.protein_lfq import solving as _solving
from bijux_proteomics.quantification.rollup.protein_lfq.analysis import (
    build_protein_lfq_report_from_features,
    build_protein_lfq_report_from_peptides,
    build_protein_lfq_report_from_psms,
)
from bijux_proteomics.quantification.rollup.protein_lfq.models import (
    ProteinLfqDisconnectedComponentEntry,
    ProteinLfqPairwiseRatio,
    ProteinLfqReport,
    ProteinLfqRow,
    ProteinLfqSummary,
    ProteinLfqValue,
)
from bijux_proteomics.quantification.rollup.protein_lfq.rendering import (
    render_protein_lfq_disconnected_components_tsv,
    render_protein_lfq_matrix_tsv,
    render_protein_lfq_missingness_mask_tsv,
    render_protein_lfq_missingness_tsv,
    render_protein_lfq_pairwise_ratios_tsv,
    render_protein_lfq_summary_tsv,
)

_build_pairwise_ratio_rows_pure = _solving.build_pairwise_ratio_rows_pure
_build_pairwise_ratio_rows_vectorized = _solving.build_pairwise_ratio_rows_vectorized
_observed_log2_intensities_by_sample_pure = (
    _solving.observed_log2_intensities_by_sample_pure
)
_observed_log2_intensities_by_sample_vectorized = (
    _solving.observed_log2_intensities_by_sample_vectorized
)

__all__ = [
    "ProteinLfqDisconnectedComponentEntry",
    "ProteinLfqPairwiseRatio",
    "ProteinLfqReport",
    "ProteinLfqRow",
    "ProteinLfqSummary",
    "ProteinLfqValue",
    "build_protein_lfq_report_from_features",
    "build_protein_lfq_report_from_peptides",
    "build_protein_lfq_report_from_psms",
    "render_protein_lfq_disconnected_components_tsv",
    "render_protein_lfq_matrix_tsv",
    "render_protein_lfq_missingness_mask_tsv",
    "render_protein_lfq_missingness_tsv",
    "render_protein_lfq_pairwise_ratios_tsv",
    "render_protein_lfq_summary_tsv",
]

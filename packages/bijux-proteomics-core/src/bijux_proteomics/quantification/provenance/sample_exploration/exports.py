# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Stable filesystem exports for sample exploration reports."""

from __future__ import annotations

from pathlib import Path

from bijux_proteomics._output_tables import write_output_table_tsv
from bijux_proteomics.quantification.provenance.sample_exploration.models import (
    SampleExplorationReport,
)
from bijux_proteomics.quantification.provenance.sample_exploration.rendering import (
    render_sample_cluster_tsv,
    render_sample_correlation_tsv,
    render_sample_distance_tsv,
    render_sample_exploration_summary_tsv,
    render_sample_outlier_tsv,
    render_sample_pca_scores_tsv,
    render_sample_pca_variance_tsv,
)


def export_sample_exploration_summary_tsv(
    report: SampleExplorationReport, path: Path
) -> None:
    """Write one compact sample-exploration summary to a stable TSV artifact."""

    write_output_table_tsv(path, render_sample_exploration_summary_tsv(report))


def export_sample_pca_scores_tsv(report: SampleExplorationReport, path: Path) -> None:
    """Write one sample-level PCA score table to a stable TSV artifact."""

    write_output_table_tsv(path, render_sample_pca_scores_tsv(report))


def export_sample_correlation_tsv(report: SampleExplorationReport, path: Path) -> None:
    """Write pairwise sample correlations to a stable TSV artifact."""

    write_output_table_tsv(path, render_sample_correlation_tsv(report))


def export_sample_pca_variance_tsv(report: SampleExplorationReport, path: Path) -> None:
    """Write PCA explained-variance rows to a stable TSV artifact."""

    write_output_table_tsv(path, render_sample_pca_variance_tsv(report))


def export_sample_distance_tsv(report: SampleExplorationReport, path: Path) -> None:
    """Write pairwise sample distances to a stable TSV artifact."""

    write_output_table_tsv(path, render_sample_distance_tsv(report))


def export_sample_outlier_tsv(report: SampleExplorationReport, path: Path) -> None:
    """Write metric-labeled sample outliers to a stable TSV artifact."""

    write_output_table_tsv(path, render_sample_outlier_tsv(report))


def export_sample_cluster_tsv(report: SampleExplorationReport, path: Path) -> None:
    """Write the deterministic cluster table to a stable TSV artifact."""

    write_output_table_tsv(path, render_sample_cluster_tsv(report))


__all__ = [
    "export_sample_cluster_tsv",
    "export_sample_correlation_tsv",
    "export_sample_distance_tsv",
    "export_sample_exploration_summary_tsv",
    "export_sample_outlier_tsv",
    "export_sample_pca_scores_tsv",
    "export_sample_pca_variance_tsv",
]

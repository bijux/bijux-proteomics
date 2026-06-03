# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi
# ruff: noqa: F401,F403,F405

"""Heatmap, power, and sample exploration CLI commands."""

from __future__ import annotations

from pathlib import Path

import click

from bijux_proteomics.interfaces.python_api.quantification_reports import (
    run_heatmap_matrix_command,
    run_power_estimate_command,
    run_sample_exploration_command,
)
from bijux_proteomics.interfaces.support import *  # noqa: F401,F403,F405


@click.command("heatmap-matrix")
@click.argument(
    "input_table", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--entity-level",
    type=_quant_entity_level_choice(),
    default=QuantEntityLevel.PROTEIN.value,
    show_default=True,
)
@click.option(
    "--aggregation",
    type=_quant_rollup_choice(),
    default=QuantRollupMethod.SUM.value,
    show_default=True,
)
@click.option("--top-n", type=int, default=3, show_default=True)
@click.option(
    "--normalization",
    type=_normalization_choice(),
    default=NormalizationMethod.MEDIAN.value,
    show_default=True,
)
@click.option("--sample-column", default="sample_id", show_default=True)
@click.option("--feature-id-column", default="feature_id", show_default=True)
@click.option("--peptide-column", default="peptide", show_default=True)
@click.option("--intensity-column", default="intensity", show_default=True)
@click.option("--protein-refs-column", default="proteins", show_default=True)
@click.option("--charge-column", default="charge", show_default=True)
@click.option("--mz-column", default="mz", show_default=True)
@click.option(
    "--retention-time-column", default="retention_time_seconds", show_default=True
)
@click.option("--missing-reason-column", default="missing_reason", show_default=True)
@click.option("--protein-separator", default=";", show_default=True)
@click.option(
    "--design",
    "design_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option("--entity-id", "entity_ids", multiple=True)
@click.option("--protein-ref", "protein_refs", multiple=True)
@click.option(
    "--min-observed-fraction",
    type=float,
    default=0.5,
    show_default=True,
)
@click.option("--max-entities", type=int, default=None)
@click.option("--z-score/--no-z-score", default=True, show_default=True)
@click.option(
    "--missing-value-policy",
    type=_heatmap_missing_value_choice(),
    default=HeatmapMissingValuePolicy.FILL_ROW_MEDIAN.value,
    show_default=True,
)
@click.option(
    "--summary-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--matrix-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--row-metadata-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--column-metadata-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def heatmap_matrix_command(
    input_table: Path,
    entity_level: str,
    aggregation: str,
    top_n: int,
    normalization: str,
    sample_column: str,
    feature_id_column: str,
    peptide_column: str,
    intensity_column: str,
    protein_refs_column: str | None,
    charge_column: str | None,
    mz_column: str | None,
    retention_time_column: str | None,
    missing_reason_column: str | None,
    protein_separator: str,
    design_path: Path | None,
    entity_ids: tuple[str, ...],
    protein_refs: tuple[str, ...],
    min_observed_fraction: float,
    max_entities: int | None,
    z_score: bool,
    missing_value_policy: str,
    summary_tsv_out: Path | None,
    matrix_tsv_out: Path | None,
    row_metadata_tsv_out: Path | None,
    column_metadata_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    "Prepare one normalized matrix for heatmaps and clustering."
    return run_heatmap_matrix_command(
        input_table,
        entity_level,
        aggregation,
        top_n,
        normalization,
        sample_column,
        feature_id_column,
        peptide_column,
        intensity_column,
        protein_refs_column,
        charge_column,
        mz_column,
        retention_time_column,
        missing_reason_column,
        protein_separator,
        design_path,
        entity_ids,
        protein_refs,
        min_observed_fraction,
        max_entities,
        z_score,
        missing_value_policy,
        summary_tsv_out,
        matrix_tsv_out,
        row_metadata_tsv_out,
        column_metadata_tsv_out,
        out_path,
    )


@click.command("power-estimate")
@click.argument(
    "input_table", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--entity-level",
    type=_quant_entity_level_choice(),
    default=QuantEntityLevel.PROTEIN.value,
    show_default=True,
)
@click.option(
    "--aggregation",
    type=_quant_rollup_choice(),
    default=QuantRollupMethod.SUM.value,
    show_default=True,
)
@click.option("--top-n", type=int, default=3, show_default=True)
@click.option(
    "--normalization",
    type=_normalization_choice(),
    default=NormalizationMethod.MEDIAN.value,
    show_default=True,
)
@click.option("--sample-column", default="sample_id", show_default=True)
@click.option("--feature-id-column", default="feature_id", show_default=True)
@click.option("--peptide-column", default="peptide", show_default=True)
@click.option("--intensity-column", default="intensity", show_default=True)
@click.option("--protein-refs-column", default="proteins", show_default=True)
@click.option("--charge-column", default="charge", show_default=True)
@click.option("--mz-column", default="mz", show_default=True)
@click.option(
    "--retention-time-column", default="retention_time_seconds", show_default=True
)
@click.option("--missing-reason-column", default="missing_reason", show_default=True)
@click.option("--protein-separator", default=";", show_default=True)
@click.option(
    "--design",
    "design_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option("--fdr-target", type=float, default=0.05, show_default=True)
@click.option("--target-power", type=float, default=0.8, show_default=True)
@click.option(
    "--replicates-per-condition",
    "replicate_counts",
    type=int,
    multiple=True,
)
@click.option(
    "--summary-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--variance-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--effect-size-grid-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def power_estimate_command(
    input_table: Path,
    entity_level: str,
    aggregation: str,
    top_n: int,
    normalization: str,
    sample_column: str,
    feature_id_column: str,
    peptide_column: str,
    intensity_column: str,
    protein_refs_column: str | None,
    charge_column: str | None,
    mz_column: str | None,
    retention_time_column: str | None,
    missing_reason_column: str | None,
    protein_separator: str,
    design_path: Path | None,
    fdr_target: float,
    target_power: float,
    replicate_counts: tuple[int, ...],
    summary_tsv_out: Path | None,
    variance_tsv_out: Path | None,
    effect_size_grid_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    "Estimate pilot variance and detectable effect sizes across replicate counts."
    return run_power_estimate_command(
        input_table,
        entity_level,
        aggregation,
        top_n,
        normalization,
        sample_column,
        feature_id_column,
        peptide_column,
        intensity_column,
        protein_refs_column,
        charge_column,
        mz_column,
        retention_time_column,
        missing_reason_column,
        protein_separator,
        design_path,
        fdr_target,
        target_power,
        replicate_counts,
        summary_tsv_out,
        variance_tsv_out,
        effect_size_grid_tsv_out,
        out_path,
    )


@click.command("sample-exploration")
@click.argument(
    "input_table", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--entity-level",
    type=_quant_entity_level_choice(),
    default=QuantEntityLevel.PROTEIN.value,
    show_default=True,
)
@click.option(
    "--aggregation",
    type=_quant_rollup_choice(),
    default=QuantRollupMethod.SUM.value,
    show_default=True,
)
@click.option("--top-n", type=int, default=3, show_default=True)
@click.option(
    "--normalization",
    type=_normalization_choice(),
    default=NormalizationMethod.MEDIAN.value,
    show_default=True,
)
@click.option("--sample-column", default="sample_id", show_default=True)
@click.option("--feature-id-column", default="feature_id", show_default=True)
@click.option("--peptide-column", default="peptide", show_default=True)
@click.option("--intensity-column", default="intensity", show_default=True)
@click.option("--protein-refs-column", default="proteins", show_default=True)
@click.option("--charge-column", default="charge", show_default=True)
@click.option(
    "--retention-time-column", default="retention_time_seconds", show_default=True
)
@click.option("--mz-column", default="mz", show_default=True)
@click.option("--missing-reason-column", default="missing_reason", show_default=True)
@click.option("--protein-separator", default=";", show_default=True)
@click.option(
    "--design",
    "design_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--summary-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--scores-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--explained-variance-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--distances-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--correlations-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--clusters-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--outliers-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def sample_exploration_command(
    input_table: Path,
    entity_level: str,
    aggregation: str,
    top_n: int,
    normalization: str,
    sample_column: str,
    feature_id_column: str,
    peptide_column: str,
    intensity_column: str,
    protein_refs_column: str | None,
    charge_column: str | None,
    retention_time_column: str | None,
    mz_column: str | None,
    missing_reason_column: str | None,
    protein_separator: str,
    design_path: Path | None,
    summary_tsv_out: Path | None,
    scores_tsv_out: Path | None,
    explained_variance_tsv_out: Path | None,
    distances_tsv_out: Path | None,
    correlations_tsv_out: Path | None,
    clusters_tsv_out: Path | None,
    outliers_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    "Prepare sample-level PCA, correlation, distance, clustering, and outlier outputs."
    return run_sample_exploration_command(
        input_table,
        entity_level,
        aggregation,
        top_n,
        normalization,
        sample_column,
        feature_id_column,
        peptide_column,
        intensity_column,
        protein_refs_column,
        charge_column,
        retention_time_column,
        mz_column,
        missing_reason_column,
        protein_separator,
        design_path,
        summary_tsv_out,
        scores_tsv_out,
        explained_variance_tsv_out,
        distances_tsv_out,
        correlations_tsv_out,
        clusters_tsv_out,
        outliers_tsv_out,
        out_path,
    )


COMMANDS = (
    heatmap_matrix_command,
    power_estimate_command,
    sample_exploration_command,
)

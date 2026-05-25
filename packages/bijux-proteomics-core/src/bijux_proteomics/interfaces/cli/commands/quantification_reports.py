# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi
# ruff: noqa: F401,F403,F405

"""Heatmap, power, and sample exploration CLI commands."""

from __future__ import annotations

from bijux_proteomics.interfaces.cli.support import *  # noqa: F401,F403,F405

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
    'Prepare one normalized matrix for heatmaps and clustering.'
    return run_heatmap_matrix_command(input_table, entity_level, aggregation, top_n, normalization, sample_column, feature_id_column, peptide_column, intensity_column, protein_refs_column, charge_column, mz_column, retention_time_column, missing_reason_column, protein_separator, design_path, entity_ids, protein_refs, min_observed_fraction, max_entities, z_score, missing_value_policy, summary_tsv_out, matrix_tsv_out, row_metadata_tsv_out, column_metadata_tsv_out, out_path)

def run_heatmap_matrix_command(
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
    try:
        mapping = Ms1FeatureColumnMapping(
            sample_id=sample_column,
            feature_id=feature_id_column,
            peptide=peptide_column,
            intensity=intensity_column,
            protein_refs=protein_refs_column,
            charge=charge_column,
            mz=mz_column,
            retention_time_seconds=retention_time_column,
            missing_reason=missing_reason_column,
            protein_separator=protein_separator,
        )
        parse_report = parse_ms1_feature_table(input_table, mapping=mapping)
        design_entries: tuple[ExperimentalDesignEntry, ...] = ()
        if design_path is not None:
            design_report = parse_experimental_design_table(design_path)
            if design_report.rejected_rows:
                raise click.ClickException("design table contains rejected rows")
            design_entries = design_report.accepted_entries
        raw_table = build_label_free_intensity_table(
            parse_report.accepted_records,
            entity_level=QuantEntityLevel(entity_level),
            aggregation_method=QuantRollupMethod(aggregation),
            top_n=top_n,
        )
        report = build_heatmap_preparation_report(
            normalize_label_free_table(
                raw_table,
                method=NormalizationMethod(normalization),
            ),
            design_entries=design_entries,
            policy=HeatmapPreparationPolicy(
                entity_ids=tuple(dict.fromkeys(entity_ids)),
                protein_refs=tuple(dict.fromkeys(protein_refs)),
                min_observed_fraction=min_observed_fraction,
                max_entity_count=max_entities,
                z_score_rows=z_score,
                missing_value_policy=HeatmapMissingValuePolicy(
                    missing_value_policy.lower()
                ),
            ),
        )
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        export_heatmap_summary_tsv(report, summary_tsv_out)
    if matrix_tsv_out is not None:
        export_heatmap_matrix_tsv(report, matrix_tsv_out)
    if row_metadata_tsv_out is not None:
        export_heatmap_row_metadata_tsv(report, row_metadata_tsv_out)
    if column_metadata_tsv_out is not None:
        export_heatmap_column_metadata_tsv(report, column_metadata_tsv_out)

    _emit_json(
        {
            "accepted_features": len(parse_report.accepted_records),
            "rejected_features": len(parse_report.rejected_rows),
            "heatmap_report": report.to_dict(),
            "outputs": {
                "summary_tsv": (
                    None if summary_tsv_out is None else str(summary_tsv_out)
                ),
                "matrix_tsv": None if matrix_tsv_out is None else str(matrix_tsv_out),
                "row_metadata_tsv": (
                    None
                    if row_metadata_tsv_out is None
                    else str(row_metadata_tsv_out)
                ),
                "column_metadata_tsv": (
                    None
                    if column_metadata_tsv_out is None
                    else str(column_metadata_tsv_out)
                ),
            },
        },
        out_path=out_path,
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
    'Estimate pilot variance and detectable effect sizes across replicate counts.'
    return run_power_estimate_command(input_table, entity_level, aggregation, top_n, normalization, sample_column, feature_id_column, peptide_column, intensity_column, protein_refs_column, charge_column, mz_column, retention_time_column, missing_reason_column, protein_separator, design_path, fdr_target, target_power, replicate_counts, summary_tsv_out, variance_tsv_out, effect_size_grid_tsv_out, out_path)

def run_power_estimate_command(
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
    try:
        mapping = Ms1FeatureColumnMapping(
            sample_id=sample_column,
            feature_id=feature_id_column,
            peptide=peptide_column,
            intensity=intensity_column,
            protein_refs=protein_refs_column,
            charge=charge_column,
            mz=mz_column,
            retention_time_seconds=retention_time_column,
            missing_reason=missing_reason_column,
            protein_separator=protein_separator,
        )
        parse_report = parse_ms1_feature_table(input_table, mapping=mapping)
        design_entries: tuple[ExperimentalDesignEntry, ...] = ()
        if design_path is not None:
            design_report = parse_experimental_design_table(design_path)
            if design_report.rejected_rows:
                raise click.ClickException("design table contains rejected rows")
            design_entries = design_report.accepted_entries
        raw_table = build_label_free_intensity_table(
            parse_report.accepted_records,
            entity_level=QuantEntityLevel(entity_level),
            aggregation_method=QuantRollupMethod(aggregation),
            top_n=top_n,
        )
        report = build_power_estimation_report(
            normalize_label_free_table(
                raw_table,
                method=NormalizationMethod(normalization),
            ),
            design_entries,
            policy=PowerEstimationPolicy(
                fdr_target=fdr_target,
                target_power=target_power,
                candidate_replicates_per_condition=replicate_counts,
            ),
        )
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        export_power_estimation_summary_tsv(report, summary_tsv_out)
    if variance_tsv_out is not None:
        export_power_variance_tsv(report, variance_tsv_out)
    if effect_size_grid_tsv_out is not None:
        export_power_effect_size_grid_tsv(report, effect_size_grid_tsv_out)

    _emit_json(
        {
            "accepted_features": len(parse_report.accepted_records),
            "rejected_features": len(parse_report.rejected_rows),
            "power_estimation_report": report.to_dict(),
            "outputs": {
                "summary_tsv": (
                    None if summary_tsv_out is None else str(summary_tsv_out)
                ),
                "variance_tsv": (
                    None if variance_tsv_out is None else str(variance_tsv_out)
                ),
                "effect_size_grid_tsv": (
                    None
                    if effect_size_grid_tsv_out is None
                    else str(effect_size_grid_tsv_out)
                ),
            },
        },
        out_path=out_path,
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
    'Prepare sample-level PCA, correlation, distance, clustering, and outlier outputs.'
    return run_sample_exploration_command(input_table, entity_level, aggregation, top_n, normalization, sample_column, feature_id_column, peptide_column, intensity_column, protein_refs_column, charge_column, retention_time_column, mz_column, missing_reason_column, protein_separator, design_path, summary_tsv_out, scores_tsv_out, explained_variance_tsv_out, distances_tsv_out, correlations_tsv_out, clusters_tsv_out, outliers_tsv_out, out_path)

def run_sample_exploration_command(
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
    try:
        mapping = Ms1FeatureColumnMapping(
            sample_id=sample_column,
            feature_id=feature_id_column,
            peptide=peptide_column,
            intensity=intensity_column,
            protein_refs=protein_refs_column,
            charge=charge_column,
            mz=mz_column,
            retention_time_seconds=retention_time_column,
            missing_reason=missing_reason_column,
            protein_separator=protein_separator,
        )
        parse_report = parse_ms1_feature_table(input_table, mapping=mapping)
        design_entries: tuple[ExperimentalDesignEntry, ...] = ()
        if design_path is not None:
            design_report = parse_experimental_design_table(design_path)
            if design_report.rejected_rows:
                raise click.ClickException("design table contains rejected rows")
            design_entries = design_report.accepted_entries
        raw_table = build_label_free_intensity_table(
            parse_report.accepted_records,
            entity_level=QuantEntityLevel(entity_level),
            aggregation_method=QuantRollupMethod(aggregation),
            top_n=top_n,
        )
        report = build_sample_exploration_report(
            normalize_label_free_table(
                raw_table,
                method=NormalizationMethod(normalization),
            ),
            design_entries,
        )
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        export_sample_exploration_summary_tsv(report, summary_tsv_out)
    if scores_tsv_out is not None:
        export_sample_pca_scores_tsv(report, scores_tsv_out)
    if explained_variance_tsv_out is not None:
        export_sample_pca_variance_tsv(report, explained_variance_tsv_out)
    if distances_tsv_out is not None:
        export_sample_distance_tsv(report, distances_tsv_out)
    if correlations_tsv_out is not None:
        export_sample_correlation_tsv(report, correlations_tsv_out)
    if clusters_tsv_out is not None:
        export_sample_cluster_tsv(report, clusters_tsv_out)
    if outliers_tsv_out is not None:
        export_sample_outlier_tsv(report, outliers_tsv_out)

    _emit_json(
        {
            "accepted_features": len(parse_report.accepted_records),
            "rejected_features": len(parse_report.rejected_rows),
            "sample_exploration_report": report.to_dict(),
            "outputs": {
                "summary_tsv": (
                    None if summary_tsv_out is None else str(summary_tsv_out)
                ),
                "scores_tsv": None if scores_tsv_out is None else str(scores_tsv_out),
                "explained_variance_tsv": (
                    None
                    if explained_variance_tsv_out is None
                    else str(explained_variance_tsv_out)
                ),
                "distances_tsv": (
                    None if distances_tsv_out is None else str(distances_tsv_out)
                ),
                "correlations_tsv": (
                    None
                    if correlations_tsv_out is None
                    else str(correlations_tsv_out)
                ),
                "clusters_tsv": (
                    None if clusters_tsv_out is None else str(clusters_tsv_out)
                ),
                "outliers_tsv": (
                    None if outliers_tsv_out is None else str(outliers_tsv_out)
                ),
            },
        },
        out_path=out_path,
    )

COMMANDS = (
    heatmap_matrix_command,
    power_estimate_command,
    sample_exploration_command,
)

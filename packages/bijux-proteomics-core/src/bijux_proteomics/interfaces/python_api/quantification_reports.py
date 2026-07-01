# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi
"""Heatmap, power, and sample exploration Python API entrypoints."""

from __future__ import annotations

from bijux_proteomics.interfaces.support.foundation import (
    Path,
    click,
)
from bijux_proteomics.interfaces.support.io_and_dia import (
    ExperimentalDesignEntry,
    parse_experimental_design_table,
)
from bijux_proteomics.interfaces.support.output_protocol.artifact_output import (
    _emit_json,
)
from bijux_proteomics.interfaces.support.ptm_quantification.quantification import (
    HeatmapMissingValuePolicy,
    HeatmapPreparationPolicy,
    Ms1FeatureColumnMapping,
    NormalizationMethod,
    PowerEstimationPolicy,
    QuantEntityLevel,
    QuantRollupMethod,
    build_heatmap_preparation_report,
    build_label_free_intensity_table,
    build_power_estimation_report,
    build_sample_exploration_report,
    export_heatmap_column_metadata_tsv,
    export_heatmap_matrix_tsv,
    export_heatmap_row_metadata_tsv,
    export_heatmap_summary_tsv,
    export_power_effect_size_grid_tsv,
    export_power_estimation_summary_tsv,
    export_power_variance_tsv,
    export_sample_cluster_tsv,
    export_sample_correlation_tsv,
    export_sample_distance_tsv,
    export_sample_exploration_summary_tsv,
    export_sample_outlier_tsv,
    export_sample_pca_scores_tsv,
    export_sample_pca_variance_tsv,
    normalize_label_free_table,
    parse_ms1_feature_table,
)


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
                    None if row_metadata_tsv_out is None else str(row_metadata_tsv_out)
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
                    None if correlations_tsv_out is None else str(correlations_tsv_out)
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


__all__ = [
    "run_heatmap_matrix_command",
    "run_power_estimate_command",
    "run_sample_exploration_command",
]

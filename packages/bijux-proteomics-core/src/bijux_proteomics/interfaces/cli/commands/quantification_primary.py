# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi
# ruff: noqa: F401,F403,F405

"""Primary quantification CLI commands."""

from __future__ import annotations

from pathlib import Path

import click

from bijux_proteomics.interfaces.python_api.quantification_primary import (
    run_quantify_command,
)
from bijux_proteomics.interfaces.support import *  # noqa: F401,F403,F405


@click.command("quantify")
@click.argument(
    "input_table", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--measure",
    type=_quant_measure_choice(),
    default=QuantMeasureKind.INTENSITY.value,
    show_default=True,
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
@click.option(
    "--imputation",
    type=_imputation_choice(),
    default=ImputationMethod.NONE.value,
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
@click.option("--condition-a", default=None)
@click.option("--condition-b", default=None)
@click.option(
    "--differential-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--broken-pairs-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--multi-contrast-consistency-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--batch-effect-summary-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--batch-effect-batches-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--batch-effect-components-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--time-course-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--design-covariate",
    "design_covariates",
    multiple=True,
)
@click.option(
    "--design-batch-field",
    default="batch",
    show_default=True,
)
@click.option(
    "--design-pairing-field",
    default=None,
)
@click.option(
    "--design-timepoint-field",
    default=None,
)
@click.option(
    "--design-timepoint-order-file",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--design-matrix-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--design-coefficients-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--design-contrasts-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--limma-assay-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--limma-samples-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--limma-design-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--limma-contrasts-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--msstats-input-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--limma-results",
    "limma_results_path",
    type=click.Path(exists=True, path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--msstats-results",
    "msstats_results_path",
    type=click.Path(exists=True, path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--report-out", type=click.Path(path_type=Path, dir_okay=False), default=None
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
    help="Optional JSON report output path.",
)
def quantify_command(
    input_table: Path,
    measure: str,
    entity_level: str,
    aggregation: str,
    top_n: int,
    normalization: str,
    imputation: str,
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
    condition_a: str | None,
    condition_b: str | None,
    differential_tsv_out: Path | None,
    broken_pairs_tsv_out: Path | None,
    multi_contrast_consistency_tsv_out: Path | None,
    batch_effect_summary_tsv_out: Path | None,
    batch_effect_batches_tsv_out: Path | None,
    batch_effect_components_tsv_out: Path | None,
    time_course_tsv_out: Path | None,
    design_covariates: tuple[str, ...],
    design_batch_field: str,
    design_pairing_field: str | None,
    design_timepoint_field: str | None,
    design_timepoint_order_file: Path | None,
    design_matrix_tsv_out: Path | None,
    design_coefficients_tsv_out: Path | None,
    design_contrasts_tsv_out: Path | None,
    limma_assay_tsv_out: Path | None,
    limma_samples_tsv_out: Path | None,
    limma_design_tsv_out: Path | None,
    limma_contrasts_tsv_out: Path | None,
    msstats_input_tsv_out: Path | None,
    limma_results_path: Path | None,
    msstats_results_path: Path | None,
    report_out: Path | None,
    out_path: Path | None,
) -> None:
    "Build a quantification matrix and optional differential report from MS1 features."
    return run_quantify_command(
        input_table,
        measure,
        entity_level,
        aggregation,
        top_n,
        normalization,
        imputation,
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
        condition_a,
        condition_b,
        differential_tsv_out,
        broken_pairs_tsv_out,
        multi_contrast_consistency_tsv_out,
        batch_effect_summary_tsv_out,
        batch_effect_batches_tsv_out,
        batch_effect_components_tsv_out,
        time_course_tsv_out,
        design_covariates,
        design_batch_field,
        design_pairing_field,
        design_timepoint_field,
        design_timepoint_order_file,
        design_matrix_tsv_out,
        design_coefficients_tsv_out,
        design_contrasts_tsv_out,
        limma_assay_tsv_out,
        limma_samples_tsv_out,
        limma_design_tsv_out,
        limma_contrasts_tsv_out,
        msstats_input_tsv_out,
        limma_results_path,
        msstats_results_path,
        report_out,
        out_path,
    )


COMMANDS = (quantify_command,)

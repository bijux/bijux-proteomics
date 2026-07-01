# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Differential review CLI commands."""

from __future__ import annotations

from pathlib import Path

import click

from bijux_proteomics.interfaces.python_api.differential_analysis import (
    run_dia_dda_compare_command,
    run_dia_differential_command,
    run_target_panel_review_command,
)
from bijux_proteomics.interfaces.support.io_and_dia import TargetPanelSourceKind
from bijux_proteomics.interfaces.support.ptm_quantification.quantification import (
    NormalizationMethod,
)
from bijux_proteomics.interfaces.support.sequence_support.cli_choices import (
    _normalization_choice,
)
from bijux_proteomics.interfaces.support.workflow import DiaDifferentialSourceKind


@click.command("dia-differential")
@click.argument(
    "input_path", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument(
    "design_path", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--source-kind",
    type=click.Choice([kind.value for kind in DiaDifferentialSourceKind]),
    required=True,
)
@click.option(
    "--config",
    "config_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option("--max-q-value", type=float, default=0.01, show_default=True)
@click.option(
    "--normalization",
    type=_normalization_choice(),
    default=NormalizationMethod.MEDIAN.value,
    show_default=True,
)
@click.option("--condition-a", default=None)
@click.option("--condition-b", default=None)
@click.option("--design-batch-field", default="batch", show_default=True)
@click.option("--design-pairing-field", default=None)
@click.option("--design-covariate", "design_covariates", multiple=True)
@click.option("--matrix-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option(
    "--normalized-matrix-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
)
@click.option("--differential-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--qc-summary-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option(
    "--design-matrix-tsv-out", type=click.Path(path_type=Path, dir_okay=False)
)
@click.option(
    "--design-coefficients-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
)
@click.option("--volcano-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--volcano-json-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--volcano-svg-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--volcano-html-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option(
    "--volcano-adjusted-p-value-threshold",
    type=float,
    default=0.1,
    show_default=True,
)
@click.option(
    "--volcano-absolute-log2-fold-change-threshold",
    type=float,
    default=1.0,
    show_default=True,
)
@click.option(
    "--volcano-top-label-count",
    type=int,
    default=10,
    show_default=True,
)
@click.option(
    "--sample-balance-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def dia_differential_command(
    input_path: Path,
    design_path: Path,
    source_kind: str,
    config_path: Path | None,
    max_q_value: float,
    normalization: str,
    condition_a: str | None,
    condition_b: str | None,
    design_batch_field: str,
    design_pairing_field: str | None,
    design_covariates: tuple[str, ...],
    matrix_tsv_out: Path | None,
    normalized_matrix_tsv_out: Path | None,
    differential_tsv_out: Path | None,
    qc_summary_tsv_out: Path | None,
    design_matrix_tsv_out: Path | None,
    design_coefficients_tsv_out: Path | None,
    volcano_tsv_out: Path | None,
    volcano_json_out: Path | None,
    volcano_svg_out: Path | None,
    volcano_html_out: Path | None,
    volcano_adjusted_p_value_threshold: float,
    volcano_absolute_log2_fold_change_threshold: float,
    volcano_top_label_count: int,
    sample_balance_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    """Run DIA-native differential analysis from DIA-NN or Spectronaut evidence."""
    return run_dia_differential_command(
        input_path,
        design_path,
        source_kind,
        config_path,
        max_q_value,
        normalization,
        condition_a,
        condition_b,
        design_batch_field,
        design_pairing_field,
        design_covariates,
        matrix_tsv_out,
        normalized_matrix_tsv_out,
        differential_tsv_out,
        qc_summary_tsv_out,
        design_matrix_tsv_out,
        design_coefficients_tsv_out,
        volcano_tsv_out,
        volcano_json_out,
        volcano_svg_out,
        volcano_html_out,
        volcano_adjusted_p_value_threshold,
        volcano_absolute_log2_fold_change_threshold,
        volcano_top_label_count,
        sample_balance_tsv_out,
        out_path,
    )


@click.command("dia-dda-compare")
@click.argument(
    "diann_report_path", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument(
    "dda_psm_path", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option("--max-q-value", type=float, default=0.05, show_default=True)
@click.option(
    "--dia-differential-tsv",
    "dia_differential_tsv_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
)
@click.option(
    "--dda-differential-tsv",
    "dda_differential_tsv_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
)
@click.option(
    "--differential-significance-threshold",
    type=float,
    default=0.05,
    show_default=True,
)
@click.option("--summary-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option(
    "--protein-overlap-tsv-out", type=click.Path(path_type=Path, dir_okay=False)
)
@click.option(
    "--peptide-overlap-tsv-out", type=click.Path(path_type=Path, dir_okay=False)
)
@click.option("--correlation-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--exclusive-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--conflicts-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--differential-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def dia_dda_compare_command(
    diann_report_path: Path,
    dda_psm_path: Path,
    max_q_value: float,
    dia_differential_tsv_path: Path | None,
    dda_differential_tsv_path: Path | None,
    differential_significance_threshold: float,
    summary_tsv_out: Path | None,
    protein_overlap_tsv_out: Path | None,
    peptide_overlap_tsv_out: Path | None,
    correlation_tsv_out: Path | None,
    exclusive_tsv_out: Path | None,
    conflicts_tsv_out: Path | None,
    differential_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    """Compare DIA-NN and DDA evidence, conflicts, and optional differential results."""
    return run_dia_dda_compare_command(
        diann_report_path,
        dda_psm_path,
        max_q_value,
        dia_differential_tsv_path,
        dda_differential_tsv_path,
        differential_significance_threshold,
        summary_tsv_out,
        protein_overlap_tsv_out,
        peptide_overlap_tsv_out,
        correlation_tsv_out,
        exclusive_tsv_out,
        conflicts_tsv_out,
        differential_tsv_out,
        out_path,
    )


@click.command("target-panel-review")
@click.argument(
    "input_path", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument(
    "panel_path", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--source-kind",
    type=click.Choice([kind.value for kind in TargetPanelSourceKind]),
    required=True,
)
@click.option(
    "--config",
    "config_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--include-decoys/--exclude-decoys",
    default=False,
    show_default=True,
)
@click.option("--max-q-value", type=float, default=None)
@click.option("--summary-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--target-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--missing-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--intensity-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--matrix-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def target_panel_review_command(
    input_path: Path,
    panel_path: Path,
    source_kind: str,
    config_path: Path | None,
    include_decoys: bool,
    max_q_value: float | None,
    summary_tsv_out: Path | None,
    target_tsv_out: Path | None,
    missing_tsv_out: Path | None,
    intensity_tsv_out: Path | None,
    matrix_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    """Review a user-defined peptide or protein panel against DIA or LFQ matrices."""
    return run_target_panel_review_command(
        input_path,
        panel_path,
        source_kind,
        config_path,
        include_decoys,
        max_q_value,
        summary_tsv_out,
        target_tsv_out,
        missing_tsv_out,
        intensity_tsv_out,
        matrix_tsv_out,
        out_path,
    )


COMMANDS = (
    dia_differential_command,
    dia_dda_compare_command,
    target_panel_review_command,
)

# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Multiplex ratio and differential CLI commands."""

from __future__ import annotations

from pathlib import Path

import click

from bijux_proteomics.interfaces.python_api.multiplex_analysis import (
    run_tmt_differential_command,
    run_tmt_integrate_plexes_command,
    run_tmt_ratio_command,
    run_tmt_report_command,
)
from bijux_proteomics.interfaces.support.multiplex_targeted import (
    TmtNormalizationMethod,
    TmtSearchResultSourceKind,
)
from bijux_proteomics.interfaces.support.ptm_quantification import NormalizationMethod
from bijux_proteomics.interfaces.support.sequence_support.cli_choices import (
    _label_based_differential_normalization_choice,
    _tmt_normalization_method_choice,
    _tmt_ratio_normalization_choice,
    _tmt_source_kind_choice,
)


@click.command("tmt-ratios")
@click.argument(
    "input_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument(
    "design_path", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--control-channel",
    required=True,
)
@click.option(
    "--source-kind",
    type=_tmt_source_kind_choice(),
    default=TmtSearchResultSourceKind.MAXQUANT.value,
    show_default=True,
)
@click.option(
    "--normalization-method",
    type=_tmt_ratio_normalization_choice(),
    default="none",
    show_default=True,
)
@click.option("--row-id-column", default=None)
@click.option("--peptide-column", default=None)
@click.option("--protein-refs-column", default=None)
@click.option("--multiplex-group-column", default=None)
@click.option("--default-multiplex-group", default=None)
@click.option("--protein-separator", default=";", show_default=True)
@click.option("--channel-column", "channel_columns", multiple=True)
@click.option("--summary-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option(
    "--peptide-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
)
@click.option(
    "--protein-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def tmt_ratio_command(
    input_tsv: Path,
    design_path: Path,
    control_channel: str,
    source_kind: str,
    normalization_method: str,
    row_id_column: str | None,
    peptide_column: str | None,
    protein_refs_column: str | None,
    multiplex_group_column: str | None,
    default_multiplex_group: str | None,
    protein_separator: str,
    channel_columns: tuple[str, ...],
    summary_tsv_out: Path | None,
    peptide_tsv_out: Path | None,
    protein_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    """Compute governed TMT sample/control ratios across multiplex channels."""
    return run_tmt_ratio_command(
        input_tsv,
        design_path,
        control_channel,
        source_kind,
        normalization_method,
        row_id_column,
        peptide_column,
        protein_refs_column,
        multiplex_group_column,
        default_multiplex_group,
        protein_separator,
        channel_columns,
        summary_tsv_out,
        peptide_tsv_out,
        protein_tsv_out,
        out_path,
    )


@click.command("tmt-integrate-plexes")
@click.argument(
    "input_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument(
    "design_path", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--source-kind",
    type=_tmt_source_kind_choice(),
    default=TmtSearchResultSourceKind.MAXQUANT.value,
    show_default=True,
)
@click.option(
    "--plex-effect-ratio-threshold",
    default=1.25,
    show_default=True,
    type=float,
)
@click.option("--row-id-column", default=None)
@click.option("--peptide-column", default=None)
@click.option("--protein-refs-column", default=None)
@click.option("--multiplex-group-column", default=None)
@click.option("--default-multiplex-group", default=None)
@click.option("--protein-separator", default=";", show_default=True)
@click.option("--channel-column", "channel_columns", multiple=True)
@click.option("--summary-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--alignment-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--plex-effect-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option(
    "--protein-matrix-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def tmt_integrate_plexes_command(
    input_tsv: Path,
    design_path: Path,
    source_kind: str,
    plex_effect_ratio_threshold: float,
    row_id_column: str | None,
    peptide_column: str | None,
    protein_refs_column: str | None,
    multiplex_group_column: str | None,
    default_multiplex_group: str | None,
    protein_separator: str,
    channel_columns: tuple[str, ...],
    summary_tsv_out: Path | None,
    alignment_tsv_out: Path | None,
    plex_effect_tsv_out: Path | None,
    protein_matrix_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    """Integrate multiple TMT plexes through bridge-normalized protein matrices."""
    return run_tmt_integrate_plexes_command(
        input_tsv,
        design_path,
        source_kind,
        plex_effect_ratio_threshold,
        row_id_column,
        peptide_column,
        protein_refs_column,
        multiplex_group_column,
        default_multiplex_group,
        protein_separator,
        channel_columns,
        summary_tsv_out,
        alignment_tsv_out,
        plex_effect_tsv_out,
        protein_matrix_tsv_out,
        out_path,
    )


@click.command("tmt-differential")
@click.argument(
    "input_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument(
    "design_path", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--source-kind",
    type=_tmt_source_kind_choice(),
    default=TmtSearchResultSourceKind.MAXQUANT.value,
    show_default=True,
)
@click.option(
    "--normalization-method",
    type=_label_based_differential_normalization_choice(),
    default=NormalizationMethod.MEDIAN.value,
    show_default=True,
)
@click.option("--condition-a", default=None)
@click.option("--condition-b", default=None)
@click.option("--batch-field", default="batch", show_default=True)
@click.option("--covariate-field", "covariate_fields", multiple=True)
@click.option("--pairing-field", default=None)
@click.option("--row-id-column", default=None)
@click.option("--peptide-column", default=None)
@click.option("--protein-refs-column", default=None)
@click.option("--multiplex-group-column", default=None)
@click.option("--default-multiplex-group", default=None)
@click.option("--protein-separator", default=";", show_default=True)
@click.option("--channel-column", "channel_columns", multiple=True)
@click.option(
    "--raw-matrix-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
)
@click.option(
    "--normalized-matrix-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
)
@click.option(
    "--results-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
)
@click.option(
    "--balance-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
)
@click.option(
    "--volcano-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
)
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
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def tmt_differential_command(
    input_tsv: Path,
    design_path: Path,
    source_kind: str,
    normalization_method: str,
    condition_a: str | None,
    condition_b: str | None,
    batch_field: str,
    covariate_fields: tuple[str, ...],
    pairing_field: str | None,
    row_id_column: str | None,
    peptide_column: str | None,
    protein_refs_column: str | None,
    multiplex_group_column: str | None,
    default_multiplex_group: str | None,
    protein_separator: str,
    channel_columns: tuple[str, ...],
    raw_matrix_tsv_out: Path | None,
    normalized_matrix_tsv_out: Path | None,
    results_tsv_out: Path | None,
    balance_tsv_out: Path | None,
    volcano_tsv_out: Path | None,
    volcano_json_out: Path | None,
    volcano_svg_out: Path | None,
    volcano_html_out: Path | None,
    volcano_adjusted_p_value_threshold: float,
    volcano_absolute_log2_fold_change_threshold: float,
    volcano_top_label_count: int,
    out_path: Path | None,
) -> None:
    """Run differential analysis over governed TMT protein matrices."""
    return run_tmt_differential_command(
        input_tsv,
        design_path,
        source_kind,
        normalization_method,
        condition_a,
        condition_b,
        batch_field,
        covariate_fields,
        pairing_field,
        row_id_column,
        peptide_column,
        protein_refs_column,
        multiplex_group_column,
        default_multiplex_group,
        protein_separator,
        channel_columns,
        raw_matrix_tsv_out,
        normalized_matrix_tsv_out,
        results_tsv_out,
        balance_tsv_out,
        volcano_tsv_out,
        volcano_json_out,
        volcano_svg_out,
        volcano_html_out,
        volcano_adjusted_p_value_threshold,
        volcano_absolute_log2_fold_change_threshold,
        volcano_top_label_count,
        out_path,
    )


@click.command("tmt-report")
@click.argument(
    "input_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument(
    "design_path", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--control-channel",
    required=True,
)
@click.option(
    "--source-kind",
    type=_tmt_source_kind_choice(),
    default=TmtSearchResultSourceKind.MAXQUANT.value,
    show_default=True,
)
@click.option(
    "--channel-normalization-method",
    type=_tmt_normalization_method_choice(),
    default=TmtNormalizationMethod.MEDIAN.value,
    show_default=True,
)
@click.option(
    "--differential-normalization-method",
    type=_label_based_differential_normalization_choice(),
    default=NormalizationMethod.MEDIAN.value,
    show_default=True,
)
@click.option("--condition-a", default=None)
@click.option("--condition-b", default=None)
@click.option("--batch-field", default="batch", show_default=True)
@click.option("--covariate-field", "covariate_fields", multiple=True)
@click.option("--pairing-field", default=None)
@click.option("--row-id-column", default=None)
@click.option("--peptide-column", default=None)
@click.option("--protein-refs-column", default=None)
@click.option("--multiplex-group-column", default=None)
@click.option("--default-multiplex-group", default=None)
@click.option("--protein-separator", default=";", show_default=True)
@click.option("--channel-column", "channel_columns", multiple=True)
@click.option(
    "--output-dir",
    required=True,
    type=click.Path(path_type=Path, file_okay=False),
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def tmt_report_command(
    input_tsv: Path,
    design_path: Path,
    control_channel: str,
    source_kind: str,
    channel_normalization_method: str,
    differential_normalization_method: str,
    condition_a: str | None,
    condition_b: str | None,
    batch_field: str,
    covariate_fields: tuple[str, ...],
    pairing_field: str | None,
    row_id_column: str | None,
    peptide_column: str | None,
    protein_refs_column: str | None,
    multiplex_group_column: str | None,
    default_multiplex_group: str | None,
    protein_separator: str,
    channel_columns: tuple[str, ...],
    output_dir: Path,
    out_path: Path | None,
) -> None:
    """Build a governed TMT report directory with channel quality, ratios, and protein changes."""
    return run_tmt_report_command(
        input_tsv,
        design_path,
        control_channel,
        source_kind,
        channel_normalization_method,
        differential_normalization_method,
        condition_a,
        condition_b,
        batch_field,
        covariate_fields,
        pairing_field,
        row_id_column,
        peptide_column,
        protein_refs_column,
        multiplex_group_column,
        default_multiplex_group,
        protein_separator,
        channel_columns,
        output_dir,
        out_path,
    )


COMMANDS = (
    tmt_ratio_command,
    tmt_integrate_plexes_command,
    tmt_differential_command,
    tmt_report_command,
)

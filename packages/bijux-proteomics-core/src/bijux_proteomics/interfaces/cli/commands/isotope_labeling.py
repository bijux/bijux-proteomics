# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Stable-isotope labeling CLI commands."""

from __future__ import annotations

from pathlib import Path

import click

from bijux_proteomics.interfaces.python_api.isotope_labeling import (
    run_silac_differential_command,
    run_silac_quantify_command,
    run_silac_report_command,
    run_silac_validate_command,
    run_tmt_validate_command,
)
from bijux_proteomics.interfaces.support.multiplex_targeted import (
    SilacLabel,
    TmtSearchResultSourceKind,
)
from bijux_proteomics.interfaces.support.ptm_quantification.quantification import (
    NormalizationMethod,
)
from bijux_proteomics.interfaces.support.sequence_support.cli_choices import (
    _label_based_differential_normalization_choice,
    _silac_label_choice,
    _tmt_source_kind_choice,
)


@click.command("silac-quantify")
@click.argument(
    "input_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option("--sample-id-column", default="sample_id", show_default=True)
@click.option("--peptide-column", default="peptide", show_default=True)
@click.option("--protein-refs-column", default="protein_refs", show_default=True)
@click.option("--charge-column", default="charge", show_default=True)
@click.option("--label-column", default="label", show_default=True)
@click.option("--intensity-column", default="intensity", show_default=True)
@click.option("--feature-id-column", default="feature_id", show_default=True)
@click.option("--protein-separator", default=";", show_default=True)
@click.option("--labels", default="light,heavy", show_default=True)
@click.option(
    "--reference-label",
    type=_silac_label_choice(),
    default=SilacLabel.LIGHT.value,
    show_default=True,
)
@click.option("--collapse-charge-states", is_flag=True)
@click.option("--summary-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--peptide-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--protein-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def silac_quantify_command(
    input_tsv: Path,
    sample_id_column: str,
    peptide_column: str,
    protein_refs_column: str,
    charge_column: str,
    label_column: str,
    intensity_column: str,
    feature_id_column: str,
    protein_separator: str,
    labels: str,
    reference_label: str,
    collapse_charge_states: bool,
    summary_tsv_out: Path | None,
    peptide_tsv_out: Path | None,
    protein_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    """Quantify SILAC pair or triplet evidence from labeled feature tables."""
    return run_silac_quantify_command(
        input_tsv,
        sample_id_column,
        peptide_column,
        protein_refs_column,
        charge_column,
        label_column,
        intensity_column,
        feature_id_column,
        protein_separator,
        labels,
        reference_label,
        collapse_charge_states,
        summary_tsv_out,
        peptide_tsv_out,
        protein_tsv_out,
        out_path,
    )


@click.command("silac-differential")
@click.argument(
    "input_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument(
    "design_path", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option("--sample-id-column", default="sample_id", show_default=True)
@click.option("--peptide-column", default="peptide", show_default=True)
@click.option("--protein-refs-column", default="protein_refs", show_default=True)
@click.option("--charge-column", default="charge", show_default=True)
@click.option("--label-column", default="label", show_default=True)
@click.option("--intensity-column", default="intensity", show_default=True)
@click.option("--feature-id-column", default="feature_id", show_default=True)
@click.option("--protein-separator", default=";", show_default=True)
@click.option("--labels", default="light,heavy", show_default=True)
@click.option(
    "--reference-label",
    type=_silac_label_choice(),
    default=SilacLabel.LIGHT.value,
    show_default=True,
)
@click.option("--collapse-charge-states", is_flag=True)
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
def silac_differential_command(
    input_tsv: Path,
    design_path: Path,
    sample_id_column: str,
    peptide_column: str,
    protein_refs_column: str,
    charge_column: str,
    label_column: str,
    intensity_column: str,
    feature_id_column: str,
    protein_separator: str,
    labels: str,
    reference_label: str,
    collapse_charge_states: bool,
    normalization_method: str,
    condition_a: str | None,
    condition_b: str | None,
    batch_field: str,
    covariate_fields: tuple[str, ...],
    pairing_field: str | None,
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
    """Run differential analysis over governed SILAC protein ratios."""
    return run_silac_differential_command(
        input_tsv,
        design_path,
        sample_id_column,
        peptide_column,
        protein_refs_column,
        charge_column,
        label_column,
        intensity_column,
        feature_id_column,
        protein_separator,
        labels,
        reference_label,
        collapse_charge_states,
        normalization_method,
        condition_a,
        condition_b,
        batch_field,
        covariate_fields,
        pairing_field,
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


@click.command("silac-report")
@click.argument(
    "input_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument(
    "design_path", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option("--sample-id-column", default="sample_id", show_default=True)
@click.option("--peptide-column", default="peptide", show_default=True)
@click.option("--protein-refs-column", default="protein_refs", show_default=True)
@click.option("--charge-column", default="charge", show_default=True)
@click.option("--label-column", default="label", show_default=True)
@click.option("--intensity-column", default="intensity", show_default=True)
@click.option("--feature-id-column", default="feature_id", show_default=True)
@click.option("--protein-separator", default=";", show_default=True)
@click.option("--labels", default="light,heavy", show_default=True)
@click.option(
    "--reference-label",
    type=_silac_label_choice(),
    default=SilacLabel.LIGHT.value,
    show_default=True,
)
@click.option("--collapse-charge-states", is_flag=True)
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
def silac_report_command(
    input_tsv: Path,
    design_path: Path,
    sample_id_column: str,
    peptide_column: str,
    protein_refs_column: str,
    charge_column: str,
    label_column: str,
    intensity_column: str,
    feature_id_column: str,
    protein_separator: str,
    labels: str,
    reference_label: str,
    collapse_charge_states: bool,
    differential_normalization_method: str,
    condition_a: str | None,
    condition_b: str | None,
    batch_field: str,
    covariate_fields: tuple[str, ...],
    pairing_field: str | None,
    output_dir: Path,
    out_path: Path | None,
) -> None:
    """Build a governed SILAC report directory with ratios, QC, and differential results."""
    return run_silac_report_command(
        input_tsv,
        design_path,
        sample_id_column,
        peptide_column,
        protein_refs_column,
        charge_column,
        label_column,
        intensity_column,
        feature_id_column,
        protein_separator,
        labels,
        reference_label,
        collapse_charge_states,
        differential_normalization_method,
        condition_a,
        condition_b,
        batch_field,
        covariate_fields,
        pairing_field,
        output_dir,
        out_path,
    )


@click.command("silac-validate")
@click.argument(
    "input_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option("--sample-id-column", default="sample_id", show_default=True)
@click.option("--peptide-column", default="peptide", show_default=True)
@click.option("--protein-refs-column", default="protein_refs", show_default=True)
@click.option("--charge-column", default="charge", show_default=True)
@click.option("--label-column", default="label", show_default=True)
@click.option("--intensity-column", default="intensity", show_default=True)
@click.option("--feature-id-column", default="feature_id", show_default=True)
@click.option("--protein-separator", default=";", show_default=True)
@click.option("--labels", default="light,heavy", show_default=True)
@click.option("--collapse-charge-states", is_flag=True)
@click.option("--summary-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--label-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--distribution-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--weak-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def silac_validate_command(
    input_tsv: Path,
    sample_id_column: str,
    peptide_column: str,
    protein_refs_column: str,
    charge_column: str,
    label_column: str,
    intensity_column: str,
    feature_id_column: str,
    protein_separator: str,
    labels: str,
    collapse_charge_states: bool,
    summary_tsv_out: Path | None,
    label_tsv_out: Path | None,
    distribution_tsv_out: Path | None,
    weak_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    """Validate expected SILAC labels and weak labeling evidence."""
    return run_silac_validate_command(
        input_tsv,
        sample_id_column,
        peptide_column,
        protein_refs_column,
        charge_column,
        label_column,
        intensity_column,
        feature_id_column,
        protein_separator,
        labels,
        collapse_charge_states,
        summary_tsv_out,
        label_tsv_out,
        distribution_tsv_out,
        weak_tsv_out,
        out_path,
    )


@click.command("tmt-validate")
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
@click.option("--row-id-column", default=None)
@click.option("--peptide-column", default=None)
@click.option("--protein-refs-column", default=None)
@click.option("--multiplex-group-column", default=None)
@click.option("--default-multiplex-group", default=None)
@click.option("--protein-separator", default=";", show_default=True)
@click.option("--channel-column", "channel_columns", multiple=True)
@click.option("--summary-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--channel-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--distribution-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--weak-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def tmt_validate_command(
    input_tsv: Path,
    design_path: Path,
    source_kind: str,
    row_id_column: str | None,
    peptide_column: str | None,
    protein_refs_column: str | None,
    multiplex_group_column: str | None,
    default_multiplex_group: str | None,
    protein_separator: str,
    channel_columns: tuple[str, ...],
    summary_tsv_out: Path | None,
    channel_tsv_out: Path | None,
    distribution_tsv_out: Path | None,
    weak_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    """Validate expected TMT channels and weak reporter evidence."""
    return run_tmt_validate_command(
        input_tsv,
        design_path,
        source_kind,
        row_id_column,
        peptide_column,
        protein_refs_column,
        multiplex_group_column,
        default_multiplex_group,
        protein_separator,
        channel_columns,
        summary_tsv_out,
        channel_tsv_out,
        distribution_tsv_out,
        weak_tsv_out,
        out_path,
    )


COMMANDS = (
    silac_quantify_command,
    silac_differential_command,
    silac_report_command,
    silac_validate_command,
    tmt_validate_command,
)

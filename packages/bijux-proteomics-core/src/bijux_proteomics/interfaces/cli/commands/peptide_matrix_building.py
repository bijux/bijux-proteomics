# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi
# ruff: noqa: F401,F403,F405

"""Peptide-matrix CLI commands."""

from __future__ import annotations

from bijux_proteomics.interfaces.support import *  # noqa: F401,F403,F405
from bijux_proteomics.interfaces.python_api.peptide_matrix_building import run_peptide_matrix_command

@click.command("peptide-matrix")
@click.argument(
    "input_table", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--input-kind",
    type=_peptide_matrix_builder_input_kind_choice(),
    default="feature",
    show_default=True,
)
@click.option(
    "--grouping-mode",
    type=_peptide_matrix_grouping_choice(),
    default=PeptideMatrixGroupingMode.MODIFIED_PEPTIDE.value,
    show_default=True,
)
@click.option(
    "--separate-charge-states/--merge-charge-states",
    default=False,
    show_default=True,
)
@click.option(
    "--aggregation",
    type=_quant_rollup_choice(),
    default=QuantRollupMethod.SUM.value,
    show_default=True,
)
@click.option("--top-n", type=int, default=3, show_default=True)
@click.option("--sample-column", default="sample_id", show_default=True)
@click.option("--feature-id-column", default="feature_id", show_default=True)
@click.option("--precursor-id-column", default="precursor_id", show_default=True)
@click.option("--run-column", default="run_id", show_default=True)
@click.option("--spectrum-id-column", default="spectrum_id", show_default=True)
@click.option("--peptide-column", default="peptide", show_default=True)
@click.option(
    "--modified-peptide-column",
    default="modified_peptide",
    show_default=True,
)
@click.option("--intensity-column", default="intensity", show_default=True)
@click.option("--protein-refs-column", default="proteins", show_default=True)
@click.option("--charge-column", default="charge", show_default=True)
@click.option("--score-column", default="score", show_default=True)
@click.option("--q-value-column", default="q_value", show_default=True)
@click.option("--decoy-label-column", default=None)
@click.option("--contaminant-label-column", default=None)
@click.option("--mz-column", default="mz", show_default=True)
@click.option(
    "--retention-time-column", default="retention_time_seconds", show_default=True
)
@click.option("--missing-reason-column", default="missing_reason", show_default=True)
@click.option("--protein-separator", default=";", show_default=True)
@click.option("--chunk-size-rows", type=int, default=None)
@click.option(
    "--summary-tsv-out", type=click.Path(path_type=Path, dir_okay=False), default=None
)
@click.option(
    "--matrix-tsv-out", type=click.Path(path_type=Path, dir_okay=False), default=None
)
@click.option(
    "--missingness-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--missingness-mask-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--aggregation-table-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
    help="Optional JSON peptide-matrix output path.",
)
def peptide_matrix_command(
    input_table: Path,
    input_kind: str,
    grouping_mode: str,
    separate_charge_states: bool,
    aggregation: str,
    top_n: int,
    sample_column: str,
    feature_id_column: str,
    precursor_id_column: str,
    run_column: str,
    spectrum_id_column: str,
    peptide_column: str,
    modified_peptide_column: str,
    intensity_column: str,
    protein_refs_column: str | None,
    charge_column: str,
    score_column: str,
    q_value_column: str | None,
    decoy_label_column: str | None,
    contaminant_label_column: str | None,
    mz_column: str | None,
    retention_time_column: str | None,
    missing_reason_column: str | None,
    protein_separator: str,
    chunk_size_rows: int | None,
    summary_tsv_out: Path | None,
    matrix_tsv_out: Path | None,
    missingness_tsv_out: Path | None,
    missingness_mask_tsv_out: Path | None,
    aggregation_table_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    'Build one peptide-by-sample intensity matrix from feature, precursor, or PSM evidence.'
    return run_peptide_matrix_command(input_table, input_kind, grouping_mode, separate_charge_states, aggregation, top_n, sample_column, feature_id_column, precursor_id_column, run_column, spectrum_id_column, peptide_column, modified_peptide_column, intensity_column, protein_refs_column, charge_column, score_column, q_value_column, decoy_label_column, contaminant_label_column, mz_column, retention_time_column, missing_reason_column, protein_separator, chunk_size_rows, summary_tsv_out, matrix_tsv_out, missingness_tsv_out, missingness_mask_tsv_out, aggregation_table_tsv_out, out_path)

COMMANDS = (
    peptide_matrix_command,
)

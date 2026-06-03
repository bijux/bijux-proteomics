# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi
# ruff: noqa: F401,F403,F405

"""Protein-matrix and LFQ CLI commands."""

from __future__ import annotations

from pathlib import Path

import click

from bijux_proteomics.interfaces.python_api.protein_matrix_lfq import (
    run_protein_lfq_command,
    run_protein_matrix_command,
)
from bijux_proteomics.interfaces.support import *  # noqa: F401,F403,F405


@click.command("protein-matrix")
@click.argument(
    "input_table", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--input-kind",
    type=_peptide_matrix_input_kind_choice(),
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
    "--target-kind",
    type=_protein_matrix_target_choice(),
    default=ProteinMatrixTargetKind.PROTEIN.value,
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
@click.option(
    "--unique-peptide-only/--include-shared-peptides",
    default=False,
    show_default=True,
)
@click.option("--sample-column", default="sample_id", show_default=True)
@click.option("--feature-id-column", default="feature_id", show_default=True)
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
    "--contributions-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
    help="Optional protein_value_contributors.tsv output path.",
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
    help="Optional JSON protein-matrix output path.",
)
def protein_matrix_command(
    input_table: Path,
    input_kind: str,
    grouping_mode: str,
    target_kind: str,
    separate_charge_states: bool,
    aggregation: str,
    top_n: int,
    unique_peptide_only: bool,
    sample_column: str,
    feature_id_column: str,
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
    summary_tsv_out: Path | None,
    matrix_tsv_out: Path | None,
    missingness_tsv_out: Path | None,
    contributions_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    """Build one protein-by-sample intensity matrix from feature or PSM evidence."""
    return run_protein_matrix_command(
        input_table,
        input_kind,
        grouping_mode,
        target_kind,
        separate_charge_states,
        aggregation,
        top_n,
        unique_peptide_only,
        sample_column,
        feature_id_column,
        run_column,
        spectrum_id_column,
        peptide_column,
        modified_peptide_column,
        intensity_column,
        protein_refs_column,
        charge_column,
        score_column,
        q_value_column,
        decoy_label_column,
        contaminant_label_column,
        mz_column,
        retention_time_column,
        missing_reason_column,
        protein_separator,
        summary_tsv_out,
        matrix_tsv_out,
        missingness_tsv_out,
        contributions_tsv_out,
        out_path,
    )


@click.command("protein-lfq")
@click.argument(
    "input_table", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--input-kind",
    type=_peptide_matrix_input_kind_choice(),
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
    "--target-kind",
    type=_protein_matrix_target_choice(),
    default=ProteinMatrixTargetKind.PROTEIN.value,
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
@click.option(
    "--unique-peptide-only/--include-shared-peptides",
    default=False,
    show_default=True,
)
@click.option("--minimum-shared-peptides", type=int, default=1, show_default=True)
@click.option("--sample-column", default="sample_id", show_default=True)
@click.option("--feature-id-column", default="feature_id", show_default=True)
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
@click.option(
    "--summary-tsv-out", type=click.Path(path_type=Path, dir_okay=False), default=None
)
@click.option(
    "--matrix-tsv-out", type=click.Path(path_type=Path, dir_okay=False), default=None
)
@click.option(
    "--pairwise-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--missingness-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--disconnected-components-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--peptide-profile-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
    help="Optional peptide profile inconsistency TSV output path.",
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
    help="Optional JSON protein-lfq output path.",
)
def protein_lfq_command(
    input_table: Path,
    input_kind: str,
    grouping_mode: str,
    target_kind: str,
    separate_charge_states: bool,
    aggregation: str,
    top_n: int,
    unique_peptide_only: bool,
    minimum_shared_peptides: int,
    sample_column: str,
    feature_id_column: str,
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
    summary_tsv_out: Path | None,
    matrix_tsv_out: Path | None,
    pairwise_tsv_out: Path | None,
    missingness_tsv_out: Path | None,
    disconnected_components_tsv_out: Path | None,
    peptide_profile_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    """Build one MaxLFQ-like protein abundance matrix from feature or PSM evidence."""
    return run_protein_lfq_command(
        input_table,
        input_kind,
        grouping_mode,
        target_kind,
        separate_charge_states,
        aggregation,
        top_n,
        unique_peptide_only,
        minimum_shared_peptides,
        sample_column,
        feature_id_column,
        run_column,
        spectrum_id_column,
        peptide_column,
        modified_peptide_column,
        intensity_column,
        protein_refs_column,
        charge_column,
        score_column,
        q_value_column,
        decoy_label_column,
        contaminant_label_column,
        mz_column,
        retention_time_column,
        missing_reason_column,
        protein_separator,
        summary_tsv_out,
        matrix_tsv_out,
        pairwise_tsv_out,
        missingness_tsv_out,
        disconnected_components_tsv_out,
        peptide_profile_tsv_out,
        out_path,
    )


COMMANDS = (
    protein_matrix_command,
    protein_lfq_command,
)

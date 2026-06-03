# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi
# ruff: noqa: F401,F403,F405

"""DIA precursor-matrix CLI commands."""

from __future__ import annotations

from pathlib import Path

import click

from bijux_proteomics.interfaces.python_api.dia_precursor_matrices import (
    run_diann_precursor_matrix_command,
    run_spectronaut_precursor_matrix_command,
)
from bijux_proteomics.interfaces.support import *  # noqa: F401,F403,F405


@click.command("diann-precursor-matrix")
@click.argument(
    "result_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
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
@click.option(
    "--q-value-filter-timing",
    type=click.Choice(
        [timing.value for timing in DiaPrecursorQValueFilterTiming],
        case_sensitive=False,
    ),
    default=DiaPrecursorQValueFilterTiming.BEFORE_MATRIX_CONSTRUCTION.value,
    show_default=True,
)
@click.option("--summary-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--matrix-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--qvalue-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--metadata-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def diann_precursor_matrix_command(
    result_tsv: Path,
    config_path: Path | None,
    include_decoys: bool,
    max_q_value: float | None,
    q_value_filter_timing: str,
    summary_tsv_out: Path | None,
    matrix_tsv_out: Path | None,
    qvalue_tsv_out: Path | None,
    metadata_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    """Build a DIA precursor-by-sample matrix from one DIA-NN report."""
    return run_diann_precursor_matrix_command(
        result_tsv,
        config_path,
        include_decoys,
        max_q_value,
        q_value_filter_timing,
        summary_tsv_out,
        matrix_tsv_out,
        qvalue_tsv_out,
        metadata_tsv_out,
        out_path,
    )


@click.command("spectronaut-precursor-matrix")
@click.argument(
    "result_tsv", type=click.Path(exists=True, dir_okay=False, path_type=Path)
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
@click.option(
    "--q-value-filter-timing",
    type=click.Choice(
        [timing.value for timing in DiaPrecursorQValueFilterTiming],
        case_sensitive=False,
    ),
    default=DiaPrecursorQValueFilterTiming.BEFORE_MATRIX_CONSTRUCTION.value,
    show_default=True,
)
@click.option("--summary-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--matrix-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--qvalue-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--metadata-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def spectronaut_precursor_matrix_command(
    result_tsv: Path,
    config_path: Path | None,
    include_decoys: bool,
    max_q_value: float | None,
    q_value_filter_timing: str,
    summary_tsv_out: Path | None,
    matrix_tsv_out: Path | None,
    qvalue_tsv_out: Path | None,
    metadata_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    """Build a DIA precursor-by-sample matrix from one Spectronaut report."""
    return run_spectronaut_precursor_matrix_command(
        result_tsv,
        config_path,
        include_decoys,
        max_q_value,
        q_value_filter_timing,
        summary_tsv_out,
        matrix_tsv_out,
        qvalue_tsv_out,
        metadata_tsv_out,
        out_path,
    )


COMMANDS = (
    diann_precursor_matrix_command,
    spectronaut_precursor_matrix_command,
)

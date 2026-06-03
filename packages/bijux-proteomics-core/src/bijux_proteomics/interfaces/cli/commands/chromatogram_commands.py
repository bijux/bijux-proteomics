# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi
# ruff: noqa: F401,F403,F405

"""Chromatogram and DIA trace CLI commands."""

from __future__ import annotations

from pathlib import Path

import click

from bijux_proteomics.interfaces.python_api.chromatogram_commands import (
    run_dia_fragment_coelution_command,
    run_xic_align_retention_times_command,
    run_xic_extract_command,
    run_xic_pick_peaks_command,
    run_xic_score_evidence_command,
)
from bijux_proteomics.interfaces.support import *  # noqa: F401,F403,F405


@click.command("xic-extract")
@click.argument(
    "input_mzml", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument(
    "target_table", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option("--tolerance-da", type=float, default=None)
@click.option("--tolerance-ppm", type=float, default=None)
@click.option(
    "--tsv-out", type=click.Path(path_type=Path, dir_okay=False), default=None
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
    help="Optional JSON extraction output path.",
)
def xic_extract_command(
    input_mzml: Path,
    target_table: Path,
    tolerance_da: float | None,
    tolerance_ppm: float | None,
    tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    "Extract precursor XIC traces directly from mzML MS1 spectra."
    return run_xic_extract_command(
        input_mzml, target_table, tolerance_da, tolerance_ppm, tsv_out, out_path
    )


@click.command("xic-pick-peaks")
@click.argument(
    "input_mzml", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument(
    "target_table", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option("--tolerance-da", type=float, default=None)
@click.option("--tolerance-ppm", type=float, default=None)
@click.option(
    "--trace-tsv-out", type=click.Path(path_type=Path, dir_okay=False), default=None
)
@click.option(
    "--peak-tsv-out", type=click.Path(path_type=Path, dir_okay=False), default=None
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
    help="Optional JSON peak-picking output path.",
)
def xic_pick_peaks_command(
    input_mzml: Path,
    target_table: Path,
    tolerance_da: float | None,
    tolerance_ppm: float | None,
    trace_tsv_out: Path | None,
    peak_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    "Extract XIC traces and detect chromatographic peaks from mzML."
    return run_xic_pick_peaks_command(
        input_mzml,
        target_table,
        tolerance_da,
        tolerance_ppm,
        trace_tsv_out,
        peak_tsv_out,
        out_path,
    )


@click.command("xic-align-retention-times")
@click.argument(
    "target_table", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument(
    "input_mzml",
    nargs=-1,
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
)
@click.option("--tolerance-da", type=float, default=None)
@click.option("--tolerance-ppm", type=float, default=None)
@click.option(
    "--reference-run-id",
    default=None,
    help="Optional reference run id; defaults to the first mzML stem.",
)
@click.option(
    "--aligned-rt-tolerance-seconds",
    type=float,
    default=5.0,
    show_default=True,
)
@click.option("--min-anchor-count", type=int, default=2, show_default=True)
@click.option(
    "--model-tsv-out", type=click.Path(path_type=Path, dir_okay=False), default=None
)
@click.option(
    "--residual-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--failed-anchor-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
    help="Optional JSON retention-time alignment output path.",
)
def xic_align_retention_times_command(
    target_table: Path,
    input_mzml: tuple[Path, ...],
    tolerance_da: float | None,
    tolerance_ppm: float | None,
    reference_run_id: str | None,
    aligned_rt_tolerance_seconds: float,
    min_anchor_count: int,
    model_tsv_out: Path | None,
    residual_tsv_out: Path | None,
    failed_anchor_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    "Align run-to-run retention times from common chromatographic anchors."
    return run_xic_align_retention_times_command(
        target_table,
        input_mzml,
        tolerance_da,
        tolerance_ppm,
        reference_run_id,
        aligned_rt_tolerance_seconds,
        min_anchor_count,
        model_tsv_out,
        residual_tsv_out,
        failed_anchor_tsv_out,
        out_path,
    )


@click.command("xic-score-evidence")
@click.argument(
    "target_table", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument(
    "input_mzml",
    nargs=-1,
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
)
@click.option("--tolerance-da", type=float, default=None)
@click.option("--tolerance-ppm", type=float, default=None)
@click.option(
    "--aligned-rt-tolerance-seconds",
    type=float,
    default=5.0,
    show_default=True,
)
@click.option("--min-anchor-count", type=int, default=2, show_default=True)
@click.option(
    "--target-tsv-out", type=click.Path(path_type=Path, dir_okay=False), default=None
)
@click.option(
    "--peptide-tsv-out", type=click.Path(path_type=Path, dir_okay=False), default=None
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
    help="Optional JSON chromatographic evidence output path.",
)
def xic_score_evidence_command(
    target_table: Path,
    input_mzml: tuple[Path, ...],
    tolerance_da: float | None,
    tolerance_ppm: float | None,
    aligned_rt_tolerance_seconds: float,
    min_anchor_count: int,
    target_tsv_out: Path | None,
    peptide_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    "Score chromatographic precursor and peptide evidence across mzML runs."
    return run_xic_score_evidence_command(
        target_table,
        input_mzml,
        tolerance_da,
        tolerance_ppm,
        aligned_rt_tolerance_seconds,
        min_anchor_count,
        target_tsv_out,
        peptide_tsv_out,
        out_path,
    )


@click.command("dia-fragment-coelution")
@click.argument(
    "target_table", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument(
    "input_mzml",
    nargs=-1,
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
)
@click.option("--tolerance-da", type=float, default=None)
@click.option("--tolerance-ppm", type=float, default=None)
@click.option(
    "--apex-tolerance-seconds",
    type=float,
    default=5.0,
    show_default=True,
)
@click.option("--min-correlation", type=float, default=0.8, show_default=True)
@click.option("--min-passing-fragment-count", type=int, default=2, show_default=True)
@click.option(
    "--run-tsv-out", type=click.Path(path_type=Path, dir_okay=False), default=None
)
@click.option(
    "--fragment-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--ratio-fragment-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--ratio-observation-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
    help="Optional JSON DIA fragment coelution output path.",
)
def dia_fragment_coelution_command(
    target_table: Path,
    input_mzml: tuple[Path, ...],
    tolerance_da: float | None,
    tolerance_ppm: float | None,
    apex_tolerance_seconds: float,
    min_correlation: float,
    min_passing_fragment_count: int,
    run_tsv_out: Path | None,
    fragment_tsv_out: Path | None,
    ratio_fragment_tsv_out: Path | None,
    ratio_observation_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    "Score coelution among DIA fragment traces assigned to one precursor."
    return run_dia_fragment_coelution_command(
        target_table,
        input_mzml,
        tolerance_da,
        tolerance_ppm,
        apex_tolerance_seconds,
        min_correlation,
        min_passing_fragment_count,
        run_tsv_out,
        fragment_tsv_out,
        ratio_fragment_tsv_out,
        ratio_observation_tsv_out,
        out_path,
    )


COMMANDS = (
    xic_extract_command,
    xic_pick_peaks_command,
    xic_align_retention_times_command,
    xic_score_evidence_command,
    dia_fragment_coelution_command,
)

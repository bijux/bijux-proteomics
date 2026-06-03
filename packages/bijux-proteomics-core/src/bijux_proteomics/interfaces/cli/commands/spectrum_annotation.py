# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi
# ruff: noqa: F401,F403,F405

"""Spectrum annotation CLI commands."""

from __future__ import annotations

from pathlib import Path

import click

from bijux_proteomics.interfaces.python_api.spectrum_annotation import (
    run_precursor_isotope_fit_command,
    run_raw_signal_evidence_card_command,
    run_spectrum_annotate_command,
    run_spectrum_score_chimeric_command,
)
from bijux_proteomics.interfaces.support import *  # noqa: F401,F403,F405


@click.command("spectrum-annotate")
@click.argument(
    "input_mgf", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option("--peptide", required=True)
@click.option(
    "--spectrum-id",
    default=None,
    help="Optional target spectrum id; defaults to the first accepted spectrum.",
)
@click.option("--tolerance-da", type=float, default=None)
@click.option("--tolerance-ppm", type=float, default=None)
@click.option(
    "--tsv-out", type=click.Path(path_type=Path, dir_okay=False), default=None
)
@click.option(
    "--plot-out", type=click.Path(path_type=Path, dir_okay=False), default=None
)
@click.option(
    "--unmatched-peak-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
    help="Optional JSON annotation output path.",
)
def spectrum_annotate_command(
    input_mgf: Path,
    peptide: str,
    spectrum_id: str | None,
    tolerance_da: float | None,
    tolerance_ppm: float | None,
    tsv_out: Path | None,
    plot_out: Path | None,
    unmatched_peak_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    "Annotate one spectrum against a peptide sequence."
    return run_spectrum_annotate_command(
        input_mgf,
        peptide,
        spectrum_id,
        tolerance_da,
        tolerance_ppm,
        tsv_out,
        plot_out,
        unmatched_peak_tsv_out,
        out_path,
    )


@click.command("spectrum-score-chimeric")
@click.argument(
    "input_path", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument(
    "psm_path", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--kind",
    type=click.Choice(["auto", "mgf", "mzml"]),
    default="auto",
    show_default=True,
)
@click.option("--tolerance-da", type=float, default=None)
@click.option("--tolerance-ppm", type=float, default=None)
@click.option(
    "--default-isolation-window-half-width-da",
    type=float,
    default=1.0,
    show_default=True,
)
@click.option(
    "--chimeric-score-threshold",
    type=float,
    default=0.45,
    show_default=True,
)
@click.option(
    "--spectra-tsv-out", type=click.Path(path_type=Path, dir_okay=False), default=None
)
@click.option(
    "--competition-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
    help="Optional JSON chimeric-spectrum output path.",
)
def spectrum_score_chimeric_command(
    input_path: Path,
    psm_path: Path,
    kind: str,
    tolerance_da: float | None,
    tolerance_ppm: float | None,
    default_isolation_window_half_width_da: float,
    chimeric_score_threshold: float,
    spectra_tsv_out: Path | None,
    competition_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    "Score spectra for competing peptide evidence that suggests chimeric MS/MS."
    return run_spectrum_score_chimeric_command(
        input_path,
        psm_path,
        kind,
        tolerance_da,
        tolerance_ppm,
        default_isolation_window_half_width_da,
        chimeric_score_threshold,
        spectra_tsv_out,
        competition_tsv_out,
        out_path,
    )


@click.command("raw-signal-evidence-card")
@click.argument(
    "xic_target_table", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument(
    "chromatogram_mzml",
    nargs=-1,
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
)
@click.option(
    "--fragment-target-table",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--spectrum-mzml",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--psm-tsv",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option("--precursor-id", "precursor_ids", multiple=True)
@click.option("--peptide-ref", "peptide_refs", multiple=True)
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
    "--apex-tolerance-seconds",
    type=float,
    default=5.0,
    show_default=True,
)
@click.option("--min-correlation", type=float, default=0.8, show_default=True)
@click.option("--min-passing-fragment-count", type=int, default=2, show_default=True)
@click.option("--fragment-ms-level", type=int, default=2, show_default=True)
@click.option(
    "--default-isolation-window-half-width-da",
    type=float,
    default=1.0,
    show_default=True,
)
@click.option(
    "--chimeric-score-threshold",
    type=float,
    default=0.45,
    show_default=True,
)
@click.option(
    "--summary-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--card-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--html-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
    help="Optional JSON raw-signal evidence-card output path.",
)
def raw_signal_evidence_card_command(
    xic_target_table: Path,
    chromatogram_mzml: tuple[Path, ...],
    fragment_target_table: Path | None,
    spectrum_mzml: Path | None,
    psm_tsv: Path | None,
    precursor_ids: tuple[str, ...],
    peptide_refs: tuple[str, ...],
    tolerance_da: float | None,
    tolerance_ppm: float | None,
    aligned_rt_tolerance_seconds: float,
    min_anchor_count: int,
    apex_tolerance_seconds: float,
    min_correlation: float,
    min_passing_fragment_count: int,
    fragment_ms_level: int,
    default_isolation_window_half_width_da: float,
    chimeric_score_threshold: float,
    summary_tsv_out: Path | None,
    card_tsv_out: Path | None,
    html_out: Path | None,
    out_path: Path | None,
) -> None:
    "Build one structured raw-signal evidence-card review for selected precursors."
    return run_raw_signal_evidence_card_command(
        xic_target_table,
        chromatogram_mzml,
        fragment_target_table,
        spectrum_mzml,
        psm_tsv,
        precursor_ids,
        peptide_refs,
        tolerance_da,
        tolerance_ppm,
        aligned_rt_tolerance_seconds,
        min_anchor_count,
        apex_tolerance_seconds,
        min_correlation,
        min_passing_fragment_count,
        fragment_ms_level,
        default_isolation_window_half_width_da,
        chimeric_score_threshold,
        summary_tsv_out,
        card_tsv_out,
        html_out,
        out_path,
    )


@click.command("precursor-isotope-fit")
@click.argument(
    "target_table", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument(
    "input_mzml",
    nargs=-1,
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
)
@click.option("--extraction-tolerance-da", type=float, default=None)
@click.option("--extraction-tolerance-ppm", type=float, default=None)
@click.option("--fit-tolerance-da", type=float, default=None)
@click.option("--fit-tolerance-ppm", type=float, default=None)
@click.option("--max-isotope-index", type=int, default=2, show_default=True)
@click.option(
    "--summary-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--entry-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--peak-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
    help="Optional JSON precursor isotope-fit output path.",
)
def precursor_isotope_fit_command(
    target_table: Path,
    input_mzml: tuple[Path, ...],
    extraction_tolerance_da: float | None,
    extraction_tolerance_ppm: float | None,
    fit_tolerance_da: float | None,
    fit_tolerance_ppm: float | None,
    max_isotope_index: int,
    summary_tsv_out: Path | None,
    entry_tsv_out: Path | None,
    peak_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    "Compare predicted precursor isotope envelopes against observed MS1 peaks."
    return run_precursor_isotope_fit_command(
        target_table,
        input_mzml,
        extraction_tolerance_da,
        extraction_tolerance_ppm,
        fit_tolerance_da,
        fit_tolerance_ppm,
        max_isotope_index,
        summary_tsv_out,
        entry_tsv_out,
        peak_tsv_out,
        out_path,
    )


COMMANDS = (
    spectrum_annotate_command,
    spectrum_score_chimeric_command,
    raw_signal_evidence_card_command,
    precursor_isotope_fit_command,
)

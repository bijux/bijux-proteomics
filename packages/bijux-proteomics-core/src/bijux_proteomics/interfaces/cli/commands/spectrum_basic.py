# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi
# ruff: noqa: F401,F403,F405

"""Spectrum parsing and QC CLI commands."""

from __future__ import annotations

from bijux_proteomics.interfaces.support import *  # noqa: F401,F403,F405
from bijux_proteomics.interfaces.python_api.spectrum_basic import run_spectrum_parse_command, run_spectrum_stats_command, run_spectrum_summary_command, run_spectrum_qc_command, run_mzml_inspect_command

@click.command("spectrum-parse")
@click.argument(
    "input_mgf", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option("--chunk-size", type=int, default=500, show_default=True)
@click.option(
    "--accepted-jsonl-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--rejected-json-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
    help="Optional JSON report output path.",
)
def spectrum_parse_command(
    input_mgf: Path,
    chunk_size: int,
    accepted_jsonl_out: Path | None,
    rejected_json_out: Path | None,
    out_path: Path | None,
) -> None:
    'Parse one MGF file and report accepted spectra, rejections, and streaming facts.'
    return run_spectrum_parse_command(input_mgf, chunk_size, accepted_jsonl_out, rejected_json_out, out_path)

@click.command("spectrum-stats")
@click.argument(
    "input_mgf", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--provenance-out", type=click.Path(path_type=Path, dir_okay=False), default=None
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
    help="Optional JSON report output path.",
)
def spectrum_stats_command(
    input_mgf: Path,
    provenance_out: Path | None,
    out_path: Path | None,
) -> None:
    'Summarize one MGF collection.'
    return run_spectrum_stats_command(input_mgf, provenance_out, out_path)

@click.command("spectrum-summary")
@click.argument(
    "input_path", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--kind",
    type=click.Choice(["auto", "mgf", "mzml"]),
    default="auto",
    show_default=True,
)
@click.option(
    "--summary-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--charge-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--precursor-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--peak-count-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
    help="Optional JSON report output path.",
)
def spectrum_summary_command(
    input_path: Path,
    kind: str,
    summary_tsv_out: Path | None,
    charge_tsv_out: Path | None,
    precursor_tsv_out: Path | None,
    peak_count_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    'Build reviewable summary tables over one MGF or mzML spectra file.'
    return run_spectrum_summary_command(input_path, kind, summary_tsv_out, charge_tsv_out, precursor_tsv_out, peak_count_tsv_out, out_path)

@click.command("spectrum-qc")
@click.argument(
    "input_path", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--kind",
    type=click.Choice(["auto", "mgf", "mzml"]),
    default="auto",
    show_default=True,
)
@click.option(
    "--time-bin-seconds",
    type=float,
    default=60.0,
    show_default=True,
)
@click.option(
    "--summary-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--msms-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--tic-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--bpc-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--charge-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--precursor-intensity-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--flagged-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--spectrum-qc-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--plot-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
    help="Optional JSON run-QC output path.",
)
def spectrum_qc_command(
    input_path: Path,
    kind: str,
    time_bin_seconds: float,
    summary_tsv_out: Path | None,
    msms_tsv_out: Path | None,
    tic_tsv_out: Path | None,
    bpc_tsv_out: Path | None,
    charge_tsv_out: Path | None,
    precursor_intensity_tsv_out: Path | None,
    flagged_tsv_out: Path | None,
    spectrum_qc_tsv_out: Path | None,
    plot_out: Path | None,
    out_path: Path | None,
) -> None:
    'Build run-level QC directly from one MGF or mzML spectra file.'
    return run_spectrum_qc_command(input_path, kind, time_bin_seconds, summary_tsv_out, msms_tsv_out, tic_tsv_out, bpc_tsv_out, charge_tsv_out, precursor_intensity_tsv_out, flagged_tsv_out, spectrum_qc_tsv_out, plot_out, out_path)

@click.command("mzml-inspect")
@click.argument(
    "input_mzml", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--spectra-jsonl-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--chromatograms-json-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
    help="Optional JSON report output path.",
)
def mzml_inspect_command(
    input_mzml: Path,
    spectra_jsonl_out: Path | None,
    chromatograms_json_out: Path | None,
    out_path: Path | None,
) -> None:
    'Inspect one mzML run with practical spectra, decoding, and chromatogram review.'
    return run_mzml_inspect_command(input_mzml, spectra_jsonl_out, chromatograms_json_out, out_path)

COMMANDS = (
    spectrum_parse_command,
    spectrum_stats_command,
    spectrum_summary_command,
    spectrum_qc_command,
    mzml_inspect_command,
)

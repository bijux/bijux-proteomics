# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi
# ruff: noqa: F401,F403,F405

"""Spectral library CLI commands."""

from __future__ import annotations

from pathlib import Path

import click

from bijux_proteomics.interfaces.python_api.spectral_library_commands import (
    run_spectral_library_import_command,
    run_spectral_library_search_command,
    run_spectrum_similarity_command,
)
from bijux_proteomics.interfaces.support import *  # noqa: F401,F403,F405


@click.command("spectrum-similarity")
@click.argument(
    "query_path", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument(
    "reference_path", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--query-kind",
    type=click.Choice(["auto", "mgf", "mzml"]),
    default="auto",
    show_default=True,
)
@click.option(
    "--reference-kind",
    type=click.Choice(["auto", "mgf", "mzml"]),
    default="auto",
    show_default=True,
)
@click.option("--query-spectrum-id", default=None)
@click.option("--reference-spectrum-id", default=None)
@click.option(
    "--method",
    type=click.Choice([item.value for item in SpectralSimilarityMethod]),
    default=SpectralSimilarityMethod.COSINE.value,
    show_default=True,
)
@click.option(
    "--mode",
    type=click.Choice([item.value for item in SpectrumSimilarityMode]),
    default=SpectrumSimilarityMode.NORMALIZED.value,
    show_default=True,
)
@click.option("--top-n", type=int, default=None)
@click.option("--tolerance-da", type=float, default=None)
@click.option("--bin-width-da", type=float, default=None)
@click.option("--max-matches", type=int, default=None)
@click.option(
    "--tsv-out", type=click.Path(path_type=Path, dir_okay=False), default=None
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
    help="Optional JSON similarity output path.",
)
def spectrum_similarity_command(
    query_path: Path,
    reference_path: Path,
    query_kind: str,
    reference_kind: str,
    query_spectrum_id: str | None,
    reference_spectrum_id: str | None,
    method: str,
    mode: str,
    top_n: int | None,
    tolerance_da: float | None,
    bin_width_da: float | None,
    max_matches: int | None,
    tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    """Compare one query spectrum against one spectrum or a reference library."""
    return run_spectrum_similarity_command(
        query_path,
        reference_path,
        query_kind,
        reference_kind,
        query_spectrum_id,
        reference_spectrum_id,
        method,
        mode,
        top_n,
        tolerance_da,
        bin_width_da,
        max_matches,
        tsv_out,
        out_path,
    )


@click.command("spectral-library-import")
@click.argument(
    "input_path", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--kind",
    type=click.Choice(["auto", "msp", "mgf"]),
    default="auto",
    show_default=True,
)
@click.option("--precursor-mz", type=float, default=None)
@click.option("--tolerance-da", type=float, default=0.5, show_default=True)
@click.option("--peptide", default=None)
@click.option(
    "--summary-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--candidates-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
    help="Optional JSON library import output path.",
)
def spectral_library_import_command(
    input_path: Path,
    kind: str,
    precursor_mz: float | None,
    tolerance_da: float,
    peptide: str | None,
    summary_tsv_out: Path | None,
    candidates_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    """Import one practical spectral library and optionally retrieve candidates."""
    return run_spectral_library_import_command(
        input_path,
        kind,
        precursor_mz,
        tolerance_da,
        peptide,
        summary_tsv_out,
        candidates_tsv_out,
        out_path,
    )


@click.command("spectral-library-search")
@click.argument(
    "query_path", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.argument(
    "library_path", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--query-kind",
    type=click.Choice(["auto", "mgf", "mzml"]),
    default="auto",
    show_default=True,
)
@click.option(
    "--library-kind",
    type=click.Choice(["auto", "msp", "mgf"]),
    default="auto",
    show_default=True,
)
@click.option("--query-spectrum-id", default=None)
@click.option(
    "--precursor-tolerance-da",
    type=float,
    default=0.5,
    show_default=True,
)
@click.option(
    "--tolerance-da",
    type=float,
    default=0.02,
    show_default=True,
    help="Fragment matching tolerance in Daltons for spectrum similarity.",
)
@click.option("--bin-width-da", type=float, default=None)
@click.option(
    "--method",
    type=click.Choice([item.value for item in SpectralSimilarityMethod]),
    default=SpectralSimilarityMethod.COSINE.value,
    show_default=True,
)
@click.option(
    "--mode",
    type=click.Choice([item.value for item in SpectrumSimilarityMode]),
    default=SpectrumSimilarityMode.NORMALIZED.value,
    show_default=True,
)
@click.option("--top-n", type=int, default=None)
@click.option("--max-matches", type=int, default=10, show_default=True)
@click.option(
    "--tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
    help="Optional JSON spectral-library search output path.",
)
def spectral_library_search_command(
    query_path: Path,
    library_path: Path,
    query_kind: str,
    library_kind: str,
    query_spectrum_id: str | None,
    precursor_tolerance_da: float,
    tolerance_da: float,
    bin_width_da: float | None,
    method: str,
    mode: str,
    top_n: int | None,
    max_matches: int,
    tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    """Search one query spectrum against a practical MSP or MGF library."""
    return run_spectral_library_search_command(
        query_path,
        library_path,
        query_kind,
        library_kind,
        query_spectrum_id,
        precursor_tolerance_da,
        tolerance_da,
        bin_width_da,
        method,
        mode,
        top_n,
        max_matches,
        tsv_out,
        out_path,
    )


COMMANDS = (
    spectrum_similarity_command,
    spectral_library_import_command,
    spectral_library_search_command,
)

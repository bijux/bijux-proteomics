# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi
# ruff: noqa: F401,F403,F405

"""Spectral library CLI commands."""

from __future__ import annotations

from bijux_proteomics.interfaces.cli.support import *  # noqa: F401,F403,F405

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
    'Compare one query spectrum against one spectrum or a reference library.'
    return run_spectrum_similarity_command(query_path, reference_path, query_kind, reference_kind, query_spectrum_id, reference_spectrum_id, method, mode, top_n, tolerance_da, bin_width_da, max_matches, tsv_out, out_path)

def run_spectrum_similarity_command(
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
    try:
        query_spectra = _load_similarity_spectra(query_path, kind=query_kind)
        reference_spectra = _load_similarity_spectra(
            reference_path,
            kind=reference_kind,
        )
        query_spectrum = _select_similarity_spectrum(
            query_spectra,
            input_path=query_path,
            spectrum_id=query_spectrum_id,
        )
        active_method = SpectralSimilarityMethod(method)
        active_mode = SpectrumSimilarityMode(mode)
        if top_n is not None and top_n <= 0:
            raise ValueError("top_n must be greater than zero when provided")
        if max_matches is not None and max_matches <= 0:
            raise ValueError("max_matches must be greater than zero when provided")

        payload: dict[str, Any]
        if reference_spectrum_id is not None:
            reference_spectrum = _select_similarity_spectrum(
                reference_spectra,
                input_path=reference_path,
                spectrum_id=reference_spectrum_id,
            )
            comparison = build_spectrum_similarity_comparison_report(
                reference_spectrum,
                query_spectrum,
                tolerance_da=tolerance_da,
                bin_width_da=bin_width_da,
                method=active_method,
                mode=active_mode,
                top_n=top_n,
            )
            library_report = build_spectrum_library_similarity_report(
                query_spectrum,
                (reference_spectrum,),
                tolerance_da=tolerance_da,
                bin_width_da=bin_width_da,
                method=active_method,
                mode=active_mode,
                top_n=top_n,
                max_matches=1,
            )
            payload = {
                "comparison": comparison.to_dict(),
                "library_report": library_report.to_dict(),
            }
        else:
            library_report = build_spectrum_library_similarity_report(
                query_spectrum,
                reference_spectra,
                tolerance_da=tolerance_da,
                bin_width_da=bin_width_da,
                method=active_method,
                mode=active_mode,
                top_n=top_n,
                max_matches=max_matches,
            )
            payload = {
                "comparison": None,
                "library_report": library_report.to_dict(),
            }
        if tsv_out is not None:
            _write_text_output(tsv_out, render_spectrum_similarity_tsv(library_report))
        payload["tsv_out"] = str(tsv_out) if tsv_out is not None else None
        _emit_json(payload, out_path=out_path)
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc

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
    'Import one practical spectral library and optionally retrieve candidates.'
    return run_spectral_library_import_command(input_path, kind, precursor_mz, tolerance_da, peptide, summary_tsv_out, candidates_tsv_out, out_path)

def run_spectral_library_import_command(
    input_path: Path,
    kind: str,
    precursor_mz: float | None,
    tolerance_da: float,
    peptide: str | None,
    summary_tsv_out: Path | None,
    candidates_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    try:
        active_kind = None if kind == "auto" else kind
        report = import_spectral_library(input_path, library_format=active_kind)
        summary = build_spectral_library_summary(report)
        index = build_spectral_library_index(report.entries)
        candidates = (
            find_spectral_library_candidates(
                index,
                precursor_mz=precursor_mz,
                tolerance_da=tolerance_da,
                peptide_query=peptide,
            )
            if precursor_mz is not None
            else None
        )
        if summary_tsv_out is not None:
            _write_text_output(
                summary_tsv_out,
                render_spectral_library_summary_tsv(summary),
            )
        if candidates_tsv_out is not None:
            if candidates is None:
                raise ValueError(
                    "candidates-tsv-out requires --precursor-mz candidate lookup input"
                )
            _write_text_output(
                candidates_tsv_out,
                render_spectral_library_candidates_tsv(candidates),
            )
        payload = {
            "import_report": report.to_dict(),
            "summary": summary.to_dict(),
            "index": {
                "entry_count": len(index.entries),
                "peptide_index": index.peptide_index,
                "precursor_centimass_index_size": len(index.precursor_centimass_index),
            },
            "candidates": candidates.to_dict() if candidates is not None else None,
            "summary_tsv_out": str(summary_tsv_out) if summary_tsv_out else None,
            "candidates_tsv_out": (
                str(candidates_tsv_out) if candidates_tsv_out else None
            ),
        }
        _emit_json(payload, out_path=out_path)
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc

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
    'Search one query spectrum against a practical MSP or MGF library.'
    return run_spectral_library_search_command(query_path, library_path, query_kind, library_kind, query_spectrum_id, precursor_tolerance_da, tolerance_da, bin_width_da, method, mode, top_n, max_matches, tsv_out, out_path)

def run_spectral_library_search_command(
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
    try:
        query_spectra = _load_similarity_spectra(query_path, kind=query_kind)
        query_spectrum = _select_similarity_spectrum(
            query_spectra,
            input_path=query_path,
            spectrum_id=query_spectrum_id,
        )
        active_library_kind = None if library_kind == "auto" else library_kind
        import_report = import_spectral_library(
            library_path,
            library_format=active_library_kind,
        )
        summary = build_spectral_library_summary(import_report)
        index = build_spectral_library_index(import_report.entries)
        search_report = search_spectral_library(
            query_spectrum,
            index,
            precursor_tolerance_da=precursor_tolerance_da,
            similarity_tolerance_da=tolerance_da,
            similarity_bin_width_da=bin_width_da,
            method=SpectralSimilarityMethod(method),
            mode=SpectrumSimilarityMode(mode),
            top_n=top_n,
            max_matches=max_matches,
        )
        if tsv_out is not None:
            _write_text_output(
                tsv_out, render_spectral_library_search_tsv(search_report)
            )
        payload = {
            "import_report": import_report.to_dict(),
            "library_summary": summary.to_dict(),
            "search_report": search_report.to_dict(),
            "warnings": (
                []
                if search_report.advisory_warning is None
                else [search_report.advisory_warning]
            ),
            "tsv_out": str(tsv_out) if tsv_out else None,
        }
        _emit_json(payload, out_path=out_path)
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc

COMMANDS = (
    spectrum_similarity_command,
    spectral_library_import_command,
    spectral_library_search_command,
)

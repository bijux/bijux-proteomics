# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi
"""Spectral library Python API entrypoints."""

from __future__ import annotations

from bijux_proteomics.interfaces.support.foundation import (
    Any,
    Path,
    click,
)
from bijux_proteomics.interfaces.support.io_and_dia import (
    SpectralSimilarityMethod,
    SpectrumSimilarityMode,
    build_spectral_library_index,
    build_spectral_library_summary,
    build_spectrum_library_similarity_report,
    build_spectrum_similarity_comparison_report,
    find_spectral_library_candidates,
    import_spectral_library,
    render_spectral_library_candidates_tsv,
    render_spectral_library_search_tsv,
    render_spectral_library_summary_tsv,
    render_spectrum_similarity_tsv,
    search_spectral_library,
)
from bijux_proteomics.interfaces.support.output_protocol.artifact_output import (
    _emit_json,
    _write_text_output,
)
from bijux_proteomics.interfaces.support.targeted_selection_io.spectrum_similarity import (
    _load_similarity_spectra,
    _select_similarity_spectrum,
)


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


__all__ = [
    "run_spectrum_similarity_command",
    "run_spectral_library_import_command",
    "run_spectral_library_search_command",
]

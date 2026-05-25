# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi
# ruff: noqa: F401,F403,F405

"""Spectrum annotation CLI commands."""

from __future__ import annotations

from bijux_proteomics.interfaces.cli.support import *  # noqa: F401,F403,F405

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
    'Annotate one spectrum against a peptide sequence.'
    return run_spectrum_annotate_command(input_mgf, peptide, spectrum_id, tolerance_da, tolerance_ppm, tsv_out, plot_out, unmatched_peak_tsv_out, out_path)

def run_spectrum_annotate_command(
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
    effective_tolerance_da = (
        0.02 if tolerance_da is None and tolerance_ppm is None else tolerance_da
    )
    report = parse_mgf(input_mgf)
    if not report.accepted_spectra:
        raise click.ClickException(
            "MGF input does not contain an accepted spectrum to annotate"
        )
    if spectrum_id is None:
        spectrum = report.accepted_spectra[0]
    else:
        try:
            spectrum = next(
                item
                for item in report.accepted_spectra
                if item.spectrum_id == spectrum_id
            )
        except StopIteration as exc:
            raise click.ClickException(f"unknown spectrum id {spectrum_id!r}") from exc
    try:
        peak_matching_report = build_spectrum_peak_match_report(
            spectrum,
            peptide=peptide,
            tolerance_da=effective_tolerance_da,
            tolerance_ppm=tolerance_ppm,
        )
        annotation = annotate_spectrum_fragments(
            spectrum,
            peptide=peptide,
            tolerance_da=effective_tolerance_da,
            tolerance_ppm=tolerance_ppm,
        )
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc
    plot_payload = build_spectrum_plot_payload(spectrum, annotation=annotation)
    if tsv_out is not None:
        export_spectrum_peak_match_tsv(peak_matching_report, tsv_out)
    if plot_out is not None:
        plot_out.write_text(plot_payload.to_stable_json() + "\n")
    if unmatched_peak_tsv_out is not None:
        export_spectrum_unmatched_peak_tsv(
            peak_matching_report,
            unmatched_peak_tsv_out,
        )
    payload = {
        "annotation": annotation.to_dict(),
        "peak_matching_report": peak_matching_report.to_dict(),
        "plot_payload": plot_payload.to_dict(),
    }
    _emit_json(payload, out_path=out_path)

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
    'Score spectra for competing peptide evidence that suggests chimeric MS/MS.'
    return run_spectrum_score_chimeric_command(input_path, psm_path, kind, tolerance_da, tolerance_ppm, default_isolation_window_half_width_da, chimeric_score_threshold, spectra_tsv_out, competition_tsv_out, out_path)

def run_spectrum_score_chimeric_command(
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
    effective_tolerance_da = (
        0.02 if tolerance_da is None and tolerance_ppm is None else tolerance_da
    )
    spectra = _load_similarity_spectra(input_path, kind=kind)
    psm_report = parse_psm_tsv(psm_path, mapping=_default_psm_mapping())
    try:
        report = score_chimeric_spectra_from_psms(
            spectra,
            psm_report.accepted_records,
            tolerance_da=effective_tolerance_da,
            tolerance_ppm=tolerance_ppm,
            default_isolation_window_half_width_da=(
                default_isolation_window_half_width_da
            ),
            chimeric_score_threshold=chimeric_score_threshold,
        )
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc
    if spectra_tsv_out is not None:
        _write_text_output(
            spectra_tsv_out,
            render_chimeric_spectrum_spectra_tsv(report),
        )
    if competition_tsv_out is not None:
        _write_text_output(
            competition_tsv_out,
            render_chimeric_spectrum_competing_evidence_tsv(report),
        )
    payload = {
        "spectrum_kind": kind if kind != "auto" else input_path.suffix.lower().lstrip("."),
        "psm_summary": {
            "total_rows": psm_report.total_rows,
            "accepted_record_count": len(psm_report.accepted_records),
            "rejected_row_count": len(psm_report.rejected_rows),
        },
        "chimeric_summary": report.summary.to_dict(),
        "spectra": [entry.to_dict() for entry in report.spectra],
        "competing_evidence": [entry.to_dict() for entry in report.competing_evidence],
        "note": report.note,
        "outputs": {
            "spectra_tsv": None if spectra_tsv_out is None else str(spectra_tsv_out),
            "competition_tsv": (
                None if competition_tsv_out is None else str(competition_tsv_out)
            ),
        },
    }
    _emit_json(payload, out_path=out_path)

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
    'Build one structured raw-signal evidence-card review for selected precursors.'
    return run_raw_signal_evidence_card_command(xic_target_table, chromatogram_mzml, fragment_target_table, spectrum_mzml, psm_tsv, precursor_ids, peptide_refs, tolerance_da, tolerance_ppm, aligned_rt_tolerance_seconds, min_anchor_count, apex_tolerance_seconds, min_correlation, min_passing_fragment_count, fragment_ms_level, default_isolation_window_half_width_da, chimeric_score_threshold, summary_tsv_out, card_tsv_out, html_out, out_path)

def run_raw_signal_evidence_card_command(
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
    try:
        report = extract_mzml_raw_signal_evidence_cards(
            chromatogram_mzml,
            xic_target_table,
            fragment_target_table=fragment_target_table,
            spectrum_mzml_path=spectrum_mzml,
            psm_path=psm_tsv,
            tolerance_da=tolerance_da,
            tolerance_ppm=tolerance_ppm,
            aligned_rt_tolerance_seconds=aligned_rt_tolerance_seconds,
            min_anchor_count=min_anchor_count,
            apex_tolerance_seconds=apex_tolerance_seconds,
            min_correlation=min_correlation,
            min_passing_fragment_count=min_passing_fragment_count,
            fragment_ms_level=fragment_ms_level,
            default_isolation_window_half_width_da=(
                default_isolation_window_half_width_da
            ),
            chimeric_score_threshold=chimeric_score_threshold,
            selected_precursor_ids=precursor_ids,
            selected_peptide_refs=peptide_refs,
        )
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        _write_text_output(
            summary_tsv_out,
            render_raw_signal_evidence_card_summary_tsv(report),
        )
    if card_tsv_out is not None:
        _write_text_output(
            card_tsv_out,
            render_raw_signal_evidence_card_tsv(report),
        )
    if html_out is not None:
        _write_text_output(html_out, render_raw_signal_evidence_cards_html(report))

    _emit_json(
        {
            "report": report.to_dict(),
            "outputs": {
                "summary_tsv": (
                    None if summary_tsv_out is None else str(summary_tsv_out)
                ),
                "card_tsv": None if card_tsv_out is None else str(card_tsv_out),
                "html": None if html_out is None else str(html_out),
            },
        },
        out_path=out_path,
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
    'Compare predicted precursor isotope envelopes against observed MS1 peaks.'
    return run_precursor_isotope_fit_command(target_table, input_mzml, extraction_tolerance_da, extraction_tolerance_ppm, fit_tolerance_da, fit_tolerance_ppm, max_isotope_index, summary_tsv_out, entry_tsv_out, peak_tsv_out, out_path)

def run_precursor_isotope_fit_command(
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
    try:
        report = extract_mzml_precursor_isotope_fit(
            input_mzml,
            target_table,
            extraction_tolerance_da=extraction_tolerance_da,
            extraction_tolerance_ppm=extraction_tolerance_ppm,
            fit_tolerance_da=fit_tolerance_da,
            fit_tolerance_ppm=fit_tolerance_ppm,
            max_isotope_index=max_isotope_index,
        )
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        _write_text_output(
            summary_tsv_out,
            render_precursor_isotope_fit_summary_tsv(report),
        )
    if entry_tsv_out is not None:
        _write_text_output(
            entry_tsv_out,
            render_precursor_isotope_fit_entries_tsv(report),
        )
    if peak_tsv_out is not None:
        _write_text_output(
            peak_tsv_out,
            render_precursor_isotope_fit_peaks_tsv(report),
        )

    _emit_json(
        {
            "report": report.to_dict(),
            "outputs": {
                "summary_tsv": (
                    None if summary_tsv_out is None else str(summary_tsv_out)
                ),
                "entry_tsv": None if entry_tsv_out is None else str(entry_tsv_out),
                "peak_tsv": None if peak_tsv_out is None else str(peak_tsv_out),
            },
        },
        out_path=out_path,
    )

COMMANDS = (
    spectrum_annotate_command,
    spectrum_score_chimeric_command,
    raw_signal_evidence_card_command,
    precursor_isotope_fit_command,
)

# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi
# ruff: noqa: F401,F403,F405

"""Chromatogram and DIA trace Python API entrypoints."""

from __future__ import annotations

from bijux_proteomics.interfaces.support import *  # noqa: F401,F403,F405


def run_xic_extract_command(
    input_mzml: Path,
    target_table: Path,
    tolerance_da: float | None,
    tolerance_ppm: float | None,
    tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    try:
        report = extract_mzml_xic_traces(
            input_mzml,
            target_table,
            tolerance_da=tolerance_da,
            tolerance_ppm=tolerance_ppm,
        )
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc
    if tsv_out is not None:
        _write_text_output(tsv_out, render_xic_traces_tsv(report))
    payload = report.to_dict()
    payload["tsv_out"] = str(tsv_out) if tsv_out is not None else None
    _emit_json(payload, out_path=out_path)


def run_xic_pick_peaks_command(
    input_mzml: Path,
    target_table: Path,
    tolerance_da: float | None,
    tolerance_ppm: float | None,
    trace_tsv_out: Path | None,
    peak_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    try:
        report = extract_mzml_chromatographic_peaks(
            input_mzml,
            target_table,
            tolerance_da=tolerance_da,
            tolerance_ppm=tolerance_ppm,
        )
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc
    if trace_tsv_out is not None:
        _write_text_output(trace_tsv_out, render_xic_traces_tsv(report.trace_report))
    if peak_tsv_out is not None:
        _write_text_output(peak_tsv_out, render_chromatographic_peaks_tsv(report))
    payload = report.to_dict()
    payload["trace_tsv_out"] = str(trace_tsv_out) if trace_tsv_out is not None else None
    payload["peak_tsv_out"] = str(peak_tsv_out) if peak_tsv_out is not None else None
    _emit_json(payload, out_path=out_path)


def run_xic_align_retention_times_command(
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
    try:
        report = extract_mzml_retention_time_alignment(
            input_mzml,
            target_table,
            tolerance_da=tolerance_da,
            tolerance_ppm=tolerance_ppm,
            reference_run_id=reference_run_id,
            aligned_rt_tolerance_seconds=aligned_rt_tolerance_seconds,
            min_anchor_count=min_anchor_count,
        )
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc
    if model_tsv_out is not None:
        _write_text_output(
            model_tsv_out,
            render_retention_time_alignment_models_tsv(report),
        )
    if residual_tsv_out is not None:
        _write_text_output(
            residual_tsv_out,
            render_retention_time_alignment_residuals_tsv(report),
        )
    if failed_anchor_tsv_out is not None:
        _write_text_output(
            failed_anchor_tsv_out,
            render_retention_time_alignment_failed_anchors_tsv(report),
        )
    payload = report.to_dict()
    payload["outputs"] = {
        "model_tsv": None if model_tsv_out is None else str(model_tsv_out),
        "residual_tsv": None if residual_tsv_out is None else str(residual_tsv_out),
        "failed_anchor_tsv": (
            None if failed_anchor_tsv_out is None else str(failed_anchor_tsv_out)
        ),
    }
    _emit_json(payload, out_path=out_path)


def run_xic_score_evidence_command(
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
    try:
        report = extract_mzml_chromatographic_evidence(
            input_mzml,
            target_table,
            tolerance_da=tolerance_da,
            tolerance_ppm=tolerance_ppm,
            aligned_rt_tolerance_seconds=aligned_rt_tolerance_seconds,
            min_anchor_count=min_anchor_count,
        )
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc
    if target_tsv_out is not None:
        _write_text_output(
            target_tsv_out,
            render_chromatographic_target_evidence_tsv(report),
        )
    if peptide_tsv_out is not None:
        _write_text_output(
            peptide_tsv_out,
            render_chromatographic_peptide_evidence_tsv(report),
        )
    payload = report.to_dict()
    payload["outputs"] = {
        "target_tsv": None if target_tsv_out is None else str(target_tsv_out),
        "peptide_tsv": None if peptide_tsv_out is None else str(peptide_tsv_out),
    }
    _emit_json(payload, out_path=out_path)


def run_dia_fragment_coelution_command(
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
    try:
        report = extract_mzml_dia_fragment_trace_coelution(
            input_mzml,
            target_table,
            tolerance_da=tolerance_da,
            tolerance_ppm=tolerance_ppm,
            apex_tolerance_seconds=apex_tolerance_seconds,
            min_correlation=min_correlation,
            min_passing_fragment_count=min_passing_fragment_count,
        )
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc
    ratio_report = score_dia_fragment_ratio_stability(report)
    if run_tsv_out is not None:
        _write_text_output(
            run_tsv_out,
            render_dia_fragment_coelution_runs_tsv(report),
        )
    if fragment_tsv_out is not None:
        _write_text_output(
            fragment_tsv_out,
            render_dia_fragment_coelution_fragments_tsv(report),
        )
    if ratio_fragment_tsv_out is not None:
        _write_text_output(
            ratio_fragment_tsv_out,
            render_fragment_ratio_stability_fragments_tsv(ratio_report),
        )
    if ratio_observation_tsv_out is not None:
        _write_text_output(
            ratio_observation_tsv_out,
            render_fragment_ratio_stability_observations_tsv(ratio_report),
        )
    payload = report.to_dict()
    payload["fragment_ratio_stability_summary"] = ratio_report.summary.to_dict()
    payload["fragment_ratio_fragments"] = [
        entry.to_dict() for entry in ratio_report.fragment_entries
    ]
    payload["fragment_ratio_observations"] = [
        entry.to_dict() for entry in ratio_report.observation_entries
    ]
    payload["outputs"] = {
        "run_tsv": None if run_tsv_out is None else str(run_tsv_out),
        "fragment_tsv": None if fragment_tsv_out is None else str(fragment_tsv_out),
        "ratio_fragment_tsv": (
            None if ratio_fragment_tsv_out is None else str(ratio_fragment_tsv_out)
        ),
        "ratio_observation_tsv": (
            None
            if ratio_observation_tsv_out is None
            else str(ratio_observation_tsv_out)
        ),
    }
    _emit_json(payload, out_path=out_path)


__all__ = [
    "run_xic_extract_command",
    "run_xic_pick_peaks_command",
    "run_xic_align_retention_times_command",
    "run_xic_score_evidence_command",
    "run_dia_fragment_coelution_command",
]

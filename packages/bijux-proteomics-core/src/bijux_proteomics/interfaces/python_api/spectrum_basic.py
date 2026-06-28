# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi
"""Spectrum parsing and QC Python API entrypoints."""

from __future__ import annotations

from bijux_proteomics._output_tables import write_output_table_tsv
from bijux_proteomics.interfaces.support.foundation import (
    Path,
    click,
    json,
)
from bijux_proteomics.interfaces.support.io_and_dia import (
    build_mzml_practical_review_report,
    build_spectrum_collection_summary,
    build_spectrum_metrics,
    build_spectrum_provenance_manifest,
    build_spectrum_run_qc_plot_payload,
    build_spectrum_run_qc_report,
    build_spectrum_summary_table_report,
    build_streaming_parse_profile,
    export_spectra_jsonl,
    extract_mzml_chromatograms,
    parse_mgf,
    parse_mzml,
    render_spectrum_distribution_tsv,
    render_spectrum_run_qc_distribution_tsv,
    render_spectrum_run_qc_flagged_spectra_tsv,
    render_spectrum_run_qc_spectra_tsv,
    render_spectrum_run_qc_summary_tsv,
    render_spectrum_run_qc_time_bins_tsv,
    render_spectrum_run_qc_trace_tsv,
    render_spectrum_summary_tsv,
)
from bijux_proteomics.interfaces.support.output_protocol import (
    _emit_json,
    _write_text_output,
)


def run_spectrum_parse_command(
    input_mgf: Path,
    chunk_size: int,
    accepted_jsonl_out: Path | None,
    rejected_json_out: Path | None,
    out_path: Path | None,
) -> None:
    report = parse_mgf(input_mgf)
    streaming_profile = build_streaming_parse_profile(
        input_mgf,
        format_name="mgf",
        chunk_size=chunk_size,
    )

    if accepted_jsonl_out is not None:
        accepted_jsonl_out.write_text(
            "".join(
                json.dumps(
                    spectrum.to_dict(),
                    sort_keys=True,
                    separators=(",", ":"),
                )
                + "\n"
                for spectrum in report.accepted_spectra
            ),
            encoding="utf-8",
        )
    if rejected_json_out is not None:
        rejected_json_out.write_text(
            json.dumps(
                [block.to_dict() for block in report.rejected_blocks],
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )

    payload = {
        "parse_report": report.to_dict(),
        "summary": build_spectrum_collection_summary(report).to_dict(),
        "streaming_profile": streaming_profile.to_dict(),
        "accepted_jsonl_out": str(accepted_jsonl_out) if accepted_jsonl_out else None,
        "rejected_json_out": str(rejected_json_out) if rejected_json_out else None,
    }
    _emit_json(payload, out_path=out_path)


def run_spectrum_stats_command(
    input_mgf: Path,
    provenance_out: Path | None,
    out_path: Path | None,
) -> None:
    report = parse_mgf(input_mgf)
    summary = build_spectrum_collection_summary(report)
    provenance = build_spectrum_provenance_manifest(
        source_path=input_mgf, parse_report=report
    )
    if provenance_out is not None:
        provenance_out.write_text(provenance.to_stable_json() + "\n")
    payload = {
        "summary": summary.to_dict(),
        "provenance": provenance.to_dict(),
        "metrics": [
            build_spectrum_metrics(spectrum).to_dict()
            for spectrum in report.accepted_spectra
        ],
    }
    _emit_json(payload, out_path=out_path)


def run_spectrum_summary_command(
    input_path: Path,
    kind: str,
    summary_tsv_out: Path | None,
    charge_tsv_out: Path | None,
    precursor_tsv_out: Path | None,
    peak_count_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    resolved_kind = kind
    if resolved_kind == "auto":
        suffix = input_path.suffix.lower()
        if suffix == ".mgf":
            resolved_kind = "mgf"
        elif suffix == ".mzml":
            resolved_kind = "mzml"
        else:
            raise click.ClickException(
                "cannot infer spectrum summary kind; use --kind mgf or --kind mzml"
            )

    if resolved_kind == "mgf":
        mgf_parse_report = parse_mgf(input_path)
        report = build_spectrum_summary_table_report(
            mgf_parse_report.accepted_spectra,
            source_kind="mgf",
            rejected_count=len(mgf_parse_report.rejected_blocks),
        )
    elif resolved_kind == "mzml":
        mzml_parse_report = parse_mzml(input_path)
        report = build_spectrum_summary_table_report(
            mzml_parse_report.accepted_spectra,
            source_kind="mzml",
            rejected_count=len(mzml_parse_report.rejected_spectra),
        )
    else:
        raise click.ClickException("spectrum-summary supports only mgf and mzml")

    if summary_tsv_out is not None:
        write_output_table_tsv(summary_tsv_out, render_spectrum_summary_tsv(report))
    if charge_tsv_out is not None:
        write_output_table_tsv(
            charge_tsv_out,
            render_spectrum_distribution_tsv(
                report.charge_distribution,
                distribution_name="charge",
            ),
        )
    if precursor_tsv_out is not None:
        write_output_table_tsv(
            precursor_tsv_out,
            render_spectrum_distribution_tsv(
                report.precursor_mz_distribution,
                distribution_name="precursor_mz",
            ),
        )
    if peak_count_tsv_out is not None:
        write_output_table_tsv(
            peak_count_tsv_out,
            render_spectrum_distribution_tsv(
                report.peak_count_distribution,
                distribution_name="peak_count",
            ),
        )

    payload = report.to_dict()
    payload["summary_tsv_out"] = str(summary_tsv_out) if summary_tsv_out else None
    payload["charge_tsv_out"] = str(charge_tsv_out) if charge_tsv_out else None
    payload["precursor_tsv_out"] = str(precursor_tsv_out) if precursor_tsv_out else None
    payload["peak_count_tsv_out"] = (
        str(peak_count_tsv_out) if peak_count_tsv_out else None
    )
    _emit_json(payload, out_path=out_path)


def run_spectrum_qc_command(
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
    resolved_kind = kind
    if resolved_kind == "auto":
        suffix = input_path.suffix.lower()
        if suffix == ".mgf":
            resolved_kind = "mgf"
        elif suffix == ".mzml":
            resolved_kind = "mzml"
        else:
            raise click.ClickException(
                "cannot infer spectrum QC kind; use --kind mgf or --kind mzml"
            )

    if resolved_kind == "mgf":
        mgf_parse_report = parse_mgf(input_path)
        report = build_spectrum_run_qc_report(
            mgf_parse_report.accepted_spectra,
            source_kind="mgf",
            rejected_count=len(mgf_parse_report.rejected_blocks),
            time_bin_seconds=time_bin_seconds,
        )
    elif resolved_kind == "mzml":
        mzml_parse_report = parse_mzml(input_path)
        report = build_spectrum_run_qc_report(
            mzml_parse_report.accepted_spectra,
            source_kind="mzml",
            rejected_count=len(mzml_parse_report.rejected_spectra),
            chromatograms=extract_mzml_chromatograms(input_path),
            time_bin_seconds=time_bin_seconds,
        )
    else:
        raise click.ClickException("spectrum-qc supports only mgf and mzml")

    if summary_tsv_out is not None:
        _write_text_output(summary_tsv_out, render_spectrum_run_qc_summary_tsv(report))
    if msms_tsv_out is not None:
        _write_text_output(msms_tsv_out, render_spectrum_run_qc_time_bins_tsv(report))
    if tic_tsv_out is not None:
        _write_text_output(
            tic_tsv_out,
            render_spectrum_run_qc_trace_tsv(report.tic_trace, trace_name="tic"),
        )
    if bpc_tsv_out is not None:
        _write_text_output(
            bpc_tsv_out,
            render_spectrum_run_qc_trace_tsv(report.bpc_trace, trace_name="bpc"),
        )
    if charge_tsv_out is not None:
        _write_text_output(
            charge_tsv_out,
            render_spectrum_run_qc_distribution_tsv(
                report.charge_distribution,
                distribution_name="charge",
            ),
        )
    if precursor_intensity_tsv_out is not None:
        _write_text_output(
            precursor_intensity_tsv_out,
            render_spectrum_run_qc_distribution_tsv(
                report.precursor_intensity_distribution,
                distribution_name="precursor_intensity",
            ),
        )
    if flagged_tsv_out is not None:
        _write_text_output(
            flagged_tsv_out,
            render_spectrum_run_qc_flagged_spectra_tsv(report),
        )
    if spectrum_qc_tsv_out is not None:
        _write_text_output(
            spectrum_qc_tsv_out,
            render_spectrum_run_qc_spectra_tsv(report),
        )
    plot_payload = build_spectrum_run_qc_plot_payload(report)
    if plot_out is not None:
        plot_out.write_text(plot_payload.to_stable_json() + "\n", encoding="utf-8")

    payload = report.to_dict()
    payload["summary_tsv_out"] = str(summary_tsv_out) if summary_tsv_out else None
    payload["msms_tsv_out"] = str(msms_tsv_out) if msms_tsv_out else None
    payload["tic_tsv_out"] = str(tic_tsv_out) if tic_tsv_out else None
    payload["bpc_tsv_out"] = str(bpc_tsv_out) if bpc_tsv_out else None
    payload["charge_tsv_out"] = str(charge_tsv_out) if charge_tsv_out else None
    payload["precursor_intensity_tsv_out"] = (
        str(precursor_intensity_tsv_out) if precursor_intensity_tsv_out else None
    )
    payload["flagged_tsv_out"] = str(flagged_tsv_out) if flagged_tsv_out else None
    payload["spectrum_qc_tsv_out"] = (
        str(spectrum_qc_tsv_out) if spectrum_qc_tsv_out else None
    )
    payload["plot_out"] = str(plot_out) if plot_out else None
    _emit_json(payload, out_path=out_path)


def run_mzml_inspect_command(
    input_mzml: Path,
    spectra_jsonl_out: Path | None,
    chromatograms_json_out: Path | None,
    out_path: Path | None,
) -> None:
    review = build_mzml_practical_review_report(input_mzml)
    parse_report = parse_mzml(input_mzml)

    if spectra_jsonl_out is not None:
        export_spectra_jsonl(parse_report.accepted_spectra, spectra_jsonl_out)
    if chromatograms_json_out is not None:
        chromatograms_json_out.write_text(
            review.chromatograms.to_stable_json() + "\n",
            encoding="utf-8",
        )

    payload = review.to_dict()
    payload["spectra_jsonl_out"] = (
        str(spectra_jsonl_out) if spectra_jsonl_out is not None else None
    )
    payload["chromatograms_json_out"] = (
        str(chromatograms_json_out) if chromatograms_json_out is not None else None
    )
    _emit_json(payload, out_path=out_path)


__all__ = [
    "run_spectrum_parse_command",
    "run_spectrum_stats_command",
    "run_spectrum_summary_command",
    "run_spectrum_qc_command",
    "run_mzml_inspect_command",
]

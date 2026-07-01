# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi
"""Input validation and experiment planning Python API entrypoints."""

from __future__ import annotations

from bijux_proteomics.interfaces.support.foundation import (
    Path,
    click,
)
from bijux_proteomics.interfaces.support.identification import (
    apply_q_values,
    build_contaminant_peptide_match_report,
    build_peptide_summary_report,
    build_protein_summary_report,
    build_psm_evidence_inspection_report,
    build_psm_summary_report,
    parse_psm_tsv,
)
from bijux_proteomics.interfaces.support.io_and_dia import (
    FormatConversionTarget,
    ProteomicsFormatKind,
    build_mzml_collection_summary,
    build_spectrum_collection_summary,
    build_spectrum_metrics,
    convert_proteomics_format,
    parse_experimental_design_table,
    parse_mgf,
    parse_mzml,
    validate_proteomics_input,
)
from bijux_proteomics.interfaces.support.output_protocol.artifact_output import (
    _emit_json,
    _read_identifier_lines,
    _write_text_output,
)
from bijux_proteomics.interfaces.support.output_protocol.protocol_policy import (
    _build_protocol_consistency_report_from_inputs,
)
from bijux_proteomics.interfaces.support.review_sequences_study import (
    FastaParseMode,
    build_experiment_feasibility_report,
    build_fasta_database_profile,
    build_fasta_stats,
    build_lcms_run_qc_report,
    build_sample_sheet_repair_suggestion_report,
    export_sample_sheet_repair_suggestions_tsv,
    parse_fasta_document,
    render_experiment_feasibility_group_sizes_tsv,
    render_experiment_feasibility_invalid_contrasts_tsv,
    render_experiment_feasibility_missing_metadata_tsv,
    render_experiment_feasibility_model_support_tsv,
    render_experiment_feasibility_valid_contrasts_tsv,
    render_protocol_consistency_tsv,
)
from bijux_proteomics.interfaces.support.sequence_support.input_resolution import (
    _default_psm_mapping,
    _infer_input_kind,
)


def run_validate_command(
    input_path: Path,
    input_kind: str,
    mode: str,
    out_path: Path | None,
) -> None:
    resolved_kind = _infer_input_kind(input_path, input_kind)
    try:
        report = validate_proteomics_input(
            input_path,
            input_kind=ProteomicsFormatKind(resolved_kind),
        )
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc
    _emit_json(report, out_path=out_path)


def run_summarize_command(
    input_path: Path,
    input_kind: str,
    mode: str,
    out_path: Path | None,
) -> None:
    resolved_kind = _infer_input_kind(input_path, input_kind)
    if resolved_kind == "fasta":
        fasta_report = parse_fasta_document(
            input_path.read_text(), mode=FastaParseMode(mode)
        )
        payload = {
            "input_kind": resolved_kind,
            "summary": build_fasta_stats(
                fasta_report.accepted_records,
                rejected_records=fasta_report.rejected_records,
            ).to_dict(),
            "profile": build_fasta_database_profile(
                fasta_report.accepted_records,
                rejected_records=fasta_report.rejected_records,
            ).to_dict(),
            "database_composition": fasta_report.database_composition.to_dict(),
            "rejected_records": len(fasta_report.rejected_records),
            "duplicate_accessions": list(fasta_report.duplicate_accessions),
        }
    elif resolved_kind == "psm":
        psm_report = parse_psm_tsv(input_path, mapping=_default_psm_mapping())
        normalized = apply_q_values(psm_report.accepted_records)
        payload = {
            "input_kind": resolved_kind,
            "inspection": build_psm_evidence_inspection_report(psm_report).to_dict(),
            "psm_summary": build_psm_summary_report(normalized).to_dict(),
            "peptide_summary": build_peptide_summary_report(normalized).to_dict(),
            "protein_summary": build_protein_summary_report(normalized).to_dict(),
            "contaminant_report": build_contaminant_peptide_match_report(
                normalized
            ).to_dict(),
            "rejected_rows": len(psm_report.rejected_rows),
        }
    elif resolved_kind == "mgf":
        mgf_report = parse_mgf(input_path)
        payload = {
            "input_kind": resolved_kind,
            "summary": build_spectrum_collection_summary(mgf_report).to_dict(),
            "metrics": [
                build_spectrum_metrics(spectrum).to_dict()
                for spectrum in mgf_report.accepted_spectra
            ],
        }
    elif resolved_kind == "mzml":
        mzml_report = parse_mzml(input_path)
        payload = {
            "input_kind": resolved_kind,
            "metadata": mzml_report.metadata.to_dict(),
            "summary": build_mzml_collection_summary(mzml_report).to_dict(),
            "metrics": [
                build_spectrum_metrics(spectrum).to_dict()
                for spectrum in mzml_report.accepted_spectra
            ],
        }
    elif resolved_kind == "design-table":
        design_report = parse_experimental_design_table(input_path)
        payload = {
            "input_kind": resolved_kind,
            "accepted_entries": len(design_report.accepted_entries),
            "rejected_rows": len(design_report.rejected_rows),
            "instruments": sorted(
                {
                    entry.instrument
                    for entry in design_report.accepted_entries
                    if entry.instrument is not None
                }
            ),
            "search_engines": sorted(
                {
                    entry.search_engine
                    for entry in design_report.accepted_entries
                    if entry.search_engine is not None
                }
            ),
        }
    else:
        raise click.ClickException(
            "summarize currently supports fasta, psm, mgf, mzml, and design-table inputs"
        )
    _emit_json(payload, out_path=out_path)


def run_experiment_feasibility_command(
    design_path: Path,
    condition_a: str | None,
    condition_b: str | None,
    batch_field: str | None,
    pairing_field: str | None,
    timepoint_field: str | None,
    ordered_timepoints: tuple[str, ...],
    minimum_statistical_units_per_condition: int,
    valid_contrasts_tsv_out: Path | None,
    invalid_contrasts_tsv_out: Path | None,
    group_sizes_tsv_out: Path | None,
    missing_metadata_tsv_out: Path | None,
    model_support_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    try:
        design_report = parse_experimental_design_table(design_path)
        report = build_experiment_feasibility_report(
            design_report,
            condition_a=condition_a,
            condition_b=condition_b,
            batch_field=batch_field,
            pairing_field=pairing_field,
            timepoint_field=timepoint_field,
            ordered_timepoints=ordered_timepoints,
            minimum_statistical_units_per_condition=(
                minimum_statistical_units_per_condition
            ),
        )
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if valid_contrasts_tsv_out is not None:
        _write_text_output(
            valid_contrasts_tsv_out,
            render_experiment_feasibility_valid_contrasts_tsv(report),
        )
    if invalid_contrasts_tsv_out is not None:
        _write_text_output(
            invalid_contrasts_tsv_out,
            render_experiment_feasibility_invalid_contrasts_tsv(report),
        )
    if group_sizes_tsv_out is not None:
        _write_text_output(
            group_sizes_tsv_out,
            render_experiment_feasibility_group_sizes_tsv(report),
        )
    if missing_metadata_tsv_out is not None:
        _write_text_output(
            missing_metadata_tsv_out,
            render_experiment_feasibility_missing_metadata_tsv(report),
        )
    if model_support_tsv_out is not None:
        _write_text_output(
            model_support_tsv_out,
            render_experiment_feasibility_model_support_tsv(report),
        )

    _emit_json(
        {
            "report": report.to_dict(),
            "outputs": {
                "valid_contrasts_tsv": (
                    None
                    if valid_contrasts_tsv_out is None
                    else str(valid_contrasts_tsv_out)
                ),
                "invalid_contrasts_tsv": (
                    None
                    if invalid_contrasts_tsv_out is None
                    else str(invalid_contrasts_tsv_out)
                ),
                "group_sizes_tsv": (
                    None if group_sizes_tsv_out is None else str(group_sizes_tsv_out)
                ),
                "missing_metadata_tsv": (
                    None
                    if missing_metadata_tsv_out is None
                    else str(missing_metadata_tsv_out)
                ),
                "model_support_tsv": (
                    None
                    if model_support_tsv_out is None
                    else str(model_support_tsv_out)
                ),
            },
        },
        out_path=out_path,
    )


def run_protocol_consistency_report_command(
    protocol_context_tsv: Path,
    spectra_path: Path | None,
    psm_path: Path | None,
    proteins_fasta: Path | None,
    reporter_table: Path | None,
    ptm_evidence_tsv: Path | None,
    diagnostics_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    try:
        run_qc_report = None
        digestion_inputs = (spectra_path, psm_path, proteins_fasta)
        if any(path is not None for path in digestion_inputs) and any(
            path is None for path in digestion_inputs
        ):
            raise ValueError(
                "spectra, psm, and proteins-fasta must be provided together for digestion consistency checks"
            )
        if all(path is not None for path in digestion_inputs):
            proteins_fasta_path = proteins_fasta
            spectra_input_path = spectra_path
            psm_input_path = psm_path
            if (
                proteins_fasta_path is None
                or spectra_input_path is None
                or psm_input_path is None
            ):
                raise ValueError(
                    "digestion consistency checks require spectra, psm, and proteins-fasta inputs"
                )
            fasta_report = parse_fasta_document(
                proteins_fasta_path.read_text(),
                mode=FastaParseMode.STRICT,
            )
            if fasta_report.rejected_records:
                rejected = ", ".join(
                    record.source_identifier for record in fasta_report.rejected_records
                )
                raise ValueError(
                    "FASTA input contains rejected records under strict mode: "
                    f"{rejected}"
                )
            spectrum_report = parse_mgf(spectra_input_path)
            psm_report = parse_psm_tsv(psm_input_path, mapping=_default_psm_mapping())
            run_qc_report = build_lcms_run_qc_report(
                spectrum_report.accepted_spectra,
                psm_report.accepted_records,
                protein_sequences={
                    record.canonical_accession: record.residues
                    for record in fasta_report.accepted_records
                },
            )
        report = _build_protocol_consistency_report_from_inputs(
            protocol_context_tsv_path=protocol_context_tsv,
            run_qc_report=run_qc_report,
            reporter_table_path=reporter_table,
            ptm_evidence_tsv_path=ptm_evidence_tsv,
        )
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if diagnostics_tsv_out is not None:
        _write_text_output(
            diagnostics_tsv_out,
            render_protocol_consistency_tsv(report),
        )
    _emit_json(
        {
            "report": report.to_dict(),
            "outputs": {
                "diagnostics_tsv": (
                    None if diagnostics_tsv_out is None else str(diagnostics_tsv_out)
                )
            },
        },
        out_path=out_path,
    )


def run_sample_sheet_repair_suggestions_command(
    design_path: Path,
    observed_sample_ids: tuple[str, ...],
    observed_run_ids: tuple[str, ...],
    observed_sample_id_file: Path | None,
    observed_run_id_file: Path | None,
    suggestions_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    try:
        design_report = parse_experimental_design_table(design_path)
        report = build_sample_sheet_repair_suggestion_report(
            design_report,
            observed_sample_ids=(
                *observed_sample_ids,
                *_read_identifier_lines(observed_sample_id_file),
            ),
            observed_run_ids=(
                *observed_run_ids,
                *_read_identifier_lines(observed_run_id_file),
            ),
        )
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if suggestions_tsv_out is not None:
        export_sample_sheet_repair_suggestions_tsv(report, suggestions_tsv_out)

    _emit_json(
        {
            "report": report.to_dict(),
            "outputs": {
                "suggestions_tsv": (
                    None if suggestions_tsv_out is None else str(suggestions_tsv_out)
                )
            },
        },
        out_path=out_path,
    )


def run_format_convert_command(
    input_path: Path,
    input_kind: str,
    target_format: str,
    out_path: Path,
) -> None:
    resolved_kind = _infer_input_kind(input_path, input_kind)
    try:
        report = convert_proteomics_format(
            input_path=input_path,
            output_path=out_path,
            input_kind=ProteomicsFormatKind(resolved_kind),
            target_format=FormatConversionTarget(target_format),
        )
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc
    _emit_json(report)


__all__ = [
    "run_validate_command",
    "run_summarize_command",
    "run_experiment_feasibility_command",
    "run_protocol_consistency_report_command",
    "run_sample_sheet_repair_suggestions_command",
    "run_format_convert_command",
]

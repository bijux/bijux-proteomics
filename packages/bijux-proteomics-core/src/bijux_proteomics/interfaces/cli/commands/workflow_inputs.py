# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi
# ruff: noqa: F401,F403,F405

"""Input validation and experiment planning CLI commands."""

from __future__ import annotations

from bijux_proteomics.interfaces.cli.support import *  # noqa: F401,F403,F405

@click.command("validate")
@click.argument(
    "input_path", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--kind",
    "input_kind",
    type=_validate_kind_choice(),
    default="auto",
    show_default=True,
)
@click.option(
    "--mode",
    type=_mode_choice(),
    default=FastaParseMode.STRICT.value,
    show_default=True,
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
    help="Optional JSON validation output path.",
)
def validate_command(
    input_path: Path,
    input_kind: str,
    mode: str,
    out_path: Path | None,
) -> None:
    'Validate one FASTA, PSM TSV, MGF, mzML, design table, or modification registry input.'
    return run_validate_command(input_path, input_kind, mode, out_path)

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

@click.command("summarize")
@click.argument(
    "input_path", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--kind",
    "input_kind",
    type=_validate_kind_choice(),
    default="auto",
    show_default=True,
)
@click.option(
    "--mode",
    type=_mode_choice(),
    default=FastaParseMode.STRICT.value,
    show_default=True,
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
    help="Optional JSON summary output path.",
)
def summarize_command(
    input_path: Path,
    input_kind: str,
    mode: str,
    out_path: Path | None,
) -> None:
    'Summarize one FASTA, PSM TSV, MGF, mzML, or design-table input.'
    return run_summarize_command(input_path, input_kind, mode, out_path)

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

@click.command("experiment-feasibility")
@click.argument(
    "design_path", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option("--condition-a", default=None)
@click.option("--condition-b", default=None)
@click.option("--batch-field", default=None)
@click.option("--pairing-field", default=None)
@click.option("--timepoint-field", default=None)
@click.option("--ordered-timepoint", "ordered_timepoints", multiple=True)
@click.option(
    "--minimum-statistical-units-per-condition",
    default=2,
    show_default=True,
    type=int,
)
@click.option(
    "--valid-contrasts-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--invalid-contrasts-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--group-sizes-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--missing-metadata-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
@click.option(
    "--model-support-tsv-out",
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
def experiment_feasibility_command(
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
    'Report what a study design can and cannot support before analysis.'
    return run_experiment_feasibility_command(design_path, condition_a, condition_b, batch_field, pairing_field, timepoint_field, ordered_timepoints, minimum_statistical_units_per_condition, valid_contrasts_tsv_out, invalid_contrasts_tsv_out, group_sizes_tsv_out, missing_metadata_tsv_out, model_support_tsv_out, out_path)

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

@click.command("protocol-consistency-report")
@click.argument(
    "protocol_context_tsv",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
)
@click.option(
    "--spectra",
    "spectra_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--psm",
    "psm_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--proteins-fasta",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--reporter-table",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--ptm-evidence-tsv",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--diagnostics-tsv-out",
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
def protocol_consistency_report_command(
    protocol_context_tsv: Path,
    spectra_path: Path | None,
    psm_path: Path | None,
    proteins_fasta: Path | None,
    reporter_table: Path | None,
    ptm_evidence_tsv: Path | None,
    diagnostics_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    'Check whether observed evidence matches the declared lab protocol context.'
    return run_protocol_consistency_report_command(protocol_context_tsv, spectra_path, psm_path, proteins_fasta, reporter_table, ptm_evidence_tsv, diagnostics_tsv_out, out_path)

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
            fasta_report = parse_fasta_document(
                proteins_fasta.read_text(),
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
            spectrum_report = parse_mgf(spectra_path)
            psm_report = parse_psm_tsv(psm_path, mapping=_default_psm_mapping())
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

@click.command("sample-sheet-repair-suggestions")
@click.argument(
    "design_path", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--observed-sample-id",
    "observed_sample_ids",
    multiple=True,
    help="Observed sample id from analysis data. Repeat for multiple ids.",
)
@click.option(
    "--observed-run-id",
    "observed_run_ids",
    multiple=True,
    help="Observed run id from analysis data. Repeat for multiple ids.",
)
@click.option(
    "--observed-sample-id-file",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
    help="Optional text file with one observed sample id per line.",
)
@click.option(
    "--observed-run-id-file",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
    help="Optional text file with one observed run id per line.",
)
@click.option(
    "--suggestions-tsv-out",
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
def sample_sheet_repair_suggestions_command(
    design_path: Path,
    observed_sample_ids: tuple[str, ...],
    observed_run_ids: tuple[str, ...],
    observed_sample_id_file: Path | None,
    observed_run_id_file: Path | None,
    suggestions_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    'Suggest exact sample-sheet repairs without rewriting study metadata.'
    return run_sample_sheet_repair_suggestions_command(design_path, observed_sample_ids, observed_run_ids, observed_sample_id_file, observed_run_id_file, suggestions_tsv_out, out_path)

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

@click.command("format-convert")
@click.argument(
    "input_path", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--kind",
    "input_kind",
    type=_validate_kind_choice(),
    default="auto",
    show_default=True,
)
@click.option("--to", "target_format", type=_conversion_target_choice(), required=True)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    required=True,
    help="Where to write the converted normalized output.",
)
def format_convert_command(
    input_path: Path,
    input_kind: str,
    target_format: str,
    out_path: Path,
) -> None:
    'Convert one supported input into a normalized Bijux output surface.'
    return run_format_convert_command(input_path, input_kind, target_format, out_path)

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

COMMANDS = (
    validate_command,
    summarize_command,
    experiment_feasibility_command,
    protocol_consistency_report_command,
    sample_sheet_repair_suggestions_command,
    format_convert_command,
)

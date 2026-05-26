# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi
# ruff: noqa: F401,F403,F405

"""Peptide-matrix Python API entrypoints."""

from __future__ import annotations

from bijux_proteomics.interfaces.support import *  # noqa: F401,F403,F405
from bijux_proteomics.identification import parse_psm_tsv_chunked
from bijux_proteomics.quantification import (
    parse_ms1_feature_table_chunked,
    parse_precursor_intensity_table_chunked,
)

def run_peptide_matrix_command(
    input_table: Path,
    input_kind: str,
    grouping_mode: str,
    separate_charge_states: bool,
    aggregation: str,
    top_n: int,
    sample_column: str,
    feature_id_column: str,
    precursor_id_column: str,
    run_column: str,
    spectrum_id_column: str,
    peptide_column: str,
    modified_peptide_column: str,
    intensity_column: str,
    protein_refs_column: str | None,
    charge_column: str,
    score_column: str,
    q_value_column: str | None,
    decoy_label_column: str | None,
    contaminant_label_column: str | None,
    mz_column: str | None,
    retention_time_column: str | None,
    missing_reason_column: str | None,
    protein_separator: str,
    chunk_size_rows: int | None,
    summary_tsv_out: Path | None,
    matrix_tsv_out: Path | None,
    missingness_tsv_out: Path | None,
    missingness_mask_tsv_out: Path | None,
    aggregation_table_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    try:
        grouping = PeptideMatrixGroupingMode(grouping_mode)
        rollup_method = QuantRollupMethod(aggregation)
        if input_kind == "feature":
            feature_mapping = Ms1FeatureColumnMapping(
                sample_id=sample_column,
                feature_id=feature_id_column,
                peptide=peptide_column,
                intensity=intensity_column,
                protein_refs=protein_refs_column,
                charge=charge_column,
                mz=mz_column,
                retention_time_seconds=retention_time_column,
                missing_reason=missing_reason_column,
                protein_separator=protein_separator,
            )
            parse_report = (
                parse_ms1_feature_table_chunked(
                    input_table,
                    mapping=feature_mapping,
                    chunk_size_rows=chunk_size_rows,
                )
                if chunk_size_rows is not None
                else parse_ms1_feature_table(input_table, mapping=feature_mapping)
            )
            report = build_peptide_intensity_matrix_from_features(
                parse_report.accepted_records,
                grouping_mode=grouping,
                separate_charge_states=separate_charge_states,
                aggregation_method=rollup_method,
                top_n=top_n,
            )
            payload = {
                "input_kind": input_kind,
                "accepted_source_records": len(parse_report.accepted_records),
                "rejected_source_records": len(parse_report.rejected_rows),
                "report": report.to_dict(),
            }
        elif input_kind == "precursor":
            precursor_mapping = PrecursorIntensityColumnMapping(
                peptide=peptide_column,
                modified_peptide=modified_peptide_column,
                intensity=intensity_column,
                sample_id=sample_column,
                run_id=run_column,
                protein_refs=protein_refs_column,
                precursor_id=precursor_id_column,
                charge=charge_column,
                missing_reason=missing_reason_column,
                protein_separator=protein_separator,
            )
            precursor_parse_report = (
                parse_precursor_intensity_table_chunked(
                    input_table,
                    mapping=precursor_mapping,
                    chunk_size_rows=chunk_size_rows,
                )
                if chunk_size_rows is not None
                else parse_precursor_intensity_table(
                    input_table,
                    mapping=precursor_mapping,
                )
            )
            report = build_peptide_intensity_matrix_from_precursors(
                precursor_parse_report.accepted_records,
                grouping_mode=grouping,
                separate_charge_states=separate_charge_states,
                aggregation_method=rollup_method,
                top_n=top_n,
            )
            payload = {
                "input_kind": input_kind,
                "accepted_source_records": len(
                    precursor_parse_report.accepted_records
                ),
                "rejected_source_records": len(precursor_parse_report.rejected_rows),
                "report": report.to_dict(),
            }
        else:
            psm_mapping = _build_psm_mapping(
                run_id_column=run_column,
                spectrum_id_column=spectrum_id_column,
                peptide_column=peptide_column,
                modified_peptide_column=modified_peptide_column,
                charge_column=charge_column,
                score_column=score_column,
                q_value_column=q_value_column,
                protein_refs_column=protein_refs_column,
                decoy_label_column=decoy_label_column,
                contaminant_label_column=contaminant_label_column,
                protein_separator=protein_separator,
                intensity_column=intensity_column,
            )
            psm_parse_report = (
                parse_psm_tsv_chunked(
                    input_table,
                    mapping=psm_mapping,
                    chunk_size_rows=chunk_size_rows,
                )
                if chunk_size_rows is not None
                else parse_psm_tsv(input_table, mapping=psm_mapping)
            )
            report = build_peptide_intensity_matrix_from_psms(
                psm_parse_report.accepted_records,
                grouping_mode=grouping,
                separate_charge_states=separate_charge_states,
                aggregation_method=rollup_method,
                top_n=top_n,
            )
            payload = {
                "input_kind": input_kind,
                "accepted_source_records": len(psm_parse_report.accepted_records),
                "rejected_source_records": len(psm_parse_report.rejected_rows),
                "report": report.to_dict(),
            }
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        _write_text_output(
            summary_tsv_out,
            render_peptide_intensity_matrix_summary_tsv(report),
        )
    if matrix_tsv_out is not None:
        _write_text_output(matrix_tsv_out, render_peptide_intensity_matrix_tsv(report))
    if missingness_tsv_out is not None:
        _write_text_output(
            missingness_tsv_out,
            render_peptide_intensity_missingness_tsv(report),
        )
    if missingness_mask_tsv_out is not None:
        _write_text_output(
            missingness_mask_tsv_out,
            render_peptide_intensity_missingness_mask_tsv(report),
        )
    if aggregation_table_tsv_out is not None:
        _write_text_output(
            aggregation_table_tsv_out,
            render_peptide_intensity_aggregation_tsv(report),
        )
    payload["outputs"] = {
        "summary_tsv": None if summary_tsv_out is None else str(summary_tsv_out),
        "matrix_tsv": None if matrix_tsv_out is None else str(matrix_tsv_out),
        "missingness_tsv": (
            None if missingness_tsv_out is None else str(missingness_tsv_out)
        ),
        "missingness_mask_tsv": (
            None
            if missingness_mask_tsv_out is None
            else str(missingness_mask_tsv_out)
        ),
        "aggregation_table_tsv": (
            None
            if aggregation_table_tsv_out is None
            else str(aggregation_table_tsv_out)
        ),
    }
    _emit_json(payload, out_path=out_path)

__all__ = ['run_peptide_matrix_command']

# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi
"""Protein grouping and ambiguity Python API entrypoints."""

from __future__ import annotations

from bijux_proteomics.interfaces.support.foundation import (
    Path,
    click,
)
from bijux_proteomics.interfaces.support.identification import (
    build_core_protein_inference_benchmark_suite,
    build_protein_ambiguity_review_report,
    build_protein_grouping_review_report,
    filter_psms_by_fdr,
    parse_psm_tsv,
    render_protein_ambiguity_entries_tsv,
    render_protein_ambiguity_summary_tsv,
    render_protein_grouping_entries_tsv,
    render_protein_grouping_summary_tsv,
    render_protein_inference_benchmark_assessments_tsv,
    render_protein_inference_benchmark_scenarios_tsv,
    render_protein_inference_benchmark_summary_tsv,
)
from bijux_proteomics.interfaces.support.output_protocol.artifact_output import (
    _emit_json,
    _write_text_output,
)
from bijux_proteomics.interfaces.support.sequence_support.input_resolution import (
    _build_decoy_policy,
    _build_psm_mapping,
)


def run_protein_groups_command(
    input_tsv: Path,
    threshold: float,
    score_orientation: str,
    spectrum_id_column: str,
    peptide_column: str,
    run_id_column: str | None,
    modified_peptide_column: str | None,
    charge_column: str,
    score_column: str,
    q_value_column: str | None,
    protein_refs_column: str | None,
    decoy_label_column: str | None,
    contaminant_label_column: str | None,
    protein_separator: str,
    decoy_prefix: str | None,
    decoy_suffix: str | None,
    summary_tsv_out: Path | None,
    group_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    try:
        mapping = _build_psm_mapping(
            run_id_column=run_id_column,
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
        )
        decoy_policy = _build_decoy_policy(
            decoy_prefix=decoy_prefix,
            decoy_suffix=decoy_suffix,
        )
        parse_report = parse_psm_tsv(
            input_tsv,
            mapping=mapping,
            decoy_policy=decoy_policy,
        )
        filtered_records = filter_psms_by_fdr(
            parse_report.accepted_records,
            threshold=threshold,
            score_orientation=score_orientation,
        )
        review = build_protein_grouping_review_report(filtered_records)
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        _write_text_output(
            summary_tsv_out,
            render_protein_grouping_summary_tsv(review),
        )
    if group_tsv_out is not None:
        _write_text_output(
            group_tsv_out,
            render_protein_grouping_entries_tsv(review),
        )

    payload = {
        "threshold": threshold,
        "score_orientation": score_orientation,
        "accepted_rows": len(parse_report.accepted_records),
        "rejected_rows": len(parse_report.rejected_rows),
        "grouped_rows": len(filtered_records),
        **review.to_dict(),
        "outputs": {
            "summary_tsv": None if summary_tsv_out is None else str(summary_tsv_out),
            "group_tsv": None if group_tsv_out is None else str(group_tsv_out),
        },
    }
    _emit_json(payload, out_path=out_path)


def run_protein_ambiguity_command(
    input_tsv: Path,
    threshold: float,
    score_orientation: str,
    high_q_value: float,
    medium_q_value: float,
    spectrum_id_column: str,
    peptide_column: str,
    run_id_column: str | None,
    modified_peptide_column: str | None,
    charge_column: str,
    score_column: str,
    q_value_column: str | None,
    protein_refs_column: str | None,
    decoy_label_column: str | None,
    contaminant_label_column: str | None,
    protein_separator: str,
    decoy_prefix: str | None,
    decoy_suffix: str | None,
    summary_tsv_out: Path | None,
    ambiguity_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    try:
        mapping = _build_psm_mapping(
            run_id_column=run_id_column,
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
        )
        decoy_policy = _build_decoy_policy(
            decoy_prefix=decoy_prefix,
            decoy_suffix=decoy_suffix,
        )
        parse_report = parse_psm_tsv(
            input_tsv,
            mapping=mapping,
            decoy_policy=decoy_policy,
        )
        filtered_records = filter_psms_by_fdr(
            parse_report.accepted_records,
            threshold=threshold,
            score_orientation=score_orientation,
        )
        review = build_protein_ambiguity_review_report(
            filtered_records,
            threshold=threshold,
            high_q_value=high_q_value,
            medium_q_value=medium_q_value,
        )
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        _write_text_output(
            summary_tsv_out,
            render_protein_ambiguity_summary_tsv(review),
        )
    if ambiguity_tsv_out is not None:
        _write_text_output(
            ambiguity_tsv_out,
            render_protein_ambiguity_entries_tsv(review),
        )

    payload = {
        "threshold": threshold,
        "score_orientation": score_orientation,
        "high_q_value": high_q_value,
        "medium_q_value": medium_q_value,
        "accepted_rows": len(parse_report.accepted_records),
        "rejected_rows": len(parse_report.rejected_rows),
        "grouped_rows": len(filtered_records),
        "ambiguity_rows": len(review.entries),
        **review.to_dict(),
        "outputs": {
            "summary_tsv": None if summary_tsv_out is None else str(summary_tsv_out),
            "ambiguity_tsv": (
                None if ambiguity_tsv_out is None else str(ambiguity_tsv_out)
            ),
        },
    }
    _emit_json(payload, out_path=out_path)


def run_protein_inference_benchmarks_command(
    picked_threshold: float,
    summary_tsv_out: Path | None,
    scenarios_tsv_out: Path | None,
    assessments_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    try:
        suite = build_core_protein_inference_benchmark_suite(
            picked_threshold=picked_threshold
        )
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        _write_text_output(
            summary_tsv_out,
            render_protein_inference_benchmark_summary_tsv(suite),
        )
    if scenarios_tsv_out is not None:
        _write_text_output(
            scenarios_tsv_out,
            render_protein_inference_benchmark_scenarios_tsv(suite),
        )
    if assessments_tsv_out is not None:
        _write_text_output(
            assessments_tsv_out,
            render_protein_inference_benchmark_assessments_tsv(suite),
        )

    payload = suite.to_dict()
    payload["picked_threshold"] = picked_threshold
    payload["outputs"] = {
        "summary_tsv": None if summary_tsv_out is None else str(summary_tsv_out),
        "scenarios_tsv": None if scenarios_tsv_out is None else str(scenarios_tsv_out),
        "assessments_tsv": (
            None if assessments_tsv_out is None else str(assessments_tsv_out)
        ),
    }
    _emit_json(payload, out_path=out_path)


__all__ = [
    "run_protein_groups_command",
    "run_protein_ambiguity_command",
    "run_protein_inference_benchmarks_command",
]

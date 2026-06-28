# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi
"""PSM and evidence review Python API entrypoints."""

from __future__ import annotations

from bijux_proteomics.interfaces.support.foundation import (
    Path,
    click,
)
from bijux_proteomics.interfaces.support.identification import (
    RunDetectionContext,
    apply_q_values,
    build_generic_psm_mapper_report,
    build_peptide_cross_run_reproducibility_report,
    build_peptide_evidence_review_report,
    build_peptide_summary_report,
    build_protein_cross_run_reproducibility_report,
    build_protein_evidence_review_report,
    build_protein_summary_report,
    build_psm_evidence_inspection_report,
    build_psm_summary_report,
    build_search_result_provenance_manifest,
    export_psm_jsonl,
    export_psm_tsv,
    parse_psm_tsv,
    render_cross_run_reproducibility_entries_tsv,
    render_cross_run_reproducibility_summary_tsv,
    render_generic_psm_mapper_tsv,
    render_peptide_evidence_entries_tsv,
    render_peptide_evidence_summary_tsv,
    render_protein_evidence_entries_tsv,
    render_protein_evidence_summary_tsv,
    render_psm_evidence_inspection_summary_tsv,
    render_psm_inspection_distribution_tsv,
    render_rejected_evidence_tsv,
)
from bijux_proteomics.interfaces.support.io_and_dia import parse_experimental_design_table
from bijux_proteomics.interfaces.support.output_protocol import (
    _emit_json,
    _write_text_output,
)
from bijux_proteomics.interfaces.support.sequence_support import (
    _build_decoy_policy,
    _build_psm_mapping,
    _build_run_detection_contexts,
)


def run_psm_map_command(
    input_tsv: Path,
    mapping_path: Path,
    normalized_tsv_out: Path | None,
    rejected_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    try:
        report = build_generic_psm_mapper_report(
            input_tsv,
            mapping_path=mapping_path,
        )
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if normalized_tsv_out is not None:
        _write_text_output(
            normalized_tsv_out,
            render_generic_psm_mapper_tsv(report.mapped_rows),
        )
    if rejected_tsv_out is not None:
        _write_text_output(
            rejected_tsv_out,
            render_rejected_evidence_tsv(report.rejected_evidence_rows),
        )

    payload = {
        "column_mapping": report.column_mapping.to_dict(),
        "source_columns": list(report.source_columns),
        "normalization": {
            "adapter": report.normalization.adapter_manifest.to_dict(),
            "accepted_rows": len(report.normalization.parse_report.accepted_records),
            "rejected_rows": len(report.normalization.parse_report.rejected_rows),
        },
        "summary": report.summary.to_dict(),
        "rejected_rows": [row.to_dict() for row in report.rejected_rows],
        "rejected_evidence_rows": [
            row.to_dict() for row in report.rejected_evidence_rows
        ],
        "mapped_rows": [row.to_dict() for row in report.mapped_rows],
        "outputs": {
            "normalized_tsv": None
            if normalized_tsv_out is None
            else str(normalized_tsv_out),
            "rejected_tsv": None if rejected_tsv_out is None else str(rejected_tsv_out),
        },
    }
    _emit_json(payload, out_path=out_path)


def run_psm_inspect_command(
    input_tsv: Path,
    spectrum_id_column: str,
    peptide_column: str,
    run_id_column: str | None,
    modified_peptide_column: str | None,
    charge_column: str,
    score_column: str,
    q_value_column: str | None,
    pep_column: str | None,
    protein_refs_column: str | None,
    decoy_label_column: str | None,
    contaminant_label_column: str | None,
    protein_separator: str,
    protease: str,
    decoy_prefix: str | None,
    decoy_suffix: str | None,
    jsonl_out: Path | None,
    tsv_out: Path | None,
    provenance_out: Path | None,
    summary_tsv_out: Path | None,
    score_distribution_tsv_out: Path | None,
    q_value_distribution_tsv_out: Path | None,
    charge_distribution_tsv_out: Path | None,
    peptide_length_distribution_tsv_out: Path | None,
    missed_cleavage_distribution_tsv_out: Path | None,
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
            posterior_error_probability_column=pep_column,
            protein_refs_column=protein_refs_column,
            decoy_label_column=decoy_label_column,
            contaminant_label_column=contaminant_label_column,
            protein_separator=protein_separator,
        )
        decoy_policy = _build_decoy_policy(
            decoy_prefix=decoy_prefix,
            decoy_suffix=decoy_suffix,
        )
        report = parse_psm_tsv(
            input_tsv,
            mapping=mapping,
            decoy_policy=decoy_policy,
        )
        normalized = apply_q_values(report.accepted_records)
        inspection = build_psm_evidence_inspection_report(report, protease=protease)
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc

    if jsonl_out is not None:
        export_psm_jsonl(normalized, jsonl_out)
    if tsv_out is not None:
        export_psm_tsv(normalized, tsv_out)
    if summary_tsv_out is not None:
        _write_text_output(
            summary_tsv_out,
            render_psm_evidence_inspection_summary_tsv(inspection),
        )
    if score_distribution_tsv_out is not None:
        _write_text_output(
            score_distribution_tsv_out,
            render_psm_inspection_distribution_tsv(inspection.score_distribution),
        )
    if q_value_distribution_tsv_out is not None:
        _write_text_output(
            q_value_distribution_tsv_out,
            render_psm_inspection_distribution_tsv(inspection.q_value_distribution),
        )
    if charge_distribution_tsv_out is not None:
        _write_text_output(
            charge_distribution_tsv_out,
            render_psm_inspection_distribution_tsv(inspection.charge_distribution),
        )
    if peptide_length_distribution_tsv_out is not None:
        _write_text_output(
            peptide_length_distribution_tsv_out,
            render_psm_inspection_distribution_tsv(
                inspection.peptide_length_distribution
            ),
        )
    if missed_cleavage_distribution_tsv_out is not None:
        _write_text_output(
            missed_cleavage_distribution_tsv_out,
            render_psm_inspection_distribution_tsv(
                inspection.missed_cleavage_distribution
            ),
        )

    provenance = build_search_result_provenance_manifest(
        source_path=input_tsv,
        parse_report=report,
        decoy_policy=decoy_policy,
    )
    if provenance_out is not None:
        provenance_out.write_text(provenance.to_stable_json() + "\n")

    payload = {
        "accepted_rows": len(report.accepted_records),
        "rejected_rows": len(report.rejected_rows),
        "inspection": inspection.to_dict(),
        "psm_summary": build_psm_summary_report(normalized).to_dict(),
        "peptide_summary": build_peptide_summary_report(normalized).to_dict(),
        "protein_summary": build_protein_summary_report(normalized).to_dict(),
        "provenance": provenance.to_dict(),
        "outputs": {
            "summary_tsv": None if summary_tsv_out is None else str(summary_tsv_out),
            "score_distribution_tsv": None
            if score_distribution_tsv_out is None
            else str(score_distribution_tsv_out),
            "q_value_distribution_tsv": None
            if q_value_distribution_tsv_out is None
            else str(q_value_distribution_tsv_out),
            "charge_distribution_tsv": None
            if charge_distribution_tsv_out is None
            else str(charge_distribution_tsv_out),
            "peptide_length_distribution_tsv": None
            if peptide_length_distribution_tsv_out is None
            else str(peptide_length_distribution_tsv_out),
            "missed_cleavage_distribution_tsv": None
            if missed_cleavage_distribution_tsv_out is None
            else str(missed_cleavage_distribution_tsv_out),
        },
    }
    _emit_json(payload, out_path=out_path)


def run_peptide_evidence_command(
    input_tsv: Path,
    threshold: float,
    score_orientation: str,
    strong_q_value: float,
    reproducible_spectrum_count: int,
    spectrum_id_column: str,
    peptide_column: str,
    run_id_column: str | None,
    modified_peptide_column: str | None,
    charge_column: str,
    score_column: str,
    q_value_column: str | None,
    pep_column: str | None,
    protein_refs_column: str | None,
    decoy_label_column: str | None,
    contaminant_label_column: str | None,
    protein_separator: str,
    decoy_prefix: str | None,
    decoy_suffix: str | None,
    summary_tsv_out: Path | None,
    entries_tsv_out: Path | None,
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
            posterior_error_probability_column=pep_column,
            protein_refs_column=protein_refs_column,
            decoy_label_column=decoy_label_column,
            contaminant_label_column=contaminant_label_column,
            protein_separator=protein_separator,
        )
        decoy_policy = _build_decoy_policy(
            decoy_prefix=decoy_prefix,
            decoy_suffix=decoy_suffix,
        )
        report = parse_psm_tsv(
            input_tsv,
            mapping=mapping,
            decoy_policy=decoy_policy,
        )
        review = build_peptide_evidence_review_report(
            report.accepted_records,
            threshold=threshold,
            score_orientation=score_orientation,
            strong_q_value=strong_q_value,
            reproducible_spectrum_count=reproducible_spectrum_count,
        )
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        _write_text_output(
            summary_tsv_out,
            render_peptide_evidence_summary_tsv(review),
        )
    if entries_tsv_out is not None:
        _write_text_output(
            entries_tsv_out,
            render_peptide_evidence_entries_tsv(review),
        )

    payload = review.to_dict()
    payload["accepted_rows"] = len(report.accepted_records)
    payload["rejected_rows"] = len(report.rejected_rows)
    payload["outputs"] = {
        "summary_tsv": None if summary_tsv_out is None else str(summary_tsv_out),
        "entries_tsv": None if entries_tsv_out is None else str(entries_tsv_out),
    }
    _emit_json(payload, out_path=out_path)


def run_protein_evidence_command(
    input_tsv: Path,
    high_q_value: float,
    moderate_q_value: float,
    score_orientation: str,
    design_tsv: Path | None,
    exploratory_protein: tuple[str, ...],
    spectrum_id_column: str,
    peptide_column: str,
    run_id_column: str | None,
    modified_peptide_column: str | None,
    charge_column: str,
    score_column: str,
    q_value_column: str | None,
    pep_column: str | None,
    protein_refs_column: str | None,
    decoy_label_column: str | None,
    contaminant_label_column: str | None,
    protein_separator: str,
    decoy_prefix: str | None,
    decoy_suffix: str | None,
    summary_tsv_out: Path | None,
    entries_tsv_out: Path | None,
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
            posterior_error_probability_column=pep_column,
            protein_refs_column=protein_refs_column,
            decoy_label_column=decoy_label_column,
            contaminant_label_column=contaminant_label_column,
            protein_separator=protein_separator,
        )
        decoy_policy = _build_decoy_policy(
            decoy_prefix=decoy_prefix,
            decoy_suffix=decoy_suffix,
        )
        report = parse_psm_tsv(
            input_tsv,
            mapping=mapping,
            decoy_policy=decoy_policy,
        )
        run_contexts: tuple[RunDetectionContext, ...] = ()
        if design_tsv is not None:
            design_report = parse_experimental_design_table(design_tsv)
            if design_report.rejected_rows:
                raise ValueError("design table contains rejected rows")
            run_contexts = _build_run_detection_contexts(design_report.accepted_entries)
        review = build_protein_evidence_review_report(
            report.accepted_records,
            high_q_value=high_q_value,
            moderate_q_value=moderate_q_value,
            score_orientation=score_orientation,
            run_contexts=run_contexts,
            exploratory_protein_refs=exploratory_protein,
        )
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        _write_text_output(
            summary_tsv_out,
            render_protein_evidence_summary_tsv(review),
        )
    if entries_tsv_out is not None:
        _write_text_output(
            entries_tsv_out,
            render_protein_evidence_entries_tsv(review),
        )

    payload = review.to_dict()
    payload["accepted_rows"] = len(report.accepted_records)
    payload["rejected_rows"] = len(report.rejected_rows)
    payload["outputs"] = {
        "summary_tsv": None if summary_tsv_out is None else str(summary_tsv_out),
        "entries_tsv": None if entries_tsv_out is None else str(entries_tsv_out),
    }
    _emit_json(payload, out_path=out_path)


def run_cross_run_reproducibility_command(
    input_tsv: Path,
    entity_type: str,
    design_tsv: Path,
    exploratory_entity: tuple[str, ...],
    spectrum_id_column: str,
    peptide_column: str,
    run_id_column: str,
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
    entries_tsv_out: Path | None,
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
        psm_report = parse_psm_tsv(
            input_tsv,
            mapping=mapping,
            decoy_policy=decoy_policy,
        )
        design_report = parse_experimental_design_table(design_tsv)
        if design_report.rejected_rows:
            raise ValueError("design table contains rejected rows")
        run_contexts = _build_run_detection_contexts(design_report.accepted_entries)
        if entity_type == "peptide":
            reproducibility_report = build_peptide_cross_run_reproducibility_report(
                psm_report.accepted_records,
                run_contexts=run_contexts,
                exploratory_canonical_peptides=exploratory_entity,
            )
        else:
            reproducibility_report = build_protein_cross_run_reproducibility_report(
                psm_report.accepted_records,
                run_contexts=run_contexts,
                exploratory_protein_refs=exploratory_entity,
            )
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        _write_text_output(
            summary_tsv_out,
            render_cross_run_reproducibility_summary_tsv(reproducibility_report),
        )
    if entries_tsv_out is not None:
        _write_text_output(
            entries_tsv_out,
            render_cross_run_reproducibility_entries_tsv(reproducibility_report),
        )

    payload = reproducibility_report.to_dict()
    payload["accepted_rows"] = len(psm_report.accepted_records)
    payload["rejected_rows"] = len(psm_report.rejected_rows)
    payload["outputs"] = {
        "summary_tsv": None if summary_tsv_out is None else str(summary_tsv_out),
        "entries_tsv": None if entries_tsv_out is None else str(entries_tsv_out),
    }
    _emit_json(payload, out_path=out_path)


__all__ = [
    "run_psm_map_command",
    "run_psm_inspect_command",
    "run_peptide_evidence_command",
    "run_protein_evidence_command",
    "run_cross_run_reproducibility_command",
]

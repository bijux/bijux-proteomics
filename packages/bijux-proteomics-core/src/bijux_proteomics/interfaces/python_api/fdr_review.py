# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi
# ruff: noqa: F401,F403,F405

"""FDR review Python API entrypoints."""

from __future__ import annotations

from bijux_proteomics.interfaces.support import *  # noqa: F401,F403,F405

def run_fdr_command(
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
    pep_column: str | None,
    protein_refs_column: str | None,
    decoy_label_column: str | None,
    contaminant_label_column: str | None,
    protein_separator: str,
    decoy_prefix: str | None,
    decoy_suffix: str | None,
    jsonl_out: Path | None,
    tsv_out: Path | None,
    provenance_out: Path | None,
    summary_tsv_out: Path | None,
    entries_tsv_out: Path | None,
    audit_out: Path | None,
    calibration_out: Path | None,
    score_separation_summary_tsv_out: Path | None,
    score_separation_bins_tsv_out: Path | None,
    error_rate_summary_tsv_out: Path | None,
    error_rate_entries_tsv_out: Path | None,
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
        parse_report = parse_psm_tsv(
            input_tsv,
            mapping=mapping,
            decoy_policy=decoy_policy,
        )
        annotated_records = annotate_psm_error_rates(
            parse_report.accepted_records,
            score_orientation=score_orientation,
        )
        fdr_report = build_psm_target_decoy_fdr_report(
            annotated_records,
            threshold=threshold,
            score_orientation=score_orientation,
        )
        error_rate_report = build_psm_error_rate_annotation_report(
            parse_report.accepted_records,
            score_orientation=score_orientation,
        )
        accepted = tuple(
            entry.psm.model_copy(update={"q_value": entry.q_value})
            for entry in fdr_report.entries
            if entry.accepted
        )
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc

    if jsonl_out is not None:
        export_psm_jsonl(accepted, jsonl_out)
    if tsv_out is not None:
        export_psm_tsv(accepted, tsv_out)
    if summary_tsv_out is not None:
        summary_tsv_out.write_text(
            render_psm_target_decoy_fdr_summary_tsv(fdr_report), encoding="utf-8"
        )
    if entries_tsv_out is not None:
        entries_tsv_out.write_text(
            render_psm_target_decoy_fdr_tsv(fdr_report), encoding="utf-8"
        )

    fdr_policy = FdrPolicy(
        threshold=threshold,
        score_orientation=score_orientation,
        decoy_policy=decoy_policy,
    )
    provenance = build_search_result_provenance_manifest(
        source_path=input_tsv,
        parse_report=parse_report,
        decoy_policy=decoy_policy,
        fdr_policy=fdr_policy,
    )
    audit_trail = build_fdr_audit_trail(
        parse_report.accepted_records,
        threshold=threshold,
        score_orientation=score_orientation,
    )
    calibration_plot = build_calibration_plot_data(
        annotated_records,
        score_orientation=score_orientation,
    )
    score_separation = build_score_separation_diagnostic_report(
        annotated_records,
        score_orientation=score_orientation,
    )
    if provenance_out is not None:
        provenance_out.write_text(provenance.to_stable_json() + "\n")
    if audit_out is not None:
        audit_out.write_text(audit_trail.to_stable_json() + "\n")
    if calibration_out is not None:
        calibration_out.write_text(calibration_plot.to_stable_json() + "\n")
    if score_separation_summary_tsv_out is not None:
        score_separation_summary_tsv_out.write_text(
            render_score_separation_summary_tsv(score_separation),
            encoding="utf-8",
        )
    if score_separation_bins_tsv_out is not None:
        score_separation_bins_tsv_out.write_text(
            render_score_separation_bins_tsv(score_separation),
            encoding="utf-8",
        )
    if error_rate_summary_tsv_out is not None:
        error_rate_summary_tsv_out.write_text(
            render_psm_error_rate_annotation_summary_tsv(error_rate_report),
            encoding="utf-8",
        )
    if error_rate_entries_tsv_out is not None:
        error_rate_entries_tsv_out.write_text(
            render_psm_error_rate_annotation_tsv(error_rate_report),
            encoding="utf-8",
        )

    payload = {
        "threshold": threshold,
        "score_orientation": score_orientation,
        "input_psms": len(parse_report.accepted_records),
        "accepted_psms": len(accepted),
        "fdr_unstable": score_separation.summary.fdr_unstable,
        "fdr_report": fdr_report.summary.to_dict(),
        "fdr_reproducibility_hash": fdr_report.reproducibility_hash,
        "error_rate_annotation": error_rate_report.to_dict(),
        "psm_summary": build_psm_summary_report(accepted).to_dict(),
        "peptide_summary": build_peptide_summary_report(accepted).to_dict(),
        "protein_summary": build_protein_summary_report(accepted).to_dict(),
        "audit_trail": audit_trail.to_dict(),
        "calibration_plot": calibration_plot.to_dict(),
        "score_separation": score_separation.to_dict(),
        "provenance": provenance.to_dict(),
    }
    _emit_json(payload, out_path=out_path)

def run_fdr_reference_check_command(
    reference_json: Path,
    summary_tsv_out: Path | None,
    entries_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    try:
        raw_cases = json.loads(reference_json.read_text(encoding="utf-8"))
        cases = tuple(
            TargetDecoyReferenceCase.model_validate(case) for case in raw_cases
        )
        report = build_target_decoy_reference_validation_report(cases)
    except (ValueError, TypeError) as exc:
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        _write_text_output(
            summary_tsv_out,
            render_target_decoy_reference_summary_tsv(report),
        )
    if entries_tsv_out is not None:
        _write_text_output(
            entries_tsv_out,
            render_target_decoy_reference_entries_tsv(report),
        )

    payload = report.to_dict()
    payload["outputs"] = {
        "summary_tsv": None if summary_tsv_out is None else str(summary_tsv_out),
        "entries_tsv": None if entries_tsv_out is None else str(entries_tsv_out),
    }
    _emit_json(payload, out_path=out_path)

def run_fdr_levels_command(
    input_tsv: Path,
    thresholds: tuple[float, ...],
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
        parse_report = parse_psm_tsv(
            input_tsv,
            mapping=mapping,
            decoy_policy=decoy_policy,
        )
        review = build_evidence_level_fdr_review_report(
            parse_report.accepted_records,
            thresholds=tuple(thresholds),
            score_orientation=score_orientation,
        )
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        _write_text_output(
            summary_tsv_out,
            render_evidence_level_fdr_summary_tsv(review),
        )
    if entries_tsv_out is not None:
        _write_text_output(
            entries_tsv_out,
            render_evidence_level_fdr_entries_tsv(review),
        )

    payload = review.to_dict()
    payload["accepted_rows"] = len(parse_report.accepted_records)
    payload["rejected_rows"] = len(parse_report.rejected_rows)
    payload["outputs"] = {
        "summary_tsv": None if summary_tsv_out is None else str(summary_tsv_out),
        "entries_tsv": None if entries_tsv_out is None else str(entries_tsv_out),
    }
    _emit_json(payload, out_path=out_path)

def run_picked_protein_fdr_command(
    input_tsv: Path,
    thresholds: tuple[float, ...],
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
        parse_report = parse_psm_tsv(
            input_tsv,
            mapping=mapping,
            decoy_policy=decoy_policy,
        )
        review = build_picked_protein_fdr_review_report(
            parse_report.accepted_records,
            thresholds=tuple(thresholds),
            score_orientation=score_orientation,
            decoy_policy=decoy_policy,
        )
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        _write_text_output(
            summary_tsv_out,
            render_picked_protein_fdr_summary_tsv(review),
        )
    if entries_tsv_out is not None:
        _write_text_output(
            entries_tsv_out,
            render_picked_protein_fdr_entries_tsv(review),
        )

    payload = review.to_dict()
    payload["accepted_rows"] = len(parse_report.accepted_records)
    payload["rejected_rows"] = len(parse_report.rejected_rows)
    payload["outputs"] = {
        "summary_tsv": None if summary_tsv_out is None else str(summary_tsv_out),
        "entries_tsv": None if entries_tsv_out is None else str(entries_tsv_out),
    }
    _emit_json(payload, out_path=out_path)

__all__ = ['run_fdr_command', 'run_fdr_reference_check_command', 'run_fdr_levels_command', 'run_picked_protein_fdr_command']

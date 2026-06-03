# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi
# ruff: noqa: F401,F403,F405

"""Search import and quant benchmark Python API entrypoints."""

from __future__ import annotations

from bijux_proteomics.interfaces.support import *  # noqa: F401,F403,F405
from bijux_proteomics.interfaces.support.workflow import *  # noqa: F401,F403,F405


def run_comet_import_command(
    result_path: Path,
    config_path: Path | None,
    summary_tsv_out: Path | None,
    canonical_psm_tsv_out: Path | None,
    psm_tsv_out: Path | None,
    rejected_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    try:
        report = build_comet_import_report(result_path, config_path=config_path)
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        _write_text_output(summary_tsv_out, render_comet_summary_tsv(report.summary))
    if canonical_psm_tsv_out is not None:
        _write_text_output(
            canonical_psm_tsv_out,
            render_comet_canonical_psm_tsv(report.canonical_psms),
        )
    if psm_tsv_out is not None:
        _write_text_output(psm_tsv_out, render_comet_psm_tsv(report.psm_rows))
    if rejected_tsv_out is not None:
        _write_text_output(
            rejected_tsv_out,
            render_rejected_evidence_tsv(report.rejected_evidence_rows),
        )

    payload = {
        "import_kind": report.import_kind.value,
        "summary": report.summary.to_dict(),
        "normalization": None
        if report.normalization is None
        else {
            "adapter": report.normalization.adapter_manifest.to_dict(),
            "accepted_rows": len(report.normalization.parse_report.accepted_records),
            "rejected_rows": len(report.normalization.parse_report.rejected_rows),
        },
        "parameter_report": None
        if report.parameter_report is None
        else report.parameter_report.to_dict(),
        "canonical_psms": [row.to_dict() for row in report.canonical_psms],
        "psm_rows": [row.to_dict() for row in report.psm_rows],
        "rejected_evidence_rows": [
            row.to_dict() for row in report.rejected_evidence_rows
        ],
        "outputs": {
            "summary_tsv": None if summary_tsv_out is None else str(summary_tsv_out),
            "canonical_psm_tsv": None
            if canonical_psm_tsv_out is None
            else str(canonical_psm_tsv_out),
            "psm_tsv": None if psm_tsv_out is None else str(psm_tsv_out),
            "rejected_tsv": None if rejected_tsv_out is None else str(rejected_tsv_out),
        },
    }
    _emit_json(payload, out_path=out_path)


def run_maxquant_import_command(
    evidence_txt: Path,
    peptides_txt: Path,
    protein_groups_txt: Path,
    config_path: Path | None,
    summary_tsv_out: Path | None,
    evidence_tsv_out: Path | None,
    peptide_tsv_out: Path | None,
    protein_group_tsv_out: Path | None,
    lfq_candidate_tsv_out: Path | None,
    rejected_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    try:
        report = build_maxquant_import_report(
            evidence_txt,
            peptides_txt_path=peptides_txt,
            protein_groups_txt_path=protein_groups_txt,
            config_path=config_path,
        )
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        _write_text_output(summary_tsv_out, render_maxquant_summary_tsv(report.summary))
    if evidence_tsv_out is not None:
        _write_text_output(
            evidence_tsv_out,
            render_maxquant_evidence_tsv(report.evidence_rows),
        )
    if peptide_tsv_out is not None:
        _write_text_output(
            peptide_tsv_out, render_maxquant_peptide_tsv(report.peptide_rows)
        )
    if protein_group_tsv_out is not None:
        _write_text_output(
            protein_group_tsv_out,
            render_maxquant_protein_group_tsv(report.protein_group_rows),
        )
    if lfq_candidate_tsv_out is not None:
        _write_text_output(
            lfq_candidate_tsv_out,
            render_maxquant_lfq_candidate_tsv(report.lfq_matrix_candidates),
        )
    if rejected_tsv_out is not None:
        _write_text_output(
            rejected_tsv_out,
            render_rejected_evidence_tsv(report.rejected_evidence_rows),
        )

    payload = {
        "summary": report.summary.to_dict(),
        "evidence_normalization": {
            "adapter": report.evidence_normalization.adapter_manifest.to_dict(),
            "accepted_rows": len(
                report.evidence_normalization.parse_report.accepted_records
            ),
            "rejected_rows": len(
                report.evidence_normalization.parse_report.rejected_rows
            ),
        },
        "parameter_report": None
        if report.parameter_report is None
        else report.parameter_report.to_dict(),
        "evidence_rows": [row.to_dict() for row in report.evidence_rows],
        "peptide_rows": [row.to_dict() for row in report.peptide_rows],
        "protein_group_rows": [row.to_dict() for row in report.protein_group_rows],
        "lfq_matrix_candidates": [
            row.to_dict() for row in report.lfq_matrix_candidates
        ],
        "rejected_evidence_rows": [
            row.to_dict() for row in report.rejected_evidence_rows
        ],
        "outputs": {
            "summary_tsv": None if summary_tsv_out is None else str(summary_tsv_out),
            "evidence_tsv": None if evidence_tsv_out is None else str(evidence_tsv_out),
            "peptide_tsv": None if peptide_tsv_out is None else str(peptide_tsv_out),
            "protein_group_tsv": None
            if protein_group_tsv_out is None
            else str(protein_group_tsv_out),
            "lfq_candidate_tsv": None
            if lfq_candidate_tsv_out is None
            else str(lfq_candidate_tsv_out),
            "rejected_tsv": None if rejected_tsv_out is None else str(rejected_tsv_out),
        },
    }
    _emit_json(payload, out_path=out_path)


def run_maxquant_benchmark_command(
    evidence_txt: Path,
    peptides_txt: Path,
    protein_groups_txt: Path,
    config_path: Path | None,
    design_tsv: Path | None,
    condition_a: str | None,
    condition_b: str | None,
    summary_tsv_out: Path | None,
    protein_identity_tsv_out: Path | None,
    filtering_tsv_out: Path | None,
    lfq_tsv_out: Path | None,
    differential_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    design_entries: tuple[ExperimentalDesignEntry, ...] | None = None
    if design_tsv is not None:
        try:
            design_report = parse_experimental_design_table(design_tsv)
        except Exception as exc:  # noqa: BLE001
            raise click.ClickException(str(exc)) from exc
        if design_report.rejected_rows:
            raise click.ClickException(
                "design table contains rejected rows and cannot drive a MaxQuant benchmark differential comparison"
            )
        design_entries = tuple(design_report.accepted_entries)

    try:
        report = build_maxquant_benchmark_report(
            evidence_txt,
            peptides_txt_path=peptides_txt,
            protein_groups_txt_path=protein_groups_txt,
            config_path=config_path,
            design_entries=design_entries,
            condition_a=condition_a,
            condition_b=condition_b,
        )
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        _write_text_output(
            summary_tsv_out,
            render_maxquant_benchmark_summary_tsv(report),
        )
    if protein_identity_tsv_out is not None:
        _write_text_output(
            protein_identity_tsv_out,
            render_maxquant_protein_identity_comparison_tsv(report),
        )
    if filtering_tsv_out is not None:
        _write_text_output(
            filtering_tsv_out,
            render_maxquant_filtering_comparison_tsv(report),
        )
    if lfq_tsv_out is not None:
        _write_text_output(lfq_tsv_out, render_maxquant_lfq_comparison_tsv(report))
    if differential_tsv_out is not None:
        _write_text_output(
            differential_tsv_out,
            render_maxquant_differential_comparison_tsv(report),
        )

    payload = {
        "summary": report.summary.to_dict(),
        "protein_identity_comparison": report.protein_identity_comparison.to_dict(),
        "filtering_comparison_count": len(report.filtering_comparisons),
        "lfq_comparison_count": len(report.lfq_comparisons),
        "differential_comparison_count": len(report.differential_comparisons),
        "outputs": {
            "summary_tsv": None if summary_tsv_out is None else str(summary_tsv_out),
            "protein_identity_tsv": None
            if protein_identity_tsv_out is None
            else str(protein_identity_tsv_out),
            "filtering_tsv": None
            if filtering_tsv_out is None
            else str(filtering_tsv_out),
            "lfq_tsv": None if lfq_tsv_out is None else str(lfq_tsv_out),
            "differential_tsv": None
            if differential_tsv_out is None
            else str(differential_tsv_out),
        },
    }
    _emit_json(payload, out_path=out_path)


def run_diann_import_command(
    result_tsv: Path,
    config_path: Path | None,
    summary_tsv_out: Path | None,
    precursor_tsv_out: Path | None,
    protein_group_tsv_out: Path | None,
    rejected_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    try:
        report = build_diann_import_report(result_tsv, config_path=config_path)
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        _write_text_output(summary_tsv_out, render_diann_summary_tsv(report.summary))
    if precursor_tsv_out is not None:
        _write_text_output(
            precursor_tsv_out,
            render_diann_precursor_tsv(report.precursor_rows),
        )
    if protein_group_tsv_out is not None:
        _write_text_output(
            protein_group_tsv_out,
            render_diann_protein_group_tsv(report.protein_group_rows),
        )
    if rejected_tsv_out is not None:
        _write_text_output(
            rejected_tsv_out,
            render_rejected_evidence_tsv(report.rejected_evidence_rows),
        )

    payload = {
        "summary": report.summary.to_dict(),
        "normalization": None
        if report.normalization is None
        else {
            "adapter": report.normalization.adapter_manifest.to_dict(),
            "accepted_rows": len(report.normalization.parse_report.accepted_records),
            "rejected_rows": len(report.normalization.parse_report.rejected_rows),
        },
        "parameter_report": None
        if report.parameter_report is None
        else report.parameter_report.to_dict(),
        "precursor_rows": [row.to_dict() for row in report.precursor_rows],
        "protein_group_rows": [row.to_dict() for row in report.protein_group_rows],
        "rejected_rows": [row.to_dict() for row in report.rejected_rows],
        "rejected_evidence_rows": [
            row.to_dict() for row in report.rejected_evidence_rows
        ],
        "dia_native_report": report.dia_native_report.to_dict(),
        "outputs": {
            "summary_tsv": None if summary_tsv_out is None else str(summary_tsv_out),
            "precursor_tsv": None
            if precursor_tsv_out is None
            else str(precursor_tsv_out),
            "protein_group_tsv": None
            if protein_group_tsv_out is None
            else str(protein_group_tsv_out),
            "rejected_tsv": None if rejected_tsv_out is None else str(rejected_tsv_out),
        },
    }
    _emit_json(payload, out_path=out_path)


def run_diann_benchmark_command(
    result_tsv: Path,
    config_path: Path | None,
    summary_tsv_out: Path | None,
    count_comparisons_tsv_out: Path | None,
    protein_quantities_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    try:
        report = build_diann_benchmark_report(
            result_tsv,
            config_path=config_path,
        )
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        _write_text_output(summary_tsv_out, render_diann_benchmark_summary_tsv(report))
    if count_comparisons_tsv_out is not None:
        _write_text_output(
            count_comparisons_tsv_out,
            render_diann_benchmark_count_comparisons_tsv(report),
        )
    if protein_quantities_tsv_out is not None:
        _write_text_output(
            protein_quantities_tsv_out,
            render_diann_benchmark_protein_quantities_tsv(report),
        )

    payload = {
        "summary": report.summary.to_dict(),
        "count_comparison_count": len(report.count_comparisons),
        "protein_quantity_comparison_count": len(report.protein_quantity_comparisons),
        "outputs": {
            "summary_tsv": None if summary_tsv_out is None else str(summary_tsv_out),
            "count_comparisons_tsv": None
            if count_comparisons_tsv_out is None
            else str(count_comparisons_tsv_out),
            "protein_quantities_tsv": None
            if protein_quantities_tsv_out is None
            else str(protein_quantities_tsv_out),
        },
    }
    _emit_json(payload, out_path=out_path)


__all__ = [
    "run_comet_import_command",
    "run_maxquant_import_command",
    "run_maxquant_benchmark_command",
    "run_diann_import_command",
    "run_diann_benchmark_command",
]

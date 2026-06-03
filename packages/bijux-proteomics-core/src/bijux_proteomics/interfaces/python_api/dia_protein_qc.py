# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi
# ruff: noqa: F401,F403,F405

"""DIA protein-matrix and QC Python API entrypoints."""

from __future__ import annotations

from bijux_proteomics.interfaces.support import *  # noqa: F401,F403,F405
from bijux_proteomics.interfaces.support.workflow import *  # noqa: F401,F403,F405


def run_diann_protein_matrix_command(
    result_tsv: Path,
    config_path: Path | None,
    include_decoys: bool,
    max_q_value: float | None,
    peptide_rollup: str,
    target_kind: str,
    shared_peptides: str,
    protein_rollup: str,
    summary_tsv_out: Path | None,
    peptide_tsv_out: Path | None,
    protein_tsv_out: Path | None,
    rollup_evidence_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    try:
        peptide_report = build_diann_peptide_matrix_report(
            result_tsv,
            config_path=config_path,
            include_decoys=include_decoys,
            max_q_value=max_q_value,
            rollup_method=DiaPeptideRollupMethod(peptide_rollup),
        )
        protein_report = build_dia_protein_matrix_report(
            peptide_report,
            target_kind=DiaProteinMatrixTargetKind(target_kind),
            shared_peptide_policy=DiaSharedPeptidePolicy(shared_peptides),
            rollup_method=DiaProteinRollupMethod(protein_rollup),
        )
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        _write_text_output(
            summary_tsv_out,
            render_dia_protein_matrix_summary_tsv(protein_report),
        )
    if peptide_tsv_out is not None:
        _write_text_output(
            peptide_tsv_out,
            render_dia_peptide_quantity_matrix_tsv(peptide_report),
        )
    if protein_tsv_out is not None:
        _write_text_output(
            protein_tsv_out,
            render_dia_protein_quantity_matrix_tsv(protein_report),
        )
    if rollup_evidence_tsv_out is not None:
        _write_text_output(
            rollup_evidence_tsv_out,
            render_dia_protein_rollup_evidence_tsv(protein_report),
        )

    payload = {
        "source_name": protein_report.source_name,
        "sample_ids": list(protein_report.sample_ids),
        "peptide_rollup_method": peptide_report.rollup_method.value,
        "target_kind": protein_report.target_kind.value,
        "shared_peptide_policy": protein_report.shared_peptide_policy.value,
        "protein_rollup_method": protein_report.rollup_method.value,
        "peptide_summary": peptide_report.summary.to_dict(),
        "protein_summary": protein_report.summary.to_dict(),
        "peptide_rows": [row.to_dict() for row in peptide_report.rows],
        "protein_rows": [row.to_dict() for row in protein_report.rows],
        "rollup_evidence_entries": [
            entry.to_dict() for entry in protein_report.rollup_evidence_entries
        ],
        "outputs": {
            "summary_tsv": None if summary_tsv_out is None else str(summary_tsv_out),
            "peptide_tsv": None if peptide_tsv_out is None else str(peptide_tsv_out),
            "protein_tsv": None if protein_tsv_out is None else str(protein_tsv_out),
            "rollup_evidence_tsv": (
                None
                if rollup_evidence_tsv_out is None
                else str(rollup_evidence_tsv_out)
            ),
        },
    }
    _emit_json(payload, out_path=out_path)


def run_spectronaut_protein_matrix_command(
    result_tsv: Path,
    config_path: Path | None,
    include_decoys: bool,
    max_q_value: float | None,
    peptide_rollup: str,
    target_kind: str,
    shared_peptides: str,
    protein_rollup: str,
    summary_tsv_out: Path | None,
    peptide_tsv_out: Path | None,
    protein_tsv_out: Path | None,
    rollup_evidence_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    try:
        peptide_report = build_spectronaut_peptide_matrix_report(
            result_tsv,
            config_path=config_path,
            include_decoys=include_decoys,
            max_q_value=max_q_value,
            rollup_method=DiaPeptideRollupMethod(peptide_rollup),
        )
        protein_report = build_spectronaut_protein_matrix_report(
            result_tsv,
            config_path=config_path,
            include_decoys=include_decoys,
            max_q_value=max_q_value,
            peptide_rollup_method=DiaPeptideRollupMethod(peptide_rollup),
            target_kind=DiaProteinMatrixTargetKind(target_kind),
            shared_peptide_policy=DiaSharedPeptidePolicy(shared_peptides),
            protein_rollup_method=DiaProteinRollupMethod(protein_rollup),
        )
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        _write_text_output(
            summary_tsv_out,
            render_dia_protein_matrix_summary_tsv(protein_report),
        )
    if peptide_tsv_out is not None:
        _write_text_output(
            peptide_tsv_out,
            render_dia_peptide_quantity_matrix_tsv(peptide_report),
        )
    if protein_tsv_out is not None:
        _write_text_output(
            protein_tsv_out,
            render_dia_protein_quantity_matrix_tsv(protein_report),
        )
    if rollup_evidence_tsv_out is not None:
        _write_text_output(
            rollup_evidence_tsv_out,
            render_dia_protein_rollup_evidence_tsv(protein_report),
        )

    payload = {
        "source_name": protein_report.source_name,
        "sample_ids": list(protein_report.sample_ids),
        "peptide_rollup_method": peptide_report.rollup_method.value,
        "target_kind": protein_report.target_kind.value,
        "shared_peptide_policy": protein_report.shared_peptide_policy.value,
        "protein_rollup_method": protein_report.rollup_method.value,
        "peptide_summary": peptide_report.summary.to_dict(),
        "protein_summary": protein_report.summary.to_dict(),
        "peptide_rows": [row.to_dict() for row in peptide_report.rows],
        "protein_rows": [row.to_dict() for row in protein_report.rows],
        "rollup_evidence_entries": [
            entry.to_dict() for entry in protein_report.rollup_evidence_entries
        ],
        "outputs": {
            "summary_tsv": None if summary_tsv_out is None else str(summary_tsv_out),
            "peptide_tsv": None if peptide_tsv_out is None else str(peptide_tsv_out),
            "protein_tsv": None if protein_tsv_out is None else str(protein_tsv_out),
            "rollup_evidence_tsv": (
                None
                if rollup_evidence_tsv_out is None
                else str(rollup_evidence_tsv_out)
            ),
        },
    }
    _emit_json(payload, out_path=out_path)


def run_diann_run_qc_command(
    result_tsv: Path,
    config_path: Path | None,
    include_decoys: bool,
    max_q_value: float | None,
    summary_tsv_out: Path | None,
    run_tsv_out: Path | None,
    intensity_tsv_out: Path | None,
    correlation_tsv_out: Path | None,
    outlier_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    try:
        report = build_diann_run_qc_report(
            result_tsv,
            config_path=config_path,
            include_decoys=include_decoys,
            max_q_value=max_q_value,
        )
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        _write_text_output(summary_tsv_out, render_dia_run_qc_summary_tsv(report))
    if run_tsv_out is not None:
        _write_text_output(run_tsv_out, render_dia_run_qc_run_table_tsv(report))
    if intensity_tsv_out is not None:
        _write_text_output(
            intensity_tsv_out,
            render_dia_run_qc_intensity_distribution_tsv(report),
        )
    if correlation_tsv_out is not None:
        _write_text_output(
            correlation_tsv_out,
            render_dia_run_qc_correlation_tsv(report),
        )
    if outlier_tsv_out is not None:
        _write_text_output(outlier_tsv_out, render_dia_run_qc_outlier_tsv(report))

    payload = {
        "source_name": report.source_name,
        "summary": report.summary.to_dict(),
        "run_entries": [entry.to_dict() for entry in report.run_entries],
        "intensity_distribution": [
            entry.to_dict() for entry in report.intensity_distribution
        ],
        "pairwise_correlations": [
            entry.to_dict() for entry in report.pairwise_correlations
        ],
        "outlier_runs": [entry.to_dict() for entry in report.outlier_runs],
        "outputs": {
            "summary_tsv": None if summary_tsv_out is None else str(summary_tsv_out),
            "run_tsv": None if run_tsv_out is None else str(run_tsv_out),
            "intensity_tsv": (
                None if intensity_tsv_out is None else str(intensity_tsv_out)
            ),
            "correlation_tsv": (
                None if correlation_tsv_out is None else str(correlation_tsv_out)
            ),
            "outlier_tsv": (None if outlier_tsv_out is None else str(outlier_tsv_out)),
        },
    }
    _emit_json(payload, out_path=out_path)


def run_diann_library_coverage_command(
    result_tsv: Path,
    library_path: Path,
    design_path: Path | None,
    include_decoys: bool,
    max_q_value: float | None,
    shared_peptides: str,
    summary_tsv_out: Path | None,
    sample_tsv_out: Path | None,
    condition_tsv_out: Path | None,
    peptide_tsv_out: Path | None,
    protein_tsv_out: Path | None,
    outside_library_peptide_tsv_out: Path | None,
    outside_library_protein_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    try:
        report = build_diann_library_coverage_report(
            result_tsv,
            library_path,
            design_path=design_path,
            include_decoys=include_decoys,
            max_q_value=max_q_value,
            shared_peptide_policy=DiaSharedPeptidePolicy(shared_peptides),
        )
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        _write_text_output(
            summary_tsv_out,
            render_dia_library_coverage_summary_tsv(report),
        )
    if sample_tsv_out is not None:
        _write_text_output(
            sample_tsv_out,
            render_dia_library_coverage_sample_tsv(report),
        )
    if condition_tsv_out is not None:
        _write_text_output(
            condition_tsv_out,
            render_dia_library_coverage_condition_tsv(report),
        )
    if peptide_tsv_out is not None:
        _write_text_output(
            peptide_tsv_out,
            render_dia_library_coverage_peptide_tsv(report),
        )
    if protein_tsv_out is not None:
        _write_text_output(
            protein_tsv_out,
            render_dia_library_coverage_protein_tsv(report),
        )
    if outside_library_peptide_tsv_out is not None:
        _write_text_output(
            outside_library_peptide_tsv_out,
            render_dia_library_coverage_observed_outside_peptide_tsv(report),
        )
    if outside_library_protein_tsv_out is not None:
        _write_text_output(
            outside_library_protein_tsv_out,
            render_dia_library_coverage_observed_outside_protein_tsv(report),
        )

    payload = {
        "source_name": report.source_name,
        "library_source_format": report.library_source_format,
        "summary": report.summary.to_dict(),
        "sample_entries": [entry.to_dict() for entry in report.sample_entries],
        "condition_entries": [entry.to_dict() for entry in report.condition_entries],
        "peptide_entries": [entry.to_dict() for entry in report.peptide_entries],
        "protein_entries": [entry.to_dict() for entry in report.protein_entries],
        "observed_outside_library_peptide_entries": [
            entry.to_dict() for entry in report.observed_outside_library_peptide_entries
        ],
        "observed_outside_library_protein_entries": [
            entry.to_dict() for entry in report.observed_outside_library_protein_entries
        ],
        "outputs": {
            "summary_tsv": None if summary_tsv_out is None else str(summary_tsv_out),
            "sample_tsv": None if sample_tsv_out is None else str(sample_tsv_out),
            "condition_tsv": (
                None if condition_tsv_out is None else str(condition_tsv_out)
            ),
            "peptide_tsv": None if peptide_tsv_out is None else str(peptide_tsv_out),
            "protein_tsv": None if protein_tsv_out is None else str(protein_tsv_out),
            "outside_library_peptide_tsv": (
                None
                if outside_library_peptide_tsv_out is None
                else str(outside_library_peptide_tsv_out)
            ),
            "outside_library_protein_tsv": (
                None
                if outside_library_protein_tsv_out is None
                else str(outside_library_protein_tsv_out)
            ),
        },
    }
    _emit_json(payload, out_path=out_path)


__all__ = [
    "run_diann_protein_matrix_command",
    "run_spectronaut_protein_matrix_command",
    "run_diann_run_qc_command",
    "run_diann_library_coverage_command",
]

# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi
"""Vendor import Python API entrypoints."""

from __future__ import annotations

from bijux_proteomics.interfaces.support.foundation import (
    Path,
    click,
)
from bijux_proteomics.interfaces.support.identification import (
    build_openms_import_report,
    build_spectronaut_import_report,
    render_openms_feature_tsv,
    render_openms_protein_tsv,
    render_openms_psm_tsv,
    render_openms_summary_tsv,
    render_rejected_evidence_tsv,
    render_spectronaut_precursor_quantity_tsv,
    render_spectronaut_precursor_tsv,
    render_spectronaut_protein_group_quantity_tsv,
    render_spectronaut_protein_group_tsv,
    render_spectronaut_summary_tsv,
)
from bijux_proteomics.interfaces.support.output_protocol.artifact_output import (
    _emit_json,
    _write_text_output,
)


def run_spectronaut_import_command(
    result_tsv: Path,
    config_path: Path | None,
    summary_tsv_out: Path | None,
    precursor_tsv_out: Path | None,
    precursor_quantity_tsv_out: Path | None,
    protein_group_tsv_out: Path | None,
    protein_group_quantity_tsv_out: Path | None,
    rejected_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    try:
        report = build_spectronaut_import_report(result_tsv, config_path=config_path)
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        _write_text_output(
            summary_tsv_out,
            render_spectronaut_summary_tsv(report.summary),
        )
    if precursor_tsv_out is not None:
        _write_text_output(
            precursor_tsv_out,
            render_spectronaut_precursor_tsv(report.precursor_rows),
        )
    if precursor_quantity_tsv_out is not None:
        _write_text_output(
            precursor_quantity_tsv_out,
            render_spectronaut_precursor_quantity_tsv(report.precursor_quantity_rows),
        )
    if protein_group_tsv_out is not None:
        _write_text_output(
            protein_group_tsv_out,
            render_spectronaut_protein_group_tsv(report.protein_group_rows),
        )
    if protein_group_quantity_tsv_out is not None:
        _write_text_output(
            protein_group_quantity_tsv_out,
            render_spectronaut_protein_group_quantity_tsv(
                report.protein_group_quantity_rows
            ),
        )
    if rejected_tsv_out is not None:
        _write_text_output(
            rejected_tsv_out,
            render_rejected_evidence_tsv(report.rejected_evidence_rows),
        )

    payload = {
        "summary": report.summary.to_dict(),
        "normalization": {
            "adapter": report.normalization.adapter_manifest.to_dict(),
            "accepted_rows": len(report.normalization.parse_report.accepted_records),
            "rejected_rows": len(report.normalization.parse_report.rejected_rows),
        },
        "parameter_report": None
        if report.parameter_report is None
        else report.parameter_report.to_dict(),
        "precursor_evidence_rows": [
            row.to_dict() for row in report.precursor_evidence_rows
        ],
        "precursor_rows": [row.to_dict() for row in report.precursor_rows],
        "precursor_quantity_rows": [
            row.to_dict() for row in report.precursor_quantity_rows
        ],
        "protein_group_rows": [row.to_dict() for row in report.protein_group_rows],
        "protein_group_quantity_rows": [
            row.to_dict() for row in report.protein_group_quantity_rows
        ],
        "rejected_evidence_rows": [
            row.to_dict() for row in report.rejected_evidence_rows
        ],
        "outputs": {
            "summary_tsv": None if summary_tsv_out is None else str(summary_tsv_out),
            "precursor_tsv": None
            if precursor_tsv_out is None
            else str(precursor_tsv_out),
            "precursor_quantity_tsv": None
            if precursor_quantity_tsv_out is None
            else str(precursor_quantity_tsv_out),
            "protein_group_tsv": None
            if protein_group_tsv_out is None
            else str(protein_group_tsv_out),
            "protein_group_quantity_tsv": None
            if protein_group_quantity_tsv_out is None
            else str(protein_group_quantity_tsv_out),
            "rejected_tsv": None if rejected_tsv_out is None else str(rejected_tsv_out),
        },
    }
    _emit_json(payload, out_path=out_path)


def run_openms_import_command(
    idxml_path: Path,
    feature_table_path: Path,
    summary_tsv_out: Path | None,
    psm_tsv_out: Path | None,
    protein_tsv_out: Path | None,
    feature_tsv_out: Path | None,
    rejected_feature_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    try:
        report = build_openms_import_report(
            idxml_path,
            feature_table_path=feature_table_path,
        )
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        _write_text_output(summary_tsv_out, render_openms_summary_tsv(report.summary))
    if psm_tsv_out is not None:
        _write_text_output(psm_tsv_out, render_openms_psm_tsv(report.psm_rows))
    if protein_tsv_out is not None:
        _write_text_output(
            protein_tsv_out,
            render_openms_protein_tsv(report.protein_rows),
        )
    if feature_tsv_out is not None:
        _write_text_output(
            feature_tsv_out,
            render_openms_feature_tsv(report.feature_rows),
        )
    if rejected_feature_tsv_out is not None:
        _write_text_output(
            rejected_feature_tsv_out,
            render_rejected_evidence_tsv(report.rejected_evidence_rows),
        )

    payload = {
        "summary": report.summary.to_dict(),
        "feature_parse_summary": report.feature_parse_summary.to_dict(),
        "psm_rows": [row.to_dict() for row in report.psm_rows],
        "protein_rows": [row.to_dict() for row in report.protein_rows],
        "feature_rows": [row.to_dict() for row in report.feature_rows],
        "rejected_feature_rows": [
            row.to_dict() for row in report.rejected_feature_rows
        ],
        "rejected_evidence_rows": [
            row.to_dict() for row in report.rejected_evidence_rows
        ],
        "outputs": {
            "summary_tsv": None if summary_tsv_out is None else str(summary_tsv_out),
            "psm_tsv": None if psm_tsv_out is None else str(psm_tsv_out),
            "protein_tsv": None if protein_tsv_out is None else str(protein_tsv_out),
            "feature_tsv": None if feature_tsv_out is None else str(feature_tsv_out),
            "rejected_feature_tsv": None
            if rejected_feature_tsv_out is None
            else str(rejected_feature_tsv_out),
        },
    }
    _emit_json(payload, out_path=out_path)


__all__ = ["run_spectronaut_import_command", "run_openms_import_command"]

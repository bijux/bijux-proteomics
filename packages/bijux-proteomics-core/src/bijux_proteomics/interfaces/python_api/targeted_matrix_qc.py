# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi
"""Targeted matrix and assay QC Python API entrypoints."""

from __future__ import annotations

from typing import cast

from bijux_proteomics.interfaces.support.foundation import (
    Path,
    click,
)
from bijux_proteomics.interfaces.support.io_and_dia import (
    build_transition_qc_report_from_table,
    parse_experimental_design_table,
    render_transition_qc_sample_tsv,
    render_transition_qc_summary_tsv,
    render_transition_qc_transition_tsv,
    render_transition_qc_weak_tsv,
)
from bijux_proteomics.interfaces.support.multiplex_targeted.targeted import (
    TargetedResultSourceKind,
    build_skyline_result_import_report,
    build_targeted_carryover_report,
    build_transition_table_result_import_report,
    render_targeted_assay_qc_coelution_tsv,
    render_targeted_assay_qc_fragment_ratio_tsv,
    render_targeted_assay_qc_replicate_cv_tsv,
    render_targeted_assay_qc_retention_tsv,
    render_targeted_assay_qc_summary_tsv,
    render_targeted_assay_qc_target_tsv,
    render_targeted_assay_qc_transition_coelution_tsv,
    render_targeted_assay_qc_transition_qc_tsv,
    render_targeted_assay_qc_transition_tsv,
    render_targeted_assay_qc_unreliable_tsv,
    render_targeted_carryover_candidates_tsv,
    render_targeted_carryover_summary_tsv,
    render_targeted_matrix_excluded_transition_tsv,
    render_targeted_matrix_flagged_tsv,
    render_targeted_matrix_missingness_tsv,
    render_targeted_matrix_retained_transition_tsv,
    render_targeted_matrix_sample_tsv,
    render_targeted_matrix_summary_tsv,
    render_targeted_matrix_target_tsv,
    render_targeted_result_observation_tsv,
)
from bijux_proteomics.interfaces.support.output_protocol.artifact_output import (
    _emit_json,
    _write_text_output,
)
from bijux_proteomics.interfaces.support.output_protocol.workflow_execution import (
    _run_orchestrated_workflow,
)
from bijux_proteomics.interfaces.support.workflow import (
    TargetedWorkflowConfig,
    TargetedWorkflowStage,
)
from bijux_proteomics.targeted.assay_qc import TargetedAssayQcReport
from bijux_proteomics.targeted.result_import import TargetedResultImportReport
from bijux_proteomics.targeted.target_matrix import TargetedMatrixReport


def run_transition_qc_command(
    transition_table: Path,
    weak_detection_fraction_threshold: float,
    weak_relative_share_threshold: float,
    summary_tsv_out: Path | None,
    transition_tsv_out: Path | None,
    sample_tsv_out: Path | None,
    weak_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    try:
        report = build_transition_qc_report_from_table(
            transition_table,
            weak_detection_fraction_threshold=weak_detection_fraction_threshold,
            weak_relative_share_threshold=weak_relative_share_threshold,
        )
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        _write_text_output(summary_tsv_out, render_transition_qc_summary_tsv(report))
    if transition_tsv_out is not None:
        _write_text_output(
            transition_tsv_out,
            render_transition_qc_transition_tsv(report),
        )
    if sample_tsv_out is not None:
        _write_text_output(sample_tsv_out, render_transition_qc_sample_tsv(report))
    if weak_tsv_out is not None:
        _write_text_output(weak_tsv_out, render_transition_qc_weak_tsv(report))

    payload = {
        "source_name": report.source_name,
        "sample_ids": list(report.sample_ids),
        "summary": report.summary.to_dict(),
        "entries": [entry.to_dict() for entry in report.entries],
        "weak_transitions": [entry.to_dict() for entry in report.weak_transitions],
        "note": report.note,
        "outputs": {
            "summary_tsv": None if summary_tsv_out is None else str(summary_tsv_out),
            "transition_tsv": (
                None if transition_tsv_out is None else str(transition_tsv_out)
            ),
            "sample_tsv": None if sample_tsv_out is None else str(sample_tsv_out),
            "weak_tsv": None if weak_tsv_out is None else str(weak_tsv_out),
        },
    }
    _emit_json(payload, out_path=out_path)


def run_targeted_target_matrix_command(
    input_path: Path,
    source_kind: str,
    summary_tsv_out: Path | None,
    observation_tsv_out: Path | None,
    target_tsv_out: Path | None,
    sample_tsv_out: Path | None,
    flagged_tsv_out: Path | None,
    retained_transition_tsv_out: Path | None,
    excluded_transition_tsv_out: Path | None,
    missingness_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    result = _run_orchestrated_workflow(
        TargetedWorkflowConfig(
            input_tsv_path=input_path,
            source_kind=TargetedResultSourceKind(source_kind),
            stage=TargetedWorkflowStage.MATRIX,
        )
    )
    import_report = cast(TargetedResultImportReport, result.source_report)
    matrix_report = cast(TargetedMatrixReport, result.report)

    if summary_tsv_out is not None:
        _write_text_output(
            summary_tsv_out, render_targeted_matrix_summary_tsv(matrix_report)
        )
    if observation_tsv_out is not None:
        _write_text_output(
            observation_tsv_out,
            render_targeted_result_observation_tsv(import_report),
        )
    if target_tsv_out is not None:
        _write_text_output(
            target_tsv_out, render_targeted_matrix_target_tsv(matrix_report)
        )
    if sample_tsv_out is not None:
        _write_text_output(
            sample_tsv_out, render_targeted_matrix_sample_tsv(matrix_report)
        )
    if flagged_tsv_out is not None:
        _write_text_output(
            flagged_tsv_out, render_targeted_matrix_flagged_tsv(matrix_report)
        )
    if retained_transition_tsv_out is not None:
        _write_text_output(
            retained_transition_tsv_out,
            render_targeted_matrix_retained_transition_tsv(matrix_report),
        )
    if excluded_transition_tsv_out is not None:
        _write_text_output(
            excluded_transition_tsv_out,
            render_targeted_matrix_excluded_transition_tsv(matrix_report),
        )
    if missingness_tsv_out is not None:
        _write_text_output(
            missingness_tsv_out,
            render_targeted_matrix_missingness_tsv(matrix_report),
        )

    payload = {
        "source_kind": import_report.source_kind.value,
        "source_name": matrix_report.source_name,
        "import_summary": import_report.summary.to_dict(),
        "matrix_summary": matrix_report.summary.to_dict(),
        "observations": [item.to_dict() for item in import_report.observations],
        "targets": [row.to_dict() for row in matrix_report.rows],
        "retained_transitions": [
            item.to_dict() for item in matrix_report.retained_transitions
        ],
        "excluded_transitions": [
            item.to_dict() for item in matrix_report.excluded_transitions
        ],
        "missingness": [item.to_dict() for item in matrix_report.missingness],
        "note": matrix_report.note,
        "outputs": {
            "summary_tsv": None if summary_tsv_out is None else str(summary_tsv_out),
            "observation_tsv": (
                None if observation_tsv_out is None else str(observation_tsv_out)
            ),
            "target_tsv": None if target_tsv_out is None else str(target_tsv_out),
            "sample_tsv": None if sample_tsv_out is None else str(sample_tsv_out),
            "flagged_tsv": None if flagged_tsv_out is None else str(flagged_tsv_out),
            "retained_transition_tsv": (
                None
                if retained_transition_tsv_out is None
                else str(retained_transition_tsv_out)
            ),
            "excluded_transition_tsv": (
                None
                if excluded_transition_tsv_out is None
                else str(excluded_transition_tsv_out)
            ),
            "missingness_tsv": (
                None if missingness_tsv_out is None else str(missingness_tsv_out)
            ),
        },
    }
    _emit_json(payload, out_path=out_path)


def run_targeted_assay_qc_command(
    input_path: Path,
    design_path: Path,
    source_kind: str,
    summary_tsv_out: Path | None,
    target_qc_tsv_out: Path | None,
    transition_tsv_out: Path | None,
    coelution_tsv_out: Path | None,
    transition_coelution_tsv_out: Path | None,
    transition_qc_tsv_out: Path | None,
    fragment_ratio_tsv_out: Path | None,
    retention_tsv_out: Path | None,
    replicate_cv_tsv_out: Path | None,
    unreliable_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    result = _run_orchestrated_workflow(
        TargetedWorkflowConfig(
            input_tsv_path=input_path,
            source_kind=TargetedResultSourceKind(source_kind),
            stage=TargetedWorkflowStage.ASSAY_QC,
            design_tsv_path=design_path,
        )
    )
    import_report = cast(TargetedResultImportReport, result.source_report)
    assay_qc_report = cast(TargetedAssayQcReport, result.report)

    if summary_tsv_out is not None:
        _write_text_output(
            summary_tsv_out, render_targeted_assay_qc_summary_tsv(assay_qc_report)
        )
    if target_qc_tsv_out is not None:
        _write_text_output(
            target_qc_tsv_out,
            render_targeted_assay_qc_target_tsv(assay_qc_report),
        )
    if transition_tsv_out is not None:
        _write_text_output(
            transition_tsv_out,
            render_targeted_assay_qc_transition_tsv(assay_qc_report),
        )
    if coelution_tsv_out is not None:
        _write_text_output(
            coelution_tsv_out,
            render_targeted_assay_qc_coelution_tsv(assay_qc_report),
        )
    if transition_coelution_tsv_out is not None:
        _write_text_output(
            transition_coelution_tsv_out,
            render_targeted_assay_qc_transition_coelution_tsv(assay_qc_report),
        )
    if transition_qc_tsv_out is not None:
        _write_text_output(
            transition_qc_tsv_out,
            render_targeted_assay_qc_transition_qc_tsv(assay_qc_report),
        )
    if fragment_ratio_tsv_out is not None:
        _write_text_output(
            fragment_ratio_tsv_out,
            render_targeted_assay_qc_fragment_ratio_tsv(assay_qc_report),
        )
    if retention_tsv_out is not None:
        _write_text_output(
            retention_tsv_out,
            render_targeted_assay_qc_retention_tsv(assay_qc_report),
        )
    if replicate_cv_tsv_out is not None:
        _write_text_output(
            replicate_cv_tsv_out,
            render_targeted_assay_qc_replicate_cv_tsv(assay_qc_report),
        )
    if unreliable_tsv_out is not None:
        _write_text_output(
            unreliable_tsv_out,
            render_targeted_assay_qc_unreliable_tsv(assay_qc_report),
        )

    payload = {
        "source_kind": import_report.source_kind.value,
        "source_name": assay_qc_report.source_name,
        "import_summary": import_report.summary.to_dict(),
        "design_summary": {
            "accepted_entry_count": result.design_row_count,
            "rejected_row_count": 0,
        },
        "assay_qc_summary": assay_qc_report.summary.to_dict(),
        "transition_coelution_summary": assay_qc_report.transition_coelution.summary.to_dict(),
        "fragment_ratio_stability_summary": (
            assay_qc_report.fragment_ratio_stability.summary.to_dict()
        ),
        "target_qc": [entry.to_dict() for entry in assay_qc_report.target_qc],
        "transition_consistency": [
            entry.to_dict() for entry in assay_qc_report.transition_consistency
        ],
        "target_coelution": [
            entry.to_dict()
            for entry in assay_qc_report.transition_coelution.target_entries
        ],
        "transition_coelution": [
            entry.to_dict()
            for entry in assay_qc_report.transition_coelution.transition_entries
        ],
        "transition_qc": [entry.to_dict() for entry in assay_qc_report.transition_qc],
        "fragment_ratios": [
            entry.to_dict() for entry in assay_qc_report.fragment_ratios
        ],
        "retention_time_consistency": [
            entry.to_dict() for entry in assay_qc_report.retention_time_consistency
        ],
        "replicate_cv": [entry.to_dict() for entry in assay_qc_report.replicate_cv],
        "unreliable_targets": [
            entry.to_dict() for entry in assay_qc_report.unreliable_targets
        ],
        "note": assay_qc_report.note,
        "outputs": {
            "summary_tsv": None if summary_tsv_out is None else str(summary_tsv_out),
            "target_qc_tsv": (
                None if target_qc_tsv_out is None else str(target_qc_tsv_out)
            ),
            "transition_tsv": (
                None if transition_tsv_out is None else str(transition_tsv_out)
            ),
            "coelution_tsv": (
                None if coelution_tsv_out is None else str(coelution_tsv_out)
            ),
            "transition_coelution_tsv": (
                None
                if transition_coelution_tsv_out is None
                else str(transition_coelution_tsv_out)
            ),
            "transition_qc_tsv": (
                None if transition_qc_tsv_out is None else str(transition_qc_tsv_out)
            ),
            "fragment_ratio_tsv": (
                None if fragment_ratio_tsv_out is None else str(fragment_ratio_tsv_out)
            ),
            "retention_tsv": None
            if retention_tsv_out is None
            else str(retention_tsv_out),
            "replicate_cv_tsv": (
                None if replicate_cv_tsv_out is None else str(replicate_cv_tsv_out)
            ),
            "unreliable_tsv": (
                None if unreliable_tsv_out is None else str(unreliable_tsv_out)
            ),
        },
    }
    _emit_json(payload, out_path=out_path)


def run_targeted_carryover_review_command(
    input_path: Path,
    design_path: Path,
    source_kind: str,
    summary_tsv_out: Path | None,
    candidate_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    source_kind_value = TargetedResultSourceKind(source_kind)
    if source_kind_value is TargetedResultSourceKind.SKYLINE_EXPORT:
        import_report = build_skyline_result_import_report(input_path)
    else:
        import_report = build_transition_table_result_import_report(input_path)
    design_report = parse_experimental_design_table(design_path)
    try:
        carryover_report = build_targeted_carryover_report(
            import_report,
            design_report.accepted_entries,
        )
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        _write_text_output(
            summary_tsv_out,
            render_targeted_carryover_summary_tsv(carryover_report),
        )
    if candidate_tsv_out is not None:
        _write_text_output(
            candidate_tsv_out,
            render_targeted_carryover_candidates_tsv(carryover_report),
        )

    payload = {
        "source_kind": import_report.source_kind.value,
        "source_name": carryover_report.source_name,
        "import_summary": import_report.summary.to_dict(),
        "design_summary": {
            "accepted_entry_count": len(design_report.accepted_entries),
            "rejected_row_count": len(design_report.rejected_rows),
        },
        "carryover_summary": carryover_report.summary.to_dict(),
        "candidates": [entry.to_dict() for entry in carryover_report.candidates],
        "note": carryover_report.note,
        "outputs": {
            "summary_tsv": None if summary_tsv_out is None else str(summary_tsv_out),
            "candidate_tsv": (
                None if candidate_tsv_out is None else str(candidate_tsv_out)
            ),
        },
    }
    _emit_json(payload, out_path=out_path)


__all__ = [
    "run_transition_qc_command",
    "run_targeted_target_matrix_command",
    "run_targeted_assay_qc_command",
    "run_targeted_carryover_review_command",
]

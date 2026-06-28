# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi
"""Result explanation Python API entrypoints."""

from __future__ import annotations

from bijux_proteomics.interfaces.support.foundation import (
    Path,
    click,
)
from bijux_proteomics.interfaces.support.review_sequences_study import (
    FailureExplanationRequest,
    ResultExplanationKind,
    ResultExplanationRequest,
    ResultQueryKind,
    ResultQueryRequest,
    build_analysis_recommendation_report_from_artifacts,
    build_compact_result_summary_report_from_artifacts,
    build_failure_explanation_report,
    build_result_explanation_report_from_artifacts,
    build_result_query_report_from_artifacts,
    render_analysis_recommendation_summary_tsv,
    render_analysis_recommendation_tsv,
    render_compact_result_summary_entry_tsv,
    render_compact_result_summary_markdown,
    render_compact_result_summary_overview_tsv,
    render_failure_explanation_summary_tsv,
    render_failure_explanation_tsv,
    render_result_explanation_evidence_tsv,
    render_result_explanation_summary_tsv,
    render_result_explanation_tsv,
    render_result_query_answer_tsv,
    render_result_query_evidence_tsv,
    render_result_query_summary_tsv,
)
from bijux_proteomics.interfaces.support.output_protocol import (
    _emit_json,
    _write_text_output,
)


def run_result_question_answer_command(
    biological_report_dir: Path | None,
    ptm_report_dir: Path | None,
    run_qc_assessment_tsv_paths: tuple[Path, ...],
    query_kind: str,
    subject_id: str | None,
    summary_tsv_out: Path | None,
    answer_tsv_out: Path | None,
    evidence_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    if biological_report_dir is None and ptm_report_dir is None:
        raise click.ClickException(
            "at least one of --biological-report-dir or --ptm-report-dir must be provided"
        )

    try:
        report = build_result_query_report_from_artifacts(
            (
                ResultQueryRequest(
                    query_id="result_query",
                    query_kind=ResultQueryKind(query_kind),
                    subject_id=subject_id,
                ),
            ),
            biological_report_dir=biological_report_dir,
            ptm_report_dir=ptm_report_dir,
            run_qc_assessment_tsv_paths=run_qc_assessment_tsv_paths,
        )
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        _write_text_output(summary_tsv_out, render_result_query_summary_tsv(report))
    if answer_tsv_out is not None:
        _write_text_output(answer_tsv_out, render_result_query_answer_tsv(report))
    if evidence_tsv_out is not None:
        _write_text_output(
            evidence_tsv_out,
            render_result_query_evidence_tsv(report),
        )

    payload = {
        "biological_report_dir": (
            None if biological_report_dir is None else str(biological_report_dir)
        ),
        "ptm_report_dir": None if ptm_report_dir is None else str(ptm_report_dir),
        "run_qc_assessment_tsv_paths": [
            str(path) for path in run_qc_assessment_tsv_paths
        ],
        "report": report.to_dict(),
        "outputs": {
            "summary_tsv": None if summary_tsv_out is None else str(summary_tsv_out),
            "answer_tsv": None if answer_tsv_out is None else str(answer_tsv_out),
            "evidence_tsv": (
                None if evidence_tsv_out is None else str(evidence_tsv_out)
            ),
        },
    }
    _emit_json(payload, out_path=out_path)


def run_result_explanation_command(
    biological_report_dir: Path | None,
    ptm_report_dir: Path | None,
    run_qc_assessment_tsv_paths: tuple[Path, ...],
    explanation_kind: str,
    subject_id: str | None,
    summary_tsv_out: Path | None,
    explanation_tsv_out: Path | None,
    evidence_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    if (
        biological_report_dir is None
        and ptm_report_dir is None
        and not run_qc_assessment_tsv_paths
    ):
        raise click.ClickException(
            "at least one governed biological report, PTM report, or QC assessment input must be provided"
        )

    try:
        report = build_result_explanation_report_from_artifacts(
            (
                ResultExplanationRequest(
                    explanation_id="result_explanation",
                    explanation_kind=ResultExplanationKind(explanation_kind),
                    subject_id=subject_id,
                ),
            ),
            biological_report_dir=biological_report_dir,
            ptm_report_dir=ptm_report_dir,
            run_qc_assessment_tsv_paths=run_qc_assessment_tsv_paths,
        )
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        _write_text_output(
            summary_tsv_out,
            render_result_explanation_summary_tsv(report),
        )
    if explanation_tsv_out is not None:
        _write_text_output(
            explanation_tsv_out,
            render_result_explanation_tsv(report),
        )
    if evidence_tsv_out is not None:
        _write_text_output(
            evidence_tsv_out,
            render_result_explanation_evidence_tsv(report),
        )

    payload = {
        "biological_report_dir": (
            None if biological_report_dir is None else str(biological_report_dir)
        ),
        "ptm_report_dir": None if ptm_report_dir is None else str(ptm_report_dir),
        "run_qc_assessment_tsv_paths": [
            str(path) for path in run_qc_assessment_tsv_paths
        ],
        "report": report.to_dict(),
        "outputs": {
            "summary_tsv": None if summary_tsv_out is None else str(summary_tsv_out),
            "explanation_tsv": (
                None if explanation_tsv_out is None else str(explanation_tsv_out)
            ),
            "evidence_tsv": (
                None if evidence_tsv_out is None else str(evidence_tsv_out)
            ),
        },
    }
    _emit_json(payload, out_path=out_path)


def run_failure_explanation_command(
    failure_text: str,
    workflow_name: str | None,
    summary_tsv_out: Path | None,
    explanation_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    report = build_failure_explanation_report(
        (
            FailureExplanationRequest(
                failure_id="failure_explanation",
                workflow_name=workflow_name,
                failure_text=failure_text,
            ),
        )
    )
    if summary_tsv_out is not None:
        _write_text_output(
            summary_tsv_out,
            render_failure_explanation_summary_tsv(report),
        )
    if explanation_tsv_out is not None:
        _write_text_output(
            explanation_tsv_out,
            render_failure_explanation_tsv(report),
        )

    payload = {
        "workflow_name": workflow_name,
        "report": report.to_dict(),
        "outputs": {
            "summary_tsv": None if summary_tsv_out is None else str(summary_tsv_out),
            "explanation_tsv": (
                None if explanation_tsv_out is None else str(explanation_tsv_out)
            ),
        },
    }
    _emit_json(payload, out_path=out_path)


def run_analysis_recommendations_command(
    biological_report_dir: Path | None,
    ptm_report_dir: Path | None,
    run_qc_assessment_tsv_paths: tuple[Path, ...],
    batch_effect_summary_tsv: Path | None,
    summary_tsv_out: Path | None,
    recommendation_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    if (
        biological_report_dir is None
        and ptm_report_dir is None
        and not run_qc_assessment_tsv_paths
        and batch_effect_summary_tsv is None
    ):
        raise click.ClickException(
            "at least one governed biological report, PTM report, QC assessment, or batch summary input must be provided"
        )

    try:
        report = build_analysis_recommendation_report_from_artifacts(
            biological_report_dir=biological_report_dir,
            ptm_report_dir=ptm_report_dir,
            run_qc_assessment_tsv_paths=run_qc_assessment_tsv_paths,
            batch_effect_summary_tsv_path=batch_effect_summary_tsv,
        )
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        _write_text_output(
            summary_tsv_out, render_analysis_recommendation_summary_tsv(report)
        )
    if recommendation_tsv_out is not None:
        _write_text_output(
            recommendation_tsv_out,
            render_analysis_recommendation_tsv(report),
        )

    payload = {
        "biological_report_dir": (
            None if biological_report_dir is None else str(biological_report_dir)
        ),
        "ptm_report_dir": None if ptm_report_dir is None else str(ptm_report_dir),
        "run_qc_assessment_tsv_paths": [
            str(path) for path in run_qc_assessment_tsv_paths
        ],
        "batch_effect_summary_tsv": (
            None if batch_effect_summary_tsv is None else str(batch_effect_summary_tsv)
        ),
        "report": report.to_dict(),
        "outputs": {
            "summary_tsv": None if summary_tsv_out is None else str(summary_tsv_out),
            "recommendation_tsv": (
                None if recommendation_tsv_out is None else str(recommendation_tsv_out)
            ),
        },
    }
    _emit_json(payload, out_path=out_path)


def run_compact_result_summary_command(
    biological_report_dir: Path,
    ptm_report_dir: Path | None,
    run_qc_assessment_tsv_paths: tuple[Path, ...],
    batch_effect_summary_tsv: Path | None,
    overview_tsv_out: Path | None,
    entry_tsv_out: Path | None,
    markdown_out: Path | None,
    out_path: Path | None,
) -> None:
    try:
        report = build_compact_result_summary_report_from_artifacts(
            biological_report_dir=biological_report_dir,
            ptm_report_dir=ptm_report_dir,
            run_qc_assessment_tsv_paths=run_qc_assessment_tsv_paths,
            batch_effect_summary_tsv_path=batch_effect_summary_tsv,
        )
        markdown = render_compact_result_summary_markdown(report)
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if overview_tsv_out is not None:
        _write_text_output(
            overview_tsv_out,
            render_compact_result_summary_overview_tsv(report),
        )
    if entry_tsv_out is not None:
        _write_text_output(
            entry_tsv_out,
            render_compact_result_summary_entry_tsv(report),
        )
    if markdown_out is not None:
        _write_text_output(markdown_out, markdown)

    payload = {
        "biological_report_dir": str(biological_report_dir),
        "ptm_report_dir": None if ptm_report_dir is None else str(ptm_report_dir),
        "run_qc_assessment_tsv_paths": [
            str(path) for path in run_qc_assessment_tsv_paths
        ],
        "batch_effect_summary_tsv": (
            None if batch_effect_summary_tsv is None else str(batch_effect_summary_tsv)
        ),
        "report": report.to_dict(),
        "markdown": markdown,
        "outputs": {
            "overview_tsv": None if overview_tsv_out is None else str(overview_tsv_out),
            "entry_tsv": None if entry_tsv_out is None else str(entry_tsv_out),
            "markdown": None if markdown_out is None else str(markdown_out),
        },
    }
    _emit_json(payload, out_path=out_path)


__all__ = [
    "run_result_question_answer_command",
    "run_result_explanation_command",
    "run_failure_explanation_command",
    "run_analysis_recommendations_command",
    "run_compact_result_summary_command",
]

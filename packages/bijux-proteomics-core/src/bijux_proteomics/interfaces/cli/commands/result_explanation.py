# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi
# ruff: noqa: F401,F403,F405

"""Result explanation CLI commands."""

from __future__ import annotations

from pathlib import Path

import click

from bijux_proteomics.interfaces.python_api.result_explanation import (
    run_analysis_recommendations_command,
    run_compact_result_summary_command,
    run_failure_explanation_command,
    run_result_explanation_command,
    run_result_question_answer_command,
)
from bijux_proteomics.interfaces.support import *  # noqa: F401,F403,F405


@click.command("result-question-answer")
@click.option(
    "--biological-report-dir",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--ptm-report-dir",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--run-qc-assessment-tsv",
    "run_qc_assessment_tsv_paths",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    multiple=True,
)
@click.option(
    "--query-kind",
    type=click.Choice([entry.value for entry in ResultQueryKind]),
    required=True,
)
@click.option("--subject-id", default=None)
@click.option("--summary-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--answer-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--evidence-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def result_question_answer_command(
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
    """Answer deterministic result questions from governed report artifacts."""
    return run_result_question_answer_command(
        biological_report_dir,
        ptm_report_dir,
        run_qc_assessment_tsv_paths,
        query_kind,
        subject_id,
        summary_tsv_out,
        answer_tsv_out,
        evidence_tsv_out,
        out_path,
    )


@click.command("result-explanation")
@click.option(
    "--biological-report-dir",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--ptm-report-dir",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--run-qc-assessment-tsv",
    "run_qc_assessment_tsv_paths",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    multiple=True,
)
@click.option(
    "--explanation-kind",
    type=click.Choice([entry.value for entry in ResultExplanationKind]),
    required=True,
)
@click.option("--subject-id", default=None)
@click.option("--summary-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option(
    "--explanation-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
)
@click.option("--evidence-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def result_explanation_command(
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
    """Explain deterministic result decisions from governed report artifacts."""
    return run_result_explanation_command(
        biological_report_dir,
        ptm_report_dir,
        run_qc_assessment_tsv_paths,
        explanation_kind,
        subject_id,
        summary_tsv_out,
        explanation_tsv_out,
        evidence_tsv_out,
        out_path,
    )


@click.command("failure-explanation")
@click.argument("failure_text")
@click.option("--workflow-name", default=None)
@click.option("--summary-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option(
    "--explanation-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def failure_explanation_command(
    failure_text: str,
    workflow_name: str | None,
    summary_tsv_out: Path | None,
    explanation_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    """Explain one expected scientific workflow failure deterministically."""
    return run_failure_explanation_command(
        failure_text, workflow_name, summary_tsv_out, explanation_tsv_out, out_path
    )


@click.command("analysis-recommendations")
@click.option(
    "--biological-report-dir",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--ptm-report-dir",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--run-qc-assessment-tsv",
    "run_qc_assessment_tsv_paths",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    multiple=True,
)
@click.option(
    "--batch-effect-summary-tsv",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option("--summary-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option(
    "--recommendation-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def analysis_recommendations_command(
    biological_report_dir: Path | None,
    ptm_report_dir: Path | None,
    run_qc_assessment_tsv_paths: tuple[Path, ...],
    batch_effect_summary_tsv: Path | None,
    summary_tsv_out: Path | None,
    recommendation_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    """Recommend deterministic next analysis actions from governed artifacts."""
    return run_analysis_recommendations_command(
        biological_report_dir,
        ptm_report_dir,
        run_qc_assessment_tsv_paths,
        batch_effect_summary_tsv,
        summary_tsv_out,
        recommendation_tsv_out,
        out_path,
    )


@click.command("compact-result-summary")
@click.option(
    "--biological-report-dir",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    required=True,
)
@click.option(
    "--ptm-report-dir",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--run-qc-assessment-tsv",
    "run_qc_assessment_tsv_paths",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    multiple=True,
)
@click.option(
    "--batch-effect-summary-tsv",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
)
@click.option("--overview-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--entry-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--markdown-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def compact_result_summary_command(
    biological_report_dir: Path,
    ptm_report_dir: Path | None,
    run_qc_assessment_tsv_paths: tuple[Path, ...],
    batch_effect_summary_tsv: Path | None,
    overview_tsv_out: Path | None,
    entry_tsv_out: Path | None,
    markdown_out: Path | None,
    out_path: Path | None,
) -> None:
    """Render a short collaborator summary constrained to governed evidence surfaces."""
    return run_compact_result_summary_command(
        biological_report_dir,
        ptm_report_dir,
        run_qc_assessment_tsv_paths,
        batch_effect_summary_tsv,
        overview_tsv_out,
        entry_tsv_out,
        markdown_out,
        out_path,
    )


COMMANDS = (
    result_question_answer_command,
    result_explanation_command,
    failure_explanation_command,
    analysis_recommendations_command,
    compact_result_summary_command,
)

# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi
# ruff: noqa: F401,F403,F405

"""Result search and comparison CLI commands."""

from __future__ import annotations

from bijux_proteomics.interfaces.support import *  # noqa: F401,F403,F405
from bijux_proteomics.interfaces.python_api.results_query import (
    run_interactive_result_bundle_command,
    run_interactive_result_comparison_command,
    run_result_manifest_command,
    run_result_search_command,
    run_validate_result_command,
)

@click.command("result-search")
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
@click.option("--query", "query_text", required=True)
@click.option("--limit", type=int, default=20, show_default=True)
@click.option("--summary-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--hit-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def result_search_command(
    biological_report_dir: Path | None,
    ptm_report_dir: Path | None,
    query_text: str,
    limit: int,
    summary_tsv_out: Path | None,
    hit_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    'Search governed protein, PTM-site, pathway, and peptide result objects.'
    return run_result_search_command(biological_report_dir, ptm_report_dir, query_text, limit, summary_tsv_out, hit_tsv_out, out_path)

@click.command("interactive-result-comparison")
@click.option(
    "--left-biological-report-dir",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--left-ptm-report-dir",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--left-run-qc-assessment-tsv",
    "left_run_qc_assessment_tsv_paths",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    multiple=True,
)
@click.option(
    "--right-biological-report-dir",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--right-ptm-report-dir",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    default=None,
)
@click.option(
    "--right-run-qc-assessment-tsv",
    "right_run_qc_assessment_tsv_paths",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    multiple=True,
)
@click.option("--summary-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--protein-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--ptm-site-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--qc-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--pathway-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def interactive_result_comparison_command(
    left_biological_report_dir: Path | None,
    left_ptm_report_dir: Path | None,
    left_run_qc_assessment_tsv_paths: tuple[Path, ...],
    right_biological_report_dir: Path | None,
    right_ptm_report_dir: Path | None,
    right_run_qc_assessment_tsv_paths: tuple[Path, ...],
    summary_tsv_out: Path | None,
    protein_tsv_out: Path | None,
    ptm_site_tsv_out: Path | None,
    qc_tsv_out: Path | None,
    pathway_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    'Compare two governed result bundles for frontend-ready review clients.'
    return run_interactive_result_comparison_command(left_biological_report_dir, left_ptm_report_dir, left_run_qc_assessment_tsv_paths, right_biological_report_dir, right_ptm_report_dir, right_run_qc_assessment_tsv_paths, summary_tsv_out, protein_tsv_out, ptm_site_tsv_out, qc_tsv_out, pathway_tsv_out, out_path)

@click.command("interactive-result-bundle")
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
@click.option("--summary-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def interactive_result_bundle_command(
    biological_report_dir: Path | None,
    ptm_report_dir: Path | None,
    run_qc_assessment_tsv_paths: tuple[Path, ...],
    summary_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    'Build one frontend-ready result bundle from governed report artifacts.'
    return run_interactive_result_bundle_command(biological_report_dir, ptm_report_dir, run_qc_assessment_tsv_paths, summary_tsv_out, out_path)

@click.command("result-manifest")
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
    "--input",
    "input_paths",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    multiple=True,
)
@click.option(
    "--command",
    "commands",
    multiple=True,
    required=True,
)
@click.option("--summary-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--input-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--command-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--file-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--warning-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--manifest-json-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def result_manifest_command(
    biological_report_dir: Path | None,
    ptm_report_dir: Path | None,
    run_qc_assessment_tsv_paths: tuple[Path, ...],
    input_paths: tuple[Path, ...],
    commands: tuple[str, ...],
    summary_tsv_out: Path | None,
    input_tsv_out: Path | None,
    command_tsv_out: Path | None,
    file_tsv_out: Path | None,
    warning_tsv_out: Path | None,
    manifest_json_out: Path | None,
    out_path: Path | None,
) -> None:
    'Emit a machine-readable completeness manifest over exported result directories.'
    return run_result_manifest_command(biological_report_dir, ptm_report_dir, run_qc_assessment_tsv_paths, input_paths, commands, summary_tsv_out, input_tsv_out, command_tsv_out, file_tsv_out, warning_tsv_out, manifest_json_out, out_path)

@click.command("validate-result")
@click.argument(
    "result_root",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
)
@click.option(
    "--command",
    "commands",
    multiple=True,
)
@click.option("--summary-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--input-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--command-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--file-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--warning-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--manifest-json-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def validate_result_command(
    result_root: Path,
    commands: tuple[str, ...],
    summary_tsv_out: Path | None,
    input_tsv_out: Path | None,
    command_tsv_out: Path | None,
    file_tsv_out: Path | None,
    warning_tsv_out: Path | None,
    manifest_json_out: Path | None,
    out_path: Path | None,
) -> None:
    'Validate one governed result root and emit a stable completeness manifest.'
    return run_validate_result_command(
        result_root,
        commands,
        summary_tsv_out,
        input_tsv_out,
        command_tsv_out,
        file_tsv_out,
        warning_tsv_out,
        manifest_json_out,
        out_path,
    )

COMMANDS = (
    result_search_command,
    interactive_result_comparison_command,
    interactive_result_bundle_command,
    result_manifest_command,
    validate_result_command,
)

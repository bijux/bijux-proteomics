# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi
# ruff: noqa: F401,F403,F405

"""Result search and comparison CLI commands."""

from __future__ import annotations

from bijux_proteomics.interfaces.cli.support import *  # noqa: F401,F403,F405

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

def run_result_search_command(
    biological_report_dir: Path | None,
    ptm_report_dir: Path | None,
    query_text: str,
    limit: int,
    summary_tsv_out: Path | None,
    hit_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    if biological_report_dir is None and ptm_report_dir is None:
        raise click.ClickException(
            "at least one governed biological report or PTM report input must be provided"
        )

    try:
        index = build_result_search_index_from_artifacts(
            biological_report_dir=biological_report_dir,
            ptm_report_dir=ptm_report_dir,
        )
        report = search_result_index(index, query_text, limit=limit)
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        _write_text_output(summary_tsv_out, render_result_search_summary_tsv(report))
    if hit_tsv_out is not None:
        _write_text_output(hit_tsv_out, render_result_search_hit_tsv(report))

    payload = {
        "biological_report_dir": (
            None if biological_report_dir is None else str(biological_report_dir)
        ),
        "ptm_report_dir": None if ptm_report_dir is None else str(ptm_report_dir),
        "query_text": query_text,
        "limit": limit,
        "index": index.to_dict(),
        "report": report.to_dict(),
        "outputs": {
            "summary_tsv": None if summary_tsv_out is None else str(summary_tsv_out),
            "hit_tsv": None if hit_tsv_out is None else str(hit_tsv_out),
        },
    }
    _emit_json(payload, out_path=out_path)

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

def run_interactive_result_comparison_command(
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
    try:
        payload = build_interactive_result_comparison_from_artifacts(
            left_biological_report_dir=left_biological_report_dir,
            left_ptm_report_dir=left_ptm_report_dir,
            left_run_qc_assessment_tsv_paths=left_run_qc_assessment_tsv_paths,
            right_biological_report_dir=right_biological_report_dir,
            right_ptm_report_dir=right_ptm_report_dir,
            right_run_qc_assessment_tsv_paths=right_run_qc_assessment_tsv_paths,
        )
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        _write_text_output(
            summary_tsv_out,
            render_interactive_result_comparison_summary_tsv(payload),
        )
    if protein_tsv_out is not None:
        _write_text_output(
            protein_tsv_out,
            render_interactive_result_comparison_protein_tsv(payload),
        )
    if ptm_site_tsv_out is not None:
        _write_text_output(
            ptm_site_tsv_out,
            render_interactive_result_comparison_ptm_site_tsv(payload),
        )
    if qc_tsv_out is not None:
        _write_text_output(
            qc_tsv_out,
            render_interactive_result_comparison_qc_tsv(payload),
        )
    if pathway_tsv_out is not None:
        _write_text_output(
            pathway_tsv_out,
            render_interactive_result_comparison_pathway_tsv(payload),
        )

    json_payload = {
        "left_biological_report_dir": (
            None
            if left_biological_report_dir is None
            else str(left_biological_report_dir)
        ),
        "left_ptm_report_dir": (
            None if left_ptm_report_dir is None else str(left_ptm_report_dir)
        ),
        "left_run_qc_assessment_tsv_paths": [
            str(path) for path in left_run_qc_assessment_tsv_paths
        ],
        "right_biological_report_dir": (
            None
            if right_biological_report_dir is None
            else str(right_biological_report_dir)
        ),
        "right_ptm_report_dir": (
            None if right_ptm_report_dir is None else str(right_ptm_report_dir)
        ),
        "right_run_qc_assessment_tsv_paths": [
            str(path) for path in right_run_qc_assessment_tsv_paths
        ],
        "payload": payload.to_dict(),
        "outputs": {
            "summary_tsv": None if summary_tsv_out is None else str(summary_tsv_out),
            "protein_tsv": None if protein_tsv_out is None else str(protein_tsv_out),
            "ptm_site_tsv": (
                None if ptm_site_tsv_out is None else str(ptm_site_tsv_out)
            ),
            "qc_tsv": None if qc_tsv_out is None else str(qc_tsv_out),
            "pathway_tsv": None if pathway_tsv_out is None else str(pathway_tsv_out),
        },
    }
    _emit_json(json_payload, out_path=out_path)

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

def run_interactive_result_bundle_command(
    biological_report_dir: Path | None,
    ptm_report_dir: Path | None,
    run_qc_assessment_tsv_paths: tuple[Path, ...],
    summary_tsv_out: Path | None,
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
        bundle = build_interactive_result_bundle_from_artifacts(
            biological_report_dir=biological_report_dir,
            ptm_report_dir=ptm_report_dir,
            run_qc_assessment_tsv_paths=run_qc_assessment_tsv_paths,
        )
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        _write_text_output(
            summary_tsv_out,
            render_interactive_result_bundle_summary_tsv(bundle),
        )

    payload = {
        "biological_report_dir": (
            None if biological_report_dir is None else str(biological_report_dir)
        ),
        "ptm_report_dir": None if ptm_report_dir is None else str(ptm_report_dir),
        "run_qc_assessment_tsv_paths": [str(path) for path in run_qc_assessment_tsv_paths],
        "bundle": bundle.to_dict(),
        "outputs": {
            "summary_tsv": None if summary_tsv_out is None else str(summary_tsv_out),
        },
    }
    _emit_json(payload, out_path=out_path)

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

def run_result_manifest_command(
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
    try:
        report = build_result_manifest_from_artifacts(
            biological_report_dir=biological_report_dir,
            ptm_report_dir=ptm_report_dir,
            run_qc_assessment_tsv_paths=run_qc_assessment_tsv_paths,
            input_paths=input_paths,
            commands=commands,
        )
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        _write_text_output(summary_tsv_out, render_result_manifest_summary_tsv(report))
    if input_tsv_out is not None:
        _write_text_output(input_tsv_out, render_result_manifest_input_tsv(report))
    if command_tsv_out is not None:
        _write_text_output(command_tsv_out, render_result_manifest_command_tsv(report))
    if file_tsv_out is not None:
        _write_text_output(file_tsv_out, render_result_manifest_file_tsv(report))
    if warning_tsv_out is not None:
        _write_text_output(warning_tsv_out, render_result_manifest_warning_tsv(report))
    if manifest_json_out is not None:
        _write_text_output(manifest_json_out, report.to_stable_json() + "\n")

    payload = {
        "biological_report_dir": (
            None if biological_report_dir is None else str(biological_report_dir)
        ),
        "ptm_report_dir": None if ptm_report_dir is None else str(ptm_report_dir),
        "run_qc_assessment_tsv_paths": [str(path) for path in run_qc_assessment_tsv_paths],
        "input_paths": [str(path) for path in input_paths],
        "commands": list(commands),
        "report": report.to_dict(),
        "outputs": {
            "summary_tsv": None if summary_tsv_out is None else str(summary_tsv_out),
            "input_tsv": None if input_tsv_out is None else str(input_tsv_out),
            "command_tsv": None if command_tsv_out is None else str(command_tsv_out),
            "file_tsv": None if file_tsv_out is None else str(file_tsv_out),
            "warning_tsv": None if warning_tsv_out is None else str(warning_tsv_out),
            "manifest_json": (
                None if manifest_json_out is None else str(manifest_json_out)
            ),
        },
    }
    _emit_json(payload, out_path=out_path)

COMMANDS = (
    result_search_command,
    interactive_result_comparison_command,
    interactive_result_bundle_command,
    result_manifest_command,
)

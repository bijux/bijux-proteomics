# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi
# ruff: noqa: F401,F403,F405

"""Result search and comparison Python API entrypoints."""

from __future__ import annotations

from bijux_proteomics.interfaces.support import *  # noqa: F401,F403,F405
from bijux_proteomics.interfaces.support.workflow import *  # noqa: F401,F403,F405
from bijux_proteomics.workflow.demo.scale_demo import ScaleDemoReport
from bijux_proteomics.workflow.demo.surprising_demo import SurprisingDemoReport


def _resolve_result_root_report_dirs(
    result_root: Path,
) -> tuple[Path | None, Path | None]:
    if not result_root.exists():
        raise click.ClickException(f"result root does not exist: {result_root}")
    if not result_root.is_dir():
        raise click.ClickException(
            f"result root must be a directory, not a file path: {result_root}"
        )

    direct_biological = _manifest_parent_if_present(
        result_root, "biological_report_manifest.json"
    )
    direct_ptm = _manifest_parent_if_present(result_root, "ptm_report_manifest.json")
    if direct_biological is not None or direct_ptm is not None:
        return direct_biological, direct_ptm

    surprising_report_path = result_root / "surprising_demo_report.json"
    if surprising_report_path.exists():
        report = SurprisingDemoReport.model_validate_json(
            surprising_report_path.read_text(encoding="utf-8")
        )
        return (
            _resolve_relative_result_dir(
                result_root, report.artifacts.biological_output_dir
            ),
            _resolve_relative_result_dir(result_root, report.artifacts.ptm_output_dir),
        )

    scale_report_path = result_root / "scale_demo_report.json"
    if scale_report_path.exists():
        scale_report = ScaleDemoReport.model_validate_json(
            scale_report_path.read_text(encoding="utf-8")
        )
        return (
            _resolve_relative_result_dir(
                result_root, scale_report.artifacts.biological_output_dir
            ),
            None,
        )

    biological_candidates = (
        result_root / "biological_review",
        result_root / "biological_report",
    )
    ptm_candidates = (
        result_root / "ptm_review",
        result_root / "ptm_report",
    )
    biological_report_dir = next(
        (
            path
            for path in biological_candidates
            if (path / "biological_report_manifest.json").exists()
        ),
        None,
    )
    ptm_report_dir = next(
        (
            path
            for path in ptm_candidates
            if (path / "ptm_report_manifest.json").exists()
        ),
        None,
    )
    if biological_report_dir is not None or ptm_report_dir is not None:
        return biological_report_dir, ptm_report_dir

    raise click.ClickException(
        "result root must contain a governed biological report, PTM report, "
        "surprising demo report, or scale demo report"
    )


def _manifest_parent_if_present(root: Path, manifest_name: str) -> Path | None:
    manifest_path = root / manifest_name
    if manifest_path.exists():
        return root
    return None


def _resolve_relative_result_dir(root: Path, relative_dir: str) -> Path:
    path = (root / relative_dir).resolve()
    if not path.exists():
        raise click.ClickException(
            f"result root references a missing governed report directory: {path}"
        )
    return path


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


def run_validate_result_command(
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
    biological_report_dir, ptm_report_dir = _resolve_result_root_report_dirs(
        result_root
    )
    command_texts = commands if commands else (f"validate-result {result_root}",)
    manifest_path = (
        manifest_json_out
        if manifest_json_out is not None
        else result_root / "result_manifest.json"
    )

    run_result_manifest_command(
        biological_report_dir=biological_report_dir,
        ptm_report_dir=ptm_report_dir,
        run_qc_assessment_tsv_paths=(),
        input_paths=(),
        commands=command_texts,
        summary_tsv_out=summary_tsv_out,
        input_tsv_out=input_tsv_out,
        command_tsv_out=command_tsv_out,
        file_tsv_out=file_tsv_out,
        warning_tsv_out=warning_tsv_out,
        manifest_json_out=manifest_path,
        out_path=out_path,
    )


def run_query_result_command(
    result_root: Path,
    query_text: str,
    limit: int,
    summary_tsv_out: Path | None,
    hit_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    biological_report_dir, ptm_report_dir = _resolve_result_root_report_dirs(
        result_root
    )
    run_result_search_command(
        biological_report_dir=biological_report_dir,
        ptm_report_dir=ptm_report_dir,
        query_text=query_text,
        limit=limit,
        summary_tsv_out=summary_tsv_out,
        hit_tsv_out=hit_tsv_out,
        out_path=out_path,
    )


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
        "run_qc_assessment_tsv_paths": [
            str(path) for path in run_qc_assessment_tsv_paths
        ],
        "bundle": bundle.to_dict(),
        "outputs": {
            "summary_tsv": None if summary_tsv_out is None else str(summary_tsv_out),
        },
    }
    _emit_json(payload, out_path=out_path)


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
        "run_qc_assessment_tsv_paths": [
            str(path) for path in run_qc_assessment_tsv_paths
        ],
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


__all__ = [
    "run_interactive_result_bundle_command",
    "run_interactive_result_comparison_command",
    "run_query_result_command",
    "run_result_manifest_command",
    "run_result_search_command",
    "run_validate_result_command",
]

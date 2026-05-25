# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi
# ruff: noqa: F401,F403,F405

"""Public benchmark and demo CLI commands."""

from __future__ import annotations

from bijux_proteomics.interfaces.cli.support import *  # noqa: F401,F403,F405

@click.command("public-benchmark-runner")
@click.argument(
    "benchmark_path",
    type=click.Path(path_type=Path),
)
@click.option(
    "--run-output-root",
    type=click.Path(path_type=Path, file_okay=False),
    default=Path("artifacts/public-benchmark-runs"),
    show_default=True,
)
@click.option("--summary-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--failures-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option(
    "--signal-assessments-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def public_benchmark_runner_command(
    benchmark_path: Path,
    run_output_root: Path,
    summary_tsv_out: Path | None,
    failures_tsv_out: Path | None,
    signal_assessments_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    'Run one public benchmark descriptor or a whole public benchmark root.'
    return run_public_benchmark_runner_command(benchmark_path, run_output_root, summary_tsv_out, failures_tsv_out, signal_assessments_tsv_out, out_path)

def run_public_benchmark_runner_command(
    benchmark_path: Path,
    run_output_root: Path,
    summary_tsv_out: Path | None,
    failures_tsv_out: Path | None,
    signal_assessments_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    try:
        benchmark_path = resolve_public_benchmark_path(benchmark_path)
        if benchmark_path.is_dir():
            suite = run_public_benchmark_descriptor_suite(
                benchmark_path,
                output_root=run_output_root,
            )
            payload: Any = suite
        else:
            run_report = run_public_benchmark_descriptor(
                benchmark_path,
                output_root=run_output_root,
            )
            from bijux_proteomics.workflow.public_benchmark_runner import (
                PublicBenchmarkSuiteReport,
            )

            suite = PublicBenchmarkSuiteReport(
                benchmark_root=str(benchmark_path.parent),
                output_root=str(run_output_root),
                runs=(run_report,),
                passed_count=1 if run_report.status == "passed" else 0,
                failed_count=1 if run_report.status == "failed" else 0,
                note=(
                    "single benchmark descriptor wrapped as a one-row suite for "
                    "summary and failure rendering"
                ),
            )
            payload = run_report
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        _write_text_output(
            summary_tsv_out,
            render_public_benchmark_suite_summary_tsv(suite),
        )
    if failures_tsv_out is not None:
        _write_text_output(
            failures_tsv_out,
            render_public_benchmark_suite_failures_tsv(suite),
        )
    if signal_assessments_tsv_out is not None:
        _write_text_output(
            signal_assessments_tsv_out,
            render_public_benchmark_suite_signal_assessments_tsv(suite),
        )
    _emit_json(payload, out_path=out_path)

@click.command("build-trust-bundle")
@click.option(
    "--benchmarks",
    "benchmark_root",
    type=click.Path(file_okay=False, path_type=Path),
    required=True,
)
@click.option(
    "--out",
    "output_dir",
    type=click.Path(file_okay=False, path_type=Path),
    required=True,
)
@click.option("--summary-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option(
    "--manifest-json-out",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def build_trust_bundle_command(
    benchmark_root: Path,
    output_dir: Path,
    summary_tsv_out: Path | None,
    manifest_json_out: Path | None,
) -> None:
    'Build a regenerable trust bundle from public benchmark descriptors.'
    return run_build_trust_bundle_command(benchmark_root, output_dir, summary_tsv_out, manifest_json_out)

def run_build_trust_bundle_command(
    benchmark_root: Path,
    output_dir: Path,
    summary_tsv_out: Path | None,
    manifest_json_out: Path | None,
) -> None:
    try:
        benchmark_root = resolve_public_benchmark_root(benchmark_root)
        report = build_public_benchmark_trust_bundle(
            benchmark_root,
            output_dir=output_dir,
        )
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        _write_text_output(summary_tsv_out, render_trust_bundle_run_summary_tsv(report))
    if manifest_json_out is not None:
        manifest_json_out.write_text(report.to_stable_json() + "\n", encoding="utf-8")
    _emit_json(report)

@click.command("demo")
@click.option(
    "--out-dir",
    "output_dir",
    type=click.Path(file_okay=False, path_type=Path),
    default=Path("artifacts/proteomics-demo"),
    show_default=True,
)
@click.option("--summary-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--findings-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--claims-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option(
    "--contradictions-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
)
@click.option(
    "--belief-audit-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def surprising_demo_command(
    output_dir: Path,
    summary_tsv_out: Path | None,
    findings_tsv_out: Path | None,
    claims_tsv_out: Path | None,
    contradictions_tsv_out: Path | None,
    belief_audit_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    'Run the shipped proteomics demo from local example data only.'
    return run_surprising_demo_command(output_dir, summary_tsv_out, findings_tsv_out, claims_tsv_out, contradictions_tsv_out, belief_audit_tsv_out, out_path)

def run_surprising_demo_command(
    output_dir: Path,
    summary_tsv_out: Path | None,
    findings_tsv_out: Path | None,
    claims_tsv_out: Path | None,
    contradictions_tsv_out: Path | None,
    belief_audit_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    try:
        report = run_surprising_demo(SurprisingDemoConfig(output_dir=output_dir))
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        _write_text_output(summary_tsv_out, render_surprising_demo_summary_tsv(report))
    if findings_tsv_out is not None:
        _write_text_output(findings_tsv_out, render_surprising_demo_findings_tsv(report))
    if claims_tsv_out is not None:
        claims_tsv_out.write_text(
            (output_dir / report.artifacts.claims_tsv).read_text(encoding="utf-8"),
            encoding="utf-8",
        )
    if contradictions_tsv_out is not None:
        contradictions_tsv_out.write_text(
            (output_dir / report.artifacts.contradictions_tsv).read_text(
                encoding="utf-8"
            ),
            encoding="utf-8",
        )
    if belief_audit_tsv_out is not None:
        belief_audit_tsv_out.write_text(
            (output_dir / report.artifacts.belief_audit_tsv).read_text(
                encoding="utf-8"
            ),
            encoding="utf-8",
        )
    _emit_json(report, out_path=out_path)

@click.command("demo-query")
@click.option(
    "--out-dir",
    "output_dir",
    type=click.Path(file_okay=False, path_type=Path),
    default=Path("artifacts/proteomics-demo"),
    show_default=True,
)
@click.option(
    "--query-kind",
    type=click.Choice([entry.value for entry in SurprisingDemoQueryKind]),
    default=None,
)
@click.option("--subject-id", default=None)
@click.option("--summary-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--answers-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def surprising_demo_query_command(
    output_dir: Path,
    query_kind: str | None,
    subject_id: str | None,
    summary_tsv_out: Path | None,
    answers_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    'Answer deterministic shipped-demo questions from owned local outputs.'
    return run_surprising_demo_query_command(output_dir, query_kind, subject_id, summary_tsv_out, answers_tsv_out, out_path)

def run_surprising_demo_query_command(
    output_dir: Path,
    query_kind: str | None,
    subject_id: str | None,
    summary_tsv_out: Path | None,
    answers_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    if (query_kind is None) != (subject_id is None):
        raise click.ClickException(
            "--query-kind and --subject-id must be provided together for one-off queries"
        )

    try:
        ensure_surprising_demo_outputs(output_dir)
        requests = (
            build_surprising_demo_example_requests(output_dir)
            if query_kind is None
            else (
                SurprisingDemoQueryRequest(
                    query_id="demo-query",
                    query_kind=SurprisingDemoQueryKind(query_kind),
                    subject_id=subject_id,
                ),
            )
        )
        report = build_surprising_demo_interrogation_report(output_dir, requests)
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        _write_text_output(
            summary_tsv_out,
            render_surprising_demo_interrogation_summary_tsv(report),
        )
    if answers_tsv_out is not None:
        _write_text_output(
            answers_tsv_out,
            render_surprising_demo_interrogation_answers_tsv(report),
        )
    _emit_json(report, out_path=out_path)

@click.command("demo-report")
@click.option(
    "--out-dir",
    "output_dir",
    type=click.Path(file_okay=False, path_type=Path),
    default=Path("artifacts/proteomics-demo"),
    show_default=True,
)
@click.option("--summary-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--sentences-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--html-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def surprising_demo_report_command(
    output_dir: Path,
    summary_tsv_out: Path | None,
    sentences_tsv_out: Path | None,
    html_out: Path | None,
    out_path: Path | None,
) -> None:
    'Build the shipped integrated scientific report from owned local outputs.'
    return run_surprising_demo_report_command(output_dir, summary_tsv_out, sentences_tsv_out, html_out, out_path)

def run_surprising_demo_report_command(
    output_dir: Path,
    summary_tsv_out: Path | None,
    sentences_tsv_out: Path | None,
    html_out: Path | None,
    out_path: Path | None,
) -> None:
    try:
        report = build_integrated_scientific_report(output_dir)
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        _write_text_output(
            summary_tsv_out,
            render_integrated_scientific_report_summary_tsv(report),
        )
    if sentences_tsv_out is not None:
        _write_text_output(
            sentences_tsv_out,
            render_integrated_scientific_report_sentences_tsv(report),
        )
    if html_out is not None:
        html_out.write_text(
            (output_dir / report.artifacts.report_html).read_text(encoding="utf-8"),
            encoding="utf-8",
        )
    _emit_json(report, out_path=out_path)

@click.command("public-dataset-comparison")
@click.option(
    "--benchmarks",
    "benchmark_root",
    type=click.Path(file_okay=False, path_type=Path),
    required=True,
)
@click.option(
    "--run-output-root",
    type=click.Path(path_type=Path, file_okay=False),
    default=Path("artifacts/public-dataset-comparison-runs"),
    show_default=True,
)
@click.option(
    "--dataset-summary-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
)
@click.option(
    "--failure-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
)
@click.option(
    "--combined-summary-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
)
@click.option(
    "--effect-comparison-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
)
@click.option(
    "--meta-analysis-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
)
@click.option(
    "--pathway-comparison-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def public_dataset_comparison_command(
    benchmark_root: Path,
    run_output_root: Path,
    dataset_summary_tsv_out: Path | None,
    failure_tsv_out: Path | None,
    combined_summary_tsv_out: Path | None,
    effect_comparison_tsv_out: Path | None,
    meta_analysis_tsv_out: Path | None,
    pathway_comparison_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    'Run one biological question across multiple public dataset descriptors.'
    return run_public_dataset_comparison_command(benchmark_root, run_output_root, dataset_summary_tsv_out, failure_tsv_out, combined_summary_tsv_out, effect_comparison_tsv_out, meta_analysis_tsv_out, pathway_comparison_tsv_out, out_path)

def run_public_dataset_comparison_command(
    benchmark_root: Path,
    run_output_root: Path,
    dataset_summary_tsv_out: Path | None,
    failure_tsv_out: Path | None,
    combined_summary_tsv_out: Path | None,
    effect_comparison_tsv_out: Path | None,
    meta_analysis_tsv_out: Path | None,
    pathway_comparison_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    try:
        benchmark_root = resolve_public_benchmark_root(benchmark_root)
        report = build_public_dataset_comparison_report(
            benchmark_root,
            run_output_root=run_output_root,
        )
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if dataset_summary_tsv_out is not None:
        _write_text_output(
            dataset_summary_tsv_out,
            render_public_dataset_dataset_summary_tsv(report),
        )
    if failure_tsv_out is not None:
        _write_text_output(
            failure_tsv_out,
            render_public_dataset_failure_tsv(report),
        )
    if combined_summary_tsv_out is not None:
        _write_text_output(
            combined_summary_tsv_out,
            render_public_dataset_combined_summary_tsv(report),
        )
    if effect_comparison_tsv_out is not None:
        _write_text_output(
            effect_comparison_tsv_out,
            render_public_dataset_effect_comparison_tsv(report),
        )
    if meta_analysis_tsv_out is not None:
        _write_text_output(
            meta_analysis_tsv_out,
            render_public_dataset_meta_analysis_tsv(report),
        )
    if pathway_comparison_tsv_out is not None:
        _write_text_output(
            pathway_comparison_tsv_out,
            render_public_dataset_pathway_comparison_tsv(report),
        )
    _emit_json(report, out_path=out_path)

@click.command("public-dataset-evidence-cards")
@click.option(
    "--benchmarks",
    "benchmark_root",
    type=click.Path(file_okay=False, path_type=Path),
    required=True,
)
@click.option(
    "--run-output-root",
    type=click.Path(path_type=Path, file_okay=False),
    default=Path("artifacts/public-dataset-evidence-card-runs"),
    show_default=True,
)
@click.option("--summary-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option("--cards-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option(
    "--dataset-evidence-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def public_dataset_evidence_cards_command(
    benchmark_root: Path,
    run_output_root: Path,
    summary_tsv_out: Path | None,
    cards_tsv_out: Path | None,
    dataset_evidence_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    'Build cross-study evidence cards over public dataset descriptors.'
    return run_public_dataset_evidence_cards_command(benchmark_root, run_output_root, summary_tsv_out, cards_tsv_out, dataset_evidence_tsv_out, out_path)

def run_public_dataset_evidence_cards_command(
    benchmark_root: Path,
    run_output_root: Path,
    summary_tsv_out: Path | None,
    cards_tsv_out: Path | None,
    dataset_evidence_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    try:
        benchmark_root = resolve_public_benchmark_root(benchmark_root)
        report = build_public_dataset_evidence_card_report(
            benchmark_root,
            run_output_root=run_output_root,
        )
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    if summary_tsv_out is not None:
        _write_text_output(
            summary_tsv_out,
            render_cross_study_evidence_card_summary_tsv(report),
        )
    if cards_tsv_out is not None:
        _write_text_output(
            cards_tsv_out,
            render_cross_study_evidence_card_tsv(report),
        )
    if dataset_evidence_tsv_out is not None:
        _write_text_output(
            dataset_evidence_tsv_out,
            render_cross_study_evidence_dataset_tsv(report),
        )
    _emit_json(report, out_path=out_path)

@click.command("public-case-study")
@click.option("--summary-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option(
    "--report-dir",
    type=click.Path(path_type=Path, file_okay=False),
    default=None,
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def public_case_study_command(
    summary_tsv_out: Path | None,
    report_dir: Path | None,
    out_path: Path | None,
) -> None:
    'Run the owned public LFQ case study through final biological reporting.'
    return run_public_case_study_command(summary_tsv_out, report_dir, out_path)

def run_public_case_study_command(
    summary_tsv_out: Path | None,
    report_dir: Path | None,
    out_path: Path | None,
) -> None:
    try:
        report = build_lfq_cohort_biological_case_study_report()
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    export_manifest = None
    manifest_path = None
    if summary_tsv_out is not None:
        _write_text_output(
            summary_tsv_out,
            render_public_biological_case_study_summary_tsv(report),
        )
    if report_dir is not None:
        export_manifest = export_public_biological_case_study_report(report, report_dir)
        manifest_path = report_dir / "public_case_study_manifest.json"
        manifest_path.write_text(
            export_manifest.to_stable_json() + "\n",
            encoding="utf-8",
        )

    payload = {
        "case_study_id": report.summary.case_study_id,
        "workflow_family": report.summary.workflow_family,
        "source_package_id": report.case_study.source_package_id,
        "public_dataset_identity": report.case_study.public_dataset_identity,
        "summary": report.summary.to_dict(),
        "outputs": {
            "summary_tsv": None if summary_tsv_out is None else str(summary_tsv_out),
            "report_dir": None if report_dir is None else str(report_dir),
            "report_manifest_json": None
            if manifest_path is None
            else str(manifest_path),
        },
    }
    _emit_json(payload, out_path=out_path)

COMMANDS = (
    public_benchmark_runner_command,
    build_trust_bundle_command,
    surprising_demo_command,
    surprising_demo_query_command,
    surprising_demo_report_command,
    public_dataset_comparison_command,
    public_dataset_evidence_cards_command,
    public_case_study_command,
)

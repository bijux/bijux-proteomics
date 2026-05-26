# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi
# ruff: noqa: F401,F403,F405

"""Public benchmark and demo CLI commands."""

from __future__ import annotations

from bijux_proteomics.interfaces.support import *  # noqa: F401,F403,F405
from bijux_proteomics.interfaces.support.workflow import *  # noqa: F401,F403,F405
from bijux_proteomics.interfaces.python_api.benchmark_demo import run_public_benchmark_runner_command, run_build_trust_bundle_command, run_scale_demo_command, run_surprising_demo_command, run_surprising_demo_query_command, run_surprising_demo_report_command, run_public_dataset_comparison_command, run_public_dataset_evidence_cards_command, run_public_case_study_command

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

@click.command("demo-scale")
@click.option(
    "--out-dir",
    "output_dir",
    type=click.Path(file_okay=False, path_type=Path),
    default=Path("artifacts/proteomics-scale-demo"),
    show_default=True,
)
@click.option("--protein-count", type=int, default=180, show_default=True)
@click.option("--peptides-per-protein", type=int, default=4, show_default=True)
@click.option("--replicates-per-condition", type=int, default=6, show_default=True)
@click.option("--pathway-count", type=int, default=18, show_default=True)
@click.option("--summary-tsv-out", type=click.Path(path_type=Path, dir_okay=False))
@click.option(
    "--stage-metrics-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
)
@click.option(
    "--validation-tsv-out",
    type=click.Path(path_type=Path, dir_okay=False),
)
@click.option(
    "--out",
    "out_path",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
)
def scale_demo_command(
    output_dir: Path,
    protein_count: int,
    peptides_per_protein: int,
    replicates_per_condition: int,
    pathway_count: int,
    summary_tsv_out: Path | None,
    stage_metrics_tsv_out: Path | None,
    validation_tsv_out: Path | None,
    out_path: Path | None,
) -> None:
    'Generate a local scale dataset and run owned parsing, quant, graph, and report validation.'
    return run_scale_demo_command(output_dir, protein_count, peptides_per_protein, replicates_per_condition, pathway_count, summary_tsv_out, stage_metrics_tsv_out, validation_tsv_out, out_path)

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

COMMANDS = (
    public_benchmark_runner_command,
    build_trust_bundle_command,
    surprising_demo_command,
    scale_demo_command,
    surprising_demo_query_command,
    surprising_demo_report_command,
    public_dataset_comparison_command,
    public_dataset_evidence_cards_command,
    public_case_study_command,
)

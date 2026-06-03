# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Regenerable trust bundle over descriptor-driven public benchmark runs."""

from __future__ import annotations

import csv
from enum import StrEnum
from html import escape
from io import StringIO
from pathlib import Path
from typing import TypeAlias

from pydantic import ConfigDict, Field

from bijux_proteomics._atomic_files import atomic_write_text
from bijux_proteomics._output_tables import write_output_table_tsv
from bijux_proteomics.workflow.pipelines.public_benchmark_runner import (
    PublicBenchmarkRunReport,
    PublicBenchmarkSuiteReport,
    render_public_benchmark_suite_failures_tsv,
    render_public_benchmark_suite_summary_tsv,
    run_public_benchmark_descriptor,
)
from bijux_proteomics.workflow.pipelines.weak_evidence import (
    WeakEvidenceBenchmarkDescriptor,
    WeakEvidenceBenchmarkReport,
    build_flagship_weak_evidence_benchmark_descriptor,
    render_weak_evidence_benchmark_criteria_tsv,
    render_weak_evidence_benchmark_summary_tsv,
    run_weak_evidence_benchmark,
)
from bijux_proteomics.workflow.public_benchmark_descriptors import (
    list_public_benchmark_descriptor_paths,
    load_public_benchmark_descriptor,
    public_benchmark_root,
)
from bijux_proteomics_foundation import JsonModel

TrustBundleDescriptorInput: TypeAlias = Path | WeakEvidenceBenchmarkDescriptor


class TrustBundleArtifactCategory(StrEnum):
    """Stable artifact categories rendered inside the trust bundle."""

    BENCHMARK_RESULTS = "benchmark_results"
    CARDS = "cards"
    COMPARISON_TABLES = "comparison_tables"
    EVIDENCE_GRAPHS = "evidence_graphs"
    QC_FAILURES = "qc_failures"
    REJECTED_EVIDENCE = "rejected_evidence"
    WORKFLOW_OUTPUTS = "workflow_outputs"


class TrustBundleArtifactReference(JsonModel):
    """One bundle-indexed artifact reference."""

    model_config = ConfigDict(extra="forbid")

    dataset_id: str = Field(..., min_length=1)
    category: TrustBundleArtifactCategory
    relative_path: str = Field(..., min_length=1)
    note: str = Field(..., min_length=1)


class TrustBundleRunSummary(JsonModel):
    """One benchmark-run summary inside the trust bundle."""

    model_config = ConfigDict(extra="forbid")

    dataset_id: str = Field(..., min_length=1)
    accession: str = Field(..., min_length=1)
    status: str = Field(..., min_length=1)
    workflow_output_dir: str = Field(..., min_length=1)
    failure_count: int = Field(..., ge=0)
    artifact_count: int = Field(..., ge=0)
    graph_artifact_count: int = Field(..., ge=0)
    rejected_artifact_count: int = Field(..., ge=0)
    qc_artifact_count: int = Field(..., ge=0)
    card_artifact_count: int = Field(..., ge=0)
    comparison_artifact_count: int = Field(..., ge=0)


class TrustBundleReport(JsonModel):
    """Regenerable trust bundle report over public benchmark descriptors."""

    model_config = ConfigDict(extra="forbid")

    benchmark_root: str = Field(..., min_length=1)
    output_dir: str = Field(..., min_length=1)
    suite_report: PublicBenchmarkSuiteReport
    weak_evidence_reports: tuple[WeakEvidenceBenchmarkReport, ...] = Field(
        default_factory=tuple
    )
    descriptor_count: int = Field(..., ge=0)
    handwritten_result_table_count: int = Field(..., ge=0)
    runs: tuple[TrustBundleRunSummary, ...] = Field(default_factory=tuple)
    benchmark_artifacts: tuple[TrustBundleArtifactReference, ...] = Field(
        default_factory=tuple
    )
    evidence_graph_artifacts: tuple[TrustBundleArtifactReference, ...] = Field(
        default_factory=tuple
    )
    rejected_evidence_artifacts: tuple[TrustBundleArtifactReference, ...] = Field(
        default_factory=tuple
    )
    qc_artifacts: tuple[TrustBundleArtifactReference, ...] = Field(
        default_factory=tuple
    )
    card_artifacts: tuple[TrustBundleArtifactReference, ...] = Field(
        default_factory=tuple
    )
    comparison_artifacts: tuple[TrustBundleArtifactReference, ...] = Field(
        default_factory=tuple
    )
    html_index_path: str = Field(..., min_length=1)
    note: str = Field(..., min_length=1)


def build_flagship_trust_bundle_descriptors(
    output_dir: Path,
) -> tuple[TrustBundleDescriptorInput, ...]:
    """Build the shipped trust-bundle descriptor set."""

    public_descriptor_paths = list_public_benchmark_descriptor_paths(
        public_benchmark_root()
    )
    weak_evidence_descriptor = build_flagship_weak_evidence_benchmark_descriptor(
        output_dir
        / TrustBundleArtifactCategory.WORKFLOW_OUTPUTS
        / "flagship_weak_evidence_benchmark"
    )
    return (*public_descriptor_paths, weak_evidence_descriptor)


def build_trust_bundle(
    descriptors: tuple[TrustBundleDescriptorInput, ...],
    out_dir: Path,
) -> TrustBundleReport:
    """Build a regenerable trust bundle from explicit benchmark descriptors."""

    out_dir.mkdir(parents=True, exist_ok=True)
    workflow_output_root = out_dir / TrustBundleArtifactCategory.WORKFLOW_OUTPUTS
    benchmark_result_root = out_dir / TrustBundleArtifactCategory.BENCHMARK_RESULTS
    graph_root = out_dir / TrustBundleArtifactCategory.EVIDENCE_GRAPHS
    rejected_root = out_dir / TrustBundleArtifactCategory.REJECTED_EVIDENCE
    qc_root = out_dir / TrustBundleArtifactCategory.QC_FAILURES
    card_root = out_dir / TrustBundleArtifactCategory.CARDS
    comparison_root = out_dir / TrustBundleArtifactCategory.COMPARISON_TABLES
    for path in (
        workflow_output_root,
        benchmark_result_root,
        graph_root,
        rejected_root,
        qc_root,
        card_root,
        comparison_root,
    ):
        path.mkdir(parents=True, exist_ok=True)

    public_descriptor_paths, weak_evidence_descriptors = (
        _split_trust_bundle_descriptors(
            descriptors,
        )
    )
    suite = _run_public_descriptor_suite(
        public_descriptor_paths,
        output_root=workflow_output_root / "public_benchmark_runs",
    )
    weak_evidence_reports = tuple(
        run_weak_evidence_benchmark(
            descriptor.model_copy(
                update={
                    "output_root": workflow_output_root / descriptor.benchmark_id,
                }
            )
        )
        for descriptor in weak_evidence_descriptors
    )
    benchmark_artifacts = _write_benchmark_result_artifacts(
        suite,
        benchmark_result_root=benchmark_result_root,
        output_dir=out_dir,
    ) + _write_weak_evidence_result_artifacts(
        weak_evidence_reports,
        benchmark_result_root=benchmark_result_root,
        output_dir=out_dir,
    )
    workflow_artifacts = _collect_workflow_artifacts(
        suite.runs,
        weak_evidence_reports=weak_evidence_reports,
        output_dir=out_dir,
    )
    evidence_graph_artifacts = tuple(
        artifact
        for artifact in workflow_artifacts
        if artifact.category is TrustBundleArtifactCategory.EVIDENCE_GRAPHS
    )
    rejected_artifacts = tuple(
        artifact
        for artifact in workflow_artifacts
        if artifact.category is TrustBundleArtifactCategory.REJECTED_EVIDENCE
    )
    qc_artifacts = tuple(
        artifact
        for artifact in workflow_artifacts
        if artifact.category is TrustBundleArtifactCategory.QC_FAILURES
    )
    card_artifacts = tuple(
        artifact
        for artifact in workflow_artifacts
        if artifact.category is TrustBundleArtifactCategory.CARDS
    )
    comparison_artifacts = _write_comparison_artifacts(
        suite,
        benchmark_artifacts=benchmark_artifacts,
        workflow_artifacts=workflow_artifacts,
        comparison_root=comparison_root,
        output_dir=out_dir,
    )
    evidence_graph_artifacts = _write_indexed_category_artifacts(
        graph_root / "index.tsv",
        category=TrustBundleArtifactCategory.EVIDENCE_GRAPHS,
        index_note="indexed evidence graph artifacts across the trust bundle",
        references=evidence_graph_artifacts,
        output_dir=out_dir,
    )
    rejected_artifacts = _write_indexed_category_artifacts(
        rejected_root / "index.tsv",
        category=TrustBundleArtifactCategory.REJECTED_EVIDENCE,
        index_note="indexed rejected evidence artifacts across the trust bundle",
        references=rejected_artifacts,
        output_dir=out_dir,
    )
    qc_artifacts = _write_indexed_category_artifacts(
        qc_root / "index.tsv",
        category=TrustBundleArtifactCategory.QC_FAILURES,
        index_note="indexed QC and quality-warning artifacts across the trust bundle",
        references=qc_artifacts,
        output_dir=out_dir,
    )
    card_artifacts = _write_indexed_category_artifacts(
        card_root / "index.tsv",
        category=TrustBundleArtifactCategory.CARDS,
        index_note="indexed protein and PTM evidence cards across the trust bundle",
        references=card_artifacts,
        output_dir=out_dir,
    )
    handwritten_result_table_count = _count_handwritten_result_table_copies(
        descriptors,
        output_dir=out_dir,
    )
    if handwritten_result_table_count > 0:
        raise ValueError(
            "trust bundle copied one or more shipped source result tables instead of "
            "regenerating outputs from descriptors"
        )

    html_index_path = out_dir / "index.html"
    report = TrustBundleReport(
        benchmark_root=str(public_benchmark_root()),
        output_dir=str(out_dir),
        suite_report=suite,
        weak_evidence_reports=weak_evidence_reports,
        descriptor_count=len(descriptors),
        handwritten_result_table_count=handwritten_result_table_count,
        runs=(
            *(
                _summarize_public_run(
                    run,
                    workflow_artifacts=workflow_artifacts,
                )
                for run in suite.runs
            ),
            *(
                _summarize_weak_evidence_run(
                    report,
                    workflow_artifacts=workflow_artifacts,
                )
                for report in weak_evidence_reports
            ),
        ),
        benchmark_artifacts=benchmark_artifacts,
        evidence_graph_artifacts=evidence_graph_artifacts,
        rejected_evidence_artifacts=rejected_artifacts,
        qc_artifacts=qc_artifacts,
        card_artifacts=card_artifacts,
        comparison_artifacts=comparison_artifacts,
        html_index_path=str(html_index_path),
        note=(
            "trust bundle is regenerated directly from explicit benchmark descriptors, "
            "including the weak-evidence benchmark, and excludes copied handwritten "
            "source result tables"
        ),
    )
    atomic_write_text(
        html_index_path,
        _render_html_index(report, output_dir=out_dir),
    )
    atomic_write_text(
        out_dir / "trust_bundle_manifest.json",
        report.to_stable_json() + "\n",
    )
    return report


def build_public_benchmark_trust_bundle(
    benchmark_root: Path,
    *,
    output_dir: Path,
) -> TrustBundleReport:
    """Build a regenerable trust bundle from the shipped public benchmark root."""

    public_descriptor_paths = list_public_benchmark_descriptor_paths(benchmark_root)
    weak_evidence_descriptor = build_flagship_weak_evidence_benchmark_descriptor(
        output_dir
        / TrustBundleArtifactCategory.WORKFLOW_OUTPUTS
        / "flagship_weak_evidence_benchmark"
    )
    return build_trust_bundle(
        (*public_descriptor_paths, weak_evidence_descriptor),
        output_dir,
    )


def render_trust_bundle_run_summary_tsv(report: TrustBundleReport) -> str:
    """Render one run-summary TSV for trust bundle review."""

    return _dict_rows_to_tsv(
        [
            {
                "dataset_id": run.dataset_id,
                "accession": run.accession,
                "status": run.status,
                "workflow_output_dir": run.workflow_output_dir,
                "failure_count": run.failure_count,
                "artifact_count": run.artifact_count,
                "graph_artifact_count": run.graph_artifact_count,
                "rejected_artifact_count": run.rejected_artifact_count,
                "qc_artifact_count": run.qc_artifact_count,
                "card_artifact_count": run.card_artifact_count,
                "comparison_artifact_count": run.comparison_artifact_count,
            }
            for run in report.runs
        ]
    )


def _write_benchmark_result_artifacts(
    suite: PublicBenchmarkSuiteReport,
    *,
    benchmark_result_root: Path,
    output_dir: Path,
) -> tuple[TrustBundleArtifactReference, ...]:
    summary_path = benchmark_result_root / "summary.tsv"
    failures_path = benchmark_result_root / "failures.tsv"
    source_audit_path = benchmark_result_root / "source_audits.tsv"
    verified_count_path = benchmark_result_root / "verified_counts.tsv"
    suite_json_path = benchmark_result_root / "suite.json"
    run_root = benchmark_result_root / "runs"
    run_root.mkdir(parents=True, exist_ok=True)

    write_output_table_tsv(
        summary_path, render_public_benchmark_suite_summary_tsv(suite)
    )
    write_output_table_tsv(
        failures_path, render_public_benchmark_suite_failures_tsv(suite)
    )
    write_output_table_tsv(source_audit_path, _render_source_audits_tsv(suite))
    write_output_table_tsv(verified_count_path, _render_verified_counts_tsv(suite))
    atomic_write_text(suite_json_path, suite.to_stable_json() + "\n")

    references = [
        TrustBundleArtifactReference(
            dataset_id="suite",
            category=TrustBundleArtifactCategory.BENCHMARK_RESULTS,
            relative_path=str(summary_path.relative_to(output_dir)),
            note="benchmark suite summary over every public descriptor",
        ),
        TrustBundleArtifactReference(
            dataset_id="suite",
            category=TrustBundleArtifactCategory.BENCHMARK_RESULTS,
            relative_path=str(failures_path.relative_to(output_dir)),
            note="explicit benchmark downgrade and failure reasons",
        ),
        TrustBundleArtifactReference(
            dataset_id="suite",
            category=TrustBundleArtifactCategory.BENCHMARK_RESULTS,
            relative_path=str(source_audit_path.relative_to(output_dir)),
            note="source-file presence and checksum audit across the descriptor suite",
        ),
        TrustBundleArtifactReference(
            dataset_id="suite",
            category=TrustBundleArtifactCategory.BENCHMARK_RESULTS,
            relative_path=str(verified_count_path.relative_to(output_dir)),
            note="verified approximate counts emitted by successful workflow runs",
        ),
        TrustBundleArtifactReference(
            dataset_id="suite",
            category=TrustBundleArtifactCategory.BENCHMARK_RESULTS,
            relative_path=str(suite_json_path.relative_to(output_dir)),
            note="machine-readable benchmark suite report",
        ),
    ]
    for run in suite.runs:
        run_json_path = run_root / f"{run.dataset_id}.json"
        atomic_write_text(run_json_path, run.to_stable_json() + "\n")
        references.append(
            TrustBundleArtifactReference(
                dataset_id=run.dataset_id,
                category=TrustBundleArtifactCategory.BENCHMARK_RESULTS,
                relative_path=str(run_json_path.relative_to(output_dir)),
                note="machine-readable benchmark run report",
            )
        )
    return tuple(references)


def _write_weak_evidence_result_artifacts(
    reports: tuple[WeakEvidenceBenchmarkReport, ...],
    *,
    benchmark_result_root: Path,
    output_dir: Path,
) -> tuple[TrustBundleArtifactReference, ...]:
    weak_root = benchmark_result_root / "weak_evidence"
    weak_root.mkdir(parents=True, exist_ok=True)
    references: list[TrustBundleArtifactReference] = []
    for report in reports:
        benchmark_dir = weak_root / report.benchmark_id
        benchmark_dir.mkdir(parents=True, exist_ok=True)
        summary_path = benchmark_dir / "summary.tsv"
        criteria_path = benchmark_dir / "criteria.tsv"
        report_path = benchmark_dir / "report.json"
        write_output_table_tsv(
            summary_path, render_weak_evidence_benchmark_summary_tsv(report)
        )
        write_output_table_tsv(
            criteria_path, render_weak_evidence_benchmark_criteria_tsv(report)
        )
        atomic_write_text(report_path, report.to_stable_json() + "\n")
        references.extend(
            (
                TrustBundleArtifactReference(
                    dataset_id=report.benchmark_id,
                    category=TrustBundleArtifactCategory.BENCHMARK_RESULTS,
                    relative_path=str(summary_path.relative_to(output_dir)),
                    note="generated weak-evidence benchmark summary",
                ),
                TrustBundleArtifactReference(
                    dataset_id=report.benchmark_id,
                    category=TrustBundleArtifactCategory.BENCHMARK_RESULTS,
                    relative_path=str(criteria_path.relative_to(output_dir)),
                    note="generated weak-evidence benchmark criteria ledger",
                ),
                TrustBundleArtifactReference(
                    dataset_id=report.benchmark_id,
                    category=TrustBundleArtifactCategory.BENCHMARK_RESULTS,
                    relative_path=str(report_path.relative_to(output_dir)),
                    note="machine-readable weak-evidence benchmark report",
                ),
            )
        )
    return tuple(references)


def _collect_workflow_artifacts(
    runs: tuple[PublicBenchmarkRunReport, ...],
    *,
    weak_evidence_reports: tuple[WeakEvidenceBenchmarkReport, ...],
    output_dir: Path,
) -> tuple[TrustBundleArtifactReference, ...]:
    references: list[TrustBundleArtifactReference] = []
    for run in runs:
        references.extend(
            _collect_directory_artifacts(
                dataset_id=run.dataset_id,
                root_dir=Path(run.output_dir),
                output_dir=output_dir,
            )
        )
    for report in weak_evidence_reports:
        benchmark_root = _weak_evidence_output_root(report)
        references.extend(
            _collect_directory_artifacts(
                dataset_id=report.benchmark_id,
                root_dir=benchmark_root,
                output_dir=output_dir,
            )
        )
    return tuple(references)


def _collect_directory_artifacts(
    *,
    dataset_id: str,
    root_dir: Path,
    output_dir: Path,
) -> tuple[TrustBundleArtifactReference, ...]:
    if not root_dir.exists():
        return ()
    references: list[TrustBundleArtifactReference] = []
    for path in sorted(root_dir.rglob("*")):
        if not path.is_file():
            continue
        category = _classify_workflow_artifact(path.name)
        if category is None:
            continue
        references.append(
            TrustBundleArtifactReference(
                dataset_id=dataset_id,
                category=category,
                relative_path=str(path.relative_to(output_dir)),
                note=f"generated {category.value.replace('_', ' ')} artifact",
            )
        )
    return tuple(references)


def _write_comparison_artifacts(
    suite: PublicBenchmarkSuiteReport,
    *,
    benchmark_artifacts: tuple[TrustBundleArtifactReference, ...],
    workflow_artifacts: tuple[TrustBundleArtifactReference, ...],
    comparison_root: Path,
    output_dir: Path,
) -> tuple[TrustBundleArtifactReference, ...]:
    comparison_index_path = comparison_root / "index.tsv"
    references = [
        artifact
        for artifact in benchmark_artifacts
        if artifact.relative_path.endswith("summary.tsv")
        or artifact.relative_path.endswith("failures.tsv")
        or artifact.relative_path.endswith("source_audits.tsv")
        or artifact.relative_path.endswith("verified_counts.tsv")
    ]
    references.extend(
        artifact
        for artifact in workflow_artifacts
        if artifact.category is TrustBundleArtifactCategory.COMPARISON_TABLES
    )
    _write_category_index(
        comparison_index_path, tuple(references), output_dir=output_dir
    )
    references.append(
        TrustBundleArtifactReference(
            dataset_id="suite",
            category=TrustBundleArtifactCategory.COMPARISON_TABLES,
            relative_path=str(comparison_index_path.relative_to(output_dir)),
            note="indexed comparison and benchmark verification tables across the trust bundle",
        )
    )
    return tuple(references)


def _write_category_index(
    path: Path,
    references: tuple[TrustBundleArtifactReference, ...],
    *,
    output_dir: Path,
) -> None:
    rows: list[dict[str, object]] = [
        {
            "dataset_id": artifact.dataset_id,
            "category": artifact.category.value,
            "relative_path": artifact.relative_path,
            "note": artifact.note,
        }
        for artifact in references
    ]
    write_output_table_tsv(path, _dict_rows_to_tsv(rows))


def _write_indexed_category_artifacts(
    path: Path,
    *,
    category: TrustBundleArtifactCategory,
    index_note: str,
    references: tuple[TrustBundleArtifactReference, ...],
    output_dir: Path,
) -> tuple[TrustBundleArtifactReference, ...]:
    _write_category_index(path, references, output_dir=output_dir)
    return references + (
        TrustBundleArtifactReference(
            dataset_id="suite",
            category=category,
            relative_path=str(path.relative_to(output_dir)),
            note=index_note,
        ),
    )


def _classify_workflow_artifact(filename: str) -> TrustBundleArtifactCategory | None:
    name = filename.lower()
    if "rejected" in name:
        return TrustBundleArtifactCategory.REJECTED_EVIDENCE
    if "graph" in name:
        return TrustBundleArtifactCategory.EVIDENCE_GRAPHS
    if "card" in name:
        return TrustBundleArtifactCategory.CARDS
    if any(
        token in name for token in ("comparison", "correlation", "overlap", "conflict")
    ):
        return TrustBundleArtifactCategory.COMPARISON_TABLES
    if "qc" in name or "quality" in name:
        return TrustBundleArtifactCategory.QC_FAILURES
    return None


def _summarize_public_run(
    run: PublicBenchmarkRunReport,
    *,
    workflow_artifacts: tuple[TrustBundleArtifactReference, ...],
) -> TrustBundleRunSummary:
    run_artifacts = tuple(
        artifact
        for artifact in workflow_artifacts
        if artifact.dataset_id == run.dataset_id
    )
    return TrustBundleRunSummary(
        dataset_id=run.dataset_id,
        accession=run.accession,
        status=run.status,
        workflow_output_dir=run.output_dir,
        failure_count=len(run.failures),
        artifact_count=len(run_artifacts),
        graph_artifact_count=sum(
            artifact.category is TrustBundleArtifactCategory.EVIDENCE_GRAPHS
            for artifact in run_artifacts
        ),
        rejected_artifact_count=sum(
            artifact.category is TrustBundleArtifactCategory.REJECTED_EVIDENCE
            for artifact in run_artifacts
        ),
        qc_artifact_count=sum(
            artifact.category is TrustBundleArtifactCategory.QC_FAILURES
            for artifact in run_artifacts
        ),
        card_artifact_count=sum(
            artifact.category is TrustBundleArtifactCategory.CARDS
            for artifact in run_artifacts
        ),
        comparison_artifact_count=sum(
            artifact.category is TrustBundleArtifactCategory.COMPARISON_TABLES
            for artifact in run_artifacts
        ),
    )


def _summarize_weak_evidence_run(
    report: WeakEvidenceBenchmarkReport,
    *,
    workflow_artifacts: tuple[TrustBundleArtifactReference, ...],
) -> TrustBundleRunSummary:
    run_artifacts = tuple(
        artifact
        for artifact in workflow_artifacts
        if artifact.dataset_id == report.benchmark_id
    )
    return TrustBundleRunSummary(
        dataset_id=report.benchmark_id,
        accession=f"benchmark:{report.benchmark_id}",
        status=report.summary.status.value,
        workflow_output_dir=str(_weak_evidence_output_root(report)),
        failure_count=report.summary.missing_required_criterion_count,
        artifact_count=len(run_artifacts),
        graph_artifact_count=sum(
            artifact.category is TrustBundleArtifactCategory.EVIDENCE_GRAPHS
            for artifact in run_artifacts
        ),
        rejected_artifact_count=sum(
            artifact.category is TrustBundleArtifactCategory.REJECTED_EVIDENCE
            for artifact in run_artifacts
        ),
        qc_artifact_count=sum(
            artifact.category is TrustBundleArtifactCategory.QC_FAILURES
            for artifact in run_artifacts
        ),
        card_artifact_count=sum(
            artifact.category is TrustBundleArtifactCategory.CARDS
            for artifact in run_artifacts
        ),
        comparison_artifact_count=sum(
            artifact.category is TrustBundleArtifactCategory.COMPARISON_TABLES
            for artifact in run_artifacts
        ),
    )


def _run_public_descriptor_suite(
    descriptor_paths: tuple[Path, ...],
    *,
    output_root: Path,
) -> PublicBenchmarkSuiteReport:
    runs = tuple(
        run_public_benchmark_descriptor(descriptor_path, output_root=output_root)
        for descriptor_path in descriptor_paths
    )
    return PublicBenchmarkSuiteReport(
        benchmark_root=str(public_benchmark_root()),
        output_root=str(output_root),
        runs=runs,
        passed_count=sum(run.status == "passed" for run in runs),
        failed_count=sum(run.status == "failed" for run in runs),
        note=(
            "descriptor suite records which explicit public benchmark descriptors are "
            "currently runnable and which still fail under owned workflow execution"
        ),
    )


def _split_trust_bundle_descriptors(
    descriptors: tuple[TrustBundleDescriptorInput, ...],
) -> tuple[tuple[Path, ...], tuple[WeakEvidenceBenchmarkDescriptor, ...]]:
    public_descriptor_paths: list[Path] = []
    weak_evidence_descriptors: list[WeakEvidenceBenchmarkDescriptor] = []
    for descriptor in descriptors:
        if isinstance(descriptor, Path):
            public_descriptor_paths.append(descriptor)
            continue
        weak_evidence_descriptors.append(descriptor)
    return tuple(public_descriptor_paths), tuple(weak_evidence_descriptors)


def _weak_evidence_output_root(report: WeakEvidenceBenchmarkReport) -> Path:
    return report.output_root


def _count_handwritten_result_table_copies(
    descriptors: tuple[TrustBundleDescriptorInput, ...],
    *,
    output_dir: Path,
) -> int:
    source_basenames = _descriptor_source_basenames(descriptors)
    return sum(
        1
        for path in output_dir.rglob("*")
        if path.is_file() and path.name in source_basenames
    )


def _descriptor_source_basenames(
    descriptors: tuple[TrustBundleDescriptorInput, ...],
) -> set[str]:
    basenames: set[str] = set()
    for descriptor in descriptors:
        if isinstance(descriptor, Path):
            public_descriptor = load_public_benchmark_descriptor(descriptor)
            basenames.update(
                Path(source.repo_relative_path).name
                for source in public_descriptor.source_files
            )
            continue
        for path in (
            descriptor.lfq_sparse_descriptor_path,
            descriptor.ptm_descriptor_path,
            descriptor.tmt_result_tsv_path,
            descriptor.tmt_design_tsv_path,
        ):
            if path is not None:
                basenames.add(Path(path).name)
    return basenames


def _render_source_audits_tsv(suite: PublicBenchmarkSuiteReport) -> str:
    rows: list[dict[str, object]] = [
        {
            "dataset_id": run.dataset_id,
            "accession": run.accession,
            "source_id": audit.source_id,
            "schema_id": audit.schema_id,
            "repo_relative_path": audit.repo_relative_path,
            "exists": audit.exists,
            "checksum_matched": audit.checksum_matched,
            "observed_sha256": audit.observed_sha256,
        }
        for run in suite.runs
        for audit in run.source_audits
    ]
    return _dict_rows_to_tsv(rows)


def _render_verified_counts_tsv(suite: PublicBenchmarkSuiteReport) -> str:
    rows: list[dict[str, object]] = [
        {
            "dataset_id": run.dataset_id,
            "accession": run.accession,
            "metric_id": metric_id,
            "observed_value": observed_value,
        }
        for run in suite.runs
        for metric_id, observed_value in sorted(run.verified_counts.items())
    ]
    return _dict_rows_to_tsv(rows)


def _render_html_index(report: TrustBundleReport, *, output_dir: Path) -> str:
    run_rows = "\n".join(
        (
            "<tr>"
            f"<td>{escape(run.dataset_id)}</td>"
            f"<td>{escape(run.accession)}</td>"
            f"<td>{escape(run.status)}</td>"
            f"<td>{run.failure_count}</td>"
            f'<td><a href="{escape(Path(run.workflow_output_dir).relative_to(output_dir).as_posix())}/">workflow outputs</a></td>'
            "</tr>"
        )
        for run in report.runs
    )
    artifact_sections = "\n".join(
        _render_html_artifact_section(title, artifacts)
        for title, artifacts in (
            ("Benchmark Results", report.benchmark_artifacts),
            ("Evidence Graphs", report.evidence_graph_artifacts),
            ("Rejected Evidence", report.rejected_evidence_artifacts),
            ("QC Failures", report.qc_artifacts),
            ("Protein And PTM Cards", report.card_artifacts),
            ("Comparison Tables", report.comparison_artifacts),
        )
    )
    return (
        "<!DOCTYPE html>\n"
        '<html lang="en">\n'
        "<head>\n"
        '  <meta charset="utf-8" />\n'
        "  <title>Bijux Proteomics Trust Bundle</title>\n"
        "  <style>"
        "body{font-family:ui-sans-serif,system-ui,sans-serif;margin:2rem;line-height:1.5;}"
        "table{border-collapse:collapse;width:100%;margin:1rem 0;}"
        "th,td{border:1px solid #d0d7de;padding:0.5rem;text-align:left;vertical-align:top;}"
        "code{background:#f6f8fa;padding:0.1rem 0.3rem;border-radius:0.25rem;}"
        "</style>\n"
        "</head>\n"
        "<body>\n"
        "  <h1>Proteomics Trust Bundle</h1>\n"
        f"  <p>{escape(report.note)}</p>\n"
        "  <ul>\n"
        f"    <li>benchmark root: <code>{escape(report.benchmark_root)}</code></li>\n"
        f"    <li>passed benchmarks: {report.suite_report.passed_count}</li>\n"
        f"    <li>failed benchmarks: {report.suite_report.failed_count}</li>\n"
        "  </ul>\n"
        "  <h2>Benchmark Runs</h2>\n"
        "  <table>\n"
        "    <thead><tr><th>dataset</th><th>accession</th><th>status</th><th>failures</th><th>outputs</th></tr></thead>\n"
        f"    <tbody>{run_rows}</tbody>\n"
        "  </table>\n"
        f"{artifact_sections}\n"
        "</body>\n"
        "</html>\n"
    )


def _render_html_artifact_section(
    title: str,
    artifacts: tuple[TrustBundleArtifactReference, ...],
) -> str:
    rows = "\n".join(
        (
            "<tr>"
            f"<td>{escape(artifact.dataset_id)}</td>"
            f'<td><a href="{escape(artifact.relative_path)}">{escape(artifact.relative_path)}</a></td>'
            f"<td>{escape(artifact.note)}</td>"
            "</tr>"
        )
        for artifact in artifacts
    )
    return (
        f"  <h2>{escape(title)}</h2>\n"
        "  <table>\n"
        "    <thead><tr><th>dataset</th><th>artifact</th><th>note</th></tr></thead>\n"
        f"    <tbody>{rows}</tbody>\n"
        "  </table>\n"
    )


def _dict_rows_to_tsv(rows: list[dict[str, object]]) -> str:
    if not rows:
        return ""
    fieldnames = list(rows[0].keys())
    handle = StringIO()
    writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t")
    writer.writeheader()
    writer.writerows(rows)
    return handle.getvalue()

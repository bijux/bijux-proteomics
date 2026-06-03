# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Public-dataset comparison runner over descriptor-driven workflow executions."""

from __future__ import annotations

import csv
from enum import StrEnum
from io import StringIO
from pathlib import Path

from pydantic import ConfigDict, Field

from bijux_proteomics._output_tables import write_output_table_tsv
from bijux_proteomics.workflow.cross_study_effect_comparison import (
    CrossStudyProteinEffectComparisonReport,
    CrossStudyProteinStudyInput,
    build_cross_study_effect_comparison_report,
    render_cross_study_effect_comparison_tsv,
)
from bijux_proteomics.workflow.cross_study_meta_analysis import (
    CrossStudyMetaAnalysisReport,
    build_cross_study_meta_analysis_report,
    render_cross_study_meta_analysis_tsv,
)
from bijux_proteomics.workflow.cross_study_pathway_comparison import (
    CrossStudyPathwayComparisonReport,
    build_cross_study_pathway_comparison_report,
    render_cross_study_pathway_comparison_tsv,
)
from bijux_proteomics.workflow.pipelines.advanced_diann import (
    AdvancedDiannWorkflowReport,
)
from bijux_proteomics.workflow.pipelines.advanced_fragpipe import (
    AdvancedFragpipeWorkflowReport,
)
from bijux_proteomics.workflow.pipelines.advanced_maxquant import (
    AdvancedMaxquantWorkflowReport,
)
from bijux_proteomics.workflow.pipelines.advanced_ptm import AdvancedPtmWorkflowReport
from bijux_proteomics.workflow.pipelines.advanced_targeted import (
    TargetedValidationWorkflowReport,
)
from bijux_proteomics.workflow.pipelines.advanced_tmt import AdvancedTmtWorkflowReport
from bijux_proteomics.workflow.pipelines.dda_biological_workflow import (
    DdaBiologicalWorkflowBundle,
)
from bijux_proteomics.workflow.pipelines.diann_biological_workflow import (
    DiannBiologicalWorkflowBundle,
)
from bijux_proteomics.workflow.pipelines.flagship_run import ProteomicsRunBundle
from bijux_proteomics.workflow.pipelines.maxquant_biological_workflow import (
    MaxquantBiologicalWorkflowBundle,
)
from bijux_proteomics.workflow.pipelines.ptm_site_workflow import PtmSiteWorkflowBundle
from bijux_proteomics.workflow.pipelines.public_benchmark_runner import (
    PublicBenchmarkRunReport,
    PublicBenchmarkRunStatus,
    PublicBenchmarkSuiteReport,
    load_public_benchmark_descriptor,
    run_public_benchmark_descriptor_suite,
)
from bijux_proteomics.workflow.pipelines.tmt_experiment_workflow import (
    TmtExperimentWorkflowBundle,
)
from bijux_proteomics.workflow.reports.biological_reporting import (
    BiologicalResultReportBundle,
)
from bijux_proteomics.workflow.study_result import (
    ProteomicsStudyCardKind,
    ProteomicsStudyKind,
    ProteomicsStudyResult,
    build_proteomics_study_result,
)
from bijux_proteomics_foundation import JsonModel


class PublicDatasetComparisonDatasetStatus(StrEnum):
    """Stable status for one dataset included in a public comparison run."""

    PASSED = "passed"
    FAILED = "failed"


class PublicDatasetComparisonDatasetSummary(JsonModel):
    """One per-dataset biological summary in the public comparison runner."""

    model_config = ConfigDict(extra="forbid")

    dataset_id: str = Field(..., min_length=1)
    accession: str = Field(..., min_length=1)
    species: str = Field(..., min_length=1)
    search_engine: str = Field(..., min_length=1)
    condition_a: str = Field(..., min_length=1)
    condition_b: str = Field(..., min_length=1)
    status: PublicDatasetComparisonDatasetStatus
    failure_count: int = Field(..., ge=0)
    study_kind: ProteomicsStudyKind | None = None
    design_entry_count: int | None = Field(default=None, ge=0)
    significant_entity_count: int | None = Field(default=None, ge=0)
    protein_card_count: int | None = Field(default=None, ge=0)
    conclusion_count: int | None = Field(default=None, ge=0)
    effect_comparison_supported: bool = False
    pathway_comparison_supported: bool = False
    note: str = Field(..., min_length=1)


class PublicDatasetComparisonFailureEntry(JsonModel):
    """One exact failed-dataset reason preserved by the comparison runner."""

    model_config = ConfigDict(extra="forbid")

    dataset_id: str = Field(..., min_length=1)
    accession: str = Field(..., min_length=1)
    search_engine: str = Field(..., min_length=1)
    failure_kind: str = Field(..., min_length=1)
    subject: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)


class PublicDatasetComparisonSummary(JsonModel):
    """Summary over one public-dataset comparison run."""

    model_config = ConfigDict(extra="forbid")

    descriptor_count: int = Field(..., ge=0)
    passed_dataset_count: int = Field(..., ge=0)
    failed_dataset_count: int = Field(..., ge=0)
    failure_entry_count: int = Field(..., ge=0)
    successful_study_count: int = Field(..., ge=0)
    effect_support_study_count: int = Field(..., ge=0)
    pathway_support_study_count: int = Field(..., ge=0)
    combined_effect_group_count: int = Field(..., ge=0)
    replicated_effect_group_count: int = Field(..., ge=0)
    meta_analysis_entry_count: int = Field(..., ge=0)
    combined_pathway_comparison_count: int = Field(..., ge=0)
    shared_pathway_signal_count: int = Field(..., ge=0)


class PublicDatasetComparisonReport(JsonModel):
    """Owned report over one multi-dataset biological comparison question."""

    model_config = ConfigDict(extra="forbid")

    benchmark_root: str = Field(..., min_length=1)
    run_output_root: str = Field(..., min_length=1)
    suite_report: PublicBenchmarkSuiteReport
    dataset_summaries: tuple[PublicDatasetComparisonDatasetSummary, ...] = Field(
        default_factory=tuple
    )
    failure_entries: tuple[PublicDatasetComparisonFailureEntry, ...] = Field(
        default_factory=tuple
    )
    effect_comparison_report: CrossStudyProteinEffectComparisonReport | None = None
    meta_analysis_report: CrossStudyMetaAnalysisReport | None = None
    pathway_comparison_report: CrossStudyPathwayComparisonReport | None = None
    summary: PublicDatasetComparisonSummary
    note: str = Field(..., min_length=1)


def build_public_dataset_comparison_report(
    benchmark_root: Path,
    *,
    run_output_root: Path,
) -> PublicDatasetComparisonReport:
    """Run a public descriptor root and compare the successful biological outputs."""

    suite_report = run_public_benchmark_descriptor_suite(
        benchmark_root,
        output_root=run_output_root,
    )
    return build_public_dataset_comparison_report_from_suite(
        suite_report,
        benchmark_root=benchmark_root,
    )


def build_public_dataset_comparison_report_from_suite(
    suite_report: PublicBenchmarkSuiteReport,
    *,
    benchmark_root: Path | None = None,
) -> PublicDatasetComparisonReport:
    """Compare the successful outputs from one executed public benchmark suite."""

    failure_entries: list[PublicDatasetComparisonFailureEntry] = []
    successful_dataset_contexts: list[
        tuple[PublicBenchmarkRunReport, str, str, str, ProteomicsStudyResult]
    ] = []
    passed_dataset_without_study_contexts: list[
        tuple[PublicBenchmarkRunReport, str, str, str, str]
    ] = []
    failed_dataset_contexts: list[tuple[PublicBenchmarkRunReport, str, str, str]] = []
    successful_studies: list[CrossStudyProteinStudyInput] = []

    for run in suite_report.runs:
        descriptor = load_public_benchmark_descriptor(Path(run.descriptor_path))
        if run.status == PublicBenchmarkRunStatus.FAILED:
            failed_dataset_contexts.append(
                (
                    run,
                    descriptor.species,
                    descriptor.contrast.condition_a,
                    descriptor.contrast.condition_b,
                )
            )
            failure_entries.extend(
                PublicDatasetComparisonFailureEntry(
                    dataset_id=run.dataset_id,
                    accession=run.accession,
                    search_engine=run.search_engine,
                    failure_kind=failure.kind,
                    subject=failure.subject,
                    message=failure.message,
                )
                for failure in run.failures
            )
            continue

        if run.workflow_result is None:
            raise ValueError(
                f"public benchmark run '{run.dataset_id}' passed without a workflow result"
            )
        try:
            workflow_report = run.workflow_result.report
            if not isinstance(
                workflow_report,
                (
                    AdvancedDiannWorkflowReport,
                    AdvancedFragpipeWorkflowReport,
                    AdvancedMaxquantWorkflowReport,
                    AdvancedPtmWorkflowReport,
                    AdvancedTmtWorkflowReport,
                    BiologicalResultReportBundle,
                    DdaBiologicalWorkflowBundle,
                    DiannBiologicalWorkflowBundle,
                    MaxquantBiologicalWorkflowBundle,
                    ProteomicsRunBundle,
                    PtmSiteWorkflowBundle,
                    TargetedValidationWorkflowReport,
                    TmtExperimentWorkflowBundle,
                ),
            ):
                raise TypeError(
                    "workflow result does not preserve a study-result-supported report surface"
                )
            study_result = build_proteomics_study_result(workflow_report)
        except (TypeError, ValueError) as exc:
            passed_dataset_without_study_contexts.append(
                (
                    run,
                    descriptor.species,
                    descriptor.contrast.condition_a,
                    descriptor.contrast.condition_b,
                    str(exc),
                )
            )
            continue
        successful_dataset_contexts.append(
            (
                run,
                descriptor.species,
                descriptor.contrast.condition_a,
                descriptor.contrast.condition_b,
                study_result,
            )
        )
        successful_studies.append(
            CrossStudyProteinStudyInput(
                study_id=run.dataset_id,
                study_label=run.accession,
                species=descriptor.species,
                study_result=study_result,
            )
        )

    effect_comparison_report = (
        build_cross_study_effect_comparison_report(tuple(successful_studies))
        if successful_studies
        else None
    )
    meta_analysis_report = (
        build_cross_study_meta_analysis_report(tuple(successful_studies))
        if successful_studies
        else None
    )
    pathway_comparison_report = (
        build_cross_study_pathway_comparison_report(tuple(successful_studies))
        if successful_studies
        else None
    )
    effect_unsupported_ids = (
        set()
        if effect_comparison_report is None
        else {entry.study_id for entry in effect_comparison_report.unsupported_studies}
    )
    pathway_unsupported_ids = (
        set()
        if pathway_comparison_report is None
        else {entry.study_id for entry in pathway_comparison_report.unsupported_studies}
    )
    dataset_summaries = [
        PublicDatasetComparisonDatasetSummary(
            dataset_id=run.dataset_id,
            accession=run.accession,
            species=descriptor_species,
            search_engine=run.search_engine,
            condition_a=condition_a,
            condition_b=condition_b,
            status=PublicDatasetComparisonDatasetStatus.PASSED,
            failure_count=0,
            study_kind=study_result.study_kind,
            design_entry_count=study_result.summary.design_entry_count,
            significant_entity_count=sum(
                surface.significant_entity_count
                for surface in study_result.statistic_surfaces
            ),
            protein_card_count=sum(
                surface.card_count
                for surface in study_result.card_surfaces
                if surface.kind is ProteomicsStudyCardKind.PROTEIN_EVIDENCE
            ),
            conclusion_count=study_result.summary.conclusion_count,
            effect_comparison_supported=run.dataset_id not in effect_unsupported_ids,
            pathway_comparison_supported=run.dataset_id not in pathway_unsupported_ids,
            note=run.note,
        )
        for run, descriptor_species, condition_a, condition_b, study_result in successful_dataset_contexts
    ]
    dataset_summaries.extend(
        PublicDatasetComparisonDatasetSummary(
            dataset_id=run.dataset_id,
            accession=run.accession,
            species=descriptor_species,
            search_engine=run.search_engine,
            condition_a=condition_a,
            condition_b=condition_b,
            status=PublicDatasetComparisonDatasetStatus.PASSED,
            failure_count=0,
            effect_comparison_supported=False,
            pathway_comparison_supported=False,
            note=(
                f"{run.note} Cross-study comparison skipped because the passed "
                f"workflow output does not normalize into a proteomics study result: "
                f"{reason}"
            ),
        )
        for run, descriptor_species, condition_a, condition_b, reason in passed_dataset_without_study_contexts
    )
    dataset_summaries.extend(
        PublicDatasetComparisonDatasetSummary(
            dataset_id=run.dataset_id,
            accession=run.accession,
            species=descriptor_species,
            search_engine=run.search_engine,
            condition_a=condition_a,
            condition_b=condition_b,
            status=PublicDatasetComparisonDatasetStatus.FAILED,
            failure_count=len(run.failures),
            note=run.note,
        )
        for run, descriptor_species, condition_a, condition_b in failed_dataset_contexts
    )
    resolved_benchmark_root = (
        Path(suite_report.benchmark_root) if benchmark_root is None else benchmark_root
    )
    ordered_dataset_summaries = tuple(
        sorted(
            dataset_summaries,
            key=lambda entry: (entry.status.value, entry.dataset_id),
        )
    )
    ordered_failures = tuple(
        sorted(
            failure_entries,
            key=lambda entry: (entry.dataset_id, entry.failure_kind, entry.subject),
        )
    )
    summary = PublicDatasetComparisonSummary(
        descriptor_count=len(suite_report.runs),
        passed_dataset_count=suite_report.passed_count,
        failed_dataset_count=suite_report.failed_count,
        failure_entry_count=len(ordered_failures),
        successful_study_count=len(successful_dataset_contexts),
        effect_support_study_count=(
            0
            if effect_comparison_report is None
            else effect_comparison_report.summary.supported_study_count
        ),
        pathway_support_study_count=(
            0
            if pathway_comparison_report is None
            else pathway_comparison_report.summary.supported_study_count
        ),
        combined_effect_group_count=(
            0
            if effect_comparison_report is None
            else effect_comparison_report.summary.harmonized_group_count
        ),
        replicated_effect_group_count=(
            0
            if effect_comparison_report is None
            else effect_comparison_report.summary.replicated_hit_count
        ),
        meta_analysis_entry_count=(
            0
            if meta_analysis_report is None
            else meta_analysis_report.summary.combined_entry_count
        ),
        combined_pathway_comparison_count=(
            0
            if pathway_comparison_report is None
            else pathway_comparison_report.summary.comparison_count
        ),
        shared_pathway_signal_count=(
            0
            if pathway_comparison_report is None
            else pathway_comparison_report.summary.shared_signal_count
        ),
    )
    return PublicDatasetComparisonReport(
        benchmark_root=str(resolved_benchmark_root),
        run_output_root=suite_report.output_root,
        suite_report=suite_report,
        dataset_summaries=ordered_dataset_summaries,
        failure_entries=ordered_failures,
        effect_comparison_report=effect_comparison_report,
        meta_analysis_report=meta_analysis_report,
        pathway_comparison_report=pathway_comparison_report,
        summary=summary,
        note=(
            "public dataset comparison runs the same declared biological question "
            "across descriptor-backed public datasets, preserves exact per-dataset "
            "failures, and then compares only the successful owned study-result surfaces"
        ),
    )


def render_public_dataset_dataset_summary_tsv(
    report: PublicDatasetComparisonReport,
) -> str:
    """Render one per-dataset summary ledger as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "dataset_id",
            "accession",
            "species",
            "search_engine",
            "condition_a",
            "condition_b",
            "status",
            "failure_count",
            "study_kind",
            "design_entry_count",
            "significant_entity_count",
            "protein_card_count",
            "conclusion_count",
            "effect_comparison_supported",
            "pathway_comparison_supported",
            "note",
        ]
    )
    for entry in report.dataset_summaries:
        writer.writerow(
            [
                entry.dataset_id,
                entry.accession,
                entry.species,
                entry.search_engine,
                entry.condition_a,
                entry.condition_b,
                entry.status.value,
                entry.failure_count,
                "" if entry.study_kind is None else entry.study_kind.value,
                _format_int(entry.design_entry_count),
                _format_int(entry.significant_entity_count),
                _format_int(entry.protein_card_count),
                _format_int(entry.conclusion_count),
                str(entry.effect_comparison_supported).lower(),
                str(entry.pathway_comparison_supported).lower(),
                entry.note,
            ]
        )
    return buffer.getvalue()


def render_public_dataset_failure_tsv(report: PublicDatasetComparisonReport) -> str:
    """Render exact failed-dataset reasons as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "dataset_id",
            "accession",
            "search_engine",
            "failure_kind",
            "subject",
            "message",
        ]
    )
    for entry in report.failure_entries:
        writer.writerow(
            [
                entry.dataset_id,
                entry.accession,
                entry.search_engine,
                entry.failure_kind,
                entry.subject,
                entry.message,
            ]
        )
    return buffer.getvalue()


def render_public_dataset_combined_summary_tsv(
    report: PublicDatasetComparisonReport,
) -> str:
    """Render one-row combined public-dataset summary as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "descriptor_count",
            "passed_dataset_count",
            "failed_dataset_count",
            "failure_entry_count",
            "successful_study_count",
            "effect_support_study_count",
            "pathway_support_study_count",
            "combined_effect_group_count",
            "replicated_effect_group_count",
            "meta_analysis_entry_count",
            "combined_pathway_comparison_count",
            "shared_pathway_signal_count",
        ]
    )
    writer.writerow(
        [
            report.summary.descriptor_count,
            report.summary.passed_dataset_count,
            report.summary.failed_dataset_count,
            report.summary.failure_entry_count,
            report.summary.successful_study_count,
            report.summary.effect_support_study_count,
            report.summary.pathway_support_study_count,
            report.summary.combined_effect_group_count,
            report.summary.replicated_effect_group_count,
            report.summary.meta_analysis_entry_count,
            report.summary.combined_pathway_comparison_count,
            report.summary.shared_pathway_signal_count,
        ]
    )
    return buffer.getvalue()


def render_public_dataset_effect_comparison_tsv(
    report: PublicDatasetComparisonReport,
) -> str:
    """Render the combined cross-study effect comparison as TSV."""

    if report.effect_comparison_report is None:
        return ""
    return render_cross_study_effect_comparison_tsv(report.effect_comparison_report)


def render_public_dataset_meta_analysis_tsv(
    report: PublicDatasetComparisonReport,
) -> str:
    """Render the combined cross-study meta-analysis as TSV."""

    if report.meta_analysis_report is None:
        return ""
    return render_cross_study_meta_analysis_tsv(report.meta_analysis_report)


def render_public_dataset_pathway_comparison_tsv(
    report: PublicDatasetComparisonReport,
) -> str:
    """Render the combined cross-study pathway comparison as TSV."""

    if report.pathway_comparison_report is None:
        return ""
    return render_cross_study_pathway_comparison_tsv(report.pathway_comparison_report)


def export_public_dataset_dataset_summary_tsv(
    report: PublicDatasetComparisonReport,
    path: Path,
) -> None:
    """Write per-dataset summaries to TSV."""

    write_output_table_tsv(path, render_public_dataset_dataset_summary_tsv(report))


def export_public_dataset_failure_tsv(
    report: PublicDatasetComparisonReport,
    path: Path,
) -> None:
    """Write exact failed-dataset reasons to TSV."""

    write_output_table_tsv(path, render_public_dataset_failure_tsv(report))


def export_public_dataset_combined_summary_tsv(
    report: PublicDatasetComparisonReport,
    path: Path,
) -> None:
    """Write the combined public-dataset summary to TSV."""

    write_output_table_tsv(path, render_public_dataset_combined_summary_tsv(report))


def export_public_dataset_effect_comparison_tsv(
    report: PublicDatasetComparisonReport,
    path: Path,
) -> None:
    """Write the combined cross-study effect comparison to TSV."""

    write_output_table_tsv(path, render_public_dataset_effect_comparison_tsv(report))


def export_public_dataset_meta_analysis_tsv(
    report: PublicDatasetComparisonReport,
    path: Path,
) -> None:
    """Write the combined cross-study meta-analysis to TSV."""

    write_output_table_tsv(path, render_public_dataset_meta_analysis_tsv(report))


def export_public_dataset_pathway_comparison_tsv(
    report: PublicDatasetComparisonReport,
    path: Path,
) -> None:
    """Write the combined cross-study pathway comparison to TSV."""

    write_output_table_tsv(path, render_public_dataset_pathway_comparison_tsv(report))


def _format_int(value: int | None) -> str:
    return "" if value is None else str(value)


__all__ = [
    "PublicDatasetComparisonDatasetStatus",
    "PublicDatasetComparisonDatasetSummary",
    "PublicDatasetComparisonFailureEntry",
    "PublicDatasetComparisonReport",
    "PublicDatasetComparisonSummary",
    "build_public_dataset_comparison_report",
    "build_public_dataset_comparison_report_from_suite",
    "export_public_dataset_combined_summary_tsv",
    "export_public_dataset_dataset_summary_tsv",
    "export_public_dataset_effect_comparison_tsv",
    "export_public_dataset_failure_tsv",
    "export_public_dataset_meta_analysis_tsv",
    "export_public_dataset_pathway_comparison_tsv",
    "render_public_dataset_combined_summary_tsv",
    "render_public_dataset_dataset_summary_tsv",
    "render_public_dataset_effect_comparison_tsv",
    "render_public_dataset_failure_tsv",
    "render_public_dataset_meta_analysis_tsv",
    "render_public_dataset_pathway_comparison_tsv",
]

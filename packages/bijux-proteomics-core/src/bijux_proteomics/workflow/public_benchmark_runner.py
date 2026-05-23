# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Descriptor-driven public benchmark runner over shipped workflow owners."""

from __future__ import annotations

import csv
from enum import StrEnum
import hashlib
from pathlib import Path
from typing import Any

from pydantic import ConfigDict, Field
import yaml

from bijux_proteomics.multiplex import TmtSearchResultSourceKind
from bijux_proteomics.targeted import TargetedResultSourceKind
from bijux_proteomics.workflow.orchestrator import (
    DdaWorkflowConfig,
    DiannWorkflowConfig,
    MaxquantWorkflowConfig,
    PtmWorkflowConfig,
    TargetedWorkflowConfig,
    TargetedWorkflowStage,
    TmtWorkflowConfig,
    WorkflowMode,
    WorkflowResult,
    run_proteomics_workflow,
)
from bijux_proteomics_foundation import JsonModel


class PublicBenchmarkSearchEngine(StrEnum):
    """Stable workflow-family identifiers accepted by public descriptors."""

    DIANN = "diann"
    MAXQUANT = "maxquant"
    FRAGPIPE = "fragpipe"
    PTM = "ptm"
    TMT = "tmt"
    TARGETED = "targeted"


class PublicBenchmarkRunStatus(StrEnum):
    """Stable execution status for one public benchmark descriptor."""

    PASSED = "passed"
    FAILED = "failed"


class PublicBenchmarkFailureKind(StrEnum):
    """Stable failure classification for descriptor-driven benchmark runs."""

    MISSING_SOURCE_FILE = "missing_source_file"
    CHECKSUM_MISMATCH = "checksum_mismatch"
    MISSING_REQUIRED_SCHEMA = "missing_required_schema"
    EXECUTION_FAILED = "execution_failed"
    OUTPUT_CHECK_FAILED = "output_check_failed"
    APPROXIMATE_COUNT_MISMATCH = "approximate_count_mismatch"


class PublicBenchmarkSourceFile(JsonModel):
    """One governed input file declared by a public benchmark descriptor."""

    model_config = ConfigDict(extra="forbid")

    source_id: str = Field(..., min_length=1)
    schema_id: str = Field(..., min_length=1)
    repo_relative_path: str = Field(..., min_length=1)
    sha256: str = Field(..., min_length=64, max_length=64)
    public_reference_url: str | None = None
    note: str | None = None


class PublicBenchmarkSampleGroup(JsonModel):
    """One biological or technical group declared by a benchmark descriptor."""

    model_config = ConfigDict(extra="forbid")

    group_id: str = Field(..., min_length=1)
    sample_ids: tuple[str, ...] = Field(default_factory=tuple)
    note: str | None = None


class PublicBenchmarkContrast(JsonModel):
    """One named contrast over declared benchmark sample groups."""

    model_config = ConfigDict(extra="forbid")

    condition_a: str = Field(..., min_length=1)
    condition_b: str = Field(..., min_length=1)
    note: str | None = None


class PublicBenchmarkApproximateCount(JsonModel):
    """One approximate count expectation checked against workflow summary output."""

    model_config = ConfigDict(extra="forbid")

    metric_id: str = Field(..., min_length=1)
    expected: int = Field(..., ge=0)
    tolerance: int = Field(default=0, ge=0)


class PublicBenchmarkCommand(JsonModel):
    """One reviewer-facing command description for a benchmark descriptor."""

    model_config = ConfigDict(extra="forbid")

    cli: str = Field(..., min_length=1)
    note: str = Field(..., min_length=1)
    parameters: dict[str, str | int | float | bool] = Field(default_factory=dict)


class PublicBenchmarkOutputCheck(JsonModel):
    """One output existence check evaluated after successful workflow execution."""

    model_config = ConfigDict(extra="forbid")

    output_id: str = Field(..., min_length=1)
    relative_path: str = Field(..., min_length=1)
    note: str = Field(..., min_length=1)


class PublicBenchmarkDescriptor(JsonModel):
    """Descriptor loaded from ``benchmarks/public/<dataset>/dataset.yml``."""

    model_config = ConfigDict(extra="forbid")

    dataset_id: str = Field(..., min_length=1)
    accession: str = Field(..., min_length=1)
    species: str = Field(..., min_length=1)
    search_engine: str = Field(..., min_length=1)
    source_files: tuple[PublicBenchmarkSourceFile, ...] = Field(default_factory=tuple)
    expected_input_schemas: tuple[str, ...] = Field(default_factory=tuple)
    sample_groups: tuple[PublicBenchmarkSampleGroup, ...] = Field(default_factory=tuple)
    contrast: PublicBenchmarkContrast
    expected_approximate_counts: tuple[PublicBenchmarkApproximateCount, ...] = Field(
        default_factory=tuple
    )
    command: PublicBenchmarkCommand
    output_checks: tuple[PublicBenchmarkOutputCheck, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


class PublicBenchmarkFailure(JsonModel):
    """One explicit benchmark failure or downgrade reason."""

    model_config = ConfigDict(extra="forbid")

    kind: str = Field(..., min_length=1)
    subject: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)


class PublicBenchmarkSourceAudit(JsonModel):
    """One source-file audit row emitted during descriptor execution."""

    model_config = ConfigDict(extra="forbid")

    source_id: str = Field(..., min_length=1)
    schema_id: str = Field(..., min_length=1)
    repo_relative_path: str = Field(..., min_length=1)
    exists: bool
    checksum_matched: bool
    observed_sha256: str | None = None


class PublicBenchmarkRunReport(JsonModel):
    """Execution report for one descriptor-driven public benchmark run."""

    model_config = ConfigDict(extra="forbid")

    descriptor_path: str = Field(..., min_length=1)
    dataset_id: str = Field(..., min_length=1)
    accession: str = Field(..., min_length=1)
    search_engine: str = Field(..., min_length=1)
    status: str = Field(..., min_length=1)
    output_dir: str = Field(..., min_length=1)
    source_audits: tuple[PublicBenchmarkSourceAudit, ...] = Field(default_factory=tuple)
    failures: tuple[PublicBenchmarkFailure, ...] = Field(default_factory=tuple)
    verified_counts: dict[str, int] = Field(default_factory=dict)
    workflow_result: WorkflowResult | None = None
    note: str = Field(..., min_length=1)


class PublicBenchmarkSuiteReport(JsonModel):
    """Suite report over every descriptor found under one benchmark root."""

    model_config = ConfigDict(extra="forbid")

    benchmark_root: str = Field(..., min_length=1)
    output_root: str = Field(..., min_length=1)
    runs: tuple[PublicBenchmarkRunReport, ...] = Field(default_factory=tuple)
    passed_count: int = Field(..., ge=0)
    failed_count: int = Field(..., ge=0)
    note: str = Field(..., min_length=1)


def _repo_root() -> Path:
    return next(
        parent
        for parent in Path(__file__).resolve().parents
        if (parent / "packages").is_dir() and (parent / "docs").is_dir()
    )


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_public_benchmark_descriptor(descriptor_path: Path) -> PublicBenchmarkDescriptor:
    """Load and validate one public benchmark descriptor."""

    payload = yaml.safe_load(descriptor_path.read_text(encoding="utf-8"))
    return PublicBenchmarkDescriptor.model_validate(payload)


def list_public_benchmark_descriptor_paths(benchmark_root: Path) -> tuple[Path, ...]:
    """List every descriptor rooted under ``benchmarks/public``."""

    return tuple(sorted(benchmark_root.glob("*/dataset.yml")))


def run_public_benchmark_descriptor(
    descriptor_path: Path,
    *,
    output_root: Path,
) -> PublicBenchmarkRunReport:
    """Run one public benchmark descriptor through the owned workflow API."""

    descriptor = load_public_benchmark_descriptor(descriptor_path)
    repo_root = _repo_root()
    output_dir = output_root / descriptor.dataset_id
    output_dir.mkdir(parents=True, exist_ok=True)

    source_map: dict[str, Path] = {}
    source_audits: list[PublicBenchmarkSourceAudit] = []
    failures: list[PublicBenchmarkFailure] = []

    for source in descriptor.source_files:
        path = repo_root / source.repo_relative_path
        exists = path.exists()
        observed_sha256 = _sha256(path) if exists else None
        checksum_matched = observed_sha256 == source.sha256 if exists else False
        source_audits.append(
            PublicBenchmarkSourceAudit(
                source_id=source.source_id,
                schema_id=source.schema_id,
                repo_relative_path=source.repo_relative_path,
                exists=exists,
                checksum_matched=checksum_matched,
                observed_sha256=observed_sha256,
            )
        )
        if not exists:
            failures.append(
                PublicBenchmarkFailure(
                    kind=PublicBenchmarkFailureKind.MISSING_SOURCE_FILE,
                    subject=source.schema_id,
                    message=(
                        f"descriptor source '{source.schema_id}' is missing at "
                        f"{source.repo_relative_path}"
                    ),
                )
            )
            continue
        if not checksum_matched:
            failures.append(
                PublicBenchmarkFailure(
                    kind=PublicBenchmarkFailureKind.CHECKSUM_MISMATCH,
                    subject=source.schema_id,
                    message=(
                        f"descriptor source '{source.schema_id}' checksum mismatch: "
                        f"expected {source.sha256}, observed {observed_sha256}"
                    ),
                )
            )
            continue
        source_map[source.schema_id] = path

    missing_schemas = tuple(
        schema_id
        for schema_id in descriptor.expected_input_schemas
        if schema_id not in source_map
    )
    failures.extend(
        PublicBenchmarkFailure(
            kind=PublicBenchmarkFailureKind.MISSING_REQUIRED_SCHEMA,
            subject=schema_id,
            message=(
                f"descriptor requires input schema '{schema_id}' but no matching "
                "source file is declared with a valid checksum"
            ),
        )
        for schema_id in missing_schemas
    )
    if failures:
        return PublicBenchmarkRunReport(
            descriptor_path=str(descriptor_path),
            dataset_id=descriptor.dataset_id,
            accession=descriptor.accession,
            search_engine=descriptor.search_engine,
            status=PublicBenchmarkRunStatus.FAILED,
            output_dir=str(output_dir),
            source_audits=tuple(source_audits),
            failures=tuple(failures),
            note=(
                "public benchmark descriptor failed before workflow dispatch because "
                "one or more governed source files or required schemas were absent"
            ),
        )

    try:
        workflow_result = run_proteomics_workflow(
            _build_workflow_config(
                descriptor,
                source_map=source_map,
                output_dir=output_dir,
            )
        )
    except Exception as exc:  # noqa: BLE001
        return PublicBenchmarkRunReport(
            descriptor_path=str(descriptor_path),
            dataset_id=descriptor.dataset_id,
            accession=descriptor.accession,
            search_engine=descriptor.search_engine,
            status=PublicBenchmarkRunStatus.FAILED,
            output_dir=str(output_dir),
            source_audits=tuple(source_audits),
            failures=(
                PublicBenchmarkFailure(
                    kind=PublicBenchmarkFailureKind.EXECUTION_FAILED,
                    subject=descriptor.search_engine,
                    message=str(exc),
                ),
            ),
            note=(
                "public benchmark descriptor reached workflow dispatch but the "
                "current shipped workflow inputs still fail with an explicit owner error"
            ),
        )

    count_failures, verified_counts = _verify_approximate_counts(
        descriptor,
        workflow_result=workflow_result,
    )
    output_failures = _verify_output_checks(descriptor, output_dir=output_dir)
    failures = [*count_failures, *output_failures]

    return PublicBenchmarkRunReport(
        descriptor_path=str(descriptor_path),
        dataset_id=descriptor.dataset_id,
        accession=descriptor.accession,
        search_engine=descriptor.search_engine,
        status=(
            PublicBenchmarkRunStatus.PASSED
            if not failures
            else PublicBenchmarkRunStatus.FAILED
        ),
        output_dir=str(output_dir),
        source_audits=tuple(source_audits),
        failures=tuple(failures),
        verified_counts=verified_counts,
        workflow_result=workflow_result,
        note=(
            "public benchmark descriptor executed through the owned workflow "
            "orchestrator and then checked counts and required outputs"
            if not failures
            else "public benchmark descriptor executed, but one or more governed validation checks failed"
        ),
    )


def run_public_benchmark_descriptor_suite(
    benchmark_root: Path,
    *,
    output_root: Path,
) -> PublicBenchmarkSuiteReport:
    """Run every descriptor found under one benchmark root."""

    runs = tuple(
        run_public_benchmark_descriptor(descriptor_path, output_root=output_root)
        for descriptor_path in list_public_benchmark_descriptor_paths(benchmark_root)
    )
    return PublicBenchmarkSuiteReport(
        benchmark_root=str(benchmark_root),
        output_root=str(output_root),
        runs=runs,
        passed_count=sum(run.status == PublicBenchmarkRunStatus.PASSED for run in runs),
        failed_count=sum(run.status == PublicBenchmarkRunStatus.FAILED for run in runs),
        note=(
            "descriptor suite records which flagship public benchmark packages are "
            "currently runnable through owned workflows and which still downgrade "
            "to explicit failure reasons"
        ),
    )


def render_public_benchmark_suite_summary_tsv(
    suite: PublicBenchmarkSuiteReport,
) -> str:
    """Render one suite summary TSV for operator review."""

    rows = [
        {
            "dataset_id": run.dataset_id,
            "accession": run.accession,
            "search_engine": run.search_engine,
            "status": run.status,
            "failure_count": len(run.failures),
            "output_dir": run.output_dir,
            "note": run.note,
        }
        for run in suite.runs
    ]
    return _dict_rows_to_tsv(rows)


def render_public_benchmark_suite_failures_tsv(
    suite: PublicBenchmarkSuiteReport,
) -> str:
    """Render explicit benchmark downgrade reasons as TSV."""

    rows = [
        {
            "dataset_id": run.dataset_id,
            "accession": run.accession,
            "status": run.status,
            "failure_kind": failure.kind,
            "subject": failure.subject,
            "message": failure.message,
        }
        for run in suite.runs
        for failure in run.failures
    ]
    return _dict_rows_to_tsv(rows)


def _dict_rows_to_tsv(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return ""
    fieldnames = list(rows[0].keys())
    from io import StringIO

    handle = StringIO()
    writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t")
    writer.writeheader()
    writer.writerows(rows)
    return handle.getvalue()


def _build_workflow_config(
    descriptor: PublicBenchmarkDescriptor,
    *,
    source_map: dict[str, Path],
    output_dir: Path,
):
    condition_a = descriptor.contrast.condition_a
    condition_b = descriptor.contrast.condition_b
    parameters = descriptor.command.parameters
    engine = descriptor.search_engine

    if engine == PublicBenchmarkSearchEngine.DIANN:
        return DiannWorkflowConfig(
            result_tsv_path=source_map["result_tsv"],
            config_path=source_map.get("config_json"),
            design_tsv_path=source_map["design_tsv"],
            proteins_fasta_path=source_map["proteins_fasta"],
            condition_a=condition_a,
            condition_b=condition_b,
            output_dir=output_dir,
        )
    if engine == PublicBenchmarkSearchEngine.MAXQUANT:
        return MaxquantWorkflowConfig(
            evidence_txt_path=source_map["evidence_txt"],
            peptides_txt_path=source_map["peptides_txt"],
            protein_groups_txt_path=source_map["protein_groups_txt"],
            design_tsv_path=source_map["design_tsv"],
            proteins_fasta_path=source_map["proteins_fasta"],
            config_path=source_map.get("config_txt"),
            condition_a=condition_a,
            condition_b=condition_b,
            output_dir=output_dir,
        )
    if engine == PublicBenchmarkSearchEngine.FRAGPIPE:
        return DdaWorkflowConfig(
            mode=WorkflowMode.FRAGPIPE,
            search_result_tsv_path=source_map["search_result_tsv"],
            design_tsv_path=source_map["design_tsv"],
            proteins_fasta_path=source_map["proteins_fasta"],
            condition_a=condition_a,
            condition_b=condition_b,
            output_dir=output_dir,
        )
    if engine == PublicBenchmarkSearchEngine.PTM:
        return PtmWorkflowConfig(
            evidence_tsv_path=source_map["evidence_tsv"],
            proteins_fasta_path=source_map["proteins_fasta"],
            feature_tsv_path=source_map["feature_tsv"],
            design_tsv_path=source_map["design_tsv"],
            condition_a=condition_a,
            condition_b=condition_b,
            batch_field=str(parameters.get("batch_field", "")),
            output_dir=output_dir,
        )
    if engine == PublicBenchmarkSearchEngine.TMT:
        return TmtWorkflowConfig(
            result_tsv_path=source_map["result_tsv"],
            design_tsv_path=source_map["design_tsv"],
            control_channel=str(parameters.get("control_channel", "126")),
            source_kind=TmtSearchResultSourceKind(
                str(parameters.get("source_kind", TmtSearchResultSourceKind.MAXQUANT))
            ),
            condition_a=condition_a,
            condition_b=condition_b,
            output_dir=output_dir,
        )
    if engine == PublicBenchmarkSearchEngine.TARGETED:
        return TargetedWorkflowConfig(
            input_tsv_path=source_map["input_tsv"],
            source_kind=TargetedResultSourceKind(
                str(
                    parameters.get(
                        "source_kind", TargetedResultSourceKind.SKYLINE_EXPORT
                    )
                )
            ),
            stage=TargetedWorkflowStage(
                str(parameters.get("stage", TargetedWorkflowStage.MATRIX))
            ),
            design_tsv_path=source_map.get("design_tsv"),
            output_dir=output_dir,
        )
    raise ValueError(f"unsupported public benchmark search_engine '{engine}'")


def _verify_approximate_counts(
    descriptor: PublicBenchmarkDescriptor,
    *,
    workflow_result: WorkflowResult,
) -> tuple[list[PublicBenchmarkFailure], dict[str, int]]:
    summary = getattr(workflow_result.report, "summary", None)
    summary_dict = summary.to_dict() if summary is not None else {}
    verified_counts: dict[str, int] = {}
    failures: list[PublicBenchmarkFailure] = []

    for count_expectation in descriptor.expected_approximate_counts:
        observed = summary_dict.get(count_expectation.metric_id)
        if isinstance(observed, bool) or not isinstance(observed, int):
            continue
        verified_counts[count_expectation.metric_id] = observed
        if abs(observed - count_expectation.expected) > count_expectation.tolerance:
            failures.append(
                PublicBenchmarkFailure(
                    kind=PublicBenchmarkFailureKind.APPROXIMATE_COUNT_MISMATCH,
                    subject=count_expectation.metric_id,
                    message=(
                        f"summary metric '{count_expectation.metric_id}' observed "
                        f"{observed}, expected approximately {count_expectation.expected} "
                        f"within tolerance {count_expectation.tolerance}"
                    ),
                )
            )
    return failures, verified_counts


def _verify_output_checks(
    descriptor: PublicBenchmarkDescriptor,
    *,
    output_dir: Path,
) -> list[PublicBenchmarkFailure]:
    failures: list[PublicBenchmarkFailure] = []
    for check in descriptor.output_checks:
        path = output_dir / check.relative_path
        if not path.exists():
            failures.append(
                PublicBenchmarkFailure(
                    kind=PublicBenchmarkFailureKind.OUTPUT_CHECK_FAILED,
                    subject=check.output_id,
                    message=(
                        f"expected output '{check.output_id}' is missing at "
                        f"{path.relative_to(output_dir)}"
                    ),
                )
            )
    return failures

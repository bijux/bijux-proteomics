# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Descriptor-driven public benchmark runner over shipped workflow owners."""

from __future__ import annotations

import csv
from enum import StrEnum
import hashlib
import json
from pathlib import Path
from typing import Any

from pydantic import ConfigDict, Field

from bijux_proteomics.io.formats import parse_experimental_design_table
from bijux_proteomics.multiplex import build_multiplex_metadata_validation_report
from bijux_proteomics.multiplex import TmtSearchResultSourceKind
from bijux_proteomics.ptm import PtmProteinCorrectionMode
from bijux_proteomics.targeted import (
    TargetedResultSourceKind,
    TargetedValidationDiscoveryClaimInput,
    TargetedValidationPanelAssayInput,
)
from bijux_proteomics.workflow.public_benchmark_descriptors import (
    PublicBenchmarkDescriptor,
    PublicBenchmarkExpectedBiologicalSignal,
    PublicBenchmarkExpectedSignalDirection,
    PublicBenchmarkExpectedSignalSubjectKind,
    PublicBenchmarkKnownLimitation,
    PublicBenchmarkSearchEngine,
    load_public_benchmark_descriptor,
    list_public_benchmark_descriptor_paths,
)
from bijux_proteomics.workflow.orchestrator import (
    DdaWorkflowConfig,
    DiannWorkflowConfig,
    LabelFreeWorkflowConfig,
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
    SAMPLE_METADATA_MISMATCH = "sample_metadata_mismatch"
    MULTIPLEX_CHANNEL_MAPPING_INVALID = "multiplex_channel_mapping_invalid"
    EXPECTED_SIGNAL_MISMATCH = "expected_signal_mismatch"


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


class PublicBenchmarkExpectedSignalAssessmentStatus(StrEnum):
    """Stable benchmark signal-assessment outcomes."""

    MATCHED = "matched"
    MISMATCHED = "mismatched"
    UNVERIFIED = "unverified"


class PublicBenchmarkExpectedSignalAssessment(JsonModel):
    """Assessment of one declared biological expectation against owned outputs."""

    model_config = ConfigDict(extra="forbid")

    signal_id: str = Field(..., min_length=1)
    subject_kind: PublicBenchmarkExpectedSignalSubjectKind
    subject_id: str = Field(..., min_length=1)
    expected_direction: PublicBenchmarkExpectedSignalDirection
    status: PublicBenchmarkExpectedSignalAssessmentStatus
    source_surface: str = Field(..., min_length=1)
    observed_direction: str | None = None
    observed_effect_size: float | None = None
    observed_adjusted_p_value: float | None = Field(default=None, ge=0.0, le=1.0)
    note: str = Field(..., min_length=1)


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
    known_limitations: tuple[PublicBenchmarkKnownLimitation, ...] = Field(
        default_factory=tuple
    )
    expected_signal_assessments: tuple[PublicBenchmarkExpectedSignalAssessment, ...] = (
        Field(default_factory=tuple)
    )
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
    failures.extend(_verify_sample_metadata(descriptor, source_map=source_map))
    failures.extend(_verify_tmt_channel_mapping(descriptor, source_map=source_map))
    if failures:
        return PublicBenchmarkRunReport(
            descriptor_path=str(descriptor_path),
            dataset_id=descriptor.dataset_id,
            accession=descriptor.accession,
            search_engine=descriptor.search_engine,
            status=PublicBenchmarkRunStatus.FAILED,
            output_dir=str(output_dir),
            source_audits=tuple(source_audits),
            known_limitations=descriptor.known_limitations,
            failures=tuple(failures),
            note=(
                "public benchmark descriptor failed before workflow dispatch because "
                "governed source files, required schemas, or declared sample metadata "
                "did not match the runnable workflow inputs"
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
            known_limitations=descriptor.known_limitations,
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
    signal_failures, signal_assessments = _verify_expected_biological_signals(
        descriptor,
        output_dir=output_dir,
    )
    failures = [*count_failures, *output_failures, *signal_failures]

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
        known_limitations=descriptor.known_limitations,
        expected_signal_assessments=signal_assessments,
        failures=tuple(failures),
        verified_counts=verified_counts,
        workflow_result=workflow_result,
        note=(
            "public benchmark descriptor executed through the owned workflow "
            "orchestrator and then checked counts, required outputs, and declared "
            "biological expectations"
            if not failures
            else "public benchmark descriptor executed, but one or more governed "
            "validation checks failed"
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
            "known_limitation_count": len(run.known_limitations),
            "blocking_limitation_count": sum(
                limitation.blocks_workflow_execution
                for limitation in run.known_limitations
            ),
            "expected_signal_count": len(run.expected_signal_assessments),
            "matched_signal_count": sum(
                assessment.status
                is PublicBenchmarkExpectedSignalAssessmentStatus.MATCHED
                for assessment in run.expected_signal_assessments
            ),
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


def render_public_benchmark_suite_signal_assessments_tsv(
    suite: PublicBenchmarkSuiteReport,
) -> str:
    """Render declared biological-signal checks across one benchmark suite."""

    rows = [
        {
            "dataset_id": run.dataset_id,
            "accession": run.accession,
            "status": run.status,
            "signal_id": assessment.signal_id,
            "subject_kind": assessment.subject_kind.value,
            "subject_id": assessment.subject_id,
            "expected_direction": assessment.expected_direction.value,
            "assessment_status": assessment.status.value,
            "source_surface": assessment.source_surface,
            "observed_direction": assessment.observed_direction or "",
            "observed_effect_size": assessment.observed_effect_size,
            "observed_adjusted_p_value": assessment.observed_adjusted_p_value,
            "note": assessment.note,
        }
        for run in suite.runs
        for assessment in run.expected_signal_assessments
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
    if engine == PublicBenchmarkSearchEngine.LFQ:
        return LabelFreeWorkflowConfig(
            input_tsv_path=source_map["input_tsv"],
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
            source_protein_tsv_path=source_map.get("source_protein_tsv"),
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
            protein_correction_mode=PtmProteinCorrectionMode(
                str(
                    parameters.get(
                        "protein_correction_mode",
                        PtmProteinCorrectionMode.NONE,
                    )
                )
            ),
            max_adjusted_p_value=float(parameters.get("max_adjusted_p_value", 0.1)),
            min_absolute_log2_fold_change=float(
                parameters.get("min_absolute_log2_fold_change", 1.0)
            ),
            annotation_tsv_path=source_map.get("annotation_tsv"),
            annotation_target_species=(
                None
                if "annotation_target_species" not in parameters
                else str(parameters["annotation_target_species"])
            ),
            card_max_adjusted_p_value=float(
                parameters.get("card_max_adjusted_p_value", 0.1)
            ),
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
        stage = TargetedWorkflowStage(
            str(parameters.get("stage", TargetedWorkflowStage.MATRIX))
        )
        return TargetedWorkflowConfig(
            input_tsv_path=source_map["input_tsv"],
            source_kind=TargetedResultSourceKind(
                str(
                    parameters.get(
                        "source_kind", TargetedResultSourceKind.SKYLINE_EXPORT
                    )
                )
            ),
            stage=stage,
            design_tsv_path=source_map.get("design_tsv"),
            discovery_claims=(
                ()
                if stage is not TargetedWorkflowStage.VALIDATION
                else _load_targeted_discovery_claims(
                    source_map.get("discovery_claims_json")
                )
            ),
            panel_assays=(
                ()
                if stage is not TargetedWorkflowStage.VALIDATION
                else _load_targeted_panel_assays(source_map.get("panel_assays_json"))
            ),
            case_condition=(
                None if stage is not TargetedWorkflowStage.VALIDATION else condition_b
            ),
            control_condition=(
                None if stage is not TargetedWorkflowStage.VALIDATION else condition_a
            ),
            output_dir=output_dir,
        )
    raise ValueError(f"unsupported public benchmark search_engine '{engine}'")


def _load_targeted_discovery_claims(
    path: Path | None,
) -> tuple[TargetedValidationDiscoveryClaimInput, ...]:
    if path is None:
        return ()
    payload = json.loads(path.read_text(encoding="utf-8"))
    return tuple(
        TargetedValidationDiscoveryClaimInput.model_validate(item) for item in payload
    )


def _load_targeted_panel_assays(
    path: Path | None,
) -> tuple[TargetedValidationPanelAssayInput, ...]:
    if path is None:
        return ()
    payload = json.loads(path.read_text(encoding="utf-8"))
    return tuple(TargetedValidationPanelAssayInput.model_validate(item) for item in payload)


def _verify_approximate_counts(
    descriptor: PublicBenchmarkDescriptor,
    *,
    workflow_result: WorkflowResult,
) -> tuple[list[PublicBenchmarkFailure], dict[str, int]]:
    summary = getattr(workflow_result.report, "summary", None)
    summary_dict = summary.to_dict() if summary is not None else {}
    nested_report = getattr(workflow_result.report, "report", None)
    nested_summary = getattr(nested_report, "summary", None)
    if nested_summary is not None:
        for metric_id, observed in nested_summary.to_dict().items():
            summary_dict.setdefault(metric_id, observed)
    targeted_assay_qc_manifest = getattr(
        workflow_result.report,
        "targeted_assay_qc_workflow_manifest",
        None,
    )
    if targeted_assay_qc_manifest is not None:
        for report_name in ("import_summary", "matrix_summary", "assay_qc_summary"):
            report_summary = getattr(targeted_assay_qc_manifest, report_name, None)
            if report_summary is None:
                continue
            for metric_id, observed in report_summary.items():
                summary_dict.setdefault(metric_id, observed)
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


def _verify_sample_metadata(
    descriptor: PublicBenchmarkDescriptor,
    *,
    source_map: dict[str, Path],
) -> list[PublicBenchmarkFailure]:
    if "design_tsv" not in source_map or not descriptor.sample_metadata:
        return []

    design_report = parse_experimental_design_table(source_map["design_tsv"])
    design_entries = {entry.sample_id: entry for entry in design_report.accepted_entries}
    failures: list[PublicBenchmarkFailure] = []

    for sample in descriptor.sample_metadata:
        design_entry = design_entries.get(sample.sample_id)
        if design_entry is None:
            failures.append(
                PublicBenchmarkFailure(
                    kind=PublicBenchmarkFailureKind.SAMPLE_METADATA_MISMATCH,
                    subject=sample.sample_id,
                    message=(
                        "descriptor sample metadata declared sample_id "
                        f"'{sample.sample_id}' but the governed design table does not "
                        "contain that sample"
                    ),
                )
            )
            continue
        mismatches: list[str] = []
        _compare_declared_value(
            mismatches, "condition", sample.condition, design_entry.condition
        )
        _compare_declared_value(
            mismatches, "replicate", sample.replicate, design_entry.replicate
        )
        _compare_declared_value(
            mismatches, "fraction", sample.fraction, design_entry.fraction
        )
        _compare_declared_value(
            mismatches, "spectra_file", sample.spectra_file, design_entry.spectra_file
        )
        _compare_declared_value(
            mismatches,
            "identifications_file",
            sample.identifications_file,
            design_entry.identifications_file,
        )
        _compare_declared_value(mismatches, "batch", sample.batch, design_entry.batch)
        _compare_declared_value(
            mismatches, "instrument", sample.instrument, design_entry.instrument
        )
        _compare_declared_value(
            mismatches,
            "search_engine",
            sample.search_engine,
            design_entry.search_engine,
        )
        _compare_declared_value(
            mismatches,
            "multiplex_group",
            sample.multiplex_group,
            design_entry.multiplex_group,
        )
        _compare_declared_value(
            mismatches,
            "multiplex_channel",
            sample.multiplex_channel,
            design_entry.multiplex_channel,
        )
        if sample.sample_role is not None:
            _compare_declared_value(
                mismatches,
                "sample_role",
                sample.sample_role.value,
                design_entry.sample_role.value,
            )
        for key, expected_value in sorted(sample.metadata.items()):
            _compare_declared_value(
                mismatches,
                f"metadata.{key}",
                expected_value,
                design_entry.metadata.get(key),
            )
        if mismatches:
            failures.append(
                PublicBenchmarkFailure(
                    kind=PublicBenchmarkFailureKind.SAMPLE_METADATA_MISMATCH,
                    subject=sample.sample_id,
                    message=(
                        f"descriptor sample metadata for '{sample.sample_id}' does not "
                        f"match the governed design table: {'; '.join(mismatches)}"
                    ),
                )
            )

    declared_sample_ids = {sample.sample_id for sample in descriptor.sample_metadata}
    for design_sample_id in sorted(design_entries):
        if design_sample_id not in declared_sample_ids:
            failures.append(
                PublicBenchmarkFailure(
                    kind=PublicBenchmarkFailureKind.SAMPLE_METADATA_MISMATCH,
                    subject=design_sample_id,
                    message=(
                        f"governed design sample '{design_sample_id}' is missing from "
                        "descriptor sample_metadata"
                    ),
                )
            )
    return failures


def _verify_tmt_channel_mapping(
    descriptor: PublicBenchmarkDescriptor,
    *,
    source_map: dict[str, Path],
) -> list[PublicBenchmarkFailure]:
    if descriptor.search_engine is not PublicBenchmarkSearchEngine.TMT:
        return []
    design_path = source_map.get("design_tsv")
    if design_path is None:
        return []

    design_report = parse_experimental_design_table(design_path)
    validation_report = build_multiplex_metadata_validation_report(design_report)
    failures: list[PublicBenchmarkFailure] = []

    if validation_report.summary.missing_channel_assignment_count > 0:
        failures.append(
            PublicBenchmarkFailure(
                kind=PublicBenchmarkFailureKind.MULTIPLEX_CHANNEL_MAPPING_INVALID,
                subject="missing_channel_assignment",
                message=(
                    "tmt benchmark design is missing one or more multiplex channel "
                    "assignments; benchmark execution must block until every declared "
                    "group-channel position is mapped"
                ),
            )
        )
    if validation_report.summary.duplicate_assignment_count > 0:
        failures.append(
            PublicBenchmarkFailure(
                kind=PublicBenchmarkFailureKind.MULTIPLEX_CHANNEL_MAPPING_INVALID,
                subject="duplicate_channel_assignment",
                message=(
                    "tmt benchmark design contains duplicate multiplex channel or "
                    "sample assignments; benchmark execution must block until "
                    "multiplex mappings are unique"
                ),
            )
        )
    return failures


def _compare_declared_value(
    mismatches: list[str],
    field_name: str,
    expected_value: object | None,
    observed_value: object | None,
) -> None:
    if expected_value is None:
        return
    if str(expected_value) != str(observed_value):
        mismatches.append(
            f"{field_name} expected {expected_value!r} observed {observed_value!r}"
        )


def _verify_expected_biological_signals(
    descriptor: PublicBenchmarkDescriptor,
    *,
    output_dir: Path,
) -> tuple[list[PublicBenchmarkFailure], tuple[PublicBenchmarkExpectedSignalAssessment, ...]]:
    assessments: list[PublicBenchmarkExpectedSignalAssessment] = []
    failures: list[PublicBenchmarkFailure] = []
    for signal in descriptor.expected_biological_signals:
        assessment = _assess_expected_signal(signal, output_dir=output_dir)
        assessments.append(assessment)
        if assessment.status is not PublicBenchmarkExpectedSignalAssessmentStatus.MATCHED:
            failures.append(
                PublicBenchmarkFailure(
                    kind=PublicBenchmarkFailureKind.EXPECTED_SIGNAL_MISMATCH,
                    subject=signal.signal_id,
                    message=assessment.note,
                )
            )
    return failures, tuple(assessments)


def _assess_expected_signal(
    signal: PublicBenchmarkExpectedBiologicalSignal,
    *,
    output_dir: Path,
) -> PublicBenchmarkExpectedSignalAssessment:
    if signal.subject_kind is PublicBenchmarkExpectedSignalSubjectKind.PROTEIN:
        return _assess_protein_signal(signal, output_dir=output_dir)
    if signal.subject_kind is PublicBenchmarkExpectedSignalSubjectKind.PATHWAY:
        return _assess_pathway_signal(signal, output_dir=output_dir)
    if signal.subject_kind is PublicBenchmarkExpectedSignalSubjectKind.PTM_SITE:
        return _assess_ptm_site_signal(signal, output_dir=output_dir)
    raise ValueError(f"unsupported expected signal kind '{signal.subject_kind.value}'")


def _assess_protein_signal(
    signal: PublicBenchmarkExpectedBiologicalSignal,
    *,
    output_dir: Path,
) -> PublicBenchmarkExpectedSignalAssessment:
    rows = _load_tsv_rows(output_dir / "biological_protein_cards.tsv")
    row = next(
        (
            item
            for item in rows
            if item.get("representative_protein_ref") == signal.subject_id
            or item.get("protein_group_id") == signal.subject_id
            or item.get("gene_symbol") == signal.subject_id
        ),
        None,
    )
    if row is None:
        return _unverified_signal_assessment(
            signal,
            source_surface="biological_protein_cards.tsv",
            note=(
                f"expected protein signal '{signal.subject_id}' could not be checked "
                "because no matching protein card row was exported"
            ),
        )
    effect_size = _parse_float(row.get("log2_fold_change"))
    adjusted_p_value = _parse_float(row.get("adjusted_p_value"))
    significant = row.get("significant", "").strip().lower() == "true"
    observed_direction = _direction_from_effect_size(effect_size)
    return _finalize_directional_signal_assessment(
        signal,
        source_surface="biological_protein_cards.tsv",
        observed_direction=observed_direction,
        observed_effect_size=effect_size,
        observed_adjusted_p_value=adjusted_p_value,
        significant=significant,
    )


def _assess_pathway_signal(
    signal: PublicBenchmarkExpectedBiologicalSignal,
    *,
    output_dir: Path,
) -> PublicBenchmarkExpectedSignalAssessment:
    rows = _load_tsv_rows(
        output_dir / "biological_pathway_activity_condition_comparisons.tsv"
    )
    row = next((item for item in rows if item.get("pathway_id") == signal.subject_id), None)
    if row is None:
        return _unverified_signal_assessment(
            signal,
            source_surface="biological_pathway_activity_condition_comparisons.tsv",
            note=(
                f"expected pathway signal '{signal.subject_id}' could not be checked "
                "because no matching pathway activity comparison row was exported"
            ),
        )
    effect_size = _parse_float(row.get("activity_score_delta"))
    observed_direction = _direction_from_effect_size(effect_size)
    comparison_confidence_status = row.get("comparison_confidence_status", "")
    significant = comparison_confidence_status == "high_confidence"
    return _finalize_directional_signal_assessment(
        signal,
        source_surface="biological_pathway_activity_condition_comparisons.tsv",
        observed_direction=observed_direction,
        observed_effect_size=effect_size,
        observed_adjusted_p_value=None,
        significant=significant,
    )


def _assess_ptm_site_signal(
    signal: PublicBenchmarkExpectedBiologicalSignal,
    *,
    output_dir: Path,
) -> PublicBenchmarkExpectedSignalAssessment:
    rows = _load_tsv_rows(output_dir / "ptm_differential.tsv")
    row = next((item for item in rows if item.get("site_key") == signal.subject_id), None)
    if row is None:
        return _unverified_signal_assessment(
            signal,
            source_surface="ptm_differential.tsv",
            note=(
                f"expected PTM-site signal '{signal.subject_id}' could not be checked "
                "because no matching PTM differential row was exported"
            ),
        )
    effect_size = _parse_float(
        row.get("corrected_log2_fold_change") or row.get("log2_fold_change")
    )
    adjusted_p_value = _parse_float(row.get("adjusted_p_value"))
    observed_direction = _direction_from_effect_size(effect_size)
    significant = (
        adjusted_p_value is not None
        and signal.max_adjusted_p_value is not None
        and adjusted_p_value <= signal.max_adjusted_p_value
    )
    return _finalize_directional_signal_assessment(
        signal,
        source_surface="ptm_differential.tsv",
        observed_direction=observed_direction,
        observed_effect_size=effect_size,
        observed_adjusted_p_value=adjusted_p_value,
        significant=significant,
    )


def _finalize_directional_signal_assessment(
    signal: PublicBenchmarkExpectedBiologicalSignal,
    *,
    source_surface: str,
    observed_direction: str | None,
    observed_effect_size: float | None,
    observed_adjusted_p_value: float | None,
    significant: bool,
) -> PublicBenchmarkExpectedSignalAssessment:
    if signal.expected_direction is PublicBenchmarkExpectedSignalDirection.PRESENT:
        return PublicBenchmarkExpectedSignalAssessment(
            signal_id=signal.signal_id,
            subject_kind=signal.subject_kind,
            subject_id=signal.subject_id,
            expected_direction=signal.expected_direction,
            status=PublicBenchmarkExpectedSignalAssessmentStatus.MATCHED,
            source_surface=source_surface,
            observed_direction=observed_direction,
            observed_effect_size=observed_effect_size,
            observed_adjusted_p_value=observed_adjusted_p_value,
            note=(
                f"expected signal '{signal.subject_id}' was present on exported "
                f"{source_surface}"
            ),
        )

    expected_direction = signal.expected_direction.value
    if observed_direction != expected_direction:
        return PublicBenchmarkExpectedSignalAssessment(
            signal_id=signal.signal_id,
            subject_kind=signal.subject_kind,
            subject_id=signal.subject_id,
            expected_direction=signal.expected_direction,
            status=PublicBenchmarkExpectedSignalAssessmentStatus.MISMATCHED,
            source_surface=source_surface,
            observed_direction=observed_direction,
            observed_effect_size=observed_effect_size,
            observed_adjusted_p_value=observed_adjusted_p_value,
            note=(
                f"expected signal '{signal.subject_id}' to be {expected_direction}, "
                f"but exported {source_surface} showed direction {observed_direction or 'unresolved'}"
            ),
        )
    if signal.min_absolute_effect_size is not None and (
        observed_effect_size is None
        or abs(observed_effect_size) < signal.min_absolute_effect_size
    ):
        return PublicBenchmarkExpectedSignalAssessment(
            signal_id=signal.signal_id,
            subject_kind=signal.subject_kind,
            subject_id=signal.subject_id,
            expected_direction=signal.expected_direction,
            status=PublicBenchmarkExpectedSignalAssessmentStatus.MISMATCHED,
            source_surface=source_surface,
            observed_direction=observed_direction,
            observed_effect_size=observed_effect_size,
            observed_adjusted_p_value=observed_adjusted_p_value,
            note=(
                f"expected signal '{signal.subject_id}' had the right direction but "
                "did not reach the declared minimum absolute effect size"
            ),
        )
    if signal.max_adjusted_p_value is not None and not significant:
        return PublicBenchmarkExpectedSignalAssessment(
            signal_id=signal.signal_id,
            subject_kind=signal.subject_kind,
            subject_id=signal.subject_id,
            expected_direction=signal.expected_direction,
            status=PublicBenchmarkExpectedSignalAssessmentStatus.MISMATCHED,
            source_surface=source_surface,
            observed_direction=observed_direction,
            observed_effect_size=observed_effect_size,
            observed_adjusted_p_value=observed_adjusted_p_value,
            note=(
                f"expected signal '{signal.subject_id}' had the right direction but "
                "did not satisfy the declared adjusted-p-value or confidence threshold"
            ),
        )
    return PublicBenchmarkExpectedSignalAssessment(
        signal_id=signal.signal_id,
        subject_kind=signal.subject_kind,
        subject_id=signal.subject_id,
        expected_direction=signal.expected_direction,
        status=PublicBenchmarkExpectedSignalAssessmentStatus.MATCHED,
        source_surface=source_surface,
        observed_direction=observed_direction,
        observed_effect_size=observed_effect_size,
        observed_adjusted_p_value=observed_adjusted_p_value,
        note=(
            f"expected signal '{signal.subject_id}' matched the declared benchmark "
            "direction and threshold"
        ),
    )


def _unverified_signal_assessment(
    signal: PublicBenchmarkExpectedBiologicalSignal,
    *,
    source_surface: str,
    note: str,
) -> PublicBenchmarkExpectedSignalAssessment:
    return PublicBenchmarkExpectedSignalAssessment(
        signal_id=signal.signal_id,
        subject_kind=signal.subject_kind,
        subject_id=signal.subject_id,
        expected_direction=signal.expected_direction,
        status=PublicBenchmarkExpectedSignalAssessmentStatus.UNVERIFIED,
        source_surface=source_surface,
        note=note,
    )


def _load_tsv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as handle:
        return [
            {key: value for key, value in row.items() if key is not None}
            for row in csv.DictReader(handle, delimiter="\t")
        ]


def _parse_float(value: str | None) -> float | None:
    text = (value or "").strip()
    if not text:
        return None
    return float(text)


def _direction_from_effect_size(value: float | None) -> str | None:
    if value is None:
        return None
    if value > 0:
        return PublicBenchmarkExpectedSignalDirection.UP.value
    if value < 0:
        return PublicBenchmarkExpectedSignalDirection.DOWN.value
    return "flat"

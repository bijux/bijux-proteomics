# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Machine-readable completeness manifests over exported result directories."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from enum import StrEnum
import hashlib
from io import StringIO
from pathlib import Path

from pydantic import ConfigDict, Field, field_validator

from bijux_proteomics.domain.reason_codes import (
    ReasonCodeCategory,
    require_registered_reason_code,
)
from bijux_proteomics.io.formats import DocumentSchema
from bijux_proteomics.ptm.reporting import PtmReportExportManifest
from bijux_proteomics.workflow.exports.interactive_result_bundle import (
    build_interactive_result_bundle_from_artifacts,
)
from bijux_proteomics.workflow.reports.biological_reporting import (
    BiologicalResultReportExportManifest,
)
from bijux_proteomics_foundation import JsonModel


class ResultManifestSourceKind(StrEnum):
    """Stable exported source families that contribute files to one manifest."""

    BIOLOGICAL_REPORT = "biological_report"
    PTM_REPORT = "ptm_report"


class ResultManifestInputKind(StrEnum):
    """Stable input families preserved on one result manifest."""

    SOURCE_REPORT_DIRECTORY = "source_report_directory"
    SOURCE_REPORT_MANIFEST = "source_report_manifest"
    RUN_QC_ASSESSMENT = "run_qc_assessment"
    LAB_ACTION_PACKET = "lab_action_packet"
    ADDITIONAL_INPUT = "additional_input"


class ResultManifestWarningSeverity(StrEnum):
    """Stable warning severities preserved on one result manifest."""

    WARNING = "warning"
    ERROR = "error"


class ResultManifestInput(JsonModel):
    """One input path preserved on a machine-readable result manifest."""

    model_config = ConfigDict(extra="forbid")

    input_id: str = Field(..., min_length=1)
    input_kind: ResultManifestInputKind
    path: str = Field(..., min_length=1)
    sha256: str | None = None
    byte_size: int | None = Field(default=None, ge=0)
    note: str = Field(..., min_length=1)


class ResultManifestCommand(JsonModel):
    """One command-line invocation associated with one result package."""

    model_config = ConfigDict(extra="forbid")

    command_id: str = Field(..., min_length=1)
    command_text: str = Field(..., min_length=1)
    note: str = Field(..., min_length=1)


class ResultManifestSourceReport(JsonModel):
    """One exported source report directory preserved on one manifest."""

    model_config = ConfigDict(extra="forbid")

    source_kind: ResultManifestSourceKind
    report_dir: str = Field(..., min_length=1)
    manifest_json: str = Field(..., min_length=1)
    artifact_count: int = Field(..., ge=0)
    required_artifact_count: int = Field(..., ge=0)


class ResultManifestFileEntry(JsonModel):
    """One expected exported output file tracked for completeness checks."""

    model_config = ConfigDict(extra="forbid")

    file_id: str = Field(..., min_length=1)
    source_kind: ResultManifestSourceKind
    artifact_key: str = Field(..., min_length=1)
    relative_path: str = Field(..., min_length=1)
    required: bool
    exists: bool
    media_type: str = Field(..., min_length=1)
    byte_size: int | None = Field(default=None, ge=0)
    sha256: str | None = None
    row_count: int | None = Field(default=None, ge=0)
    note: str = Field(..., min_length=1)


class ResultManifestWarningEntry(JsonModel):
    """One major warning preserved on a machine-readable result manifest."""

    model_config = ConfigDict(extra="forbid")

    warning_id: str = Field(..., min_length=1)
    severity: ResultManifestWarningSeverity
    warning_code: str = Field(..., min_length=1)
    source_surface: str = Field(..., min_length=1)
    entity_id: str | None = None
    related_path: str | None = None
    message: str = Field(..., min_length=1)

    @field_validator("warning_code")
    @classmethod
    def _validate_warning_code(cls, value: str) -> str:
        return require_registered_reason_code(
            value,
            ReasonCodeCategory.RESULT_WARNING,
        )


class ResultManifestSummary(JsonModel):
    """Compact completeness and entity counts over one result manifest."""

    model_config = ConfigDict(extra="forbid")

    schema_version: str = Field(..., min_length=1)
    source_report_count: int = Field(..., ge=0)
    input_count: int = Field(..., ge=0)
    command_count: int = Field(..., ge=0)
    file_count: int = Field(..., ge=0)
    existing_file_count: int = Field(..., ge=0)
    missing_required_file_count: int = Field(..., ge=0)
    warning_count: int = Field(..., ge=0)
    sample_count: int = Field(..., ge=0)
    protein_count: int = Field(..., ge=0)
    peptide_count: int = Field(..., ge=0)
    ptm_site_count: int = Field(..., ge=0)
    pathway_count: int = Field(..., ge=0)
    qc_entry_count: int = Field(..., ge=0)
    card_count: int = Field(..., ge=0)
    graph_node_count: int = Field(..., ge=0)
    graph_edge_count: int = Field(..., ge=0)
    plot_count: int = Field(..., ge=0)


class ResultManifestReport(JsonModel):
    """Machine-readable result manifest over exported report directories."""

    model_config = ConfigDict(extra="forbid")

    document_schema: DocumentSchema
    summary: ResultManifestSummary
    source_reports: tuple[ResultManifestSourceReport, ...] = Field(
        default_factory=tuple
    )
    inputs: tuple[ResultManifestInput, ...] = Field(default_factory=tuple)
    commands: tuple[ResultManifestCommand, ...] = Field(default_factory=tuple)
    files: tuple[ResultManifestFileEntry, ...] = Field(default_factory=tuple)
    warnings: tuple[ResultManifestWarningEntry, ...] = Field(default_factory=tuple)
    note: str = Field(..., min_length=1)


@dataclass(frozen=True)
class _SourceArtifactContext:
    source_kind: ResultManifestSourceKind
    report_dir: Path
    manifest_filename: str
    manifest: BiologicalResultReportExportManifest | PtmReportExportManifest
    artifact_requirements: tuple[tuple[str, bool, str | None], ...]


def build_result_manifest_from_artifacts(
    *,
    biological_report_dir: Path | None = None,
    ptm_report_dir: Path | None = None,
    run_qc_assessment_tsv_paths: tuple[Path, ...] = (),
    lab_action_packet_tsv_paths: tuple[Path, ...] = (),
    input_paths: tuple[Path, ...] = (),
    commands: tuple[str, ...],
) -> ResultManifestReport:
    """Build a machine-readable completeness manifest from exported result surfaces."""

    if not commands:
        raise ValueError(
            "result manifest requires at least one explicit workflow command string"
        )
    if (
        biological_report_dir is None
        and ptm_report_dir is None
        and not run_qc_assessment_tsv_paths
    ):
        raise ValueError(
            "result manifest requires at least one biological report, PTM report, or QC assessment input"
        )

    bundle = build_interactive_result_bundle_from_artifacts(
        biological_report_dir=biological_report_dir,
        ptm_report_dir=ptm_report_dir,
        run_qc_assessment_tsv_paths=run_qc_assessment_tsv_paths,
    )
    source_contexts = tuple(
        context
        for context in (
            _load_source_context(
                report_dir=biological_report_dir,
                source_kind=ResultManifestSourceKind.BIOLOGICAL_REPORT,
                manifest_filename="biological_report_manifest.json",
                manifest_model=BiologicalResultReportExportManifest,
            ),
            _load_source_context(
                report_dir=ptm_report_dir,
                source_kind=ResultManifestSourceKind.PTM_REPORT,
                manifest_filename="ptm_report_manifest.json",
                manifest_model=PtmReportExportManifest,
            ),
        )
        if context is not None
    )
    source_reports = tuple(
        ResultManifestSourceReport(
            source_kind=context.source_kind,
            report_dir=str(context.report_dir),
            manifest_json=context.manifest_filename,
            artifact_count=len(context.artifact_requirements) + 1,
            required_artifact_count=sum(
                1 for _, required, _ in context.artifact_requirements if required
            )
            + 1,
        )
        for context in source_contexts
    )
    inputs = _build_input_entries(
        source_contexts=source_contexts,
        run_qc_assessment_tsv_paths=run_qc_assessment_tsv_paths,
        lab_action_packet_tsv_paths=lab_action_packet_tsv_paths,
        input_paths=input_paths,
    )
    command_entries = _build_command_entries(commands)
    files = _build_file_entries(source_contexts)
    warnings = _build_warning_entries(
        source_contexts=source_contexts,
        files=files,
        run_qc_assessment_tsv_paths=run_qc_assessment_tsv_paths,
    )

    schema = _build_document_schema("result_manifest")
    report = ResultManifestReport(
        document_schema=schema,
        summary=ResultManifestSummary(
            schema_version=schema.schema_version,
            source_report_count=len(source_reports),
            input_count=len(inputs),
            command_count=len(command_entries),
            file_count=len(files),
            existing_file_count=sum(1 for entry in files if entry.exists),
            missing_required_file_count=sum(
                1 for entry in files if entry.required and not entry.exists
            ),
            warning_count=len(warnings),
            sample_count=bundle.summary.sample_count,
            protein_count=bundle.summary.protein_count,
            peptide_count=bundle.summary.peptide_count,
            ptm_site_count=bundle.summary.ptm_site_count,
            pathway_count=bundle.summary.pathway_count,
            qc_entry_count=bundle.summary.qc_entry_count,
            card_count=bundle.summary.card_count,
            graph_node_count=bundle.summary.graph_node_count,
            graph_edge_count=bundle.summary.graph_edge_count,
            plot_count=bundle.summary.plot_count,
        ),
        source_reports=source_reports,
        inputs=inputs,
        commands=command_entries,
        files=files,
        warnings=warnings,
        note=(
            "machine-readable result manifests preserve explicit source report manifests, "
            "file-level completeness, entity counts, caller-supplied command lineage, "
            "archived lab action packets, and major QC or confidence warnings so "
            "downstream tools can verify one result package automatically"
        ),
    )
    payload = report.to_dict()
    return report.model_copy(
        update={"document_schema": report.document_schema.with_content_hash(payload)}
    )


def render_result_manifest_summary_tsv(report: ResultManifestReport) -> str:
    """Render compact result-manifest summary counts as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(("field", "value"))
    for field, value in (
        ("schema_version", report.summary.schema_version),
        ("source_report_count", report.summary.source_report_count),
        ("input_count", report.summary.input_count),
        ("command_count", report.summary.command_count),
        ("file_count", report.summary.file_count),
        ("existing_file_count", report.summary.existing_file_count),
        ("missing_required_file_count", report.summary.missing_required_file_count),
        ("warning_count", report.summary.warning_count),
        ("sample_count", report.summary.sample_count),
        ("protein_count", report.summary.protein_count),
        ("peptide_count", report.summary.peptide_count),
        ("ptm_site_count", report.summary.ptm_site_count),
        ("pathway_count", report.summary.pathway_count),
        ("qc_entry_count", report.summary.qc_entry_count),
        ("card_count", report.summary.card_count),
        ("graph_node_count", report.summary.graph_node_count),
        ("graph_edge_count", report.summary.graph_edge_count),
        ("plot_count", report.summary.plot_count),
        ("note", report.note),
    ):
        writer.writerow((field, value))
    return buffer.getvalue()


def render_result_manifest_input_tsv(report: ResultManifestReport) -> str:
    """Render result-manifest inputs as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(("input_id", "input_kind", "path", "sha256", "byte_size", "note"))
    for entry in report.inputs:
        writer.writerow(
            (
                entry.input_id,
                entry.input_kind.value,
                entry.path,
                "" if entry.sha256 is None else entry.sha256,
                "" if entry.byte_size is None else entry.byte_size,
                entry.note,
            )
        )
    return buffer.getvalue()


def render_result_manifest_command_tsv(report: ResultManifestReport) -> str:
    """Render result-manifest command lineage as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(("command_id", "command_text", "note"))
    for entry in report.commands:
        writer.writerow((entry.command_id, entry.command_text, entry.note))
    return buffer.getvalue()


def render_result_manifest_file_tsv(report: ResultManifestReport) -> str:
    """Render result-manifest file completeness entries as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "file_id",
            "source_kind",
            "artifact_key",
            "relative_path",
            "required",
            "exists",
            "media_type",
            "byte_size",
            "sha256",
            "row_count",
            "note",
        )
    )
    for entry in report.files:
        writer.writerow(
            (
                entry.file_id,
                entry.source_kind.value,
                entry.artifact_key,
                entry.relative_path,
                str(entry.required).lower(),
                str(entry.exists).lower(),
                entry.media_type,
                "" if entry.byte_size is None else entry.byte_size,
                "" if entry.sha256 is None else entry.sha256,
                "" if entry.row_count is None else entry.row_count,
                entry.note,
            )
        )
    return buffer.getvalue()


def render_result_manifest_warning_tsv(report: ResultManifestReport) -> str:
    """Render result-manifest major warnings as TSV."""

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "warning_id",
            "severity",
            "warning_code",
            "source_surface",
            "entity_id",
            "related_path",
            "message",
        )
    )
    for entry in report.warnings:
        writer.writerow(
            (
                entry.warning_id,
                entry.severity.value,
                entry.warning_code,
                entry.source_surface,
                "" if entry.entity_id is None else entry.entity_id,
                "" if entry.related_path is None else entry.related_path,
                entry.message,
            )
        )
    return buffer.getvalue()


def _load_source_context(
    *,
    report_dir: Path | None,
    source_kind: ResultManifestSourceKind,
    manifest_filename: str,
    manifest_model: type[
        BiologicalResultReportExportManifest | PtmReportExportManifest
    ],
) -> _SourceArtifactContext | None:
    if report_dir is None:
        return None
    manifest_path = report_dir / manifest_filename
    if not manifest_path.exists():
        raise ValueError(
            f"{manifest_filename} is required in {report_dir} for completeness verification"
        )
    manifest = manifest_model.model_validate_json(
        manifest_path.read_text(encoding="utf-8")
    )
    artifact_model = type(manifest.artifacts)
    artifact_requirements = tuple(
        (
            field_name,
            field_info.is_required(),
            value if isinstance(value, str) and value else None,
        )
        for field_name, field_info in artifact_model.model_fields.items()
        for value in (getattr(manifest.artifacts, field_name),)
    )
    return _SourceArtifactContext(
        source_kind=source_kind,
        report_dir=report_dir,
        manifest_filename=manifest_filename,
        manifest=manifest,
        artifact_requirements=artifact_requirements,
    )


def _build_input_entries(
    *,
    source_contexts: tuple[_SourceArtifactContext, ...],
    run_qc_assessment_tsv_paths: tuple[Path, ...],
    lab_action_packet_tsv_paths: tuple[Path, ...],
    input_paths: tuple[Path, ...],
) -> tuple[ResultManifestInput, ...]:
    entries: list[ResultManifestInput] = []
    for context in source_contexts:
        entries.append(
            ResultManifestInput(
                input_id=f"input:{context.source_kind.value}:directory",
                input_kind=ResultManifestInputKind.SOURCE_REPORT_DIRECTORY,
                path=str(context.report_dir),
                sha256=None,
                byte_size=None,
                note="exported source report directory supplied for completeness verification",
            )
        )
        manifest_path = context.report_dir / context.manifest_filename
        entries.append(
            ResultManifestInput(
                input_id=f"input:{context.source_kind.value}:manifest",
                input_kind=ResultManifestInputKind.SOURCE_REPORT_MANIFEST,
                path=str(manifest_path),
                sha256=_hash_file(manifest_path),
                byte_size=manifest_path.stat().st_size,
                note="source report manifest anchors the expected artifact contract",
            )
        )
    for index, path in enumerate(run_qc_assessment_tsv_paths, start=1):
        entries.append(
            ResultManifestInput(
                input_id=f"input:run_qc:{index}",
                input_kind=ResultManifestInputKind.RUN_QC_ASSESSMENT,
                path=str(path),
                sha256=_hash_file(path),
                byte_size=path.stat().st_size,
                note="explicit QC assessment input contributes major warning extraction",
            )
        )
    for index, path in enumerate(lab_action_packet_tsv_paths, start=1):
        entries.append(
            ResultManifestInput(
                input_id=f"input:lab_action_packet:{index}",
                input_kind=ResultManifestInputKind.LAB_ACTION_PACKET,
                path=str(path),
                sha256=_hash_file(path),
                byte_size=path.stat().st_size,
                note="archived lab action packet preserves failed run or sample troubleshooting across archive handoff",
            )
        )
    for index, path in enumerate(input_paths, start=1):
        entries.append(
            ResultManifestInput(
                input_id=f"input:additional:{index}",
                input_kind=ResultManifestInputKind.ADDITIONAL_INPUT,
                path=str(path),
                sha256=_hash_file(path),
                byte_size=path.stat().st_size,
                note="additional caller-supplied workflow input preserved for downstream lineage checks",
            )
        )
    return tuple(entries)


def _build_command_entries(
    commands: tuple[str, ...],
) -> tuple[ResultManifestCommand, ...]:
    return tuple(
        ResultManifestCommand(
            command_id=f"command:{index}",
            command_text=command_text,
            note="explicit workflow or export command supplied by the caller",
        )
        for index, command_text in enumerate(commands, start=1)
    )


def _build_file_entries(
    source_contexts: tuple[_SourceArtifactContext, ...],
) -> tuple[ResultManifestFileEntry, ...]:
    entries: list[ResultManifestFileEntry] = []
    for context in source_contexts:
        manifest_path = context.report_dir / context.manifest_filename
        entries.append(
            _file_entry(
                source_kind=context.source_kind,
                artifact_key="manifest_json",
                relative_path=context.manifest_filename,
                required=True,
                path=manifest_path,
                note="source report manifest is required for completeness verification",
            )
        )
        for artifact_key, required, relative_path in context.artifact_requirements:
            if relative_path is None and not required:
                continue
            entries.append(
                _file_entry(
                    source_kind=context.source_kind,
                    artifact_key=artifact_key,
                    relative_path="" if relative_path is None else relative_path,
                    required=required,
                    path=(
                        None
                        if relative_path is None
                        else context.report_dir / relative_path
                    ),
                    note=(
                        "required artifact declared by the source report manifest"
                        if required
                        else "optional artifact declared by the source report manifest"
                    ),
                )
            )
    return tuple(
        sorted(
            entries,
            key=lambda entry: (
                entry.source_kind.value,
                entry.artifact_key,
                entry.relative_path,
            ),
        )
    )


def _file_entry(
    *,
    source_kind: ResultManifestSourceKind,
    artifact_key: str,
    relative_path: str,
    required: bool,
    path: Path | None,
    note: str,
) -> ResultManifestFileEntry:
    exists = path is not None and path.exists()
    return ResultManifestFileEntry(
        file_id=f"{source_kind.value}:{artifact_key}",
        source_kind=source_kind,
        artifact_key=artifact_key,
        relative_path=relative_path,
        required=required,
        exists=exists,
        media_type=_media_type(path, relative_path),
        byte_size=None if not exists or path is None else path.stat().st_size,
        sha256=None if not exists or path is None else _hash_file(path),
        row_count=None if not exists or path is None else _row_count(path),
        note=note,
    )


def _build_warning_entries(
    *,
    source_contexts: tuple[_SourceArtifactContext, ...],
    files: tuple[ResultManifestFileEntry, ...],
    run_qc_assessment_tsv_paths: tuple[Path, ...],
) -> tuple[ResultManifestWarningEntry, ...]:
    entries: list[ResultManifestWarningEntry] = []
    for entry in files:
        if entry.required and not entry.exists:
            entries.append(
                ResultManifestWarningEntry(
                    warning_id=f"warning:missing:{entry.file_id}",
                    severity=ResultManifestWarningSeverity.ERROR,
                    warning_code="missing_required_output",
                    source_surface="result_manifest_completeness",
                    entity_id=entry.file_id,
                    related_path=entry.relative_path,
                    message=f"required output {entry.relative_path!r} is missing",
                )
            )
    for path in run_qc_assessment_tsv_paths:
        for row in _read_tsv_rows(path):
            qc_status = row.get("qc_status", "").strip().lower()
            if qc_status not in {"fail", "failed", "block", "blocked"}:
                continue
            entity_id = row.get("entity_id") or None
            entries.append(
                ResultManifestWarningEntry(
                    warning_id=(f"warning:run_qc:{path.name}:{entity_id or 'unknown'}"),
                    severity=ResultManifestWarningSeverity.ERROR,
                    warning_code="run_qc_failure",
                    source_surface="run_qc_assessment",
                    entity_id=entity_id,
                    related_path=path.name,
                    message=row.get("message", "run QC assessment failed").strip()
                    or "run QC assessment failed",
                )
            )
    for context in source_contexts:
        if context.source_kind is not ResultManifestSourceKind.BIOLOGICAL_REPORT:
            continue
        section_path = context.report_dir / "biological_report_section_confidence.tsv"
        if not section_path.exists():
            continue
        for row in _read_tsv_rows(section_path):
            confidence = row.get("confidence_label", "").strip().lower()
            if confidence not in {"invalid", "weak"}:
                continue
            section_key = row.get("section_key") or None
            entries.append(
                ResultManifestWarningEntry(
                    warning_id=(
                        f"warning:section_confidence:{section_key or 'unknown'}"
                    ),
                    severity=(
                        ResultManifestWarningSeverity.ERROR
                        if confidence == "invalid"
                        else ResultManifestWarningSeverity.WARNING
                    ),
                    warning_code=f"section_confidence_{confidence}",
                    source_surface="biological_report_section_confidence",
                    entity_id=section_key,
                    related_path=section_path.name,
                    message=row.get("rationale", "").strip()
                    or "section confidence was downgraded",
                )
            )
    return tuple(
        sorted(
            entries,
            key=lambda entry: (
                entry.severity.value,
                entry.warning_code,
                "" if entry.entity_id is None else entry.entity_id,
            ),
        )
    )


def _build_document_schema(document_kind: str) -> DocumentSchema:
    return DocumentSchema(
        created_by="bijux-proteomics-core",
        document_kind=document_kind,
        package_name="bijux-proteomics-core",
        status="generated",
    )


def _hash_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _media_type(path: Path | None, relative_path: str) -> str:
    suffix = (path.suffix if path is not None else Path(relative_path).suffix).lower()
    if suffix == ".tsv":
        return "text/tab-separated-values"
    if suffix == ".json":
        return "application/json"
    if suffix == ".html":
        return "text/html"
    if suffix == ".svg":
        return "image/svg+xml"
    return "application/octet-stream"


def _row_count(path: Path) -> int | None:
    if path.suffix.lower() != ".tsv":
        return None
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle, delimiter="\t")
        try:
            next(reader)
        except StopIteration:
            return 0
        return sum(1 for _ in reader)


def _read_tsv_rows(path: Path) -> tuple[dict[str, str], ...]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return tuple(csv.DictReader(handle, delimiter="\t"))


__all__ = [
    "ResultManifestCommand",
    "ResultManifestFileEntry",
    "ResultManifestInput",
    "ResultManifestInputKind",
    "ResultManifestReport",
    "ResultManifestSourceKind",
    "ResultManifestSourceReport",
    "ResultManifestSummary",
    "ResultManifestWarningEntry",
    "ResultManifestWarningSeverity",
    "build_result_manifest_from_artifacts",
    "render_result_manifest_command_tsv",
    "render_result_manifest_file_tsv",
    "render_result_manifest_input_tsv",
    "render_result_manifest_summary_tsv",
    "render_result_manifest_warning_tsv",
]

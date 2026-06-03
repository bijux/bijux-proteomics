# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""mzML, format-detection, and normalized run-bundle contracts."""

from __future__ import annotations

from enum import StrEnum
import hashlib
import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

from pydantic import ConfigDict, Field, field_validator, model_validator

from bijux_proteomics._scientific_tables import (
    ScientificTableValidationIssue,
    build_experimental_design_schema,
    validate_scientific_table,
)
from bijux_proteomics._tabular import DelimitedTableIssue
from bijux_proteomics.chemistry import load_modification_registry
from bijux_proteomics.domain.records import (
    Contrast,
    ContrastKind,
)
from bijux_proteomics.domain.records import (
    RejectedEvidence as CanonicalRejectedEvidence,
)
from bijux_proteomics.domain.records import (
    SampleMetadata as CanonicalSampleMetadata,
)
from bijux_proteomics.io.formats.format_validation import FormatValidationIssue
from bijux_proteomics.io.raw.mzml_reader import (
    MzmlChromatogramPoint as _MzmlChromatogramPoint,
)
from bijux_proteomics.io.raw.mzml_reader import (
    MzmlChromatogramReport as _MzmlChromatogramReport,
)
from bijux_proteomics.io.raw.mzml_reader import (
    MzmlChromatogramTrace as _MzmlChromatogramTrace,
)
from bijux_proteomics.io.raw.mzml_reader import (
    MzmlParseReport as _MzmlParseReport,
)
from bijux_proteomics.io.raw.mzml_reader import (
    MzmlRunMetadata as _MzmlRunMetadata,
)
from bijux_proteomics.io.raw.mzml_reader import (
    RejectedMzmlChromatogram as _RejectedMzmlChromatogram,
)
from bijux_proteomics.io.raw.mzml_reader import (
    RejectedMzmlSpectrum as _RejectedMzmlSpectrum,
)
from bijux_proteomics.io.raw.mzml_reader import (
    build_mzml_collection_summary as _build_mzml_collection_summary,
)
from bijux_proteomics.io.raw.mzml_reader import (
    extract_mzml_chromatograms as _extract_mzml_chromatograms,
)
from bijux_proteomics.io.raw.mzml_reader import (
    extract_mzml_metadata as _extract_mzml_metadata,
)
from bijux_proteomics.io.raw.mzml_reader import (
    parse_mzml as _parse_mzml,
)
from bijux_proteomics.io.raw.mzml_reader import (
    stream_mzml_spectra as _stream_mzml_spectra,
)
from bijux_proteomics.io.spectra import (
    MgfParseReport,
    SpectrumModel,
    build_spectrum_collection_summary,
    parse_mgf,
    render_mgf,
)
from bijux_proteomics.sequences import FastaParseMode, parse_fasta_document
from bijux_proteomics_foundation import DocumentSchema, JsonModel

if TYPE_CHECKING:
    from bijux_proteomics.identification.contracts import SearchResultColumnMapping

_NS_MZML = "http://psi.hupo.org/ms/mzml"

MzmlChromatogramPoint = _MzmlChromatogramPoint
MzmlChromatogramReport = _MzmlChromatogramReport
MzmlChromatogramTrace = _MzmlChromatogramTrace
MzmlParseReport = _MzmlParseReport
MzmlRunMetadata = _MzmlRunMetadata
RejectedMzmlChromatogram = _RejectedMzmlChromatogram
RejectedMzmlSpectrum = _RejectedMzmlSpectrum
build_mzml_collection_summary = _build_mzml_collection_summary
extract_mzml_chromatograms = _extract_mzml_chromatograms
extract_mzml_metadata = _extract_mzml_metadata
parse_mzml = _parse_mzml
stream_mzml_spectra = _stream_mzml_spectra


class ProteomicsFormatKind(StrEnum):
    """Supported top-level proteomics input kinds."""

    FASTA = "fasta"
    PSM = "psm"
    MGF = "mgf"
    MZML = "mzml"
    MOD_REGISTRY = "mod-registry"
    DESIGN_TABLE = "design-table"


class ExperimentalDesignSampleRole(StrEnum):
    """Stable sample role carried by a design-table row."""

    SAMPLE = "sample"
    POOLED_REFERENCE = "pooled_reference"
    QC_BRIDGE = "qc_bridge"


class ExperimentalDesignEntry(JsonModel):
    """One normalized experimental-design row."""

    model_config = ConfigDict(extra="forbid")

    sample_id: str = Field(..., min_length=1)
    cohort: str | None = None
    condition: str = Field(..., min_length=1)
    replicate: int = Field(..., ge=1)
    fraction: int = Field(..., ge=1)
    spectra_file: str = Field(..., min_length=1)
    identifications_file: str | None = None
    batch: str | None = None
    instrument: str | None = None
    search_engine: str | None = None
    pair_id: str | None = None
    run_order: int | None = Field(default=None, ge=1)
    technical_replicate_id: str | None = None
    multiplex_group: str | None = None
    multiplex_channel: str | None = None
    sample_role: ExperimentalDesignSampleRole = ExperimentalDesignSampleRole.SAMPLE
    metadata: dict[str, str] = Field(default_factory=dict)

    @field_validator(
        "sample_id",
        "cohort",
        "condition",
        "spectra_file",
        "identifications_file",
        "batch",
        "instrument",
        "search_engine",
        "pair_id",
        "technical_replicate_id",
        "multiplex_group",
        "multiplex_channel",
        mode="before",
    )
    @classmethod
    def _strip_text(cls, value: object) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        return text or None

    @model_validator(mode="after")
    def _validate_multiplex_semantics(self) -> ExperimentalDesignEntry:
        if bool(self.multiplex_group) != bool(self.multiplex_channel):
            raise ValueError(
                "multiplex_group and multiplex_channel must both be present when either is provided"
            )
        if (
            self.sample_role is not ExperimentalDesignSampleRole.SAMPLE
            and not self.multiplex_channel
        ):
            raise ValueError(
                "non-sample multiplex roles require explicit multiplex_group and multiplex_channel"
            )
        return self

    def to_domain_record(self) -> CanonicalSampleMetadata:
        """Convert one design-table row into canonical sample metadata."""

        return CanonicalSampleMetadata(
            sample_id=self.sample_id,
            run_id=self.spectra_file,
            condition=self.condition,
            replicate=self.replicate,
            fraction=self.fraction,
            batch=self.batch,
            pair_id=self.pair_id,
            run_order=self.run_order,
            technical_replicate_id=self.technical_replicate_id,
            plex_id=self.multiplex_group,
            channel=self.multiplex_channel,
            sample_role=self.sample_role.value,
            cohort=self.cohort,
            instrument=self.instrument,
            search_engine=self.search_engine,
            metadata=self.metadata,
        )


class ExperimentalDesignRejectedRow(JsonModel):
    """One rejected design-table row."""

    model_config = ConfigDict(extra="forbid")

    row_number: int = Field(..., ge=1)
    values: dict[str, str] = Field(default_factory=dict)
    issues: tuple[FormatValidationIssue, ...] = Field(default_factory=tuple)

    def to_domain_record(self) -> CanonicalRejectedEvidence:
        """Expose one rejected design row as canonical rejected evidence."""

        return CanonicalRejectedEvidence(
            record_kind="sample_metadata",
            rejection_reason="; ".join(issue.message for issue in self.issues)
            or "rejected design row",
            row_number=self.row_number,
            raw_fields=self.values,
            metadata={
                "source_contract": "io.experimental_design_rejected_row",
                "issue_codes": ";".join(issue.code for issue in self.issues),
            },
        )


class ExperimentalDesignReport(JsonModel):
    """Stable parse report for one experimental-design table."""

    model_config = ConfigDict(extra="forbid")

    accepted_entries: tuple[ExperimentalDesignEntry, ...] = Field(default_factory=tuple)
    rejected_rows: tuple[ExperimentalDesignRejectedRow, ...] = Field(
        default_factory=tuple
    )


def build_pairwise_contrast_record(
    *,
    left_condition: str,
    right_condition: str,
    kind: ContrastKind = ContrastKind.PAIRWISE,
    pair_id_field: str | None = None,
    metadata: dict[str, str] | None = None,
) -> Contrast:
    """Build one canonical pairwise contrast record for workflow exchange."""

    from bijux_proteomics.study.contrasts import (
        build_case_control_contrast,
        build_paired_contrast,
        build_pairwise_contrast,
    )

    if kind is ContrastKind.CASE_CONTROL:
        return build_case_control_contrast(
            case_condition=left_condition,
            control_condition=right_condition,
            metadata=metadata,
        )
    if kind is ContrastKind.PAIRED:
        return build_paired_contrast(
            left_condition=left_condition,
            right_condition=right_condition,
            pair_id_field=pair_id_field or "pair_id",
            metadata=metadata,
        )
    return build_pairwise_contrast(
        left_condition=left_condition,
        right_condition=right_condition,
        metadata=metadata,
    )


class ProteomicsRunMetadata(JsonModel):
    """Harmonized metadata for one normalized proteomics run."""

    model_config = ConfigDict(extra="forbid")

    sample_id: str | None = None
    condition: str | None = None
    replicate: int | None = Field(default=None, ge=1)
    fraction: int | None = Field(default=None, ge=1)
    batch: str | None = None
    instrument: str | None = None
    search_engine: str | None = None
    run_id: str | None = None
    acquisition_start_time_iso: str | None = None
    spectra_format: ProteomicsFormatKind | None = None
    identification_format: ProteomicsFormatKind | None = None
    spectra_source_path: str | None = None
    identifications_source_path: str | None = None


class SourceFileManifestEntry(JsonModel):
    """Stable source-file record for a normalized run bundle."""

    model_config = ConfigDict(extra="forbid")

    path: str = Field(..., min_length=1)
    detected_format: ProteomicsFormatKind
    sha256: str = Field(..., min_length=64, max_length=64)


class NormalizedRunBundleManifest(JsonModel):
    """Stable manifest for one normalized proteomics run bundle."""

    model_config = ConfigDict(extra="forbid")

    document_schema: DocumentSchema
    metadata: ProteomicsRunMetadata
    source_files: tuple[SourceFileManifestEntry, ...] = Field(default_factory=tuple)
    generated_files: tuple[str, ...] = Field(default_factory=tuple)
    spectrum_count: int = Field(..., ge=0)
    psm_count: int = Field(..., ge=0)
    rejected_spectra: int = Field(..., ge=0)
    rejected_identification_rows: int = Field(..., ge=0)


class FormatValidationReport(JsonModel):
    """Stable validation report for one detected proteomics input."""

    model_config = ConfigDict(extra="forbid")

    input_path: str = Field(..., min_length=1)
    detected_format: ProteomicsFormatKind
    valid: bool
    issues: tuple[FormatValidationIssue, ...] = Field(default_factory=tuple)
    summary: dict[str, Any] = Field(default_factory=dict)


class FormatDetectionDiagnostic(JsonModel):
    """Stable detection report for supported and unsupported proteomics inputs."""

    model_config = ConfigDict(extra="forbid")

    input_path: str = Field(..., min_length=1)
    detected_format: ProteomicsFormatKind | None = None
    supported: bool
    reasons: tuple[str, ...] = Field(default_factory=tuple)


class FormatConversionTarget(StrEnum):
    """Supported normalized conversion targets."""

    MGF = "mgf"
    SPECTRA_JSONL = "spectra-jsonl"
    PSM_JSONL = "psm-jsonl"
    DESIGN_JSONL = "design-jsonl"


class FormatConversionReport(JsonModel):
    """Stable report for one conversion operation."""

    model_config = ConfigDict(extra="forbid")

    input_path: str = Field(..., min_length=1)
    output_path: str = Field(..., min_length=1)
    input_format: ProteomicsFormatKind
    target_format: FormatConversionTarget
    written_record_count: int = Field(..., ge=0)


def _strip_text(value: str | None) -> str | None:
    if value is None:
        return None
    text = value.strip()
    return text or None


def _issue(
    code: str,
    message: str,
    *,
    field: str | None = None,
    line_number: int | None = None,
    record_id: str | None = None,
) -> FormatValidationIssue:
    return FormatValidationIssue(
        code=code,
        message=message,
        field=field,
        line_number=line_number,
        record_id=record_id,
    )


def _design_issues_from_table_issues(
    issues: tuple[DelimitedTableIssue, ...],
) -> tuple[FormatValidationIssue, ...]:
    translated: list[FormatValidationIssue] = []
    for issue in issues:
        if issue.code == "missing_required_column":
            translated.append(
                _issue(
                    "missing_design_column",
                    f"design table is missing required column {issue.column!r}",
                    field=issue.column,
                    line_number=issue.row_number,
                )
            )
            continue
        if issue.code == "missing_required_value":
            translated.append(
                _issue(
                    "missing_design_value",
                    f"design table row is missing required value for {issue.column!r}",
                    field=issue.column,
                    line_number=issue.row_number,
                )
            )
            continue
        translated.append(
            _issue(
                "invalid_design_row",
                issue.message,
                field=issue.column,
                line_number=issue.row_number,
            )
        )
    return tuple(translated)


def _design_issues_from_scientific_issues(
    issues: tuple[ScientificTableValidationIssue, ...],
) -> tuple[FormatValidationIssue, ...]:
    translated: list[FormatValidationIssue] = []
    for issue in issues:
        if issue.code == "missing_column":
            translated.append(
                _issue(
                    "missing_design_column",
                    f"design table is missing required column {issue.column!r}",
                    field=issue.column,
                    line_number=issue.row_number,
                )
            )
            continue
        if issue.code == "missing_value":
            translated.append(
                _issue(
                    "missing_design_value",
                    f"design table row is missing required value for {issue.column!r}",
                    field=issue.column,
                    line_number=issue.row_number,
                )
            )
            continue
        if issue.code == "duplicate_identifier":
            translated.append(
                _issue(
                    "duplicate_design_identifier",
                    issue.message,
                    field=issue.column,
                    line_number=issue.row_number,
                )
            )
            continue
        translated.append(
            _issue(
                "invalid_design_row",
                issue.message,
                field=issue.column,
                line_number=issue.row_number,
            )
        )
    return tuple(translated)


def _render_design_row_values(
    values: dict[str, str | int | float | bool | None],
    extra_values: dict[str, str],
) -> dict[str, str]:
    rendered = dict(extra_values)
    for key, value in values.items():
        rendered[key] = "" if value is None else str(value)
    return rendered


def _optional_design_text(value: str | int | float | bool | None) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _optional_design_int(value: str | int | float | bool | None) -> int | None:
    text = _optional_design_text(value)
    if text is None:
        return None
    return int(text)


def _default_psm_mapping() -> SearchResultColumnMapping:
    from bijux_proteomics.identification.contracts import SearchResultColumnMapping

    return SearchResultColumnMapping(
        spectrum_id="spectrum_id",
        peptide="peptide",
        charge="charge",
        score="score",
        q_value=None,
        protein_refs="proteins",
    )


def _first_bytes_text(path: Path, limit: int = 4096) -> str:
    return path.read_bytes()[:limit].decode("utf-8", errors="ignore")


def _detect_delimiter(first_line: str) -> str:
    return "\t" if "\t" in first_line else ","


def _hash_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _source_file_entry(
    path: Path, detected_format: ProteomicsFormatKind
) -> SourceFileManifestEntry:
    return SourceFileManifestEntry(
        path=str(path),
        detected_format=detected_format,
        sha256=_hash_file(path),
    )


def _build_document_schema(document_kind: str) -> DocumentSchema:
    return DocumentSchema(
        created_by="bijux-proteomics-core",
        document_kind=document_kind,
        package_name="bijux-proteomics-core",
        status="generated",
    )


def export_spectra_jsonl(spectra: tuple[SpectrumModel, ...], path: Path) -> None:
    """Write normalized spectra as stable JSONL."""
    with path.open("w", encoding="utf-8") as handle:
        for spectrum in spectra:
            handle.write(
                json.dumps(spectrum.to_dict(), sort_keys=True, separators=(",", ":"))
            )
            handle.write("\n")


def detect_proteomics_format(path: Path) -> ProteomicsFormatKind:
    """Detect the most likely proteomics format from file name and content."""
    diagnostic = diagnose_proteomics_format(path)
    if diagnostic.detected_format is None:
        raise ValueError(
            f"unsupported proteomics format for {path.name!r}: {'; '.join(diagnostic.reasons)}"
        )
    return diagnostic.detected_format


def diagnose_proteomics_format(path: Path) -> FormatDetectionDiagnostic:
    """Explain what was detected in one input path and why classification succeeded or failed."""
    suffix = path.suffix.lower()
    reasons: list[str] = []
    if suffix in {".fasta", ".fa", ".faa"}:
        return FormatDetectionDiagnostic(
            input_path=str(path),
            detected_format=ProteomicsFormatKind.FASTA,
            supported=True,
            reasons=(f"matched FASTA suffix {suffix}",),
        )
    if suffix == ".mgf":
        return FormatDetectionDiagnostic(
            input_path=str(path),
            detected_format=ProteomicsFormatKind.MGF,
            supported=True,
            reasons=("matched MGF suffix .mgf",),
        )
    if suffix == ".mzml":
        return FormatDetectionDiagnostic(
            input_path=str(path),
            detected_format=ProteomicsFormatKind.MZML,
            supported=True,
            reasons=("matched mzML suffix .mzml",),
        )
    if path.name.endswith(".design.tsv") or path.name.endswith(".design.csv"):
        return FormatDetectionDiagnostic(
            input_path=str(path),
            detected_format=ProteomicsFormatKind.DESIGN_TABLE,
            supported=True,
            reasons=("matched experimental design file name pattern",),
        )
    text = _first_bytes_text(path)
    stripped = text.lstrip()
    if "<mzML" in text or f"{{{_NS_MZML}}}" in text:
        return FormatDetectionDiagnostic(
            input_path=str(path),
            detected_format=ProteomicsFormatKind.MZML,
            supported=True,
            reasons=("matched mzML XML root content",),
        )
    if stripped.startswith("BEGIN IONS"):
        return FormatDetectionDiagnostic(
            input_path=str(path),
            detected_format=ProteomicsFormatKind.MGF,
            supported=True,
            reasons=("matched MGF block preamble",),
        )
    if stripped.startswith(">"):
        return FormatDetectionDiagnostic(
            input_path=str(path),
            detected_format=ProteomicsFormatKind.FASTA,
            supported=True,
            reasons=("matched FASTA record prefix",),
        )
    if suffix == ".json" and (
        '"static_modifications"' in text or '"variable_modifications"' in text
    ):
        return FormatDetectionDiagnostic(
            input_path=str(path),
            detected_format=ProteomicsFormatKind.MOD_REGISTRY,
            supported=True,
            reasons=("matched modification registry JSON fields",),
        )
    header = stripped.splitlines()[0] if stripped.splitlines() else ""
    header_columns = {
        column.strip()
        for column in header.split(_detect_delimiter(header))
        if column.strip()
    }
    if {"sample_id", "condition", "replicate", "fraction", "spectra_file"}.issubset(
        header_columns
    ):
        return FormatDetectionDiagnostic(
            input_path=str(path),
            detected_format=ProteomicsFormatKind.DESIGN_TABLE,
            supported=True,
            reasons=("matched experimental design header columns",),
        )
    if {"spectrum_id", "peptide", "charge", "score"}.issubset(header_columns):
        return FormatDetectionDiagnostic(
            input_path=str(path),
            detected_format=ProteomicsFormatKind.PSM,
            supported=True,
            reasons=("matched PSM header columns",),
        )
    if suffix:
        reasons.append(f"suffix {suffix!r} is not a supported proteomics input")
    if stripped.startswith("<"):
        reasons.append("XML content did not match an mzML root")
    elif header_columns:
        reasons.append(
            "tabular header did not match supported PSM or design-table columns"
        )
    else:
        reasons.append(
            "content did not match supported FASTA, MGF, mzML, JSON, or table signatures"
        )
    return FormatDetectionDiagnostic(
        input_path=str(path),
        detected_format=None,
        supported=False,
        reasons=tuple(reasons),
    )


def parse_experimental_design_table(path: Path) -> ExperimentalDesignReport:
    """Parse one experimental-design TSV or CSV table.

    Inputs:
    ``path`` must point to a governed experimental-design delimited file with
    the owned design schema columns.

    Outputs:
    Returns one ``ExperimentalDesignReport`` with accepted design entries and
    rejected rows annotated with row-level issues.

    Failure Modes:
    Propagates filesystem read failures and accumulates invalid row conversion
    problems into rejected-row issues instead of raising one exception per row.

    Scientific Caveats:
    A parsed design report captures structural and field-level validity only; it
    does not prove that file references exist, that cohorts are scientifically
    balanced, or that declared metadata match acquisition reality.
    """
    validation_report = validate_scientific_table(
        path,
        schema=build_experimental_design_schema(),
    )
    accepted_entries: list[ExperimentalDesignEntry] = []
    owned_fields = {
        "sample_id",
        "cohort",
        "condition",
        "replicate",
        "fraction",
        "spectra_file",
        "identifications_file",
        "batch",
        "instrument",
        "search_engine",
        "pair_id",
        "run_order",
        "technical_replicate_id",
        "multiplex_group",
        "multiplex_channel",
        "sample_role",
    }
    rejected_rows = [
        ExperimentalDesignRejectedRow(
            row_number=row.row_number,
            values=row.raw_values,
            issues=_design_issues_from_scientific_issues(row.issues),
        )
        for row in validation_report.rejected_rows
    ]

    for row in validation_report.accepted_rows:
        values = _render_design_row_values(row.values, row.extra_values)
        try:
            sample_role_value = (
                row.values.get("sample_role")
                or ExperimentalDesignSampleRole.SAMPLE.value
            )
            entry = ExperimentalDesignEntry(
                sample_id=str(row.values.get("sample_id") or ""),
                cohort=_optional_design_text(row.values.get("cohort")),
                condition=str(row.values.get("condition") or ""),
                replicate=int(row.values.get("replicate") or 0),
                fraction=int(row.values.get("fraction") or 0),
                spectra_file=str(row.values.get("spectra_file") or ""),
                identifications_file=_optional_design_text(
                    row.values.get("identifications_file")
                ),
                batch=_optional_design_text(row.values.get("batch")),
                instrument=_optional_design_text(row.values.get("instrument")),
                search_engine=_optional_design_text(row.values.get("search_engine")),
                pair_id=_optional_design_text(row.values.get("pair_id")),
                run_order=_optional_design_int(row.values.get("run_order")),
                technical_replicate_id=_optional_design_text(
                    row.values.get("technical_replicate_id")
                ),
                multiplex_group=_optional_design_text(
                    row.values.get("multiplex_group")
                ),
                multiplex_channel=_optional_design_text(
                    row.values.get("multiplex_channel")
                ),
                sample_role=ExperimentalDesignSampleRole(str(sample_role_value)),
                metadata={
                    key: value
                    for key, value in values.items()
                    if key not in owned_fields and value
                },
            )
        except Exception as exc:  # noqa: BLE001
            rejected_rows.append(
                ExperimentalDesignRejectedRow(
                    row_number=row.row_number,
                    values=values,
                    issues=(
                        _issue(
                            "invalid_design_row",
                            str(exc),
                            line_number=row.row_number,
                        ),
                    ),
                )
            )
            continue
        accepted_entries.append(entry)
    return ExperimentalDesignReport(
        accepted_entries=tuple(accepted_entries),
        rejected_rows=tuple(rejected_rows),
    )


def harmonize_run_metadata(
    *,
    mzml_metadata: MzmlRunMetadata | None = None,
    design_entry: ExperimentalDesignEntry | None = None,
    spectra_format: ProteomicsFormatKind | None = None,
    identification_format: ProteomicsFormatKind | None = None,
    spectra_source_path: Path | None = None,
    identifications_source_path: Path | None = None,
) -> ProteomicsRunMetadata:
    """Build one harmonized run metadata document."""
    return ProteomicsRunMetadata(
        sample_id=design_entry.sample_id if design_entry is not None else None,
        condition=design_entry.condition if design_entry is not None else None,
        replicate=design_entry.replicate if design_entry is not None else None,
        fraction=design_entry.fraction if design_entry is not None else None,
        batch=design_entry.batch if design_entry is not None else None,
        instrument=(
            design_entry.instrument
            if design_entry is not None and design_entry.instrument is not None
            else (
                mzml_metadata.instrument_names[0]
                if mzml_metadata and mzml_metadata.instrument_names
                else None
            )
        ),
        search_engine=design_entry.search_engine if design_entry is not None else None,
        run_id=mzml_metadata.run_id if mzml_metadata is not None else None,
        acquisition_start_time_iso=mzml_metadata.start_time_iso
        if mzml_metadata is not None
        else None,
        spectra_format=spectra_format,
        identification_format=identification_format,
        spectra_source_path=str(spectra_source_path)
        if spectra_source_path is not None
        else None,
        identifications_source_path=(
            str(identifications_source_path)
            if identifications_source_path is not None
            else None
        ),
    )


def validate_proteomics_input(
    path: Path,
    *,
    input_kind: ProteomicsFormatKind | None = None,
) -> FormatValidationReport:
    """Validate one proteomics input under a detected or declared format kind."""
    resolved_kind = input_kind or detect_proteomics_format(path)
    issues: list[FormatValidationIssue] = []
    summary: dict[str, Any] = {}
    if resolved_kind is ProteomicsFormatKind.FASTA:
        fasta_report = parse_fasta_document(
            path.read_text(), mode=FastaParseMode.STRICT
        )
        for rejected_record in fasta_report.rejected_records:
            issues.append(
                _issue(
                    "rejected_fasta_record",
                    "; ".join(issue.message for issue in rejected_record.issues),
                    record_id=rejected_record.source_identifier,
                )
            )
        summary = {
            "accepted_records": len(fasta_report.accepted_records),
            "rejected_records": len(fasta_report.rejected_records),
        }
    elif resolved_kind is ProteomicsFormatKind.PSM:
        from bijux_proteomics.identification.contracts import parse_psm_tsv

        psm_report = parse_psm_tsv(path, mapping=_default_psm_mapping())
        for rejected_row in psm_report.rejected_rows:
            issues.append(
                _issue(
                    "rejected_psm_row",
                    "; ".join(issue.message for issue in rejected_row.issues),
                    line_number=rejected_row.row_number,
                )
            )
        summary = {
            "accepted_rows": len(psm_report.accepted_records),
            "rejected_rows": len(psm_report.rejected_rows),
        }
    elif resolved_kind is ProteomicsFormatKind.MGF:
        mgf_report: MgfParseReport = parse_mgf(path)
        for block in mgf_report.rejected_blocks:
            for issue in block.issues:
                issues.append(
                    _issue(
                        issue.code,
                        issue.message,
                        field=issue.field,
                        line_number=issue.line_number,
                        record_id=block.title or f"block-{block.block_index}",
                    )
                )
        summary = build_spectrum_collection_summary(mgf_report).to_dict()
    elif resolved_kind is ProteomicsFormatKind.MZML:
        mzml_report = parse_mzml(path)
        for rejected_spectrum in mzml_report.rejected_spectra:
            issues.extend(rejected_spectrum.issues)
        summary = {
            "metadata": mzml_report.metadata.to_dict(),
            "summary": build_mzml_collection_summary(mzml_report).to_dict(),
        }
    elif resolved_kind is ProteomicsFormatKind.MOD_REGISTRY:
        registry = load_modification_registry(path)
        summary = {
            "static_modifications": len(registry.static_modifications),
            "variable_modifications": len(registry.variable_modifications),
        }
    else:
        design_report = parse_experimental_design_table(path)
        for design_rejected_row in design_report.rejected_rows:
            issues.extend(design_rejected_row.issues)
        summary = {
            "accepted_entries": len(design_report.accepted_entries),
            "rejected_rows": len(design_report.rejected_rows),
        }
    return FormatValidationReport(
        input_path=str(path),
        detected_format=resolved_kind,
        valid=len(issues) == 0,
        issues=tuple(issues),
        summary=summary,
    )


def convert_proteomics_format(
    *,
    input_path: Path,
    output_path: Path,
    input_kind: ProteomicsFormatKind | None = None,
    target_format: FormatConversionTarget,
) -> FormatConversionReport:
    """Convert one supported input into a normalized Bijux output table."""
    resolved_kind = input_kind or detect_proteomics_format(input_path)
    if target_format is FormatConversionTarget.MGF:
        if resolved_kind is not ProteomicsFormatKind.MZML:
            raise ValueError("mgf conversion currently supports only mzML input")
        report = parse_mzml(input_path)
        output_path.write_text(render_mgf(report.accepted_spectra), encoding="utf-8")
        written_record_count = len(report.accepted_spectra)
    elif target_format is FormatConversionTarget.SPECTRA_JSONL:
        if resolved_kind is ProteomicsFormatKind.MZML:
            spectra = parse_mzml(input_path).accepted_spectra
        elif resolved_kind is ProteomicsFormatKind.MGF:
            spectra = parse_mgf(input_path).accepted_spectra
        else:
            raise ValueError("spectra-jsonl conversion requires mzML or MGF input")
        export_spectra_jsonl(spectra, output_path)
        written_record_count = len(spectra)
    elif target_format is FormatConversionTarget.PSM_JSONL:
        from bijux_proteomics.identification.contracts import (
            export_psm_jsonl,
            parse_psm_tsv,
        )

        if resolved_kind is not ProteomicsFormatKind.PSM:
            raise ValueError("psm-jsonl conversion requires PSM TSV input")
        records = parse_psm_tsv(
            input_path, mapping=_default_psm_mapping()
        ).accepted_records
        export_psm_jsonl(records, output_path)
        written_record_count = len(records)
    else:
        if resolved_kind is not ProteomicsFormatKind.DESIGN_TABLE:
            raise ValueError("design-jsonl conversion requires a design-table input")
        design_report = parse_experimental_design_table(input_path)
        with output_path.open("w", encoding="utf-8") as handle:
            for entry in design_report.accepted_entries:
                handle.write(
                    json.dumps(entry.to_dict(), sort_keys=True, separators=(",", ":"))
                )
                handle.write("\n")
        written_record_count = len(design_report.accepted_entries)
    return FormatConversionReport(
        input_path=str(input_path),
        output_path=str(output_path),
        input_format=resolved_kind,
        target_format=target_format,
        written_record_count=written_record_count,
    )


def build_normalized_run_bundle(
    *,
    bundle_dir: Path,
    spectra_path: Path,
    identifications_path: Path | None = None,
    design_path: Path | None = None,
) -> NormalizedRunBundleManifest:
    """Build one normalized run bundle directory with spectra, IDs, and metadata.

    Inputs:
    ``bundle_dir`` is the output directory, ``spectra_path`` must reference mzML
    or MGF input, and ``identifications_path`` plus ``design_path`` optionally
    add governed identification and design metadata inputs.

    Outputs:
    Returns one ``NormalizedRunBundleManifest`` after writing normalized spectra,
    validation artifacts, optional identification exports, and metadata sidecars
    into the bundle directory.

    Failure Modes:
    Raises ``ValueError`` for unsupported spectra or identification formats and
    propagates filesystem, parsing, and export failures while building bundle
    artifacts.

    Scientific Caveats:
    The bundle normalizes owned file formats and validation summaries only; it
    does not rescue low-quality spectra, repair misassigned PSMs, or certify one
    run as scientifically trustworthy.
    """
    bundle_dir.mkdir(parents=True, exist_ok=True)
    spectra_kind = detect_proteomics_format(spectra_path)
    if spectra_kind not in {ProteomicsFormatKind.MGF, ProteomicsFormatKind.MZML}:
        raise ValueError("run bundle spectra input must be mzML or MGF")

    generated_files: list[str] = []
    source_files: list[SourceFileManifestEntry] = [
        _source_file_entry(spectra_path, spectra_kind)
    ]
    rejected_spectra = 0
    mzml_metadata: MzmlRunMetadata | None = None

    if spectra_kind is ProteomicsFormatKind.MZML:
        spectra_report = parse_mzml(spectra_path)
        accepted_spectra = spectra_report.accepted_spectra
        rejected_spectra = len(spectra_report.rejected_spectra)
        mzml_metadata = spectra_report.metadata
    else:
        mgf_report = parse_mgf(spectra_path)
        accepted_spectra = mgf_report.accepted_spectra
        rejected_spectra = len(mgf_report.rejected_blocks)

    spectra_output_path = bundle_dir / "spectra.normalized.mgf"
    spectra_output_path.write_text(render_mgf(accepted_spectra), encoding="utf-8")
    generated_files.append(spectra_output_path.name)

    spectra_validation_path = bundle_dir / "spectra.validation.json"
    spectra_validation = validate_proteomics_input(
        spectra_path, input_kind=spectra_kind
    )
    spectra_validation_path.write_text(
        spectra_validation.to_stable_json() + "\n", encoding="utf-8"
    )
    generated_files.append(spectra_validation_path.name)

    psm_count = 0
    rejected_identification_rows = 0
    identification_kind: ProteomicsFormatKind | None = None
    if identifications_path is not None:
        from bijux_proteomics.identification.contracts import (
            build_psm_summary_report,
            export_psm_jsonl,
            parse_psm_tsv,
        )

        identification_kind = detect_proteomics_format(identifications_path)
        if identification_kind is not ProteomicsFormatKind.PSM:
            raise ValueError(
                "run bundle identification input must be a normalized or generic PSM TSV"
            )
        source_files.append(
            _source_file_entry(identifications_path, identification_kind)
        )
        psm_report = parse_psm_tsv(identifications_path, mapping=_default_psm_mapping())
        psm_count = len(psm_report.accepted_records)
        rejected_identification_rows = len(psm_report.rejected_rows)
        psm_output_path = bundle_dir / "identifications.normalized.jsonl"
        export_psm_jsonl(psm_report.accepted_records, psm_output_path)
        generated_files.append(psm_output_path.name)
        psm_summary_path = bundle_dir / "identifications.summary.json"
        psm_summary = build_psm_summary_report(psm_report.accepted_records)
        psm_summary_path.write_text(
            psm_summary.to_stable_json() + "\n", encoding="utf-8"
        )
        generated_files.append(psm_summary_path.name)

    design_entry: ExperimentalDesignEntry | None = None
    if design_path is not None:
        design_kind = detect_proteomics_format(design_path)
        if design_kind is not ProteomicsFormatKind.DESIGN_TABLE:
            raise ValueError("run bundle design input must be a design table")
        source_files.append(_source_file_entry(design_path, design_kind))
        design_report = parse_experimental_design_table(design_path)
        if design_report.accepted_entries:
            design_entry = design_report.accepted_entries[0]
        design_output_path = bundle_dir / "design.normalized.jsonl"
        with design_output_path.open("w", encoding="utf-8") as handle:
            for entry in design_report.accepted_entries:
                handle.write(
                    json.dumps(entry.to_dict(), sort_keys=True, separators=(",", ":"))
                )
                handle.write("\n")
        generated_files.append(design_output_path.name)

    metadata = harmonize_run_metadata(
        mzml_metadata=mzml_metadata,
        design_entry=design_entry,
        spectra_format=spectra_kind,
        identification_format=identification_kind,
        spectra_source_path=spectra_path,
        identifications_source_path=identifications_path,
    )
    metadata_path = bundle_dir / "run.metadata.json"
    metadata_path.write_text(metadata.to_stable_json() + "\n", encoding="utf-8")
    generated_files.append(metadata_path.name)

    schema = _build_document_schema("normalized_proteomics_run_bundle")
    manifest = NormalizedRunBundleManifest(
        document_schema=schema,
        metadata=metadata,
        source_files=tuple(source_files),
        generated_files=tuple(generated_files),
        spectrum_count=len(accepted_spectra),
        psm_count=psm_count,
        rejected_spectra=rejected_spectra,
        rejected_identification_rows=rejected_identification_rows,
    )
    manifest = manifest.model_copy(
        update={
            "document_schema": manifest.document_schema.with_content_hash(
                manifest.to_dict()
            )
        }
    )
    manifest_path = bundle_dir / "bundle.manifest.json"
    manifest_path.write_text(manifest.to_stable_json() + "\n", encoding="utf-8")
    return manifest

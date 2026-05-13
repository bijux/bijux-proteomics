# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Spectral-library import, indexing, and candidate-lookup contracts."""

from __future__ import annotations

import csv
import io
from enum import StrEnum
from pathlib import Path

from pydantic import ConfigDict, Field

from bijux_proteomics.chemistry import (
    ModificationRegistryDocument,
    ParsedModifiedPeptide,
    canonicalize_modified_peptide,
    parse_modified_peptide,
)
from bijux_proteomics.io.spectra import SpectrumModel, SpectrumPeak, parse_mgf
from bijux_proteomics_foundation import DocumentSchema, JsonModel


class SpectralLibraryFormat(StrEnum):
    """Supported practical spectral-library exchange formats."""

    MSP = "msp"
    MGF = "mgf"


class RejectedSpectralLibraryEntry(JsonModel):
    """One rejected spectral-library entry with a stable reason."""

    model_config = ConfigDict(extra="forbid")

    entry_ordinal: int = Field(..., ge=1)
    source_format: SpectralLibraryFormat
    reason: str = Field(..., min_length=1)
    raw_identity: str | None = None


class SpectralLibraryEntry(JsonModel):
    """One imported spectral-library entry."""

    model_config = ConfigDict(extra="forbid")

    library_entry_id: str = Field(..., min_length=1)
    source_format: SpectralLibraryFormat
    spectrum_id: str = Field(..., min_length=1)
    precursor_mz: float = Field(..., gt=0.0)
    precursor_charge: int = Field(..., ge=1)
    peptide_sequence: str = Field(..., min_length=1)
    canonical_peptide: str = Field(..., min_length=1)
    modification_count: int = Field(..., ge=0)
    spectrum: SpectrumModel


class SpectralLibraryImportReport(JsonModel):
    """Imported spectral-library entries plus stable rejection facts."""

    model_config = ConfigDict(extra="forbid")

    document_schema: DocumentSchema
    source_path: str = Field(..., min_length=1)
    source_format: SpectralLibraryFormat
    accepted_entry_count: int = Field(..., ge=0)
    rejected_entry_count: int = Field(..., ge=0)
    entries: tuple[SpectralLibraryEntry, ...] = Field(default_factory=tuple)
    rejected_entries: tuple[RejectedSpectralLibraryEntry, ...] = Field(
        default_factory=tuple
    )


class SpectralLibrarySummary(JsonModel):
    """Compact summary over one imported spectral library."""

    model_config = ConfigDict(extra="forbid")

    source_format: SpectralLibraryFormat
    entry_count: int = Field(..., ge=0)
    unique_peptide_count: int = Field(..., ge=0)
    modified_entry_count: int = Field(..., ge=0)
    charge_counts: dict[str, int] = Field(default_factory=dict)


class SpectralLibraryIndex(JsonModel):
    """Stable spectral-library index by peptide and precursor m/z."""

    model_config = ConfigDict(extra="forbid")

    entries: tuple[SpectralLibraryEntry, ...] = Field(default_factory=tuple)
    peptide_index: dict[str, tuple[str, ...]] = Field(default_factory=dict)
    precursor_centimass_index: dict[int, tuple[str, ...]] = Field(default_factory=dict)


class SpectralLibraryCandidateMatch(JsonModel):
    """One candidate spectral-library entry returned by precursor or peptide lookup."""

    model_config = ConfigDict(extra="forbid")

    library_entry_id: str = Field(..., min_length=1)
    spectrum_id: str = Field(..., min_length=1)
    canonical_peptide: str = Field(..., min_length=1)
    precursor_mz: float = Field(..., gt=0.0)
    precursor_charge: int = Field(..., ge=1)
    precursor_delta_da: float = Field(..., ge=0.0)


class SpectralLibraryCandidateReport(JsonModel):
    """Candidate lookup report over one spectral-library index."""

    model_config = ConfigDict(extra="forbid")

    precursor_mz: float = Field(..., gt=0.0)
    tolerance_da: float = Field(..., gt=0.0)
    peptide_query: str | None = None
    candidate_count: int = Field(..., ge=0)
    matches: tuple[SpectralLibraryCandidateMatch, ...] = Field(default_factory=tuple)


def import_spectral_library(
    path: Path,
    *,
    library_format: SpectralLibraryFormat | str | None = None,
    registry: ModificationRegistryDocument | None = None,
) -> SpectralLibraryImportReport:
    """Import one practical MSP or MGF spectral library."""
    resolved = _resolve_spectral_library_format(path, library_format=library_format)
    if resolved is SpectralLibraryFormat.MSP:
        entries, rejected = _parse_msp_spectral_library(path, registry=registry)
    else:
        entries, rejected = _parse_mgf_spectral_library(path, registry=registry)
    report = SpectralLibraryImportReport(
        document_schema=DocumentSchema(
            created_by="bijux-proteomics-core",
            document_kind="spectral_library_import_report",
            package_name="bijux-proteomics-core",
            status="generated",
        ),
        source_path=str(path),
        source_format=resolved,
        accepted_entry_count=len(entries),
        rejected_entry_count=len(rejected),
        entries=tuple(entries),
        rejected_entries=tuple(rejected),
    )
    payload = report.to_dict()
    return report.model_copy(
        update={
            "document_schema": report.document_schema.with_content_hash(payload),
        }
    )


def build_spectral_library_summary(
    report: SpectralLibraryImportReport,
) -> SpectralLibrarySummary:
    """Build a compact summary over an imported spectral library."""
    charge_counts: dict[str, int] = {}
    modified_entry_count = 0
    unique_peptides: set[str] = set()
    for entry in report.entries:
        charge_key = str(entry.precursor_charge)
        charge_counts[charge_key] = charge_counts.get(charge_key, 0) + 1
        unique_peptides.add(entry.canonical_peptide)
        if entry.modification_count > 0:
            modified_entry_count += 1
    return SpectralLibrarySummary(
        source_format=report.source_format,
        entry_count=len(report.entries),
        unique_peptide_count=len(unique_peptides),
        modified_entry_count=modified_entry_count,
        charge_counts=dict(sorted(charge_counts.items())),
    )


def build_spectral_library_index(
    entries: tuple[SpectralLibraryEntry, ...],
) -> SpectralLibraryIndex:
    """Index spectral-library entries by peptide and precursor centimass."""
    peptide_index: dict[str, list[str]] = {}
    precursor_index: dict[int, list[str]] = {}
    normalized_entries = tuple(
        sorted(entries, key=lambda entry: (entry.precursor_mz, entry.library_entry_id))
    )
    for entry in normalized_entries:
        peptide_index.setdefault(entry.canonical_peptide, []).append(entry.library_entry_id)
        precursor_key = _precursor_centimass_key(entry.precursor_mz)
        precursor_index.setdefault(precursor_key, []).append(entry.library_entry_id)
    return SpectralLibraryIndex(
        entries=normalized_entries,
        peptide_index={
            key: tuple(values) for key, values in sorted(peptide_index.items())
        },
        precursor_centimass_index={
            key: tuple(values) for key, values in sorted(precursor_index.items())
        },
    )


def find_spectral_library_candidates(
    index: SpectralLibraryIndex,
    *,
    precursor_mz: float,
    tolerance_da: float = 0.5,
    peptide_query: str | None = None,
    registry: ModificationRegistryDocument | None = None,
) -> SpectralLibraryCandidateReport:
    """Search precursor-compatible spectral-library candidates."""
    if tolerance_da <= 0:
        raise ValueError("tolerance_da must be greater than zero")
    normalized_query = (
        _normalize_library_peptide_query(peptide_query, registry=registry)
        if peptide_query is not None
        else None
    )
    lower_key = _precursor_centimass_key(precursor_mz - tolerance_da)
    upper_key = _precursor_centimass_key(precursor_mz + tolerance_da)
    candidate_ids: set[str] = set()
    for key in range(lower_key, upper_key + 1):
        candidate_ids.update(index.precursor_centimass_index.get(key, ()))
    entries_by_id = {
        entry.library_entry_id: entry
        for entry in index.entries
    }
    matches = [
        SpectralLibraryCandidateMatch(
            library_entry_id=entry.library_entry_id,
            spectrum_id=entry.spectrum_id,
            canonical_peptide=entry.canonical_peptide,
            precursor_mz=entry.precursor_mz,
            precursor_charge=entry.precursor_charge,
            precursor_delta_da=abs(entry.precursor_mz - precursor_mz),
        )
        for entry_id in sorted(candidate_ids)
        for entry in (entries_by_id[entry_id],)
        if abs(entry.precursor_mz - precursor_mz) <= tolerance_da
        and (
            normalized_query is None or entry.canonical_peptide == normalized_query
        )
    ]
    ordered = tuple(
        sorted(
            matches,
            key=lambda row: (
                row.precursor_delta_da,
                row.canonical_peptide,
                row.library_entry_id,
            ),
        )
    )
    return SpectralLibraryCandidateReport(
        precursor_mz=precursor_mz,
        tolerance_da=tolerance_da,
        peptide_query=normalized_query,
        candidate_count=len(ordered),
        matches=ordered,
    )


def render_spectral_library_summary_tsv(summary: SpectralLibrarySummary) -> str:
    """Render one compact spectral-library summary row."""
    return _render_tsv(
        (
            "source_format",
            "entry_count",
            "unique_peptide_count",
            "modified_entry_count",
        ),
        (
            (
                summary.source_format.value,
                summary.entry_count,
                summary.unique_peptide_count,
                summary.modified_entry_count,
            ),
        ),
    )


def render_spectral_library_candidates_tsv(
    report: SpectralLibraryCandidateReport,
) -> str:
    """Render one stable candidate spectral-library table."""
    return _render_tsv(
        (
            "library_entry_id",
            "spectrum_id",
            "canonical_peptide",
            "precursor_mz",
            "precursor_charge",
            "precursor_delta_da",
        ),
        tuple(
            (
                row.library_entry_id,
                row.spectrum_id,
                row.canonical_peptide,
                row.precursor_mz,
                row.precursor_charge,
                row.precursor_delta_da,
            )
            for row in report.matches
        ),
    )


def _resolve_spectral_library_format(
    path: Path,
    *,
    library_format: SpectralLibraryFormat | str | None,
) -> SpectralLibraryFormat:
    if library_format is not None:
        return (
            library_format
            if isinstance(library_format, SpectralLibraryFormat)
            else SpectralLibraryFormat(library_format)
        )
    suffix = path.suffix.lower()
    if suffix == ".msp":
        return SpectralLibraryFormat.MSP
    if suffix == ".mgf":
        return SpectralLibraryFormat.MGF
    raise ValueError("spectral-library import supports only .msp and .mgf inputs")


def _parse_msp_spectral_library(
    path: Path,
    *,
    registry: ModificationRegistryDocument | None,
) -> tuple[list[SpectralLibraryEntry], list[RejectedSpectralLibraryEntry]]:
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return [], []
    blocks = [block.strip() for block in text.split("\n\n") if block.strip()]
    entries: list[SpectralLibraryEntry] = []
    rejected: list[RejectedSpectralLibraryEntry] = []
    for ordinal, block in enumerate(blocks, start=1):
        try:
            entries.append(
                _parse_msp_entry(block, ordinal=ordinal, registry=registry)
            )
        except ValueError as exc:
            rejected.append(
                RejectedSpectralLibraryEntry(
                    entry_ordinal=ordinal,
                    source_format=SpectralLibraryFormat.MSP,
                    reason=str(exc),
                    raw_identity=block.splitlines()[0] if block.splitlines() else None,
                )
            )
    return entries, rejected


def _parse_msp_entry(
    block: str,
    *,
    ordinal: int,
    registry: ModificationRegistryDocument | None,
) -> SpectralLibraryEntry:
    lines = [line.strip() for line in block.splitlines() if line.strip()]
    fields: dict[str, str] = {}
    peak_lines: list[str] = []
    in_peaks = False
    for line in lines:
        if in_peaks:
            peak_lines.append(line)
            continue
        if ":" not in line:
            raise ValueError("MSP entry header line must contain ':'")
        key, value = line.split(":", 1)
        normalized_key = key.strip().lower()
        normalized_value = value.strip()
        fields[normalized_key] = normalized_value
        if normalized_key == "num peaks":
            in_peaks = True

    name = fields.get("name")
    if not name:
        raise ValueError("MSP entry must declare a Name field")
    precursor_mz = _parse_parent_mz_from_comment(fields.get("comment", ""))
    if precursor_mz is None:
        raise ValueError("MSP entry must declare Parent in Comment")
    peptide_text, charge = _parse_name_peptide_and_charge(name)
    parsed_peptide = _parse_library_peptide(peptide_text, registry=registry)
    peaks = _parse_peak_lines(peak_lines)
    entry_id = f"msp:{ordinal}:{name}"
    spectrum = SpectrumModel(
        spectrum_id=entry_id,
        title=name,
        precursor_mz=precursor_mz,
        precursor_charge=charge,
        peaks=peaks,
    )
    return SpectralLibraryEntry(
        library_entry_id=entry_id,
        source_format=SpectralLibraryFormat.MSP,
        spectrum_id=spectrum.spectrum_id,
        precursor_mz=precursor_mz,
        precursor_charge=charge,
        peptide_sequence=parsed_peptide.sequence,
        canonical_peptide=canonicalize_modified_peptide(parsed_peptide, registry=registry),
        modification_count=len(parsed_peptide.modifications),
        spectrum=spectrum,
    )


def _parse_mgf_spectral_library(
    path: Path,
    *,
    registry: ModificationRegistryDocument | None,
) -> tuple[list[SpectralLibraryEntry], list[RejectedSpectralLibraryEntry]]:
    report = parse_mgf(path)
    entries: list[SpectralLibraryEntry] = []
    rejected = [
        RejectedSpectralLibraryEntry(
            entry_ordinal=block.block_index,
            source_format=SpectralLibraryFormat.MGF,
            reason=", ".join(issue.message for issue in block.issues),
            raw_identity=block.title,
        )
        for block in report.rejected_blocks
    ]
    for ordinal, spectrum in enumerate(report.accepted_spectra, start=1):
        try:
            entries.append(
                _build_library_entry_from_mgf_spectrum(
                    spectrum,
                    ordinal=ordinal,
                    registry=registry,
                )
            )
        except ValueError as exc:
            rejected.append(
                RejectedSpectralLibraryEntry(
                    entry_ordinal=ordinal,
                    source_format=SpectralLibraryFormat.MGF,
                    reason=str(exc),
                    raw_identity=spectrum.title or spectrum.spectrum_id,
                )
            )
    return entries, rejected


def _build_library_entry_from_mgf_spectrum(
    spectrum: SpectrumModel,
    *,
    ordinal: int,
    registry: ModificationRegistryDocument | None,
) -> SpectralLibraryEntry:
    header_fields = _parse_mgf_library_title_fields(spectrum.title)
    peptide_text = (
        header_fields.get("modifiedpeptide")
        or header_fields.get("peptide")
        or header_fields.get("seq")
    )
    if not peptide_text:
        raise ValueError(
            "MGF library spectrum title must carry SEQ, PEPTIDE, or MODIFIEDPEPTIDE"
        )
    if spectrum.precursor_charge is None:
        raise ValueError("MGF library spectrum must declare precursor charge")
    parsed_peptide = _parse_library_peptide(peptide_text, registry=registry)
    entry_id = f"mgf:{ordinal}:{spectrum.spectrum_id}"
    return SpectralLibraryEntry(
        library_entry_id=entry_id,
        source_format=SpectralLibraryFormat.MGF,
        spectrum_id=spectrum.spectrum_id,
        precursor_mz=spectrum.precursor_mz,
        precursor_charge=spectrum.precursor_charge,
        peptide_sequence=parsed_peptide.sequence,
        canonical_peptide=canonicalize_modified_peptide(parsed_peptide, registry=registry),
        modification_count=len(parsed_peptide.modifications),
        spectrum=spectrum,
    )


def _parse_name_peptide_and_charge(name: str) -> tuple[str, int]:
    text = name.strip()
    if "/" not in text:
        raise ValueError("MSP Name field must use PEPTIDE/charge form")
    peptide_text, charge_text = text.rsplit("/", 1)
    charge = int(charge_text.strip())
    if charge <= 0:
        raise ValueError("MSP Name charge must be greater than zero")
    return peptide_text.strip(), charge


def _parse_parent_mz_from_comment(comment: str) -> float | None:
    for token in comment.split():
        if "=" not in token:
            continue
        key, value = token.split("=", 1)
        if key.strip().lower() == "parent":
            return float(value.strip().strip('"'))
    return None


def _parse_peak_lines(lines: list[str]) -> tuple[SpectrumPeak, ...]:
    peaks: list[SpectrumPeak] = []
    for line in lines:
        pieces = line.split()
        if len(pieces) < 2:
            raise ValueError("spectral-library peak line must contain m/z and intensity")
        peaks.append(
            SpectrumPeak(mz=float(pieces[0]), intensity=float(pieces[1]))
        )
    return tuple(peaks)


def _parse_mgf_library_title_fields(title: str | None) -> dict[str, str]:
    if title is None:
        return {}
    parts = [part.strip() for part in title.split("|") if part.strip()]
    fields: dict[str, str] = {}
    for part in parts:
        if "=" not in part:
            continue
        key, value = part.split("=", 1)
        fields[key.strip().lower()] = value.strip()
    return fields


def _parse_library_peptide(
    text: str,
    *,
    registry: ModificationRegistryDocument | None,
) -> ParsedModifiedPeptide:
    return parse_modified_peptide(text, registry=registry)


def _normalize_library_peptide_query(
    query: str,
    *,
    registry: ModificationRegistryDocument | None,
) -> str:
    return canonicalize_modified_peptide(
        _parse_library_peptide(query, registry=registry),
        registry=registry,
    )


def _precursor_centimass_key(precursor_mz: float) -> int:
    return int(round(precursor_mz * 100))


def _render_tsv(header: tuple[str, ...], rows: tuple[tuple[object, ...], ...]) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(header)
    writer.writerows(rows)
    return buffer.getvalue()

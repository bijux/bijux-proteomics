# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Spectral-library import, indexing, and candidate-lookup contracts."""

from __future__ import annotations

import csv
from enum import StrEnum
import io
from pathlib import Path
from typing import cast

from pydantic import ConfigDict, Field

from bijux_proteomics.chemistry.modifications import (
    ModificationRegistryDocument,
    ParsedModifiedPeptide,
    canonicalize_modified_peptide,
    parse_modified_peptide,
)
from bijux_proteomics.identification.contracts import (
    PsmRecord,
    TargetDecoyLabel,
    apply_q_values,
)
from bijux_proteomics.io.spectra import (
    SpectralSimilarityMethod,
    SpectrumModel,
    SpectrumPeak,
    SpectrumSimilarityClassification,
    SpectrumSimilarityMode,
    build_spectrum_similarity_comparison_report,
    parse_mgf,
)
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
    protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    target_decoy_label: TargetDecoyLabel = TargetDecoyLabel.UNKNOWN
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
    decoy_entry_count: int = Field(..., ge=0)
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
    target_decoy_label: TargetDecoyLabel = TargetDecoyLabel.UNKNOWN
    precursor_delta_da: float = Field(..., ge=0.0)


class SpectralLibraryCandidateReport(JsonModel):
    """Candidate lookup report over one spectral-library index."""

    model_config = ConfigDict(extra="forbid")

    precursor_mz: float = Field(..., gt=0.0)
    tolerance_da: float = Field(..., gt=0.0)
    peptide_query: str | None = None
    candidate_count: int = Field(..., ge=0)
    matches: tuple[SpectralLibraryCandidateMatch, ...] = Field(default_factory=tuple)


class SpectralLibrarySearchStrategy(StrEnum):
    """Supported confidence strategies for practical spectral-library search."""

    CONCATENATED = "concatenated"
    NO_DECOY_ADVISORY = "no_decoy_advisory"


class SpectralLibrarySearchMatch(JsonModel):
    """One scored spectral-library match for a query spectrum."""

    model_config = ConfigDict(extra="forbid")

    rank: int = Field(..., ge=1)
    library_entry_id: str = Field(..., min_length=1)
    spectrum_id: str = Field(..., min_length=1)
    canonical_peptide: str = Field(..., min_length=1)
    precursor_charge: int = Field(..., ge=1)
    target_decoy_label: TargetDecoyLabel = TargetDecoyLabel.UNKNOWN
    precursor_delta_da: float = Field(..., ge=0.0)
    similarity_score: float = Field(..., ge=0.0)
    matched_peak_count: int = Field(..., ge=0)
    reference_explained_intensity_fraction: float = Field(..., ge=0.0, le=1.0)
    query_explained_intensity_fraction: float = Field(..., ge=0.0, le=1.0)
    similarity_classification: SpectrumSimilarityClassification
    q_value: float | None = Field(default=None, ge=0.0)


class SpectralLibrarySearchReport(JsonModel):
    """Practical library-search report for one query spectrum."""

    model_config = ConfigDict(extra="forbid")

    document_schema: DocumentSchema
    query_spectrum_id: str = Field(..., min_length=1)
    query_precursor_mz: float = Field(..., gt=0.0)
    precursor_tolerance_da: float = Field(..., gt=0.0)
    similarity_method: SpectralSimilarityMethod
    similarity_mode: SpectrumSimilarityMode
    similarity_tolerance_da: float | None = Field(default=None, gt=0.0)
    similarity_bin_width_da: float | None = Field(default=None, gt=0.0)
    top_n: int | None = Field(default=None, ge=1)
    candidate_count: int = Field(..., ge=0)
    decoy_candidate_count: int = Field(..., ge=0)
    search_strategy: SpectralLibrarySearchStrategy
    top_match_library_entry_id: str | None = None
    top_match_canonical_peptide: str | None = None
    top_match_similarity_score: float | None = Field(default=None, ge=0.0)
    top_match_q_value: float | None = Field(default=None, ge=0.0)
    advisory_warning: str | None = None
    matches: tuple[SpectralLibrarySearchMatch, ...] = Field(default_factory=tuple)


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
    decoy_entry_count = 0
    unique_peptides: set[str] = set()
    for entry in report.entries:
        charge_key = str(entry.precursor_charge)
        charge_counts[charge_key] = charge_counts.get(charge_key, 0) + 1
        unique_peptides.add(entry.canonical_peptide)
        if entry.modification_count > 0:
            modified_entry_count += 1
        if entry.target_decoy_label is TargetDecoyLabel.DECOY:
            decoy_entry_count += 1
    return SpectralLibrarySummary(
        source_format=report.source_format,
        entry_count=len(report.entries),
        unique_peptide_count=len(unique_peptides),
        modified_entry_count=modified_entry_count,
        decoy_entry_count=decoy_entry_count,
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
        peptide_index.setdefault(entry.canonical_peptide, []).append(
            entry.library_entry_id
        )
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
    entries_by_id = {entry.library_entry_id: entry for entry in index.entries}
    matches = [
        SpectralLibraryCandidateMatch(
            library_entry_id=entry.library_entry_id,
            spectrum_id=entry.spectrum_id,
            canonical_peptide=entry.canonical_peptide,
            precursor_mz=entry.precursor_mz,
            precursor_charge=entry.precursor_charge,
            target_decoy_label=entry.target_decoy_label,
            precursor_delta_da=abs(entry.precursor_mz - precursor_mz),
        )
        for entry_id in sorted(candidate_ids)
        for entry in (entries_by_id[entry_id],)
        if abs(entry.precursor_mz - precursor_mz) <= tolerance_da
        and (normalized_query is None or entry.canonical_peptide == normalized_query)
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


def search_spectral_library(
    query_spectrum: SpectrumModel,
    index: SpectralLibraryIndex,
    *,
    precursor_tolerance_da: float = 0.5,
    similarity_tolerance_da: float | None = 0.02,
    similarity_bin_width_da: float | None = None,
    method: SpectralSimilarityMethod = SpectralSimilarityMethod.COSINE,
    mode: SpectrumSimilarityMode = SpectrumSimilarityMode.NORMALIZED,
    top_n: int | None = None,
    max_matches: int | None = 10,
) -> SpectralLibrarySearchReport:
    """Rank precursor-compatible library spectra against one query spectrum."""
    if precursor_tolerance_da <= 0:
        raise ValueError("precursor_tolerance_da must be greater than zero")
    if similarity_tolerance_da is None and similarity_bin_width_da is None:
        raise ValueError(
            "spectral-library search requires either similarity_tolerance_da or "
            "similarity_bin_width_da"
        )
    if similarity_tolerance_da is not None and similarity_tolerance_da <= 0:
        raise ValueError("similarity_tolerance_da must be greater than zero")
    if similarity_bin_width_da is not None and similarity_bin_width_da <= 0:
        raise ValueError("similarity_bin_width_da must be greater than zero")
    if max_matches is not None and max_matches <= 0:
        raise ValueError("max_matches must be greater than zero when provided")

    candidate_report = find_spectral_library_candidates(
        index,
        precursor_mz=query_spectrum.precursor_mz,
        tolerance_da=precursor_tolerance_da,
    )
    entries_by_id = {entry.library_entry_id: entry for entry in index.entries}
    scored_matches = [
        (
            entries_by_id[candidate.library_entry_id],
            build_spectrum_similarity_comparison_report(
                entries_by_id[candidate.library_entry_id].spectrum,
                query_spectrum,
                tolerance_da=similarity_tolerance_da,
                bin_width_da=similarity_bin_width_da,
                method=method,
                mode=mode,
                top_n=top_n,
            ),
            candidate,
        )
        for candidate in candidate_report.matches
    ]
    scored_matches.sort(
        key=lambda item: (
            -item[1].score,
            -item[1].matched_peak_count,
            item[2].precursor_delta_da,
            item[0].library_entry_id,
        )
    )
    ranked_records = tuple(
        PsmRecord(
            spectrum_id=query_spectrum.spectrum_id,
            peptide=entry.canonical_peptide,
            canonical_peptide=entry.canonical_peptide,
            charge=entry.precursor_charge,
            score=report.score,
            protein_refs=(entry.library_entry_id,),
            target_decoy_label=entry.target_decoy_label,
        )
        for entry, report, _candidate in scored_matches
    )
    scored_q_values = _score_library_search_matches(ranked_records)
    q_values_by_entry_id = {
        record.protein_refs[0]: record.q_value
        for record in scored_q_values
        if record.protein_refs
    }
    displayed_matches = (
        scored_matches[:max_matches] if max_matches is not None else scored_matches
    )

    matches = tuple(
        SpectralLibrarySearchMatch(
            rank=rank,
            library_entry_id=entry.library_entry_id,
            spectrum_id=entry.spectrum_id,
            canonical_peptide=entry.canonical_peptide,
            precursor_charge=entry.precursor_charge,
            target_decoy_label=entry.target_decoy_label,
            precursor_delta_da=candidate.precursor_delta_da,
            similarity_score=report.score,
            matched_peak_count=report.matched_peak_count,
            reference_explained_intensity_fraction=(
                report.reference_explained_intensity_fraction
            ),
            query_explained_intensity_fraction=(
                report.query_explained_intensity_fraction
            ),
            similarity_classification=report.classification,
            q_value=q_values_by_entry_id.get(entry.library_entry_id),
        )
        for rank, (entry, report, candidate) in enumerate(displayed_matches, start=1)
    )
    decoy_candidate_count = sum(
        1
        for entry, _report, _candidate in scored_matches
        if entry.target_decoy_label is TargetDecoyLabel.DECOY
    )
    top_match = matches[0] if matches else None
    search_strategy = _resolve_search_strategy(index.entries)
    advisory_warning = _resolve_spectral_library_search_advisory(search_strategy)
    report = SpectralLibrarySearchReport(
        document_schema=DocumentSchema(
            created_by="bijux-proteomics-core",
            document_kind="spectral_library_search_report",
            package_name="bijux-proteomics-core",
            status="generated",
        ),
        query_spectrum_id=query_spectrum.spectrum_id,
        query_precursor_mz=query_spectrum.precursor_mz,
        precursor_tolerance_da=precursor_tolerance_da,
        similarity_method=method,
        similarity_mode=mode,
        similarity_tolerance_da=similarity_tolerance_da,
        similarity_bin_width_da=similarity_bin_width_da,
        top_n=top_n,
        candidate_count=len(scored_matches),
        decoy_candidate_count=decoy_candidate_count,
        search_strategy=search_strategy,
        top_match_library_entry_id=(
            top_match.library_entry_id if top_match is not None else None
        ),
        top_match_canonical_peptide=(
            top_match.canonical_peptide if top_match is not None else None
        ),
        top_match_similarity_score=(
            top_match.similarity_score if top_match is not None else None
        ),
        top_match_q_value=top_match.q_value if top_match is not None else None,
        advisory_warning=advisory_warning,
        matches=matches,
    )
    payload = report.to_dict()
    return report.model_copy(
        update={
            "document_schema": report.document_schema.with_content_hash(payload),
        }
    )


def render_spectral_library_summary_tsv(summary: SpectralLibrarySummary) -> str:
    """Render one compact spectral-library summary row."""
    return _render_tsv(
        (
            "source_format",
            "entry_count",
            "unique_peptide_count",
            "modified_entry_count",
            "decoy_entry_count",
        ),
        (
            (
                summary.source_format.value,
                summary.entry_count,
                summary.unique_peptide_count,
                summary.modified_entry_count,
                summary.decoy_entry_count,
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
            "target_decoy_label",
            "precursor_delta_da",
        ),
        tuple(
            (
                row.library_entry_id,
                row.spectrum_id,
                row.canonical_peptide,
                row.precursor_mz,
                row.precursor_charge,
                row.target_decoy_label.value,
                row.precursor_delta_da,
            )
            for row in report.matches
        ),
    )


def render_spectral_library_search_tsv(report: SpectralLibrarySearchReport) -> str:
    """Render one ranked spectral-library search table."""
    return _render_tsv(
        (
            "search_strategy",
            "advisory_warning",
            "rank",
            "library_entry_id",
            "spectrum_id",
            "canonical_peptide",
            "precursor_charge",
            "target_decoy_label",
            "precursor_delta_da",
            "similarity_score",
            "matched_peak_count",
            "reference_explained_intensity_fraction",
            "query_explained_intensity_fraction",
            "similarity_classification",
            "q_value",
        ),
        tuple(
            (
                report.search_strategy.value,
                report.advisory_warning,
                row.rank,
                row.library_entry_id,
                row.spectrum_id,
                row.canonical_peptide,
                row.precursor_charge,
                row.target_decoy_label.value,
                row.precursor_delta_da,
                row.similarity_score,
                row.matched_peak_count,
                row.reference_explained_intensity_fraction,
                row.query_explained_intensity_fraction,
                row.similarity_classification.value,
                row.q_value,
            )
            for row in report.matches
        ),
    )


def _resolve_spectral_library_search_advisory(
    strategy: SpectralLibrarySearchStrategy,
) -> str | None:
    if strategy is SpectralLibrarySearchStrategy.NO_DECOY_ADVISORY:
        return "library search ran without decoy entries; q-values are withheld and this report is advisory only"
    return None


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
            entries.append(_parse_msp_entry(block, ordinal=ordinal, registry=registry))
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
    comment_fields = _parse_msp_comment_fields(fields.get("comment", ""))
    precursor_mz = _parse_parent_mz_from_comment(comment_fields)
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
        canonical_peptide=canonicalize_modified_peptide(
            parsed_peptide, registry=registry
        ),
        modification_count=len(parsed_peptide.modifications),
        protein_refs=_parse_library_protein_refs(comment_fields),
        target_decoy_label=_parse_explicit_decoy_label(comment_fields),
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
        canonical_peptide=canonicalize_modified_peptide(
            parsed_peptide, registry=registry
        ),
        modification_count=len(parsed_peptide.modifications),
        protein_refs=_parse_library_protein_refs(header_fields),
        target_decoy_label=_parse_explicit_decoy_label(header_fields),
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


def _parse_msp_comment_fields(comment: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for token in comment.split():
        if "=" not in token:
            continue
        key, value = token.split("=", 1)
        fields[key.strip().lower()] = value.strip().strip('"')
    return fields


def _parse_parent_mz_from_comment(comment_fields: dict[str, str]) -> float | None:
    value = comment_fields.get("parent")
    if value is not None:
        return float(value)
    return None


def _parse_peak_lines(lines: list[str]) -> tuple[SpectrumPeak, ...]:
    peaks: list[SpectrumPeak] = []
    for line in lines:
        pieces = line.split()
        if len(pieces) < 2:
            raise ValueError(
                "spectral-library peak line must contain m/z and intensity"
            )
        peaks.append(SpectrumPeak(mz=float(pieces[0]), intensity=float(pieces[1])))
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


def _parse_explicit_decoy_label(fields: dict[str, str]) -> TargetDecoyLabel:
    normalized_fields = {
        key.lower(): value.strip().lower() for key, value in fields.items()
    }
    for key in (
        "decoy",
        "is_decoy",
        "targetdecoylabel",
        "target_decoy_label",
    ):
        value = normalized_fields.get(key)
        if value is None:
            continue
        if value in {"1", "true", "yes", "decoy"}:
            return TargetDecoyLabel.DECOY
        if value in {"0", "false", "no", "target"}:
            return TargetDecoyLabel.TARGET
    return TargetDecoyLabel.UNKNOWN


def _parse_library_protein_refs(fields: dict[str, str]) -> tuple[str, ...]:
    for key in ("proteins", "protein_ids", "protein", "protein_id"):
        value = fields.get(key)
        if value is None:
            continue
        refs = tuple(
            sorted(
                {
                    token.strip()
                    for token in value.replace(",", ";").split(";")
                    if token.strip()
                }
            )
        )
        if refs:
            return refs
    return ()


def _resolve_search_strategy(
    entries: tuple[SpectralLibraryEntry, ...],
) -> SpectralLibrarySearchStrategy:
    if any(entry.target_decoy_label is TargetDecoyLabel.DECOY for entry in entries):
        return SpectralLibrarySearchStrategy.CONCATENATED
    return SpectralLibrarySearchStrategy.NO_DECOY_ADVISORY


def _score_library_search_matches(
    records: tuple[PsmRecord, ...],
) -> tuple[PsmRecord, ...]:
    if not records:
        return ()
    has_target = any(
        record.target_decoy_label is TargetDecoyLabel.TARGET for record in records
    )
    has_decoy = any(
        record.target_decoy_label is TargetDecoyLabel.DECOY for record in records
    )
    if not (has_target and has_decoy):
        return records
    return cast(
        tuple[PsmRecord, ...],
        apply_q_values(
            records,
            score_orientation="higher_better",
            tie_handling="score_group",
        ),
    )


def _render_tsv(header: tuple[str, ...], rows: tuple[tuple[object, ...], ...]) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(header)
    writer.writerows(rows)
    return buffer.getvalue()

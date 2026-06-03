# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Corpus-level normalization and provenance review for search adapters."""

from __future__ import annotations

from pathlib import Path

from pydantic import ConfigDict, Field

from bijux_proteomics.identification.search_adapters.conformance import (
    build_search_adapter_conformance_report,
    build_search_adapter_provenance_manifest,
)
from bijux_proteomics.identification.search_adapters.contracts import (
    SearchAdapterKind,
)
from bijux_proteomics.identification.search_adapters.normalization import (
    normalize_search_results_with_adapter,
)
from bijux_proteomics_foundation import JsonModel


class SearchCorpusInputSpecification(JsonModel):
    """One declared search-result input inside an adapter corpus."""

    model_config = ConfigDict(extra="forbid")

    adapter_kind: SearchAdapterKind
    dialect_id: str = Field(..., min_length=1)
    result_file: str = Field(..., min_length=1)
    config_file: str | None = None


class SearchCorpusNormalizationEntry(JsonModel):
    """One normalized corpus input with conformance and provenance summaries."""

    model_config = ConfigDict(extra="forbid")

    adapter_kind: SearchAdapterKind
    dialect_id: str = Field(..., min_length=1)
    result_path: str = Field(..., min_length=1)
    config_path: str | None = None
    accepted_rows: int = Field(..., ge=0)
    rejected_rows: int = Field(..., ge=0)
    conformance_passes: bool
    mapped_columns: tuple[str, ...] = Field(default_factory=tuple)
    preserved_native_only_columns: tuple[str, ...] = Field(default_factory=tuple)
    unsupported_columns: tuple[str, ...] = Field(default_factory=tuple)
    lost_columns: tuple[str, ...] = Field(default_factory=tuple)
    source_sha256: str = Field(..., min_length=64, max_length=64)
    config_sha256: str | None = None


class SearchEngineCorpusReport(JsonModel):
    """Corpus-level normalization coverage for one search adapter family."""

    model_config = ConfigDict(extra="forbid")

    adapter_kind: SearchAdapterKind
    corpus_root: str = Field(..., min_length=1)
    entries: tuple[SearchCorpusNormalizationEntry, ...] = Field(default_factory=tuple)
    missing_artifacts: tuple[str, ...] = Field(default_factory=tuple)
    total_accepted_rows: int = Field(..., ge=0)
    total_rejected_rows: int = Field(..., ge=0)
    passes: bool
    note: str = Field(..., min_length=1)


class SearchAdapterCorpusConformanceEntry(JsonModel):
    """Conformance summary row for one adapter corpus report."""

    model_config = ConfigDict(extra="forbid")

    adapter_kind: SearchAdapterKind
    corpus_root: str = Field(..., min_length=1)
    corpus_passes: bool
    corpus_entry_count: int = Field(..., ge=0)
    total_accepted_rows: int = Field(..., ge=0)
    total_rejected_rows: int = Field(..., ge=0)
    unsupported_column_count: int = Field(..., ge=0)
    lost_column_count: int = Field(..., ge=0)


class SearchAdapterCorpusConformanceMatrix(JsonModel):
    """Conformance matrix across all built-in engine corpora."""

    model_config = ConfigDict(extra="forbid")

    matrix_root: str = Field(..., min_length=1)
    entries: tuple[SearchAdapterCorpusConformanceEntry, ...] = Field(
        default_factory=tuple
    )
    passes: bool


def build_search_engine_corpus_report(
    *,
    corpus_root: Path,
    adapter_kind: SearchAdapterKind,
    input_specs: tuple[SearchCorpusInputSpecification, ...],
) -> SearchEngineCorpusReport:
    """Build a corpus coverage report for one adapter from declared fixture inputs."""
    if not input_specs:
        raise ValueError("at least one corpus input specification is required")
    if any(spec.adapter_kind is not adapter_kind for spec in input_specs):
        raise ValueError("all corpus input specifications must match the adapter kind")

    entries: list[SearchCorpusNormalizationEntry] = []
    missing_artifacts: list[str] = []
    for spec in input_specs:
        result_path = corpus_root / spec.result_file
        config_path = corpus_root / spec.config_file if spec.config_file else None
        if not result_path.exists():
            missing_artifacts.append(str(result_path.relative_to(corpus_root)))
            continue
        if config_path is not None and not config_path.exists():
            missing_artifacts.append(str(config_path.relative_to(corpus_root)))
            continue

        normalization = normalize_search_results_with_adapter(
            source_path=result_path,
            adapter_kind=adapter_kind,
            dialect_id=spec.dialect_id,
        )
        conformance = build_search_adapter_conformance_report(normalization)
        provenance = build_search_adapter_provenance_manifest(
            source_path=result_path,
            normalization_report=normalization,
            config_path=config_path,
        )
        field_accounting = conformance.field_accounting
        entries.append(
            SearchCorpusNormalizationEntry(
                adapter_kind=adapter_kind,
                dialect_id=spec.dialect_id,
                result_path=str(result_path),
                config_path=str(config_path) if config_path is not None else None,
                accepted_rows=conformance.accepted_rows,
                rejected_rows=conformance.rejected_rows,
                conformance_passes=conformance.passes,
                mapped_columns=field_accounting.mapped_columns,
                preserved_native_only_columns=field_accounting.preserved_native_only_columns,
                unsupported_columns=field_accounting.unsupported_columns,
                lost_columns=field_accounting.lost_columns,
                source_sha256=provenance.source_sha256,
                config_sha256=provenance.config_sha256,
            )
        )

    total_accepted_rows = sum(entry.accepted_rows for entry in entries)
    total_rejected_rows = sum(entry.rejected_rows for entry in entries)
    passes = (
        not missing_artifacts
        and bool(entries)
        and all(entry.conformance_passes for entry in entries)
    )
    note = (
        "corpus coverage is complete and each normalization entry passed conformance checks"
        if passes
        else "corpus coverage is incomplete or has conformance failures requiring review"
    )
    return SearchEngineCorpusReport(
        adapter_kind=adapter_kind,
        corpus_root=str(corpus_root),
        entries=tuple(entries),
        missing_artifacts=tuple(sorted(set(missing_artifacts))),
        total_accepted_rows=total_accepted_rows,
        total_rejected_rows=total_rejected_rows,
        passes=passes,
        note=note,
    )


__all__ = [
    "SearchAdapterCorpusConformanceEntry",
    "SearchAdapterCorpusConformanceMatrix",
    "SearchCorpusInputSpecification",
    "SearchCorpusNormalizationEntry",
    "SearchEngineCorpusReport",
    "build_search_engine_corpus_report",
]

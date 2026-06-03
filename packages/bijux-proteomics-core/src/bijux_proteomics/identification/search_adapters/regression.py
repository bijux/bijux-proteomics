# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Regression-corpus manifests over search-adapter fixtures."""

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.identification.search_adapters.contracts import (
    SearchAdapterKind,
    SearchRegressionCorpusEntry,
    SearchRegressionCorpusManifest,
    SearchRegressionFixtureKind,
)
from bijux_proteomics.identification.search_adapters.input_review import _hash_file
from bijux_proteomics_foundation import DocumentSchema


def _fixture_adapter_kind(path: Path) -> SearchAdapterKind | None:
    stem = path.stem.lower()
    if "comet" in stem:
        return SearchAdapterKind.COMET
    if "msfragger" in stem:
        return SearchAdapterKind.MSFRAGGER
    if "sage" in stem:
        return SearchAdapterKind.SAGE
    if "maxquant" in stem:
        return SearchAdapterKind.MAXQUANT_EVIDENCE
    if "diann" in stem:
        return SearchAdapterKind.DIANN
    if "spectronaut" in stem:
        return SearchAdapterKind.SPECTRONAUT
    if "generic" in stem:
        return SearchAdapterKind.GENERIC
    return None


def _fixture_kind_for_path(path: Path) -> tuple[SearchRegressionFixtureKind, str]:
    suffix = path.suffix.lower()
    stem = path.stem.lower()
    if "malformed" in stem or "invalid" in stem:
        return (
            SearchRegressionFixtureKind.FAILURE_CASE,
            "fixture captures malformed or scientifically invalid search inputs",
        )
    if suffix == ".json" and "mapping" in stem:
        return (
            SearchRegressionFixtureKind.MAPPING_CONTROL,
            "fixture defines explicit mapping control state for generic normalization",
        )
    if stem.endswith("pipeline_export"):
        return (
            SearchRegressionFixtureKind.PIPELINE_EXPORT,
            "fixture captures a richer pipeline-style engine export surface",
        )
    if suffix in {".params", ".json"}:
        return (
            SearchRegressionFixtureKind.PARAMETER_FILE,
            "fixture captures engine parameter provenance and validation state",
        )
    if suffix in {".tsv", ".txt"} and (
        "results" in stem
        or "report" in stem
        or "evidence" in stem
        or stem.endswith("_merge")
    ):
        return (
            SearchRegressionFixtureKind.ENGINE_EXPORT_LIKE,
            "fixture captures an engine-style result export for regression coverage",
        )
    return (
        SearchRegressionFixtureKind.OTHER,
        "fixture supports auxiliary regression coverage outside the main export classes",
    )


def build_search_adapter_regression_corpus_manifest(
    corpus_root: Path,
) -> SearchRegressionCorpusManifest:
    """Build a stable manifest over a directory of search adapter regression fixtures."""
    entries: list[SearchRegressionCorpusEntry] = []
    for path in sorted(
        candidate for candidate in corpus_root.rglob("*") if candidate.is_file()
    ):
        fixture_kind, note = _fixture_kind_for_path(path)
        entries.append(
            SearchRegressionCorpusEntry(
                relative_path=str(path.relative_to(corpus_root)),
                sha256=_hash_file(path) or "",
                adapter_kind=_fixture_adapter_kind(path),
                fixture_kind=fixture_kind,
                note=note,
            )
        )
    covered_adapter_kinds = tuple(
        sorted(
            {entry.adapter_kind for entry in entries if entry.adapter_kind is not None},
            key=lambda kind: kind.value,
        )
    )
    schema = DocumentSchema(
        created_by="bijux-proteomics-core",
        document_kind="search_adapter_regression_corpus_manifest",
        package_name="bijux-proteomics-core",
        status="generated",
    )
    manifest = SearchRegressionCorpusManifest(
        document_schema=schema,
        corpus_root=str(corpus_root),
        entries=tuple(entries),
        covered_adapter_kinds=covered_adapter_kinds,
        engine_export_like_count=sum(
            entry.fixture_kind is SearchRegressionFixtureKind.ENGINE_EXPORT_LIKE
            for entry in entries
        ),
        failure_case_count=sum(
            entry.fixture_kind is SearchRegressionFixtureKind.FAILURE_CASE
            for entry in entries
        ),
    )
    return manifest.model_copy(
        update={
            "document_schema": manifest.document_schema.with_content_hash(
                manifest.to_dict()
            )
        }
    )

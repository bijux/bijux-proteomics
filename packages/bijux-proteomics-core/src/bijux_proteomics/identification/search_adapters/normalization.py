# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Shared normalization over search-adapter inputs."""

from __future__ import annotations

from pathlib import Path

from bijux_proteomics.identification.contracts import (
    PsmParseReport,
    SearchResultColumnMapping,
    SearchResultProvenanceManifest,
    TargetDecoyLabelPolicy,
    normalize_psm_records,
    parse_psm_tsv,
)
from bijux_proteomics.identification.search_adapters.contracts import (
    SearchAdapterDialectManifest,
    SearchAdapterKind,
    SearchAdapterManifest,
    SearchAdapterNormalizationReport,
)
from bijux_proteomics.identification.search_adapters.family_policy import (
    build_search_result_family_policy,
)
from bijux_proteomics.identification.search_adapters.input_review import (
    _build_evidence_rows,
    _hash_file,
    _read_search_result_rows,
)
from bijux_proteomics.identification.search_adapters.registry import (
    manifest_for_dialect,
    resolve_search_adapter_dialect,
)
from bijux_proteomics_foundation import DocumentSchema


def _build_parse_provenance(
    *,
    source_path: Path,
    parse_report: PsmParseReport,
    adapter_manifest: SearchAdapterManifest,
) -> SearchResultProvenanceManifest:
    schema = DocumentSchema(
        created_by="bijux-proteomics-core",
        document_kind="search_result_provenance_manifest",
        package_name="bijux-proteomics-core",
        status="generated",
    )
    manifest = SearchResultProvenanceManifest(
        document_schema=schema,
        source_path=str(source_path),
        source_sha256=_hash_file(source_path),
        total_rows=parse_report.total_rows,
        accepted_rows=len(parse_report.accepted_records),
        rejected_rows=len(parse_report.rejected_rows),
        column_mapping=parse_report.column_mapping,
        decoy_policy=adapter_manifest.default_decoy_policy,
        fdr_policy=None,
    )
    return manifest.model_copy(
        update={
            "document_schema": manifest.document_schema.with_content_hash(
                manifest.to_dict()
            )
        }
    )


def normalize_search_results_with_adapter(
    *,
    source_path: Path,
    adapter_kind: SearchAdapterKind,
    dialect_id: str = "default",
    mapping: SearchResultColumnMapping | None = None,
    decoy_policy: TargetDecoyLabelPolicy | None = None,
    additional_dialects: tuple[SearchAdapterDialectManifest, ...] = (),
) -> SearchAdapterNormalizationReport:
    """Normalize one search table with a built-in or user-supplied adapter mapping."""
    dialect = resolve_search_adapter_dialect(
        adapter_kind=adapter_kind,
        dialect_id=dialect_id,
        additional_dialects=additional_dialects,
    )
    manifest = manifest_for_dialect(adapter_kind=adapter_kind, dialect=dialect)
    resolved_mapping = (
        mapping or (None if dialect is None else dialect.mapping) or manifest.mapping
    )
    if resolved_mapping is None:
        raise ValueError(
            "generic adapter normalization requires an explicit column mapping"
        )
    source_columns, source_rows = _read_search_result_rows(source_path)
    parse_report = parse_psm_tsv(
        source_path,
        mapping=resolved_mapping,
        decoy_policy=decoy_policy or manifest.default_decoy_policy,
    )
    evidence_rows = _build_evidence_rows(
        source_path=source_path,
        adapter_kind=manifest.adapter_kind,
        source_rows=source_rows,
        parse_report=parse_report,
    )
    return SearchAdapterNormalizationReport(
        adapter_manifest=manifest,
        family_policy=build_search_result_family_policy(manifest),
        source_columns=source_columns,
        parse_report=parse_report,
        normalized_records=normalize_psm_records(
            tuple(
                row.normalized_record
                for row in evidence_rows
                if row.accepted and row.normalized_record is not None
            )
        ),
        evidence_rows=evidence_rows,
    )

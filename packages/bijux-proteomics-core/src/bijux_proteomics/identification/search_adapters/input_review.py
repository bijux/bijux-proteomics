# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Input assessment and field-accounting helpers for search adapters."""

from __future__ import annotations

import csv
import hashlib
from pathlib import Path

from bijux_proteomics.domain import ImportedEvidenceProvenance
from bijux_proteomics.identification.contracts import (
    PsmParseReport,
    SearchResultColumnMapping,
)
from bijux_proteomics.identification.search_adapters.contracts import (
    SearchAdapterDialectManifest,
    SearchAdapterFieldAccounting,
    SearchAdapterKind,
    SearchAdapterNormalizationReport,
    SearchInputAssessmentReport,
    SearchInputRefusal,
    SearchInputRefusalKind,
    SearchNormalizedEvidenceEntry,
)
from bijux_proteomics.identification.search_adapters.family_policy import (
    build_search_result_family_policy,
)
from bijux_proteomics.identification.search_adapters.registry import (
    manifest_for_dialect,
    resolve_search_adapter_dialect,
)


def _hash_file(path: Path | None) -> str | None:
    if path is None:
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read_search_result_rows(
    path: Path,
) -> tuple[tuple[str, ...], tuple[dict[str, str], ...]]:
    rows: list[dict[str, str]] = []
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames is None:
            raise ValueError("search result TSV must include a header row")
        source_columns = tuple(
            str(column) for column in reader.fieldnames if column is not None
        )
        for row in reader:
            if None in row:
                raise ValueError(
                    "search result TSV contains rows with inconsistent column counts"
                )
            rows.append(
                {str(key): str(value) for key, value in row.items() if key is not None}
            )
    return source_columns, tuple(rows)


def _mapped_column_names(mapping: SearchResultColumnMapping) -> tuple[str, ...]:
    return tuple(
        dict.fromkeys(
            column_name
            for column_name in (
                mapping.run_id,
                mapping.spectrum_id,
                mapping.peptide,
                mapping.modified_peptide,
                mapping.charge,
                mapping.score,
                mapping.intensity,
                mapping.q_value,
                mapping.posterior_error_probability,
                mapping.protein_refs,
                mapping.decoy_label,
                mapping.contaminant_label,
            )
            if column_name is not None
        )
    )


def _mapped_field_values(
    row: dict[str, str],
    mapping: SearchResultColumnMapping,
) -> dict[str, str]:
    values: dict[str, str] = {}
    for role_name, column_name in (
        ("run_id", mapping.run_id),
        ("spectrum_id", mapping.spectrum_id),
        ("peptide", mapping.peptide),
        ("modified_peptide", mapping.modified_peptide),
        ("charge", mapping.charge),
        ("score", mapping.score),
        ("intensity", mapping.intensity),
        ("q_value", mapping.q_value),
        ("posterior_error_probability", mapping.posterior_error_probability),
        ("protein_refs", mapping.protein_refs),
        ("decoy_label", mapping.decoy_label),
        ("contaminant_label", mapping.contaminant_label),
    ):
        if column_name is None or column_name not in row:
            continue
        values[role_name] = row[column_name]
    return values


def _build_evidence_rows(
    *,
    source_path: Path,
    adapter_kind: SearchAdapterKind,
    source_rows: tuple[dict[str, str], ...],
    parse_report: PsmParseReport,
) -> tuple[SearchNormalizedEvidenceEntry, ...]:
    rejected_by_row_number = {
        rejected.row_number: rejected for rejected in parse_report.rejected_rows
    }
    accepted_index = 0
    mapped_columns = set(_mapped_column_names(parse_report.column_mapping))
    entries: list[SearchNormalizedEvidenceEntry] = []
    for row_index, raw_fields in enumerate(source_rows, start=2):
        rejected = rejected_by_row_number.get(row_index)
        if rejected is not None:
            entries.append(
                SearchNormalizedEvidenceEntry(
                    row_number=row_index,
                    accepted=False,
                    raw_fields=raw_fields,
                    mapped_field_values=_mapped_field_values(
                        raw_fields,
                        parse_report.column_mapping,
                    ),
                    unmapped_native_fields={
                        key: value
                        for key, value in raw_fields.items()
                        if key not in mapped_columns
                    },
                    normalized_record=None,
                    issues=rejected.issues,
                )
            )
            continue
        record = parse_report.accepted_records[accepted_index]
        accepted_index += 1
        mapped_field_values = _mapped_field_values(
            raw_fields, parse_report.column_mapping
        )
        original_identifiers = _build_original_identifiers(
            mapped_field_values=mapped_field_values,
            raw_fields=raw_fields,
        )
        entries.append(
            SearchNormalizedEvidenceEntry(
                row_number=row_index,
                accepted=True,
                raw_fields=raw_fields,
                mapped_field_values=mapped_field_values,
                unmapped_native_fields={
                    key: value
                    for key, value in raw_fields.items()
                    if key not in mapped_columns
                },
                normalized_record=record.model_copy(
                    update={
                        "provenance": ImportedEvidenceProvenance.from_single_row(
                            source_engine=adapter_kind.value,
                            source_file=str(source_path),
                            source_row_number=row_index,
                            original_identifiers=original_identifiers,
                        )
                    }
                ),
                issues=(),
            )
        )
    return tuple(entries)


def _build_original_identifiers(
    *,
    mapped_field_values: dict[str, str],
    raw_fields: dict[str, str],
) -> dict[str, str]:
    identifiers: dict[str, str] = {}
    for key in (
        "run_id",
        "spectrum_id",
        "peptide",
        "modified_peptide",
        "protein_refs",
    ):
        value = mapped_field_values.get(key, "").strip()
        if value:
            identifiers[key] = value
    if not identifiers:
        for key in ("ScanNr", "SpecId", "NativeID", "Precursor.Id", "EG.PrecursorId"):
            value = raw_fields.get(key, "").strip()
            if value:
                identifiers[key] = value
    return identifiers


def _required_mapping_columns(mapping: SearchResultColumnMapping) -> tuple[str, ...]:
    return (
        mapping.spectrum_id,
        mapping.peptide,
        mapping.charge,
        mapping.score,
    )


def _mapped_field_roles(mapping: SearchResultColumnMapping) -> dict[str, str]:
    return {
        role_name: column_name
        for role_name, column_name in (
            ("spectrum_id", mapping.spectrum_id),
            ("peptide", mapping.peptide),
            ("charge", mapping.charge),
            ("score", mapping.score),
            ("q_value", mapping.q_value),
            ("posterior_error_probability", mapping.posterior_error_probability),
            ("protein_refs", mapping.protein_refs),
            ("decoy_label", mapping.decoy_label),
        )
        if column_name is not None
    }


def assess_search_result_input(
    *,
    source_path: Path,
    adapter_kind: SearchAdapterKind,
    dialect_id: str = "default",
    mapping: SearchResultColumnMapping | None = None,
    additional_dialects: tuple[SearchAdapterDialectManifest, ...] = (),
) -> SearchInputAssessmentReport:
    """Assess whether a search input is sufficiently specified and compatible."""
    refusals: list[SearchInputRefusal] = []
    source_columns: tuple[str, ...] = ()
    row_count = 0
    try:
        dialect = resolve_search_adapter_dialect(
            adapter_kind=adapter_kind,
            dialect_id=dialect_id,
            additional_dialects=additional_dialects,
        )
    except ValueError as exc:
        return SearchInputAssessmentReport(
            adapter_kind=adapter_kind,
            dialect_id=dialect_id,
            valid=False,
            source_columns=(),
            row_count=0,
            refusals=(
                SearchInputRefusal(
                    kind=SearchInputRefusalKind.UNDER_SPECIFIED_INPUT,
                    code="unknown_adapter_dialect",
                    message=str(exc),
                    remediation_hint="register the adapter dialect explicitly or use a built-in dialect identifier",
                ),
            ),
        )
    manifest = manifest_for_dialect(adapter_kind=adapter_kind, dialect=dialect)
    resolved_mapping = (
        mapping or (None if dialect is None else dialect.mapping) or manifest.mapping
    )
    if resolved_mapping is None:
        refusals.append(
            SearchInputRefusal(
                kind=SearchInputRefusalKind.UNDER_SPECIFIED_INPUT,
                code="missing_column_mapping",
                message="generic adapter input requires an explicit column mapping",
                remediation_hint="provide a SearchResultColumnMapping for the generic input table",
            )
        )
        return SearchInputAssessmentReport(
            adapter_kind=adapter_kind,
            dialect_id=dialect_id,
            valid=False,
            source_columns=(),
            row_count=0,
            refusals=tuple(refusals),
        )
    try:
        source_columns, source_rows = _read_search_result_rows(source_path)
        row_count = len(source_rows)
    except ValueError as exc:
        return SearchInputAssessmentReport(
            adapter_kind=adapter_kind,
            dialect_id=dialect_id,
            valid=False,
            source_columns=(),
            row_count=0,
            refusals=(
                SearchInputRefusal(
                    kind=SearchInputRefusalKind.MALFORMED_INPUT,
                    code="malformed_search_table",
                    message=str(exc),
                    remediation_hint="provide a tab-delimited search table with a valid header row",
                ),
            ),
        )
    if row_count == 0:
        refusals.append(
            SearchInputRefusal(
                kind=SearchInputRefusalKind.UNDER_SPECIFIED_INPUT,
                code="empty_search_table",
                message="search result table does not contain any data rows",
                remediation_hint="provide at least one search-result row for normalization",
            )
        )
    missing_required = sorted(
        column
        for column in _required_mapping_columns(resolved_mapping)
        if column not in source_columns
    )
    if missing_required:
        refusals.append(
            SearchInputRefusal(
                kind=SearchInputRefusalKind.UNDER_SPECIFIED_INPUT,
                code="missing_required_columns",
                message=f"missing required search-result columns: {', '.join(missing_required)}",
                remediation_hint="align the mapping and input header so spectrum, peptide, charge, and score columns are present",
            )
        )
    family_policy = build_search_result_family_policy(manifest)
    if family_policy.requires_target_decoy_evidence and (
        resolved_mapping.decoy_label is None
        and resolved_mapping.protein_refs is None
        and not manifest.default_decoy_policy.protein_prefix
        and not manifest.default_decoy_policy.protein_suffix
    ):
        refusals.append(
            SearchInputRefusal(
                kind=SearchInputRefusalKind.SCIENTIFIC_INCOMPATIBILITY,
                code="missing_target_decoy_evidence",
                message="database target-decoy normalization requires explicit decoy evidence or protein references that support decoy inference",
                remediation_hint="provide a decoy label column or protein references with a decoy naming policy",
            )
        )
    if (
        family_policy.requires_protein_references
        and resolved_mapping.protein_refs is None
    ):
        refusals.append(
            SearchInputRefusal(
                kind=SearchInputRefusalKind.SCIENTIFIC_INCOMPATIBILITY,
                code="missing_protein_references",
                message="this adapter family expects protein references for downstream protein-level review",
                remediation_hint="map or export the engine protein-reference column before normalization",
            )
        )
    return SearchInputAssessmentReport(
        adapter_kind=adapter_kind,
        dialect_id=dialect_id,
        valid=not refusals,
        source_columns=source_columns,
        row_count=row_count,
        refusals=tuple(refusals),
    )


def build_search_adapter_field_accounting(
    normalization_report: SearchAdapterNormalizationReport,
) -> SearchAdapterFieldAccounting:
    """Summarize mapped, preserved, unsupported, and lost adapter fields."""
    mapping = normalization_report.parse_report.column_mapping
    mapped_columns = set(_mapped_column_names(mapping))
    source_columns = set(normalization_report.source_columns)
    supported_columns = (
        set(normalization_report.adapter_manifest.native_columns) or mapped_columns
    )
    return SearchAdapterFieldAccounting(
        source_columns=tuple(normalization_report.source_columns),
        mapped_columns=tuple(sorted(source_columns & mapped_columns)),
        preserved_native_only_columns=tuple(
            sorted((source_columns & supported_columns) - mapped_columns)
        ),
        unsupported_columns=tuple(sorted(source_columns - supported_columns)),
        lost_columns=tuple(sorted(supported_columns - source_columns)),
        mapped_field_roles=_mapped_field_roles(mapping),
    )

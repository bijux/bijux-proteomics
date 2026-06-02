# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Label-free quantification and differential abundance contracts."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from bijux_proteomics.chemistry import (
    canonicalize_modified_peptide,
    parse_modified_peptide,
)
from bijux_proteomics.domain.records import ImportedEvidenceProvenance
from bijux_proteomics.io.tables import (
    iter_delimited_row_chunks,
    read_delimited_table_header,
)

if TYPE_CHECKING:
    pass

from .input_models import (
    MissingValueKind,
    Ms1FeatureColumnMapping,
    Ms1FeatureParseReport,
    Ms1FeatureRecord,
    PrecursorIntensityColumnMapping,
    PrecursorIntensityParseReport,
    PrecursorIntensityRecord,
    QuantValidationIssue,
    RejectedMs1FeatureRow,
    RejectedPrecursorIntensityRow,
)


def _detect_delimiter(first_line: str) -> str:
    return "\t" if "\t" in first_line else ","


def _parse_protein_refs(raw_value: str | None, separator: str) -> tuple[str, ...]:
    if raw_value in (None, ""):
        return ()
    text = raw_value.strip() if raw_value is not None else ""
    refs = tuple(token.strip() for token in text.split(separator) if token.strip())
    return tuple(dict.fromkeys(refs))

def _row_issue(code: str, message: str, row_number: int) -> QuantValidationIssue:
    return QuantValidationIssue(code=code, message=message, row_number=row_number)

def parse_ms1_feature_table(
    path: Path,
    *,
    mapping: Ms1FeatureColumnMapping | None = None,
) -> Ms1FeatureParseReport:
    """Parse one MS1 feature quantification table into stable feature records."""
    return _parse_ms1_feature_table_impl(
        path,
        mapping=mapping,
        chunk_size_rows=None,
    )


def parse_ms1_feature_table_chunked(
    path: Path,
    *,
    mapping: Ms1FeatureColumnMapping | None = None,
    chunk_size_rows: int,
) -> Ms1FeatureParseReport:
    """Parse one MS1 feature table in stable row chunks."""

    return _parse_ms1_feature_table_impl(
        path,
        mapping=mapping,
        chunk_size_rows=chunk_size_rows,
    )


def _parse_ms1_feature_table_impl(
    path: Path,
    *,
    mapping: Ms1FeatureColumnMapping | None = None,
    chunk_size_rows: int | None,
) -> Ms1FeatureParseReport:
    """Parse one MS1 feature table under one optional chunking policy."""
    active_mapping = mapping or Ms1FeatureColumnMapping(
        sample_id="sample_id",
        peptide="peptide",
        intensity="intensity",
        protein_refs="proteins",
        feature_id="feature_id",
        charge="charge",
        mz="mz",
        retention_time_seconds="retention_time_seconds",
        missing_reason="missing_reason",
    )
    header = read_delimited_table_header(path)
    if header is None:
        return Ms1FeatureParseReport(total_rows=0, column_mapping=active_mapping)
    required_columns = {
        active_mapping.sample_id,
        active_mapping.peptide,
        active_mapping.intensity,
    }
    missing_columns = required_columns - set(header.fieldnames)
    if missing_columns:
        raise ValueError(
            "MS1 feature table is missing required columns: "
            + ", ".join(sorted(missing_columns))
        )

    accepted: list[Ms1FeatureRecord] = []
    rejected: list[RejectedMs1FeatureRow] = []
    row_chunks = (
        iter_delimited_row_chunks(path, chunk_size_rows=chunk_size_rows)
        if chunk_size_rows is not None
        else iter_delimited_row_chunks(path, chunk_size_rows=100_000)
    )
    for chunk in row_chunks:
        for row_offset, raw_fields in enumerate(chunk.rows):
            row_number = chunk.row_number_start + row_offset
            parsed_record, rejected_row = _parse_ms1_feature_row(
                raw_fields,
                row_number=row_number,
                mapping=active_mapping,
                source_path=path,
            )
            if rejected_row is not None:
                rejected.append(rejected_row)
                continue
            if parsed_record is None:
                raise RuntimeError(
                    "accepted MS1 feature parsing rows must produce a parsed record"
                )
            accepted.append(parsed_record)

    accepted = sorted(
        accepted,
        key=lambda record: (
            record.sample_id,
            record.canonical_peptide,
            record.feature_id,
        ),
    )
    return Ms1FeatureParseReport(
        total_rows=len(accepted) + len(rejected),
        accepted_records=tuple(accepted),
        rejected_rows=tuple(rejected),
        column_mapping=active_mapping,
    )


def parse_precursor_intensity_table(
    path: Path,
    *,
    mapping: PrecursorIntensityColumnMapping | None = None,
) -> PrecursorIntensityParseReport:
    """Parse one precursor-intensity table into stable precursor records."""
    return _parse_precursor_intensity_table_impl(
        path,
        mapping=mapping,
        chunk_size_rows=None,
    )


def parse_precursor_intensity_table_chunked(
    path: Path,
    *,
    mapping: PrecursorIntensityColumnMapping | None = None,
    chunk_size_rows: int,
) -> PrecursorIntensityParseReport:
    """Parse one precursor-intensity table in stable row chunks."""

    return _parse_precursor_intensity_table_impl(
        path,
        mapping=mapping,
        chunk_size_rows=chunk_size_rows,
    )


def _parse_precursor_intensity_table_impl(
    path: Path,
    *,
    mapping: PrecursorIntensityColumnMapping | None = None,
    chunk_size_rows: int | None,
) -> PrecursorIntensityParseReport:
    """Parse one precursor-intensity table under one optional chunking policy."""

    active_mapping = mapping or PrecursorIntensityColumnMapping(
        peptide="peptide",
        modified_peptide="modified_peptide",
        intensity="intensity",
        sample_id="sample_id",
        run_id="run_id",
        protein_refs="proteins",
        precursor_id="precursor_id",
        charge="charge",
        missing_reason="missing_reason",
    )
    header = read_delimited_table_header(path)
    if header is None:
        return PrecursorIntensityParseReport(
            total_rows=0,
            column_mapping=active_mapping,
        )
    required_columns = {active_mapping.peptide, active_mapping.intensity}
    missing_columns = required_columns - set(header.fieldnames)
    if missing_columns:
        raise ValueError(
            "precursor intensity table is missing required columns: "
            + ", ".join(sorted(missing_columns))
        )
    sample_column_present = (
        active_mapping.sample_id is not None
        and active_mapping.sample_id in header.fieldnames
    )
    run_column_present = (
        active_mapping.run_id is not None and active_mapping.run_id in header.fieldnames
    )
    if not sample_column_present and not run_column_present:
        expected_columns = tuple(
            column
            for column in (active_mapping.sample_id, active_mapping.run_id)
            if column is not None
        )
        raise ValueError(
            "precursor intensity table is missing required sample or run column: "
            + ", ".join(expected_columns)
        )

    accepted: list[PrecursorIntensityRecord] = []
    rejected: list[RejectedPrecursorIntensityRow] = []
    row_chunks = (
        iter_delimited_row_chunks(path, chunk_size_rows=chunk_size_rows)
        if chunk_size_rows is not None
        else iter_delimited_row_chunks(path, chunk_size_rows=100_000)
    )
    for chunk in row_chunks:
        for row_offset, raw_fields in enumerate(chunk.rows):
            row_number = chunk.row_number_start + row_offset
            parsed_record, rejected_row = _parse_precursor_intensity_row(
                raw_fields,
                row_number=row_number,
                mapping=active_mapping,
                source_path=path,
            )
            if rejected_row is not None:
                rejected.append(rejected_row)
                continue
            if parsed_record is None:
                raise RuntimeError(
                    "accepted precursor intensity parsing rows must produce a parsed record"
                )
            accepted.append(parsed_record)

    accepted = sorted(
        accepted,
        key=lambda record: (
            record.sample_id,
            record.canonical_peptide,
            record.precursor_id,
        ),
    )
    return PrecursorIntensityParseReport(
        total_rows=len(accepted) + len(rejected),
        accepted_records=tuple(accepted),
        rejected_rows=tuple(rejected),
        column_mapping=active_mapping,
    )


def _parse_ms1_feature_row(
    raw_fields: dict[str, str],
    *,
    row_number: int,
    mapping: Ms1FeatureColumnMapping,
    source_path: Path,
) -> tuple[Ms1FeatureRecord | None, RejectedMs1FeatureRow | None]:
    issues: list[QuantValidationIssue] = []
    sample_id = raw_fields.get(mapping.sample_id, "").strip()
    peptide = raw_fields.get(mapping.peptide, "").strip()
    intensity_token = raw_fields.get(mapping.intensity, "").strip()
    missing_reason = (
        raw_fields.get(mapping.missing_reason, "").strip()
        if mapping.missing_reason
        else ""
    )
    if not sample_id:
        issues.append(_row_issue("missing_sample_id", "missing sample identifier", row_number))
    if not peptide:
        issues.append(_row_issue("missing_peptide", "missing peptide sequence", row_number))
    canonical_peptide = peptide
    if peptide:
        try:
            canonical_peptide = canonicalize_modified_peptide(peptide)
        except ValueError as exc:
            issues.append(_row_issue("invalid_peptide_notation", str(exc), row_number))

    intensity: float | None
    missing_value_kind: MissingValueKind
    normalized_missing_reason = missing_reason.strip().lower()
    if not intensity_token:
        intensity = None
        missing_value_kind = (
            MissingValueKind.FILTERED
            if normalized_missing_reason == "filtered"
            else MissingValueKind.NOT_OBSERVED
        )
    else:
        try:
            intensity = float(intensity_token)
        except ValueError:
            issues.append(_row_issue("invalid_intensity", "invalid intensity value", row_number))
            intensity = None
        if intensity is not None and intensity < 0:
            issues.append(
                _row_issue("negative_intensity", "intensity must be non-negative", row_number)
            )
        if intensity is not None and intensity == 0:
            missing_value_kind = MissingValueKind.ZERO
        else:
            missing_value_kind = MissingValueKind.OBSERVED

    charge: int | None = None
    if mapping.charge:
        charge_token = raw_fields.get(mapping.charge, "").strip()
        if charge_token:
            try:
                charge = int(charge_token)
                if charge < 1:
                    raise ValueError
            except ValueError:
                issues.append(_row_issue("invalid_charge", "invalid charge value", row_number))

    mz: float | None = None
    if mapping.mz:
        mz_token = raw_fields.get(mapping.mz, "").strip()
        if mz_token:
            try:
                mz = float(mz_token)
                if mz <= 0:
                    raise ValueError
            except ValueError:
                issues.append(_row_issue("invalid_mz", "invalid precursor m/z value", row_number))

    retention_time_seconds: float | None = None
    if mapping.retention_time_seconds:
        rt_token = raw_fields.get(mapping.retention_time_seconds, "").strip()
        if rt_token:
            try:
                retention_time_seconds = float(rt_token)
                if retention_time_seconds < 0:
                    raise ValueError
            except ValueError:
                issues.append(
                    _row_issue("invalid_retention_time", "invalid retention time value", row_number)
                )

    protein_refs = _parse_protein_refs(
        raw_fields.get(mapping.protein_refs, "") if mapping.protein_refs else "",
        mapping.protein_separator,
    )
    if issues:
        return None, RejectedMs1FeatureRow(
            row_number=row_number,
            raw_fields=raw_fields,
            issues=tuple(issues),
        )
    feature_id = (
        raw_fields.get(mapping.feature_id, "").strip()
        if mapping.feature_id
        else f"feature-{row_number}"
    ) or f"feature-{row_number}"
    return (
        Ms1FeatureRecord(
            feature_id=feature_id,
            sample_id=sample_id,
            peptide=peptide,
            canonical_peptide=canonical_peptide,
            intensity=intensity,
            protein_refs=protein_refs,
            charge=charge,
            mz=mz,
            retention_time_seconds=retention_time_seconds,
            missing_value_kind=missing_value_kind,
            missing_reason=missing_reason or None,
            provenance=ImportedEvidenceProvenance.from_single_row(
                source_engine="ms1-feature-table",
                source_file=str(source_path),
                source_row_number=row_number,
                original_identifiers={
                    "feature_id": feature_id,
                    "sample_id": sample_id,
                    "peptide": peptide,
                },
            ),
        ),
        None,
    )


def _parse_precursor_intensity_row(
    raw_fields: dict[str, str],
    *,
    row_number: int,
    mapping: PrecursorIntensityColumnMapping,
    source_path: Path,
) -> tuple[PrecursorIntensityRecord | None, RejectedPrecursorIntensityRow | None]:
    issues: list[QuantValidationIssue] = []
    sample_token = (
        raw_fields.get(mapping.sample_id, "").strip()
        if mapping.sample_id is not None
        else ""
    )
    run_token = (
        raw_fields.get(mapping.run_id, "").strip()
        if mapping.run_id is not None
        else ""
    )
    sample_id = sample_token or run_token
    if not sample_id:
        issues.append(
            _row_issue(
                "missing_sample_or_run",
                "missing sample or run identifier",
                row_number,
            )
        )

    peptide_token = raw_fields.get(mapping.peptide, "").strip()
    modified_peptide_token = (
        raw_fields.get(mapping.modified_peptide, "").strip()
        if mapping.modified_peptide
        else ""
    )
    peptide_notation = modified_peptide_token or peptide_token
    if not peptide_notation:
        issues.append(
            _row_issue(
                "missing_peptide",
                "missing peptide or modified peptide identifier",
                row_number,
            )
        )
        peptide_sequence = ""
        canonical_peptide = ""
    else:
        try:
            canonical_peptide = canonicalize_modified_peptide(peptide_notation)
            peptide_sequence = peptide_token or parse_modified_peptide(
                canonical_peptide
            ).sequence
        except ValueError as exc:
            issues.append(_row_issue("invalid_peptide_notation", str(exc), row_number))
            peptide_sequence = peptide_token
            canonical_peptide = peptide_notation

    intensity_token = raw_fields.get(mapping.intensity, "").strip()
    missing_reason = (
        raw_fields.get(mapping.missing_reason, "").strip()
        if mapping.missing_reason
        else ""
    )
    normalized_missing_reason = missing_reason.strip().lower()
    intensity: float | None
    missing_value_kind: MissingValueKind
    if not intensity_token:
        intensity = None
        missing_value_kind = (
            MissingValueKind.FILTERED
            if normalized_missing_reason == "filtered"
            else MissingValueKind.NOT_OBSERVED
        )
    else:
        try:
            intensity = float(intensity_token)
        except ValueError:
            issues.append(
                _row_issue("invalid_intensity", "invalid intensity value", row_number)
            )
            intensity = None
        if intensity is not None and intensity < 0:
            issues.append(
                _row_issue("negative_intensity", "intensity must be non-negative", row_number)
            )
        if intensity is not None and intensity == 0.0:
            missing_value_kind = MissingValueKind.ZERO
        else:
            missing_value_kind = MissingValueKind.OBSERVED

    charge: int | None = None
    if mapping.charge:
        charge_token = raw_fields.get(mapping.charge, "").strip()
        if charge_token:
            try:
                charge = int(charge_token)
                if charge < 1:
                    raise ValueError
            except ValueError:
                issues.append(_row_issue("invalid_charge", "invalid charge value", row_number))

    protein_refs = _parse_protein_refs(
        raw_fields.get(mapping.protein_refs, "") if mapping.protein_refs else "",
        mapping.protein_separator,
    )
    precursor_id = (
        raw_fields.get(mapping.precursor_id, "").strip()
        if mapping.precursor_id
        else ""
    ) or f"precursor-{row_number}"
    if issues:
        return None, RejectedPrecursorIntensityRow(
            row_number=row_number,
            raw_fields=raw_fields,
            issues=tuple(issues),
        )
    return (
        PrecursorIntensityRecord(
            precursor_id=precursor_id,
            sample_id=sample_id,
            run_id=run_token or None,
            peptide_sequence=peptide_sequence,
            modified_peptide=modified_peptide_token or None,
            canonical_peptide=canonical_peptide,
            intensity=intensity,
            protein_refs=protein_refs,
            charge=charge,
            missing_value_kind=missing_value_kind,
            missing_reason=missing_reason or None,
            provenance=ImportedEvidenceProvenance.from_single_row(
                source_engine="precursor-intensity-table",
                source_file=str(source_path),
                source_row_number=row_number,
                original_identifiers={
                    "precursor_id": precursor_id,
                    "sample_id": sample_id,
                    "run_id": run_token,
                    "peptide": peptide_sequence,
                    "modified_peptide": modified_peptide_token or peptide_sequence,
                },
            ),
        ),
        None,
    )


__all__ = [
    "parse_ms1_feature_table",
    "parse_ms1_feature_table_chunked",
    "parse_precursor_intensity_table",
    "parse_precursor_intensity_table_chunked",
]

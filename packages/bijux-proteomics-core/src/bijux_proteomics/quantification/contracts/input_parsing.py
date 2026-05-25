# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Label-free quantification and differential abundance contracts."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import TYPE_CHECKING


from bijux_proteomics.chemistry import (
    canonicalize_modified_peptide,
    parse_modified_peptide,
)
from bijux_proteomics.domain.records import ImportedEvidenceProvenance

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

    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines:
        return Ms1FeatureParseReport(total_rows=0, column_mapping=active_mapping)
    reader = csv.DictReader(lines, delimiter=_detect_delimiter(lines[0]))
    if reader.fieldnames is None:
        raise ValueError("MS1 feature table must include a header row")
    required_columns = {
        active_mapping.sample_id,
        active_mapping.peptide,
        active_mapping.intensity,
    }
    missing_columns = required_columns - set(reader.fieldnames)
    if missing_columns:
        raise ValueError(
            "MS1 feature table is missing required columns: "
            + ", ".join(sorted(missing_columns))
        )

    accepted: list[Ms1FeatureRecord] = []
    rejected: list[RejectedMs1FeatureRow] = []
    for row_number, row in enumerate(reader, start=2):
        raw_fields = {
            str(key): str(value or "") for key, value in row.items() if key is not None
        }
        issues: list[QuantValidationIssue] = []
        sample_id = raw_fields.get(active_mapping.sample_id, "").strip()
        peptide = raw_fields.get(active_mapping.peptide, "").strip()
        intensity_token = raw_fields.get(active_mapping.intensity, "").strip()
        missing_reason = (
            raw_fields.get(active_mapping.missing_reason, "").strip()
            if active_mapping.missing_reason
            else ""
        )
        if not sample_id:
            issues.append(
                _row_issue("missing_sample_id", "missing sample identifier", row_number)
            )
        if not peptide:
            issues.append(
                _row_issue("missing_peptide", "missing peptide sequence", row_number)
            )
        canonical_peptide = peptide
        if peptide:
            try:
                canonical_peptide = canonicalize_modified_peptide(peptide)
            except ValueError as exc:
                issues.append(
                    _row_issue("invalid_peptide_notation", str(exc), row_number)
                )

        intensity: float | None
        missing_value_kind: MissingValueKind
        normalized_missing_reason = missing_reason.strip().lower()
        if not intensity_token:
            intensity = None
            if normalized_missing_reason == "filtered":
                missing_value_kind = MissingValueKind.FILTERED
            else:
                missing_value_kind = MissingValueKind.NOT_OBSERVED
        else:
            try:
                intensity = float(intensity_token)
            except ValueError:
                issues.append(
                    _row_issue(
                        "invalid_intensity", "invalid intensity value", row_number
                    )
                )
                intensity = None
            if intensity is not None and intensity < 0:
                issues.append(
                    _row_issue(
                        "negative_intensity",
                        "intensity must be non-negative",
                        row_number,
                    )
                )
            if intensity is not None and intensity == 0:
                missing_value_kind = MissingValueKind.ZERO
            else:
                missing_value_kind = MissingValueKind.OBSERVED

        charge: int | None = None
        if active_mapping.charge:
            charge_token = raw_fields.get(active_mapping.charge, "").strip()
            if charge_token:
                try:
                    charge = int(charge_token)
                    if charge < 1:
                        raise ValueError
                except ValueError:
                    issues.append(
                        _row_issue("invalid_charge", "invalid charge value", row_number)
                    )

        mz: float | None = None
        if active_mapping.mz:
            mz_token = raw_fields.get(active_mapping.mz, "").strip()
            if mz_token:
                try:
                    mz = float(mz_token)
                    if mz <= 0:
                        raise ValueError
                except ValueError:
                    issues.append(
                        _row_issue(
                            "invalid_mz", "invalid precursor m/z value", row_number
                        )
                    )

        retention_time_seconds: float | None = None
        if active_mapping.retention_time_seconds:
            rt_token = raw_fields.get(active_mapping.retention_time_seconds, "").strip()
            if rt_token:
                try:
                    retention_time_seconds = float(rt_token)
                    if retention_time_seconds < 0:
                        raise ValueError
                except ValueError:
                    issues.append(
                        _row_issue(
                            "invalid_retention_time",
                            "invalid retention time value",
                            row_number,
                        )
                    )

        protein_refs = _parse_protein_refs(
            raw_fields.get(active_mapping.protein_refs, "")
            if active_mapping.protein_refs
            else "",
            active_mapping.protein_separator,
        )

        if issues:
            rejected.append(
                RejectedMs1FeatureRow(
                    row_number=row_number,
                    raw_fields=raw_fields,
                    issues=tuple(issues),
                )
            )
            continue

        accepted.append(
            Ms1FeatureRecord(
                feature_id=(
                    raw_fields.get(active_mapping.feature_id, "").strip()
                    if active_mapping.feature_id
                    else f"feature-{row_number}"
                )
                or f"feature-{row_number}",
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
                    source_file=str(path),
                    source_row_number=row_number,
                    original_identifiers={
                        "feature_id": (
                            raw_fields.get(active_mapping.feature_id, "").strip()
                            if active_mapping.feature_id
                            else f"feature-{row_number}"
                        )
                        or f"feature-{row_number}",
                        "sample_id": sample_id,
                        "peptide": peptide,
                    },
                ),
            )
        )

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

    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines:
        return PrecursorIntensityParseReport(
            total_rows=0,
            column_mapping=active_mapping,
        )
    reader = csv.DictReader(lines, delimiter=_detect_delimiter(lines[0]))
    if reader.fieldnames is None:
        raise ValueError("precursor intensity table must include a header row")

    required_columns = {active_mapping.peptide, active_mapping.intensity}
    missing_columns = required_columns - set(reader.fieldnames)
    if missing_columns:
        raise ValueError(
            "precursor intensity table is missing required columns: "
            + ", ".join(sorted(missing_columns))
        )
    sample_column_present = (
        active_mapping.sample_id is not None
        and active_mapping.sample_id in reader.fieldnames
    )
    run_column_present = (
        active_mapping.run_id is not None and active_mapping.run_id in reader.fieldnames
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
    for row_number, row in enumerate(reader, start=2):
        raw_fields = {
            str(key): str(value or "") for key, value in row.items() if key is not None
        }
        issues: list[QuantValidationIssue] = []
        sample_token = (
            raw_fields.get(active_mapping.sample_id, "").strip()
            if active_mapping.sample_id is not None
            else ""
        )
        run_token = (
            raw_fields.get(active_mapping.run_id, "").strip()
            if active_mapping.run_id is not None
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

        peptide_token = raw_fields.get(active_mapping.peptide, "").strip()
        modified_peptide_token = (
            raw_fields.get(active_mapping.modified_peptide, "").strip()
            if active_mapping.modified_peptide
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
                issues.append(
                    _row_issue("invalid_peptide_notation", str(exc), row_number)
                )
                peptide_sequence = peptide_token
                canonical_peptide = peptide_notation

        intensity_token = raw_fields.get(active_mapping.intensity, "").strip()
        missing_reason = (
            raw_fields.get(active_mapping.missing_reason, "").strip()
            if active_mapping.missing_reason
            else ""
        )
        normalized_missing_reason = missing_reason.strip().lower()
        intensity: float | None
        missing_value_kind: MissingValueKind
        if not intensity_token:
            intensity = None
            if normalized_missing_reason == "filtered":
                missing_value_kind = MissingValueKind.FILTERED
            else:
                missing_value_kind = MissingValueKind.NOT_OBSERVED
        else:
            try:
                intensity = float(intensity_token)
            except ValueError:
                issues.append(
                    _row_issue(
                        "invalid_intensity", "invalid intensity value", row_number
                    )
                )
                intensity = None
            if intensity is not None and intensity < 0:
                issues.append(
                    _row_issue(
                        "negative_intensity",
                        "intensity must be non-negative",
                        row_number,
                    )
                )
            if intensity is not None and intensity == 0.0:
                missing_value_kind = MissingValueKind.ZERO
            else:
                missing_value_kind = MissingValueKind.OBSERVED

        charge: int | None = None
        if active_mapping.charge:
            charge_token = raw_fields.get(active_mapping.charge, "").strip()
            if charge_token:
                try:
                    charge = int(charge_token)
                    if charge < 1:
                        raise ValueError
                except ValueError:
                    issues.append(
                        _row_issue("invalid_charge", "invalid charge value", row_number)
                    )

        protein_refs = _parse_protein_refs(
            raw_fields.get(active_mapping.protein_refs, "")
            if active_mapping.protein_refs
            else "",
            active_mapping.protein_separator,
        )

        precursor_id = (
            raw_fields.get(active_mapping.precursor_id, "").strip()
            if active_mapping.precursor_id
            else ""
        ) or f"precursor-{row_number}"
        if issues:
            rejected.append(
                RejectedPrecursorIntensityRow(
                    row_number=row_number,
                    raw_fields=raw_fields,
                    issues=tuple(issues),
                )
            )
            continue

        accepted.append(
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
                    source_file=str(path),
                    source_row_number=row_number,
                    original_identifiers={
                        "precursor_id": precursor_id,
                        "sample_id": sample_id,
                        "run_id": run_token,
                        "peptide": peptide_sequence,
                        "modified_peptide": modified_peptide_token or peptide_sequence,
                    },
                ),
            )
        )

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

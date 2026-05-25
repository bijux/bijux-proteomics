# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi
# ruff: noqa: F401

"""Search-result parsing, export, and ordering surfaces."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
import csv
from enum import StrEnum
import hashlib
import json
import math
from pathlib import Path
from typing import TYPE_CHECKING

from pydantic import ConfigDict, Field, field_validator, model_validator

from bijux_proteomics.chemistry import (
    canonicalize_modified_peptide,
    parse_modified_peptide,
)
from bijux_proteomics.domain.records import (
    ImportedEvidenceProvenance,
    ModifiedPeptide as CanonicalModifiedPeptide,
    PSMRecord as CanonicalPsmRecord,
    PeptideRecord as CanonicalPeptideRecord,
    ProteinGroup as CanonicalProteinGroup,
    ProteinRecord as CanonicalProteinRecord,
    RejectedEvidence as CanonicalRejectedEvidence,
    TargetDecoyState,
)
from bijux_proteomics._output_tables import write_output_table_tsv
from bijux_proteomics._scientific_tables import (
    ScientificTableRejectedRow,
    ScientificTableValidationIssue,
    build_psm_table_schema,
    validate_scientific_table,
)
from bijux_proteomics.sequences.core import NormalizedProteinRecord
from bijux_proteomics.sequences.peptide_uniqueness_index import (
    build_peptide_uniqueness_index,
)

if TYPE_CHECKING:
    from bijux_proteomics.identification.cross_run_reproducibility import (
        RunDetectionContext,
    )
from bijux_proteomics._tabular import render_rows_tsv
from bijux_proteomics_foundation import DocumentSchema, JsonModel
from bijux_proteomics.identification.contracts.psm import (
    PsmParseReport,
    PsmRecord,
    PsmSortField,
    RejectedPsmRow,
    SearchResultColumnMapping,
    SearchResultValidationIssue,
    TargetDecoyLabel,
    TargetDecoyLabelPolicy,
    _derive_canonical_psm_peptide_fields,
    _parse_contaminant_label,
    _parse_protein_refs,
    _rank_label,
    _raise_on_target_decoy_accession_collisions,
    classify_target_decoy_contaminant,
    validate_target_decoy_policy,
)

def _row_issue(code: str, message: str, row_number: int) -> SearchResultValidationIssue:
    return SearchResultValidationIssue(
        code=code, message=message, row_number=row_number
    )


def _parse_psm_row(
    row: dict[str, str],
    *,
    row_number: int,
    mapping: SearchResultColumnMapping,
    decoy_policy: TargetDecoyLabelPolicy,
) -> PsmRecord:
    issues: list[SearchResultValidationIssue] = []

    run_id = None
    if mapping.run_id:
        run_id = row.get(mapping.run_id, "").strip() or None

    spectrum_id = row.get(mapping.spectrum_id, "").strip()
    if not spectrum_id:
        issues.append(
            _row_issue("missing_spectrum_id", "missing spectrum identifier", row_number)
        )

    peptide = row.get(mapping.peptide, "").strip()
    if not peptide:
        issues.append(
            _row_issue("missing_peptide", "missing peptide sequence", row_number)
        )

    modified_peptide_token = None
    if mapping.modified_peptide:
        modified_peptide_token = row.get(mapping.modified_peptide, "").strip() or None

    try:
        charge = int(row.get(mapping.charge, "").strip())
        if charge < 1:
            raise ValueError
    except ValueError:
        issues.append(_row_issue("invalid_charge", "invalid charge value", row_number))
        charge = 0

    try:
        score = float(row.get(mapping.score, "").strip())
    except ValueError:
        issues.append(_row_issue("invalid_score", "invalid score value", row_number))
        score = 0.0

    intensity: float | None = None
    if mapping.intensity:
        intensity_token = row.get(mapping.intensity, "").strip()
        if intensity_token:
            try:
                intensity = float(intensity_token)
                if intensity < 0:
                    raise ValueError
            except ValueError:
                issues.append(
                    _row_issue(
                        "invalid_intensity", "invalid intensity value", row_number
                    )
                )

    q_value: float | None = None
    if mapping.q_value:
        q_token = row.get(mapping.q_value, "").strip()
        if q_token:
            try:
                q_value = float(q_token)
                if q_value < 0:
                    raise ValueError
            except ValueError:
                issues.append(
                    _row_issue("invalid_q_value", "invalid q-value", row_number)
                )

    posterior_error_probability: float | None = None
    if mapping.posterior_error_probability:
        pep_token = row.get(mapping.posterior_error_probability, "").strip()
        if pep_token:
            try:
                posterior_error_probability = float(pep_token)
                if posterior_error_probability < 0 or posterior_error_probability > 1:
                    raise ValueError
            except ValueError:
                issues.append(
                    _row_issue(
                        "invalid_posterior_error_probability",
                        "invalid posterior error probability",
                        row_number,
                    )
                )

    protein_refs = _parse_protein_refs(
        row.get(mapping.protein_refs) if mapping.protein_refs else None,
        mapping.protein_separator,
    )
    explicit_label = row.get(mapping.decoy_label) if mapping.decoy_label else None
    explicit_contaminant_label = None
    if mapping.contaminant_label:
        try:
            explicit_contaminant_label = _parse_contaminant_label(
                row.get(mapping.contaminant_label)
            )
        except ValueError:
            issues.append(
                _row_issue(
                    "invalid_contaminant_label",
                    "invalid contaminant label",
                    row_number,
                )
            )

    canonical_peptide = peptide
    peptide_sequence = None
    modified_peptide = None
    if modified_peptide_token:
        try:
            canonical_peptide, peptide_sequence, modified_peptide = (
                _derive_canonical_psm_peptide_fields(modified_peptide_token)
            )
        except ValueError as exc:
            issues.append(_row_issue("invalid_peptide_notation", str(exc), row_number))
    elif peptide:
        try:
            canonical_peptide, peptide_sequence, modified_peptide = (
                _derive_canonical_psm_peptide_fields(peptide)
            )
        except ValueError as exc:
            issues.append(_row_issue("invalid_peptide_notation", str(exc), row_number))

    if issues:
        raise ValueError(
            RejectedPsmRow(
                row_number=row_number, raw_fields=row, issues=tuple(issues)
            ).to_stable_json()
        )

    classification = classify_target_decoy_contaminant(
        protein_refs=protein_refs,
        target_decoy_label=explicit_label,
        explicit_contaminant_label=explicit_contaminant_label,
        policy=decoy_policy,
    )

    return PsmRecord(
        run_id=run_id,
        spectrum_id=spectrum_id,
        peptide=peptide,
        peptide_sequence=peptide_sequence,
        modified_peptide=modified_peptide,
        canonical_peptide=canonical_peptide,
        charge=charge,
        score=score,
        intensity=intensity,
        q_value=q_value,
        posterior_error_probability=posterior_error_probability,
        protein_refs=protein_refs,
        target_decoy_label=classification.target_decoy_label,
        contaminant_flag=classification.contaminant_flag,
        target_decoy_contaminant_class=(
            classification.target_decoy_contaminant_class
        ),
    )


def parse_psm_tsv(
    path: Path,
    *,
    mapping: SearchResultColumnMapping,
    decoy_policy: TargetDecoyLabelPolicy | None = None,
) -> PsmParseReport:
    """Parse a generic peptide-spectrum match TSV into stable records."""
    active_policy = decoy_policy or TargetDecoyLabelPolicy()
    accepted_records: list[PsmRecord] = []
    rejected_rows: list[RejectedPsmRow] = []
    validation_report = validate_scientific_table(
        path,
        schema=build_psm_table_schema(mapping),
    )
    header_issues = _scientific_header_validation_issues(validation_report.rejected_rows)
    if header_issues:
        raise ValueError(_scientific_header_error_message(header_issues[0], path))

    rejected_rows.extend(
        _rejected_psm_rows_from_scientific_validation(validation_report.rejected_rows)
    )

    for row in validation_report.accepted_rows:
        normalized_row = row.raw_values
        try:
            accepted_records.append(
                _parse_psm_row(
                    normalized_row,
                    row_number=row.row_number,
                    mapping=mapping,
                    decoy_policy=active_policy,
                )
            )
        except ValueError as exc:
            rejected_rows.append(RejectedPsmRow.model_validate_json(str(exc)))

    return PsmParseReport(
        total_rows=len(accepted_records) + len(rejected_rows),
        accepted_records=tuple(accepted_records),
        rejected_rows=tuple(rejected_rows),
        column_mapping=mapping,
    )


def normalize_psm_records(records: tuple[PsmRecord, ...]) -> tuple[PsmRecord, ...]:
    """Return a stable normalized PSM ordering for downstream exports."""
    return tuple(
        sorted(
            records,
            key=lambda record: (
                record.run_id or "",
                record.spectrum_id,
                record.q_value if record.q_value is not None else float("inf"),
                -record.score,
                record.canonical_peptide,
                record.charge,
            ),
        )
    )


def export_psm_jsonl(records: tuple[PsmRecord, ...], path: Path) -> None:
    """Write normalized PSM records as stable JSONL."""
    normalized = normalize_psm_records(records)
    with path.open("w", encoding="utf-8") as handle:
        for record in normalized:
            handle.write(
                json.dumps(record.to_dict(), sort_keys=True, separators=(",", ":"))
            )
            handle.write("\n")


def export_psm_tsv(records: tuple[PsmRecord, ...], path: Path) -> None:
    """Write normalized PSM records as a stable TSV table."""
    normalized = normalize_psm_records(records)
    content = render_rows_tsv(
        fieldnames=(
            "run_id",
            "spectrum_id",
            "peptide_sequence",
            "peptide",
            "modified_peptide",
            "canonical_peptide",
            "charge",
            "score",
            "intensity",
            "q_value",
            "posterior_error_probability",
            "local_fdr",
            "error_rate_provenance",
            "protein_refs",
            "target_decoy_label",
            "target_decoy_contaminant_class",
            "contaminant_flag",
            *ImportedEvidenceProvenance.tsv_header(),
        ),
        rows=tuple(
            {
                "run_id": record.run_id,
                "spectrum_id": record.spectrum_id,
                "peptide_sequence": record.peptide_sequence,
                "peptide": record.peptide,
                "modified_peptide": record.modified_peptide,
                "canonical_peptide": record.canonical_peptide,
                "charge": record.charge,
                "score": record.score,
                "intensity": record.intensity,
                "q_value": record.q_value,
                "posterior_error_probability": record.posterior_error_probability,
                "local_fdr": record.local_fdr,
                "error_rate_provenance": record.error_rate_provenance,
                "protein_refs": ";".join(record.protein_refs),
                "target_decoy_label": record.target_decoy_label.value,
                "target_decoy_contaminant_class": (
                    record.target_decoy_contaminant_class.value
                ),
                "contaminant_flag": record.contaminant_flag,
                **dict(
                    zip(
                        ImportedEvidenceProvenance.tsv_header(),
                        (
                            record.provenance.to_tsv_row()
                            if record.provenance is not None
                            else ("", "", "", "")
                        ),
                        strict=True,
                    )
                ),
            }
            for record in normalized
        ),
    )
    write_output_table_tsv(path, content)


def _scientific_header_validation_issues(
    rejected_rows: tuple[ScientificTableRejectedRow, ...],
) -> tuple[ScientificTableValidationIssue, ...]:
    if not rejected_rows:
        return ()
    first_row = rejected_rows[0]
    issues = getattr(first_row, "issues", ())
    if getattr(first_row, "row_number", None) != 1 or not issues:
        return ()
    first_issue = issues[0]
    if first_issue.code not in {"missing_column", "missing_header", "empty_table"}:
        return ()
    return tuple(issues)


def _scientific_header_error_message(
    issue: ScientificTableValidationIssue,
    path: Path,
) -> str:
    code = issue.code
    column = issue.column
    if code == "missing_header":
        return "PSM TSV must include a header row"
    if code == "empty_table":
        return "PSM TSV must include at least one data row"
    if code == "missing_column" and isinstance(column, str):
        return f"missing required PSM column {column!r}"
    if issue.message:
        return issue.message
    return f"unable to parse PSM table {path}"


def _rejected_psm_rows_from_scientific_validation(
    rejected_rows: tuple[ScientificTableRejectedRow, ...],
) -> list[RejectedPsmRow]:
    translated: list[RejectedPsmRow] = []
    for row in rejected_rows:
        if row.row_number == 1 and row.issues and row.issues[0].code in {
            "missing_column",
            "missing_header",
            "empty_table",
        }:
            continue
        translated.append(
            RejectedPsmRow(
                row_number=row.row_number,
                raw_fields=row.raw_values,
                issues=tuple(
                    _psm_issue_from_scientific_issue(issue) for issue in row.issues
                ),
            )
        )
    return translated


def _psm_issue_from_scientific_issue(
    issue: ScientificTableValidationIssue,
) -> SearchResultValidationIssue:
    if issue.code == "missing_value":
        if issue.column == "spectrum_id":
            return _row_issue(
                "missing_spectrum_id", "missing spectrum identifier", issue.row_number
            )
        if issue.column == "peptide":
            return _row_issue(
                "missing_peptide", "missing peptide sequence", issue.row_number
            )
        if issue.column == "charge":
            return _row_issue("invalid_charge", "invalid charge value", issue.row_number)
        if issue.column == "score":
            return _row_issue("invalid_score", "invalid score value", issue.row_number)
    if issue.code == "wrong_type":
        if issue.column == "charge":
            return _row_issue("invalid_charge", "invalid charge value", issue.row_number)
        if issue.column == "score":
            return _row_issue("invalid_score", "invalid score value", issue.row_number)
        if issue.column == "intensity":
            return _row_issue(
                "invalid_intensity", "invalid intensity value", issue.row_number
            )
        if issue.column == "q_value":
            return _row_issue("invalid_q_value", "invalid q-value", issue.row_number)
    if issue.code == "negative_intensity":
        return _row_issue("invalid_intensity", "invalid intensity value", issue.row_number)
    if issue.code == "invalid_q_value":
        return _row_issue("invalid_q_value", "invalid q-value", issue.row_number)
    if issue.code == "duplicate_identifier":
        return _row_issue(
            "duplicate_spectrum_id",
            issue.message,
            issue.row_number,
        )
    return _row_issue(issue.code, issue.message, issue.row_number)


def sort_psm_records(
    records: tuple[PsmRecord, ...],
    *,
    by: PsmSortField = PsmSortField.SPECTRUM,
) -> tuple[PsmRecord, ...]:
    """Sort PSMs by one stable policy."""
    if by is PsmSortField.SPECTRUM:
        return tuple(
            sorted(
                records,
                key=lambda record: (
                    record.spectrum_id,
                    -record.score,
                    record.canonical_peptide,
                ),
            )
        )
    if by is PsmSortField.SCORE:
        return tuple(
            sorted(
                records,
                key=lambda record: (
                    -record.score,
                    record.spectrum_id,
                    record.canonical_peptide,
                ),
            )
        )
    if by is PsmSortField.Q_VALUE:
        return tuple(
            sorted(
                records,
                key=lambda record: (
                    record.q_value if record.q_value is not None else float("inf"),
                    record.spectrum_id,
                    -record.score,
                    record.canonical_peptide,
                ),
            )
        )
    return tuple(
        sorted(
            records,
            key=lambda record: (
                record.canonical_peptide,
                record.spectrum_id,
                -record.score,
            ),
        )
    )


def select_best_psm_per_spectrum(
    records: tuple[PsmRecord, ...],
) -> tuple[PsmRecord, ...]:
    """Select one best PSM per spectrum with stable tie-breaking."""
    best_by_spectrum: dict[str, PsmRecord] = {}
    for record in records:
        current = best_by_spectrum.get(record.spectrum_id)
        if current is None:
            best_by_spectrum[record.spectrum_id] = record
            continue
        replacement_key = (
            record.score,
            -(record.q_value if record.q_value is not None else float("inf")),
            -_rank_label(record.target_decoy_label),
            record.canonical_peptide,
        )
        current_key = (
            current.score,
            -(current.q_value if current.q_value is not None else float("inf")),
            -_rank_label(current.target_decoy_label),
            current.canonical_peptide,
        )
        if replacement_key > current_key:
            best_by_spectrum[record.spectrum_id] = record
    return tuple(best_by_spectrum[key] for key in sorted(best_by_spectrum))

__all__ = [
    'parse_psm_tsv',
    'normalize_psm_records',
    'export_psm_jsonl',
    'export_psm_tsv',
    'sort_psm_records',
    'select_best_psm_per_spectrum',
]

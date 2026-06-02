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
from bijux_proteomics.io.tables import (
    iter_delimited_row_chunks,
    read_delimited_table_header,
)
from bijux_proteomics._output_tables import write_output_table_tsv
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
                if q_value < 0 or q_value > 1:
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

    return _parse_psm_tsv_impl(
        path,
        mapping=mapping,
        decoy_policy=decoy_policy,
        chunk_size_rows=None,
    )


def parse_psm_tsv_chunked(
    path: Path,
    *,
    mapping: SearchResultColumnMapping,
    decoy_policy: TargetDecoyLabelPolicy | None = None,
    chunk_size_rows: int,
) -> PsmParseReport:
    """Parse a generic peptide-spectrum match TSV in stable row chunks."""

    return _parse_psm_tsv_impl(
        path,
        mapping=mapping,
        decoy_policy=decoy_policy,
        chunk_size_rows=chunk_size_rows,
    )


def _parse_psm_tsv_impl(
    path: Path,
    *,
    mapping: SearchResultColumnMapping,
    decoy_policy: TargetDecoyLabelPolicy | None = None,
    chunk_size_rows: int | None,
) -> PsmParseReport:
    """Parse a generic peptide-spectrum match TSV under one optional chunking policy."""

    active_policy = decoy_policy or TargetDecoyLabelPolicy()
    header = read_delimited_table_header(path)
    if header is None:
        raise ValueError("PSM TSV must include at least one data row")
    missing_columns = _required_psm_columns(mapping) - set(header.fieldnames)
    if missing_columns:
        first_missing = sorted(missing_columns)[0]
        raise ValueError(f"missing required PSM column {first_missing!r}")
    accepted_records: list[PsmRecord] = []
    rejected_rows: list[RejectedPsmRow] = []
    row_chunks = (
        iter_delimited_row_chunks(path, chunk_size_rows=chunk_size_rows)
        if chunk_size_rows is not None
        else iter_delimited_row_chunks(path, chunk_size_rows=100_000)
    )
    for chunk in row_chunks:
        for row_offset, normalized_row in enumerate(chunk.rows):
            row_number = chunk.row_number_start + row_offset
            try:
                accepted_records.append(
                    _parse_psm_row(
                        normalized_row,
                        row_number=row_number,
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


def _required_psm_columns(mapping: SearchResultColumnMapping) -> set[str]:
    return {
        mapping.spectrum_id,
        mapping.peptide,
        mapping.charge,
        mapping.score,
    }


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
    'parse_psm_tsv_chunked',
    'normalize_psm_records',
    'export_psm_jsonl',
    'export_psm_tsv',
    'sort_psm_records',
    'select_best_psm_per_spectrum',
]

# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

"""Validation-result TSV loading for validation evidence cards."""

from __future__ import annotations

import csv
from pathlib import Path

import click

from bijux_proteomics.sequences.peptide_uniqueness_index import (
    PeptideUniquenessClass,
)
from bijux_proteomics.targeted.result_validation import (
    TargetedValidationReasonCode,
    TargetedValidationVerdict,
)
from bijux_proteomics.targeted.validation_evidence_cards import (
    ValidationEvidenceResultAssayInput,
    ValidationEvidenceResultInput,
)

from ...targeted_selection_io.field_parsing import _split_semicolon_field


def _load_validation_evidence_results(
    path: Path,
) -> tuple[ValidationEvidenceResultInput, ...]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames is None:
            raise click.ClickException(
                "validation TSV must include a header row for validation evidence cards"
            )
        required_columns = {
            "candidate_id",
            "verdict",
            "validation_log2_effect",
            "assay_evidence_count",
            "confirmed_assay_count",
            "contradicted_assay_count",
            "inconclusive_assay_count",
            "reason_codes",
            "note",
        }
        missing_columns = required_columns.difference(reader.fieldnames)
        if missing_columns:
            raise click.ClickException(
                "validation TSV is missing required columns for validation evidence cards: "
                + ", ".join(sorted(missing_columns))
            )
        rows: list[ValidationEvidenceResultInput] = []
        for row_number, row in enumerate(reader, start=2):
            try:
                rows.append(
                    ValidationEvidenceResultInput(
                        candidate_id=str(row.get("candidate_id", "")).strip(),
                        verdict=TargetedValidationVerdict(
                            str(row.get("verdict", "")).strip()
                        ),
                        validation_log2_effect=(
                            None
                            if not str(row.get("validation_log2_effect", "")).strip()
                            else float(
                                str(row.get("validation_log2_effect", "")).strip()
                            )
                        ),
                        assay_evidence_count=int(
                            str(row.get("assay_evidence_count", "")).strip()
                        ),
                        confirmed_assay_count=int(
                            str(row.get("confirmed_assay_count", "")).strip()
                        ),
                        contradicted_assay_count=int(
                            str(row.get("contradicted_assay_count", "")).strip()
                        ),
                        inconclusive_assay_count=int(
                            str(row.get("inconclusive_assay_count", "")).strip()
                        ),
                        reason_codes=tuple(
                            TargetedValidationReasonCode(code)
                            for code in _split_semicolon_field(
                                row.get("reason_codes", "")
                            )
                        ),
                        note=str(row.get("note", "")).strip(),
                    )
                )
            except Exception as exc:  # noqa: BLE001
                raise click.ClickException(
                    f"invalid validation row {row_number} in {path.name!r}: {exc}"
                ) from exc
    return tuple(rows)


def _load_validation_evidence_result_assays(
    path: Path,
) -> tuple[ValidationEvidenceResultAssayInput, ...]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames is None:
            raise click.ClickException(
                "validation-evidence TSV must include a header row for validation evidence cards"
            )
        required_columns = {
            "candidate_id",
            "assay_entry_id",
            "peptide_sequence",
            "canonical_peptide",
            "precursor_charge",
            "uniqueness_class",
            "validation_log2_effect",
            "verdict",
            "reason_codes",
            "note",
        }
        missing_columns = required_columns.difference(reader.fieldnames)
        if missing_columns:
            raise click.ClickException(
                "validation-evidence TSV is missing required columns for validation evidence cards: "
                + ", ".join(sorted(missing_columns))
            )
        rows: list[ValidationEvidenceResultAssayInput] = []
        for row_number, row in enumerate(reader, start=2):
            try:
                rows.append(
                    ValidationEvidenceResultAssayInput(
                        candidate_id=str(row.get("candidate_id", "")).strip(),
                        assay_entry_id=str(row.get("assay_entry_id", "")).strip(),
                        peptide_sequence=str(row.get("peptide_sequence", "")).strip(),
                        canonical_peptide=str(row.get("canonical_peptide", "")).strip(),
                        precursor_charge=int(
                            str(row.get("precursor_charge", "")).strip()
                        ),
                        uniqueness_class=PeptideUniquenessClass(
                            str(row.get("uniqueness_class", "")).strip()
                        ),
                        validation_log2_effect=(
                            None
                            if not str(row.get("validation_log2_effect", "")).strip()
                            else float(
                                str(row.get("validation_log2_effect", "")).strip()
                            )
                        ),
                        verdict=TargetedValidationVerdict(
                            str(row.get("verdict", "")).strip()
                        ),
                        reason_codes=tuple(
                            TargetedValidationReasonCode(code)
                            for code in _split_semicolon_field(
                                row.get("reason_codes", "")
                            )
                        ),
                        note=str(row.get("note", "")).strip(),
                    )
                )
            except Exception as exc:  # noqa: BLE001
                raise click.ClickException(
                    f"invalid validation-evidence row {row_number} in {path.name!r}: {exc}"
                ) from exc
    return tuple(rows)


__all__ = (
    "_load_validation_evidence_result_assays",
    "_load_validation_evidence_results",
)

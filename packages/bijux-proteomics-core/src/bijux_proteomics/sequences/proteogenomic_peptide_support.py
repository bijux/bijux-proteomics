# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Proteogenomic peptide support classification over reference and variant proteomes."""

from __future__ import annotations

from collections import defaultdict
import csv
from enum import StrEnum
from io import StringIO
from pathlib import Path
from typing import Sequence

from pydantic import ConfigDict, Field

from bijux_proteomics.sequences.core import (
    NormalizedProteinRecord,
    canonicalize_protein_reference,
)
from bijux_proteomics_foundation import JsonModel


class ProteogenomicPeptideSupportClass(StrEnum):
    """Stable proteogenomic evidence classes over observed peptides."""

    REFERENCE_ONLY = "reference_only"
    VARIANT_ONLY = "variant_only"
    SHARED = "shared"
    AMBIGUOUS = "ambiguous"


class ProteogenomicPeptideReference(JsonModel):
    """One peptide-backed evidence item to classify against reference and variant support."""

    model_config = ConfigDict(extra="forbid")

    evidence_key: str = Field(..., min_length=1)
    peptide_sequences: tuple[str, ...] = Field(default_factory=tuple)
    target_protein_refs: tuple[str, ...] = Field(default_factory=tuple)


class ProteogenomicVariantPeptideColumnMapping(JsonModel):
    """Column mapping for one explicit variant-peptide support table."""

    model_config = ConfigDict(extra="forbid")

    peptide_sequence: str = Field(..., min_length=1)
    variant_protein_ref: str | None = None
    reference_protein_ref: str | None = None
    variant_label: str | None = None


class ProteogenomicVariantPeptideRecord(JsonModel):
    """One explicit variant-peptide support row."""

    model_config = ConfigDict(extra="forbid")

    peptide_sequence: str = Field(..., min_length=1)
    variant_protein_ref: str | None = None
    reference_protein_ref: str | None = None
    variant_label: str | None = None
    metadata: dict[str, str] = Field(default_factory=dict)


class RejectedProteogenomicVariantPeptideRow(JsonModel):
    """One rejected variant-peptide support row."""

    model_config = ConfigDict(extra="forbid")

    row_number: int = Field(..., ge=2)
    values: dict[str, str] = Field(default_factory=dict)
    reason: str = Field(..., min_length=1)


class ProteogenomicVariantPeptideTableSummary(JsonModel):
    """Stable summary over one variant-peptide support table parse."""

    model_config = ConfigDict(extra="forbid")

    accepted_record_count: int = Field(..., ge=0)
    rejected_row_count: int = Field(..., ge=0)
    distinct_peptide_count: int = Field(..., ge=0)
    distinct_variant_protein_ref_count: int = Field(..., ge=0)
    distinct_reference_protein_ref_count: int = Field(..., ge=0)


class ProteogenomicVariantPeptideTableReport(JsonModel):
    """Governed parse report for one explicit variant-peptide support table."""

    model_config = ConfigDict(extra="forbid")

    source_path: str = Field(..., min_length=1)
    total_rows: int = Field(..., ge=0)
    accepted_records: tuple[ProteogenomicVariantPeptideRecord, ...] = Field(
        default_factory=tuple
    )
    rejected_rows: tuple[RejectedProteogenomicVariantPeptideRow, ...] = Field(
        default_factory=tuple
    )
    column_mapping: ProteogenomicVariantPeptideColumnMapping
    summary: ProteogenomicVariantPeptideTableSummary
    note: str = Field(..., min_length=1)


class ProteogenomicPeptideEvidence(JsonModel):
    """One peptide-level proteogenomic support classification."""

    model_config = ConfigDict(extra="forbid")

    peptide_sequence: str = Field(..., min_length=1)
    support_class: ProteogenomicPeptideSupportClass
    matched_reference_protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    matched_variant_protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    variant_labels: tuple[str, ...] = Field(default_factory=tuple)


class ProteogenomicPeptideSupportEntry(JsonModel):
    """Proteogenomic support summary over one peptide-backed evidence item."""

    model_config = ConfigDict(extra="forbid")

    evidence_key: str = Field(..., min_length=1)
    target_protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    support_class: ProteogenomicPeptideSupportClass
    support_reason: str = Field(..., min_length=1)
    peptide_evidence: tuple[ProteogenomicPeptideEvidence, ...] = Field(
        default_factory=tuple
    )
    reference_only_peptides: tuple[str, ...] = Field(default_factory=tuple)
    variant_only_peptides: tuple[str, ...] = Field(default_factory=tuple)
    shared_peptides: tuple[str, ...] = Field(default_factory=tuple)
    ambiguous_peptides: tuple[str, ...] = Field(default_factory=tuple)
    matched_reference_protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    matched_variant_protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    variant_labels: tuple[str, ...] = Field(default_factory=tuple)


class ProteogenomicPeptideSupportSummary(JsonModel):
    """Stable summary over one proteogenomic peptide-support pass."""

    model_config = ConfigDict(extra="forbid")

    evidence_count: int = Field(..., ge=0)
    reference_only_count: int = Field(..., ge=0)
    variant_only_count: int = Field(..., ge=0)
    shared_count: int = Field(..., ge=0)
    ambiguous_count: int = Field(..., ge=0)


class ProteogenomicPeptideSupportReport(JsonModel):
    """Owned proteogenomic support report over observed peptide-backed evidence."""

    model_config = ConfigDict(extra="forbid")

    entries: tuple[ProteogenomicPeptideSupportEntry, ...] = Field(default_factory=tuple)
    summary: ProteogenomicPeptideSupportSummary
    note: str = Field(..., min_length=1)


class _ProteinLookup(JsonModel):
    model_config = ConfigDict(extra="forbid")

    stable_ref: str
    lookup_residues: str


def parse_proteogenomic_variant_peptide_table(
    path: Path,
    *,
    mapping: ProteogenomicVariantPeptideColumnMapping | None = None,
) -> ProteogenomicVariantPeptideTableReport:
    """Parse one explicit variant-peptide support table."""

    lines = path.read_text(encoding="utf-8").splitlines()
    active_mapping = mapping or ProteogenomicVariantPeptideColumnMapping(
        peptide_sequence="peptide_sequence",
        variant_protein_ref="variant_protein_ref",
        reference_protein_ref="reference_protein_ref",
        variant_label="variant_label",
    )
    if not lines:
        return ProteogenomicVariantPeptideTableReport(
            source_path=str(path),
            total_rows=0,
            accepted_records=(),
            rejected_rows=(
                RejectedProteogenomicVariantPeptideRow(
                    row_number=2,
                    reason="proteogenomic variant peptide table is empty",
                ),
            ),
            column_mapping=active_mapping,
            summary=ProteogenomicVariantPeptideTableSummary(
                accepted_record_count=0,
                rejected_row_count=1,
                distinct_peptide_count=0,
                distinct_variant_protein_ref_count=0,
                distinct_reference_protein_ref_count=0,
            ),
            note="variant peptide table did not contain any readable rows",
        )

    reader = csv.DictReader(lines, delimiter=_infer_delimiter(lines[0]))
    if reader.fieldnames is None:
        raise ValueError("proteogenomic variant peptide table must include a header row")
    _validate_required_columns(reader.fieldnames, (active_mapping.peptide_sequence,))

    accepted_records: list[ProteogenomicVariantPeptideRecord] = []
    rejected_rows: list[RejectedProteogenomicVariantPeptideRow] = []
    seen_rows: set[tuple[str, str | None, str | None, str | None]] = set()
    for row_number, raw_row in enumerate(reader, start=2):
        values = _normalize_row(raw_row)
        peptide_sequence = values.get(active_mapping.peptide_sequence, "").strip().upper()
        variant_token = _optional_value(values, active_mapping.variant_protein_ref)
        reference_token = _optional_value(values, active_mapping.reference_protein_ref)
        variant_label = _optional_value(values, active_mapping.variant_label)
        if not peptide_sequence:
            rejected_rows.append(
                RejectedProteogenomicVariantPeptideRow(
                    row_number=row_number,
                    values=values,
                    reason="variant peptide row requires peptide_sequence",
                )
            )
            continue
        if variant_token is None and reference_token is None:
            rejected_rows.append(
                RejectedProteogenomicVariantPeptideRow(
                    row_number=row_number,
                    values=values,
                    reason=(
                        "variant peptide row requires variant_protein_ref or "
                        "reference_protein_ref"
                    ),
                )
            )
            continue
        variant_protein_ref = (
            None if variant_token is None else _canonical_or_stable_protein_ref(variant_token)
        )
        reference_protein_ref = (
            None
            if reference_token is None
            else _canonical_or_stable_protein_ref(reference_token)
        )
        record_key = (
            peptide_sequence,
            variant_protein_ref,
            reference_protein_ref,
            variant_label,
        )
        if record_key in seen_rows:
            rejected_rows.append(
                RejectedProteogenomicVariantPeptideRow(
                    row_number=row_number,
                    values=values,
                    reason=(
                        "duplicate variant peptide support row for "
                        f"{peptide_sequence}"
                    ),
                )
            )
            continue
        seen_rows.add(record_key)
        accepted_records.append(
            ProteogenomicVariantPeptideRecord(
                peptide_sequence=peptide_sequence,
                variant_protein_ref=variant_protein_ref,
                reference_protein_ref=reference_protein_ref,
                variant_label=variant_label,
                metadata={
                    key: value
                    for key, value in values.items()
                    if key
                    not in {
                        active_mapping.peptide_sequence,
                        active_mapping.variant_protein_ref,
                        active_mapping.reference_protein_ref,
                        active_mapping.variant_label,
                    }
                    and value
                },
            )
        )

    return ProteogenomicVariantPeptideTableReport(
        source_path=str(path),
        total_rows=max(len(lines) - 1, 0),
        accepted_records=tuple(accepted_records),
        rejected_rows=tuple(rejected_rows),
        column_mapping=active_mapping,
        summary=ProteogenomicVariantPeptideTableSummary(
            accepted_record_count=len(accepted_records),
            rejected_row_count=len(rejected_rows),
            distinct_peptide_count=len(
                {record.peptide_sequence for record in accepted_records}
            ),
            distinct_variant_protein_ref_count=len(
                {
                    record.variant_protein_ref
                    for record in accepted_records
                    if record.variant_protein_ref is not None
                }
            ),
            distinct_reference_protein_ref_count=len(
                {
                    record.reference_protein_ref
                    for record in accepted_records
                    if record.reference_protein_ref is not None
                }
            ),
        ),
        note=(
            "variant peptide support rows preserve explicit alternate-protein and "
            "reference-protein claims so proteogenomic peptide review can distinguish "
            "reference-only, variant-only, shared, and unresolved support"
        ),
    )


def build_proteogenomic_peptide_support_report(
    references: tuple[ProteogenomicPeptideReference, ...],
    *,
    reference_protein_records: tuple[NormalizedProteinRecord, ...] = (),
    reference_protein_sequences: dict[str, str] | None = None,
    variant_protein_records: tuple[NormalizedProteinRecord, ...] = (),
    variant_protein_sequences: dict[str, str] | None = None,
    variant_peptide_records: tuple[ProteogenomicVariantPeptideRecord, ...] = (),
    treat_isoleucine_as_leucine: bool = False,
) -> ProteogenomicPeptideSupportReport:
    """Classify peptide-backed evidence against reference and variant proteomes."""

    reference_lookup = _materialize_lookup(
        reference_protein_records,
        protein_sequences=reference_protein_sequences,
        treat_isoleucine_as_leucine=treat_isoleucine_as_leucine,
    )
    variant_lookup = _materialize_lookup(
        variant_protein_records,
        protein_sequences=variant_protein_sequences,
        treat_isoleucine_as_leucine=treat_isoleucine_as_leucine,
    )
    variant_records_by_peptide = _group_variant_records_by_peptide(
        variant_peptide_records,
        treat_isoleucine_as_leucine=treat_isoleucine_as_leucine,
    )

    entries = tuple(
        _build_support_entry(
            reference,
            reference_lookup=reference_lookup,
            variant_lookup=variant_lookup,
            variant_records_by_peptide=variant_records_by_peptide,
            treat_isoleucine_as_leucine=treat_isoleucine_as_leucine,
        )
        for reference in references
    )
    return ProteogenomicPeptideSupportReport(
        entries=entries,
        summary=ProteogenomicPeptideSupportSummary(
            evidence_count=len(entries),
            reference_only_count=sum(
                1
                for entry in entries
                if entry.support_class is ProteogenomicPeptideSupportClass.REFERENCE_ONLY
            ),
            variant_only_count=sum(
                1
                for entry in entries
                if entry.support_class is ProteogenomicPeptideSupportClass.VARIANT_ONLY
            ),
            shared_count=sum(
                1
                for entry in entries
                if entry.support_class is ProteogenomicPeptideSupportClass.SHARED
            ),
            ambiguous_count=sum(
                1
                for entry in entries
                if entry.support_class is ProteogenomicPeptideSupportClass.AMBIGUOUS
            ),
        ),
        note=(
            "proteogenomic peptide support compares observed peptides against the "
            "reference proteome plus alternate-protein or explicit variant-peptide "
            "support and only grants variant-only status when the peptide is absent "
            "from the reference proteome"
        ),
    )


def render_proteogenomic_peptide_support_summary_tsv(
    report: ProteogenomicPeptideSupportReport,
) -> str:
    """Render the compact proteogenomic support summary as TSV."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(("field", "value"))
    writer.writerow(("evidence_count", report.summary.evidence_count))
    writer.writerow(("reference_only_count", report.summary.reference_only_count))
    writer.writerow(("variant_only_count", report.summary.variant_only_count))
    writer.writerow(("shared_count", report.summary.shared_count))
    writer.writerow(("ambiguous_count", report.summary.ambiguous_count))
    writer.writerow(("note", report.note))
    return handle.getvalue()


def render_proteogenomic_peptide_support_tsv(
    report: ProteogenomicPeptideSupportReport,
) -> str:
    """Render per-evidence proteogenomic peptide support as TSV."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "evidence_key",
            "target_protein_refs",
            "support_class",
            "support_reason",
            "reference_only_peptides",
            "variant_only_peptides",
            "shared_peptides",
            "ambiguous_peptides",
            "matched_reference_protein_refs",
            "matched_variant_protein_refs",
            "variant_labels",
            "peptide_evidence",
        )
    )
    for entry in report.entries:
        writer.writerow(
            (
                entry.evidence_key,
                ";".join(entry.target_protein_refs),
                entry.support_class.value,
                entry.support_reason,
                ";".join(entry.reference_only_peptides),
                ";".join(entry.variant_only_peptides),
                ";".join(entry.shared_peptides),
                ";".join(entry.ambiguous_peptides),
                ";".join(entry.matched_reference_protein_refs),
                ";".join(entry.matched_variant_protein_refs),
                ";".join(entry.variant_labels),
                ";".join(
                    (
                        f"{peptide.peptide_sequence}:{peptide.support_class.value}:"
                        f"{';'.join(peptide.matched_reference_protein_refs)}:"
                        f"{';'.join(peptide.matched_variant_protein_refs)}"
                    )
                    for peptide in entry.peptide_evidence
                ),
            )
        )
    return handle.getvalue()


def _build_support_entry(
    reference: ProteogenomicPeptideReference,
    *,
    reference_lookup: tuple[_ProteinLookup, ...],
    variant_lookup: tuple[_ProteinLookup, ...],
    variant_records_by_peptide: dict[str, tuple[ProteogenomicVariantPeptideRecord, ...]],
    treat_isoleucine_as_leucine: bool,
) -> ProteogenomicPeptideSupportEntry:
    peptide_evidence = tuple(
        _build_peptide_evidence(
            peptide_sequence,
            reference_lookup=reference_lookup,
            variant_lookup=variant_lookup,
            variant_records=variant_records_by_peptide.get(
                _normalize_lookup_sequence(
                    peptide_sequence,
                    treat_isoleucine_as_leucine=treat_isoleucine_as_leucine,
                ),
                (),
            ),
            treat_isoleucine_as_leucine=treat_isoleucine_as_leucine,
        )
        for peptide_sequence in reference.peptide_sequences
    )
    reference_only_peptides = tuple(
        peptide.peptide_sequence
        for peptide in peptide_evidence
        if peptide.support_class is ProteogenomicPeptideSupportClass.REFERENCE_ONLY
    )
    variant_only_peptides = tuple(
        peptide.peptide_sequence
        for peptide in peptide_evidence
        if peptide.support_class is ProteogenomicPeptideSupportClass.VARIANT_ONLY
    )
    shared_peptides = tuple(
        peptide.peptide_sequence
        for peptide in peptide_evidence
        if peptide.support_class is ProteogenomicPeptideSupportClass.SHARED
    )
    ambiguous_peptides = tuple(
        peptide.peptide_sequence
        for peptide in peptide_evidence
        if peptide.support_class is ProteogenomicPeptideSupportClass.AMBIGUOUS
    )
    support_class = _resolve_entry_support_class(
        peptide_evidence,
    )
    return ProteogenomicPeptideSupportEntry(
        evidence_key=reference.evidence_key,
        target_protein_refs=tuple(sorted({_stable_protein_ref(ref) for ref in reference.target_protein_refs})),
        support_class=support_class,
        support_reason=_support_reason(
            support_class,
            peptide_evidence=peptide_evidence,
        ),
        peptide_evidence=peptide_evidence,
        reference_only_peptides=reference_only_peptides,
        variant_only_peptides=variant_only_peptides,
        shared_peptides=shared_peptides,
        ambiguous_peptides=ambiguous_peptides,
        matched_reference_protein_refs=tuple(
            sorted(
                {
                    protein_ref
                    for peptide in peptide_evidence
                    for protein_ref in peptide.matched_reference_protein_refs
                }
            )
        ),
        matched_variant_protein_refs=tuple(
            sorted(
                {
                    protein_ref
                    for peptide in peptide_evidence
                    for protein_ref in peptide.matched_variant_protein_refs
                }
            )
        ),
        variant_labels=tuple(
            sorted(
                {
                    label
                    for peptide in peptide_evidence
                    for label in peptide.variant_labels
                }
            )
        ),
    )


def _build_peptide_evidence(
    peptide_sequence: str,
    *,
    reference_lookup: tuple[_ProteinLookup, ...],
    variant_lookup: tuple[_ProteinLookup, ...],
    variant_records: tuple[ProteogenomicVariantPeptideRecord, ...],
    treat_isoleucine_as_leucine: bool,
) -> ProteogenomicPeptideEvidence:
    normalized_peptide = _normalize_lookup_sequence(
        peptide_sequence,
        treat_isoleucine_as_leucine=treat_isoleucine_as_leucine,
    )
    matched_reference_protein_refs = tuple(
        sorted(
            record.stable_ref
            for record in reference_lookup
            if normalized_peptide and normalized_peptide in record.lookup_residues
        )
    )
    matched_variant_protein_refs = set(
        record.stable_ref
        for record in variant_lookup
        if normalized_peptide and normalized_peptide in record.lookup_residues
    )
    matched_variant_protein_refs.update(
        record.variant_protein_ref
        for record in variant_records
        if record.variant_protein_ref is not None
    )
    variant_labels = tuple(
        sorted(
            {
                record.variant_label
                for record in variant_records
                if record.variant_label is not None
            }
        )
    )
    support_class = _resolve_peptide_support_class(
        has_reference_match=bool(matched_reference_protein_refs),
        has_variant_match=bool(matched_variant_protein_refs),
    )
    return ProteogenomicPeptideEvidence(
        peptide_sequence=peptide_sequence.strip().upper(),
        support_class=support_class,
        matched_reference_protein_refs=matched_reference_protein_refs,
        matched_variant_protein_refs=tuple(sorted(matched_variant_protein_refs)),
        variant_labels=variant_labels,
    )


def _resolve_peptide_support_class(
    *,
    has_reference_match: bool,
    has_variant_match: bool,
) -> ProteogenomicPeptideSupportClass:
    if has_reference_match and has_variant_match:
        return ProteogenomicPeptideSupportClass.SHARED
    if has_variant_match and not has_reference_match:
        return ProteogenomicPeptideSupportClass.VARIANT_ONLY
    if has_reference_match and not has_variant_match:
        return ProteogenomicPeptideSupportClass.REFERENCE_ONLY
    return ProteogenomicPeptideSupportClass.AMBIGUOUS


def _resolve_entry_support_class(
    peptide_evidence: tuple[ProteogenomicPeptideEvidence, ...],
) -> ProteogenomicPeptideSupportClass:
    support_classes = {
        peptide.support_class for peptide in peptide_evidence
    }
    if len(support_classes) == 1:
        return next(iter(support_classes))
    return ProteogenomicPeptideSupportClass.AMBIGUOUS


def _support_reason(
    support_class: ProteogenomicPeptideSupportClass,
    *,
    peptide_evidence: tuple[ProteogenomicPeptideEvidence, ...],
) -> str:
    if support_class is ProteogenomicPeptideSupportClass.REFERENCE_ONLY:
        return (
            "all observed peptides were found in the reference proteome and none "
            "required alternate-protein or explicit variant support"
        )
    if support_class is ProteogenomicPeptideSupportClass.VARIANT_ONLY:
        return (
            "all observed peptides were absent from the reference proteome and "
            "were supported by alternate-protein or explicit variant peptide evidence"
        )
    if support_class is ProteogenomicPeptideSupportClass.SHARED:
        return (
            "all observed peptides were present in both the reference proteome and "
            "the alternate-protein or explicit variant support set"
        )
    if any(
        peptide.support_class is ProteogenomicPeptideSupportClass.AMBIGUOUS
        for peptide in peptide_evidence
    ):
        return (
            "at least one observed peptide could not be resolved against the provided "
            "reference and variant support inputs"
        )
    return (
        "observed peptides mixed reference-only, variant-only, or shared support and "
        "do not justify one pure proteogenomic claim label"
    )


def _group_variant_records_by_peptide(
    records: tuple[ProteogenomicVariantPeptideRecord, ...],
    *,
    treat_isoleucine_as_leucine: bool,
) -> dict[str, tuple[ProteogenomicVariantPeptideRecord, ...]]:
    grouped: dict[str, list[ProteogenomicVariantPeptideRecord]] = defaultdict(list)
    for record in records:
        grouped[
            _normalize_lookup_sequence(
                record.peptide_sequence,
                treat_isoleucine_as_leucine=treat_isoleucine_as_leucine,
            )
        ].append(record)
    return {
        peptide: tuple(entries)
        for peptide, entries in grouped.items()
    }


def _materialize_lookup(
    protein_records: tuple[NormalizedProteinRecord, ...],
    *,
    protein_sequences: dict[str, str] | None,
    treat_isoleucine_as_leucine: bool,
) -> tuple[_ProteinLookup, ...]:
    by_ref: dict[str, _ProteinLookup] = {}
    for record in protein_records:
        stable_ref = _stable_record_ref(record)
        by_ref[stable_ref] = _ProteinLookup(
            stable_ref=stable_ref,
            lookup_residues=_normalize_lookup_sequence(
                record.residues,
                treat_isoleucine_as_leucine=treat_isoleucine_as_leucine,
            ),
        )
    if protein_sequences:
        for protein_ref, residues in protein_sequences.items():
            stable_ref = _stable_protein_ref(protein_ref)
            if stable_ref in by_ref:
                continue
            by_ref[stable_ref] = _ProteinLookup(
                stable_ref=stable_ref,
                lookup_residues=_normalize_lookup_sequence(
                    residues,
                    treat_isoleucine_as_leucine=treat_isoleucine_as_leucine,
                ),
            )
    return tuple(by_ref[key] for key in sorted(by_ref))


def _stable_record_ref(record: NormalizedProteinRecord) -> str:
    if isinstance(record.isoform, int):
        return f"{record.canonical_accession}-{record.isoform}"
    return record.canonical_accession


def _canonical_or_stable_protein_ref(value: str) -> str:
    try:
        return canonicalize_protein_reference(value)
    except ValueError:
        return _stable_protein_ref(value)


def _stable_protein_ref(value: str) -> str:
    token = value.strip().upper()
    if not token:
        raise ValueError("protein reference must not be empty")
    return token


def _normalize_lookup_sequence(
    sequence: str,
    *,
    treat_isoleucine_as_leucine: bool,
) -> str:
    normalized = sequence.strip().upper()
    if treat_isoleucine_as_leucine:
        return normalized.replace("I", "L")
    return normalized


def _optional_value(values: dict[str, str], column: str | None) -> str | None:
    if column is None:
        return None
    value = values.get(column, "").strip()
    return None if not value else value


def _normalize_row(raw_row: dict[str, str | None]) -> dict[str, str]:
    return {
        str(key): "" if value is None else value.strip()
        for key, value in raw_row.items()
        if key is not None
    }


def _infer_delimiter(header_line: str) -> str:
    if header_line.count("\t") >= header_line.count(","):
        return "\t"
    return ","


def _validate_required_columns(
    fieldnames: Sequence[str],
    required_columns: tuple[str, ...],
) -> None:
    missing = [column for column in required_columns if column not in fieldnames]
    if missing:
        raise ValueError(
            "proteogenomic variant peptide table is missing required columns: "
            + ", ".join(missing)
        )


__all__ = (
    "ProteogenomicPeptideEvidence",
    "ProteogenomicPeptideReference",
    "ProteogenomicPeptideSupportClass",
    "ProteogenomicPeptideSupportEntry",
    "ProteogenomicPeptideSupportReport",
    "ProteogenomicPeptideSupportSummary",
    "ProteogenomicVariantPeptideColumnMapping",
    "ProteogenomicVariantPeptideRecord",
    "ProteogenomicVariantPeptideTableReport",
    "ProteogenomicVariantPeptideTableSummary",
    "RejectedProteogenomicVariantPeptideRow",
    "build_proteogenomic_peptide_support_report",
    "parse_proteogenomic_variant_peptide_table",
    "render_proteogenomic_peptide_support_summary_tsv",
    "render_proteogenomic_peptide_support_tsv",
)

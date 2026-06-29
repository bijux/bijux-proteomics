# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Contaminant-database assembly surfaces for realistic proteomics searches."""

from __future__ import annotations

from collections import Counter
import warnings

from pydantic import ConfigDict, Field

from bijux_proteomics.sequences.fasta import (
    FastaParseMode,
    NormalizedProteinRecord,
)
from bijux_proteomics.sequences.core import (
    parse_fasta_document,
)
from bijux_proteomics_foundation import JsonModel

_CONTAMINANT_PREFIX = "CON__"
_BUILTIN_CONTAMINANT_FASTA = """>sp|P02769|ALBU_BOVIN Serum albumin OS=Bos taurus GN=ALB
MKWVTFISLLLLFSSAYSRGVFRRDTHKSEIAHRFKDLGE
>sp|P00761|TRYP_PIG Trypsin OS=Sus scrofa GN=PRSS1
MNPLLILTFVAAALAAPFDDDDKIVGGYTCGANTVPYQVSLNSGYHFCG
>sp|P13645|K1C10_HUMAN Keratin, type I cytoskeletal 10 OS=Homo sapiens GN=KRT10
MTSYSIRQTSSSGSYRGLGAPVGVGRVSKYAPSVHGGYGGQGISVSSAR
>sp|P04264|K2C1_HUMAN Keratin, type II cytoskeletal 1 OS=Homo sapiens GN=KRT1
MSRQFSSRSGYRSGGGFSSGSAGIINYQRRTTQSPSSSFSQHARSSSG
"""


class ContaminantDatabaseBuildReport(JsonModel):
    """Stable summary for one contaminant-database assembly step."""

    model_config = ConfigDict(extra="forbid")

    input_target_record_count: int = Field(..., ge=0)
    appended_builtin_record_count: int = Field(..., ge=0)
    appended_external_record_count: int = Field(..., ge=0)
    skipped_duplicate_contaminant_count: int = Field(..., ge=0)
    output_record_count: int = Field(..., ge=0)
    contaminant_accessions: tuple[str, ...] = Field(default_factory=tuple)
    contaminant_namespace_counts: dict[str, int] = Field(default_factory=dict)


def build_builtin_contaminant_records() -> tuple[NormalizedProteinRecord, ...]:
    """Build the built-in contaminant panel with explicit contaminant labels."""
    report = parse_fasta_document(
        _BUILTIN_CONTAMINANT_FASTA, mode=FastaParseMode.STRICT
    )
    return relabel_contaminant_records(report.accepted_records)


def load_builtin_contaminant_records() -> tuple[NormalizedProteinRecord, ...]:
    """Compatibility wrapper for the canonical built-in contaminant assembly surface."""
    warnings.warn(
        "load_builtin_contaminant_records is deprecated; use "
        "build_builtin_contaminant_records for the shipped contaminant panel.",
        DeprecationWarning,
        stacklevel=2,
    )
    return build_builtin_contaminant_records()


def relabel_contaminant_records(
    records: tuple[NormalizedProteinRecord, ...],
    *,
    prefix: str = _CONTAMINANT_PREFIX,
) -> tuple[NormalizedProteinRecord, ...]:
    """Normalize one contaminant collection to stable contaminant-prefixed references."""
    relabeled: list[NormalizedProteinRecord] = []
    for record in records:
        prefixed_identifier = (
            record.source_identifier
            if record.source_identifier.startswith(prefix)
            else f"{prefix}{record.source_identifier}"
        )
        prefixed_header = (
            record.source_header
            if record.source_header.startswith(prefix)
            else f"{prefix}{record.source_header}"
        )
        prefixed_accession = (
            record.canonical_accession
            if record.canonical_accession.startswith(prefix)
            else f"{prefix}{record.canonical_accession}"
        )
        relabeled.append(
            record.model_copy(
                update={
                    "source_identifier": prefixed_identifier,
                    "source_header": prefixed_header,
                    "canonical_accession": prefixed_accession,
                    "contaminant": True,
                }
            )
        )
    return tuple(relabeled)


def append_contaminant_database(
    target_records: tuple[NormalizedProteinRecord, ...],
    *,
    include_builtin: bool = True,
    external_contaminant_records: tuple[NormalizedProteinRecord, ...] = (),
) -> tuple[tuple[NormalizedProteinRecord, ...], ContaminantDatabaseBuildReport]:
    """Append built-in and external contaminants while skipping duplicate accessions."""
    appended_builtin = build_builtin_contaminant_records() if include_builtin else ()
    appended_external = relabel_contaminant_records(external_contaminant_records)
    existing_accessions = {
        _stable_record_accession(record) for record in target_records
    }
    kept_contaminants: list[NormalizedProteinRecord] = []
    skipped_duplicate_count = 0
    builtin_kept = 0
    external_kept = 0

    for source_name, records in (
        ("builtin", appended_builtin),
        ("external", appended_external),
    ):
        for record in records:
            stable_accession = _stable_record_accession(record)
            if stable_accession in existing_accessions:
                skipped_duplicate_count += 1
                continue
            kept_contaminants.append(record)
            existing_accessions.add(stable_accession)
            if source_name == "builtin":
                builtin_kept += 1
            else:
                external_kept += 1

    output_records = tuple(target_records) + tuple(kept_contaminants)
    namespace_counts = Counter(
        record.accession_namespace for record in kept_contaminants
    )
    report = ContaminantDatabaseBuildReport(
        input_target_record_count=len(target_records),
        appended_builtin_record_count=builtin_kept,
        appended_external_record_count=external_kept,
        skipped_duplicate_contaminant_count=skipped_duplicate_count,
        output_record_count=len(output_records),
        contaminant_accessions=tuple(
            sorted(record.canonical_accession for record in kept_contaminants)
        ),
        contaminant_namespace_counts=dict(sorted(namespace_counts.items())),
    )
    return output_records, report


def _stable_record_accession(record: NormalizedProteinRecord) -> str:
    if record.isoform is None:
        return f"{record.accession_namespace}:{record.canonical_accession}"
    return f"{record.accession_namespace}:{record.canonical_accession}-{record.isoform}"

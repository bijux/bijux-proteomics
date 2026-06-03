# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Spectronaut report import over precursor and protein-group evidence."""

from __future__ import annotations

import csv
from pathlib import Path

from pydantic import ConfigDict, Field

from bijux_proteomics.domain.records import ImportedEvidenceProvenance
from bijux_proteomics.chemistry import (
    canonicalize_modified_peptide,
    parse_modified_peptide,
)
from bijux_proteomics.identification.contracts import TargetDecoyLabel
from bijux_proteomics.identification.rejected_evidence_table import (
    RejectedEvidenceTableEntry,
    build_rejected_evidence_rows_from_psm_rows,
)
from bijux_proteomics.identification.search_adapters import (
    SearchAdapterKind,
    SearchAdapterNormalizationReport,
    SearchParameterReport,
    normalize_search_results_with_adapter,
    parse_search_parameter_file,
)
from bijux_proteomics.io.stable_outputs import sort_rows_by_fields, sort_strings
from bijux_proteomics_foundation import JsonModel


class SpectronautPrecursorReviewEntry(JsonModel):
    """Reviewer-facing precursor row from one Spectronaut report."""

    model_config = ConfigDict(extra="forbid")

    precursor_id: str = Field(..., min_length=1)
    peptide_sequence: str = Field(..., min_length=1)
    modified_peptide: str = Field(..., min_length=1)
    canonical_modified_peptide: str = Field(..., min_length=1)
    charge: int = Field(..., ge=1)
    cscore: float
    q_value: float = Field(..., ge=0.0, le=1.0)
    protein_group_id: str = Field(..., min_length=1)
    protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    run_name: str = Field(..., min_length=1)
    sample_name: str = Field(..., min_length=1)
    precursor_quantity: float | None = Field(default=None, ge=0.0)
    protein_group_quantity: float | None = Field(default=None, ge=0.0)
    target_decoy_label: TargetDecoyLabel
    provenance: ImportedEvidenceProvenance


class SpectronautProteinGroupReviewEntry(JsonModel):
    """Reviewer-facing protein-group row from one Spectronaut report."""

    model_config = ConfigDict(extra="forbid")

    protein_group_id: str = Field(..., min_length=1)
    protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    run_name: str = Field(..., min_length=1)
    sample_name: str = Field(..., min_length=1)
    q_value: float = Field(..., ge=0.0, le=1.0)
    protein_group_quantity: float | None = Field(default=None, ge=0.0)
    source_precursor_count: int = Field(..., ge=1)
    target_decoy_label: TargetDecoyLabel
    provenance: ImportedEvidenceProvenance


class SpectronautPrecursorQuantityEntry(JsonModel):
    """One precursor-level quantity row preserved from a Spectronaut export."""

    model_config = ConfigDict(extra="forbid")

    precursor_id: str = Field(..., min_length=1)
    protein_group_id: str = Field(..., min_length=1)
    protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    run_name: str = Field(..., min_length=1)
    sample_name: str = Field(..., min_length=1)
    precursor_quantity: float = Field(..., ge=0.0)
    target_decoy_label: TargetDecoyLabel
    provenance: ImportedEvidenceProvenance


class SpectronautProteinGroupQuantityEntry(JsonModel):
    """One protein-group quantity row preserved from a Spectronaut export."""

    model_config = ConfigDict(extra="forbid")

    protein_group_id: str = Field(..., min_length=1)
    protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    run_name: str = Field(..., min_length=1)
    sample_name: str = Field(..., min_length=1)
    q_value: float = Field(..., ge=0.0, le=1.0)
    protein_group_quantity: float = Field(..., ge=0.0)
    source_precursor_count: int = Field(..., ge=1)
    target_decoy_label: TargetDecoyLabel
    provenance: ImportedEvidenceProvenance


class SpectronautImportSummary(JsonModel):
    """Compact summary over one imported Spectronaut report."""

    model_config = ConfigDict(extra="forbid")

    accepted_precursor_count: int = Field(..., ge=0)
    rejected_precursor_count: int = Field(..., ge=0)
    protein_group_row_count: int = Field(..., ge=0)
    precursor_quantity_row_count: int = Field(..., ge=0)
    protein_group_quantity_row_count: int = Field(..., ge=0)
    modified_precursor_count: int = Field(..., ge=0)
    sample_count: int = Field(..., ge=0)
    run_count: int = Field(..., ge=0)
    precursor_quantity_count: int = Field(..., ge=0)
    protein_group_quantity_count: int = Field(..., ge=0)
    target_precursor_count: int = Field(..., ge=0)
    decoy_precursor_count: int = Field(..., ge=0)
    sample_names: tuple[str, ...] = Field(default_factory=tuple)
    run_names: tuple[str, ...] = Field(default_factory=tuple)


class SpectronautImportReport(JsonModel):
    """One governed Spectronaut report import packet."""

    model_config = ConfigDict(extra="forbid")

    normalization: SearchAdapterNormalizationReport
    precursor_evidence_rows: tuple[SpectronautPrecursorReviewEntry, ...] = Field(
        default_factory=tuple
    )
    precursor_rows: tuple[SpectronautPrecursorReviewEntry, ...] = Field(
        default_factory=tuple
    )
    protein_group_rows: tuple[SpectronautProteinGroupReviewEntry, ...] = Field(
        default_factory=tuple
    )
    precursor_quantity_rows: tuple[SpectronautPrecursorQuantityEntry, ...] = Field(
        default_factory=tuple
    )
    protein_group_quantity_rows: tuple[SpectronautProteinGroupQuantityEntry, ...] = (
        Field(default_factory=tuple)
    )
    rejected_evidence_rows: tuple[RejectedEvidenceTableEntry, ...] = Field(
        default_factory=tuple
    )
    summary: SpectronautImportSummary
    parameter_report: SearchParameterReport | None = None


def build_spectronaut_import_report(
    result_tsv_path: Path,
    *,
    config_path: Path | None = None,
) -> SpectronautImportReport:
    """Import one Spectronaut report into owned precursor and protein-group review."""
    _validate_spectronaut_export_schema(result_tsv_path)
    normalization = normalize_search_results_with_adapter(
        source_path=result_tsv_path,
        adapter_kind=SearchAdapterKind.SPECTRONAUT,
        dialect_id="review-report",
    )
    precursor_rows = _build_spectronaut_precursor_rows(normalization)
    protein_group_rows = _build_spectronaut_protein_group_rows(precursor_rows)
    precursor_quantity_rows = _build_spectronaut_precursor_quantity_rows(
        precursor_rows
    )
    protein_group_quantity_rows = _build_spectronaut_protein_group_quantity_rows(
        protein_group_rows
    )
    sample_names = tuple(sorted({row.sample_name for row in precursor_rows}))
    run_names = tuple(sorted({row.run_name for row in precursor_rows}))
    parameter_report = (
        None
        if config_path is None
        else parse_search_parameter_file(
            source_path=config_path,
            adapter_kind=SearchAdapterKind.SPECTRONAUT,
        )
    )
    summary = SpectronautImportSummary(
        accepted_precursor_count=len(precursor_rows),
        rejected_precursor_count=len(normalization.parse_report.rejected_rows),
        protein_group_row_count=len(protein_group_rows),
        precursor_quantity_row_count=len(precursor_quantity_rows),
        protein_group_quantity_row_count=len(protein_group_quantity_rows),
        modified_precursor_count=sum(
            1 for row in precursor_rows if row.modified_peptide != row.peptide_sequence
        ),
        sample_count=len(sample_names),
        run_count=len(run_names),
        precursor_quantity_count=sum(
            1 for row in precursor_rows if row.precursor_quantity is not None
        ),
        protein_group_quantity_count=sum(
            1 for row in precursor_rows if row.protein_group_quantity is not None
        ),
        target_precursor_count=sum(
            1
            for row in precursor_rows
            if row.target_decoy_label is TargetDecoyLabel.TARGET
        ),
        decoy_precursor_count=sum(
            1
            for row in precursor_rows
            if row.target_decoy_label is TargetDecoyLabel.DECOY
        ),
        sample_names=sample_names,
        run_names=run_names,
    )
    return SpectronautImportReport(
        normalization=normalization,
        precursor_evidence_rows=precursor_rows,
        precursor_rows=precursor_rows,
        protein_group_rows=protein_group_rows,
        precursor_quantity_rows=precursor_quantity_rows,
        protein_group_quantity_rows=protein_group_quantity_rows,
        rejected_evidence_rows=build_rejected_evidence_rows_from_psm_rows(
            normalization.parse_report.rejected_rows,
            source_file=result_tsv_path.name,
            entity_type="precursor",
            entity_id_columns=(
                "EG.PrecursorId",
                "FG.LabeledSequence",
                "PEP.StrippedSequence",
                "PG.ProteinGroups",
            ),
        ),
        summary=summary,
        parameter_report=parameter_report,
    )


def render_spectronaut_summary_tsv(summary: SpectronautImportSummary) -> str:
    """Render the one-row Spectronaut summary as TSV."""
    header = (
        "accepted_precursor_count",
        "rejected_precursor_count",
        "protein_group_row_count",
        "precursor_quantity_row_count",
        "protein_group_quantity_row_count",
        "modified_precursor_count",
        "sample_count",
        "run_count",
        "precursor_quantity_count",
        "protein_group_quantity_count",
        "target_precursor_count",
        "decoy_precursor_count",
        "sample_names",
        "run_names",
    )
    row = (
        str(summary.accepted_precursor_count),
        str(summary.rejected_precursor_count),
        str(summary.protein_group_row_count),
        str(summary.precursor_quantity_row_count),
        str(summary.protein_group_quantity_row_count),
        str(summary.modified_precursor_count),
        str(summary.sample_count),
        str(summary.run_count),
        str(summary.precursor_quantity_count),
        str(summary.protein_group_quantity_count),
        str(summary.target_precursor_count),
        str(summary.decoy_precursor_count),
        ";".join(summary.sample_names),
        ";".join(summary.run_names),
    )
    return "\t".join(header) + "\n" + "\t".join(row) + "\n"


def render_spectronaut_precursor_tsv(
    rows: tuple[SpectronautPrecursorReviewEntry, ...],
) -> str:
    """Render reviewer-facing Spectronaut precursor rows as TSV."""
    ordered_rows = sort_rows_by_fields(
        rows,
        "protein_group_id",
        "run_name",
        "sample_name",
        "precursor_id",
    )
    lines = [
        "\t".join(
            (
                "precursor_id",
                "peptide_sequence",
                "modified_peptide",
                "canonical_modified_peptide",
                "charge",
                "cscore",
                "q_value",
                "protein_group_id",
                "protein_refs",
                "run_name",
                "sample_name",
                "precursor_quantity",
                "protein_group_quantity",
                "target_decoy_label",
                *ImportedEvidenceProvenance.tsv_header(),
            )
        )
    ]
    for row in ordered_rows:
        lines.append(
            "\t".join(
                (
                    row.precursor_id,
                    row.peptide_sequence,
                    row.modified_peptide,
                    row.canonical_modified_peptide,
                    str(row.charge),
                    f"{row.cscore:.6g}",
                    f"{row.q_value:.6g}",
                    row.protein_group_id,
                    ";".join(sort_strings(row.protein_refs)),
                    row.run_name,
                    row.sample_name,
                    ""
                    if row.precursor_quantity is None
                    else f"{row.precursor_quantity:.6g}",
                    ""
                    if row.protein_group_quantity is None
                    else f"{row.protein_group_quantity:.6g}",
                    row.target_decoy_label.value,
                    *row.provenance.to_tsv_cells(),
                )
            )
        )
    return "\n".join(lines) + "\n"


def render_spectronaut_protein_group_tsv(
    rows: tuple[SpectronautProteinGroupReviewEntry, ...],
) -> str:
    """Render reviewer-facing Spectronaut protein-group rows as TSV."""
    ordered_rows = sort_rows_by_fields(
        rows,
        "protein_group_id",
        "run_name",
        "sample_name",
    )
    lines = [
        "\t".join(
            (
                "protein_group_id",
                "protein_refs",
                "run_name",
                "sample_name",
                "q_value",
                "protein_group_quantity",
                "source_precursor_count",
                "target_decoy_label",
                *ImportedEvidenceProvenance.tsv_header(),
            )
        )
    ]
    for row in ordered_rows:
        lines.append(
            "\t".join(
                (
                    row.protein_group_id,
                    ";".join(sort_strings(row.protein_refs)),
                    row.run_name,
                    row.sample_name,
                    f"{row.q_value:.6g}",
                    ""
                    if row.protein_group_quantity is None
                    else f"{row.protein_group_quantity:.6g}",
                    str(row.source_precursor_count),
                    row.target_decoy_label.value,
                    *row.provenance.to_tsv_cells(),
                )
            )
        )
    return "\n".join(lines) + "\n"


def render_spectronaut_precursor_quantity_tsv(
    rows: tuple[SpectronautPrecursorQuantityEntry, ...],
) -> str:
    """Render precursor quantity rows as TSV."""

    ordered_rows = sort_rows_by_fields(
        rows,
        "protein_group_id",
        "run_name",
        "sample_name",
        "precursor_id",
    )
    lines = [
        "\t".join(
            (
                "precursor_id",
                "protein_group_id",
                "protein_refs",
                "run_name",
                "sample_name",
                "precursor_quantity",
                "target_decoy_label",
                *ImportedEvidenceProvenance.tsv_header(),
            )
        )
    ]
    for row in ordered_rows:
        lines.append(
            "\t".join(
                (
                    row.precursor_id,
                    row.protein_group_id,
                    ";".join(sort_strings(row.protein_refs)),
                    row.run_name,
                    row.sample_name,
                    f"{row.precursor_quantity:.6g}",
                    row.target_decoy_label.value,
                    *row.provenance.to_tsv_cells(),
                )
            )
        )
    return "\n".join(lines) + "\n"


def render_spectronaut_protein_group_quantity_tsv(
    rows: tuple[SpectronautProteinGroupQuantityEntry, ...],
) -> str:
    """Render protein-group quantity rows as TSV."""

    ordered_rows = sort_rows_by_fields(
        rows,
        "protein_group_id",
        "run_name",
        "sample_name",
    )
    lines = [
        "\t".join(
            (
                "protein_group_id",
                "protein_refs",
                "run_name",
                "sample_name",
                "q_value",
                "protein_group_quantity",
                "source_precursor_count",
                "target_decoy_label",
                *ImportedEvidenceProvenance.tsv_header(),
            )
        )
    ]
    for row in ordered_rows:
        lines.append(
            "\t".join(
                (
                    row.protein_group_id,
                    ";".join(sort_strings(row.protein_refs)),
                    row.run_name,
                    row.sample_name,
                    f"{row.q_value:.6g}",
                    f"{row.protein_group_quantity:.6g}",
                    str(row.source_precursor_count),
                    row.target_decoy_label.value,
                    *row.provenance.to_tsv_cells(),
                )
            )
        )
    return "\n".join(lines) + "\n"


def _build_spectronaut_precursor_rows(
    normalization: SearchAdapterNormalizationReport,
) -> tuple[SpectronautPrecursorReviewEntry, ...]:
    rows: list[SpectronautPrecursorReviewEntry] = []
    for evidence_row in normalization.evidence_rows:
        if not evidence_row.accepted or evidence_row.normalized_record is None:
            continue
        record = evidence_row.normalized_record
        raw = evidence_row.raw_fields
        modified_peptide = _required_value(raw, "FG.LabeledSequence")
        parsed = parse_modified_peptide(modified_peptide)
        rows.append(
            SpectronautPrecursorReviewEntry(
                precursor_id=record.spectrum_id,
                peptide_sequence=record.peptide,
                modified_peptide=modified_peptide,
                canonical_modified_peptide=canonicalize_modified_peptide(parsed),
                charge=record.charge,
                cscore=record.score,
                q_value=record.q_value if record.q_value is not None else 1.0,
                protein_group_id=_required_value(raw, "PG.ProteinGroups"),
                protein_refs=record.protein_refs,
                run_name=_required_value(raw, "R.FileName"),
                sample_name=_required_value(raw, "R.Condition"),
                precursor_quantity=_optional_float(raw.get("FG.Quantity")),
                protein_group_quantity=_optional_float(raw.get("PG.Quantity")),
                target_decoy_label=record.target_decoy_label,
                provenance=ImportedEvidenceProvenance.from_single_row(
                    source_engine="spectronaut",
                    source_file=(
                        record.provenance.source_file
                        if record.provenance is not None
                        else ""
                    ),
                    source_row_number=evidence_row.row_number,
                    original_identifiers={
                        "precursor_id": record.spectrum_id,
                        "protein_group_id": _required_value(raw, "PG.ProteinGroups"),
                        "run_name": _required_value(raw, "R.FileName"),
                        "sample_name": _required_value(raw, "R.Condition"),
                    },
                ),
            )
        )
    return tuple(
        sorted(rows, key=lambda row: (row.q_value, -row.cscore, row.precursor_id))
    )


def _build_spectronaut_protein_group_rows(
    precursor_rows: tuple[SpectronautPrecursorReviewEntry, ...],
) -> tuple[SpectronautProteinGroupReviewEntry, ...]:
    grouped: dict[tuple[str, str, str], list[SpectronautPrecursorReviewEntry]] = {}
    for row in precursor_rows:
        grouped.setdefault(
            (row.protein_group_id, row.run_name, row.sample_name), []
        ).append(row)
    rows: list[SpectronautProteinGroupReviewEntry] = []
    for (protein_group_id, run_name, sample_name), entries in sorted(grouped.items()):
        protein_refs = tuple(
            sorted(
                {protein_ref for entry in entries for protein_ref in entry.protein_refs}
            )
        )
        quantity = next(
            (
                entry.protein_group_quantity
                for entry in entries
                if entry.protein_group_quantity is not None
            ),
            None,
        )
        rows.append(
            SpectronautProteinGroupReviewEntry(
                protein_group_id=protein_group_id,
                protein_refs=protein_refs,
                run_name=run_name,
                sample_name=sample_name,
                q_value=min(entry.q_value for entry in entries),
                protein_group_quantity=quantity,
                source_precursor_count=len(entries),
                target_decoy_label=_combine_labels(entries),
                provenance=ImportedEvidenceProvenance.combine(
                    tuple(entry.provenance for entry in entries),
                    original_identifiers={
                        "protein_group_id": protein_group_id,
                        "run_name": run_name,
                        "sample_name": sample_name,
                        "precursor_ids": ";".join(
                            sorted(entry.precursor_id for entry in entries)
                        ),
                    },
                ),
            )
        )
    return tuple(rows)


def _build_spectronaut_precursor_quantity_rows(
    precursor_rows: tuple[SpectronautPrecursorReviewEntry, ...],
) -> tuple[SpectronautPrecursorQuantityEntry, ...]:
    rows = [
        SpectronautPrecursorQuantityEntry(
            precursor_id=row.precursor_id,
            protein_group_id=row.protein_group_id,
            protein_refs=row.protein_refs,
            run_name=row.run_name,
            sample_name=row.sample_name,
            precursor_quantity=row.precursor_quantity,
            target_decoy_label=row.target_decoy_label,
            provenance=row.provenance,
        )
        for row in precursor_rows
        if row.precursor_quantity is not None
    ]
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                row.protein_group_id,
                row.run_name,
                row.sample_name,
                row.precursor_id,
            ),
        )
    )


def _build_spectronaut_protein_group_quantity_rows(
    protein_group_rows: tuple[SpectronautProteinGroupReviewEntry, ...],
) -> tuple[SpectronautProteinGroupQuantityEntry, ...]:
    rows = [
        SpectronautProteinGroupQuantityEntry(
            protein_group_id=row.protein_group_id,
            protein_refs=row.protein_refs,
            run_name=row.run_name,
            sample_name=row.sample_name,
            q_value=row.q_value,
            protein_group_quantity=row.protein_group_quantity,
            source_precursor_count=row.source_precursor_count,
            target_decoy_label=row.target_decoy_label,
            provenance=row.provenance,
        )
        for row in protein_group_rows
        if row.protein_group_quantity is not None
    ]
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                row.protein_group_id,
                row.run_name,
                row.sample_name,
            ),
        )
    )


def _combine_labels(
    entries: list[SpectronautPrecursorReviewEntry],
) -> TargetDecoyLabel:
    labels = {entry.target_decoy_label for entry in entries}
    if labels == {TargetDecoyLabel.DECOY}:
        return TargetDecoyLabel.DECOY
    if labels == {TargetDecoyLabel.TARGET}:
        return TargetDecoyLabel.TARGET
    if not labels:
        return TargetDecoyLabel.UNKNOWN
    return TargetDecoyLabel.MIXED


def _validate_spectronaut_export_schema(path: Path) -> None:
    required_columns = (
        "EG.PrecursorId",
        "PEP.StrippedSequence",
        "FG.LabeledSequence",
        "FG.Charge",
        "EG.Cscore",
        "EG.Qvalue",
        "PG.ProteinGroups",
        "PG.ProteinAccessions",
        "R.FileName",
        "R.Condition",
        "FG.Quantity",
        "PG.Quantity",
        "EG.IsDecoy",
    )
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle, delimiter="\t")
        header = next(reader, None)
    if not header:
        raise ValueError("Spectronaut schema error: export must include a header row")
    columns = {column.strip() for column in header if column.strip()}
    missing = tuple(column for column in required_columns if column not in columns)
    if missing:
        raise ValueError(
            "Spectronaut schema error: missing required exported columns: "
            + ", ".join(missing)
        )


def _required_value(row: dict[str, str], column: str) -> str:
    value = row.get(column, "").strip()
    if not value:
        raise ValueError(f"Spectronaut report is missing required {column!r} value")
    return value


def _optional_float(value: str | None) -> float | None:
    if value is None or not value.strip():
        return None
    return float(value.strip())

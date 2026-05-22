# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""DIA-NN report import over precursor and protein-group evidence."""

from __future__ import annotations

from pathlib import Path

from pydantic import ConfigDict, Field

from bijux_proteomics.dia import DiaNnImportReport, DiaNnImportRow, import_dia_nn_rows
from bijux_proteomics.identification.contracts import TargetDecoyLabel
from bijux_proteomics.identification.search_adapters import (
    SearchAdapterKind,
    SearchAdapterNormalizationReport,
    SearchParameterReport,
    normalize_search_results_with_adapter,
    parse_search_parameter_file,
)
from bijux_proteomics.scientific_tables import (
    build_diann_report_schema,
    require_valid_scientific_table,
)
from bijux_proteomics_foundation import JsonModel


class DiaNnPrecursorReviewEntry(JsonModel):
    """Reviewer-facing precursor-level row from one DIA-NN report."""

    model_config = ConfigDict(extra="forbid")

    precursor_id: str = Field(..., min_length=1)
    peptide_sequence: str = Field(..., min_length=1)
    modified_peptide: str = Field(..., min_length=1)
    canonical_peptide: str = Field(..., min_length=1)
    charge: int = Field(..., ge=1)
    q_value: float = Field(..., ge=0.0, le=1.0)
    protein_group_id: str = Field(..., min_length=1)
    protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    run_name: str = Field(..., min_length=1)
    sample_name: str = Field(..., min_length=1)
    precursor_quantity: float | None = Field(default=None, ge=0.0)
    protein_group_quantity: float | None = Field(default=None, ge=0.0)
    target_decoy_label: TargetDecoyLabel


class DiaNnProteinGroupReviewEntry(JsonModel):
    """Reviewer-facing protein-group quantity row from one DIA-NN report."""

    model_config = ConfigDict(extra="forbid")

    protein_group_id: str = Field(..., min_length=1)
    protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    run_name: str = Field(..., min_length=1)
    sample_name: str = Field(..., min_length=1)
    q_value: float = Field(..., ge=0.0, le=1.0)
    protein_group_quantity: float | None = Field(default=None, ge=0.0)
    source_precursor_count: int = Field(..., ge=1)
    target_decoy_label: TargetDecoyLabel


class DiaNnImportSummary(JsonModel):
    """Compact summary over one imported DIA-NN report."""

    model_config = ConfigDict(extra="forbid")

    accepted_precursor_count: int = Field(..., ge=0)
    rejected_precursor_count: int = Field(..., ge=0)
    protein_group_row_count: int = Field(..., ge=0)
    run_count: int = Field(..., ge=0)
    sample_count: int = Field(..., ge=0)
    precursor_quantity_count: int = Field(..., ge=0)
    protein_group_quantity_count: int = Field(..., ge=0)
    target_precursor_count: int = Field(..., ge=0)
    decoy_precursor_count: int = Field(..., ge=0)
    run_names: tuple[str, ...] = Field(default_factory=tuple)
    sample_names: tuple[str, ...] = Field(default_factory=tuple)


class DiaNnBundleImportReport(JsonModel):
    """One governed DIA-NN report import packet."""

    model_config = ConfigDict(extra="forbid")

    normalization: SearchAdapterNormalizationReport
    precursor_rows: tuple[DiaNnPrecursorReviewEntry, ...] = Field(default_factory=tuple)
    protein_group_rows: tuple[DiaNnProteinGroupReviewEntry, ...] = Field(
        default_factory=tuple
    )
    summary: DiaNnImportSummary
    dia_native_report: DiaNnImportReport
    parameter_report: SearchParameterReport | None = None


def build_diann_import_report(
    result_tsv_path: Path,
    *,
    config_path: Path | None = None,
) -> DiaNnBundleImportReport:
    """Import one DIA-NN precursor report into owned review surfaces."""
    require_valid_scientific_table(
        result_tsv_path,
        schema=build_diann_report_schema(),
    )
    normalization = normalize_search_results_with_adapter(
        source_path=result_tsv_path,
        adapter_kind=SearchAdapterKind.DIANN,
    )
    precursor_rows = _build_diann_precursor_rows(normalization)
    protein_group_rows = _build_diann_protein_group_rows(precursor_rows)
    dia_native_report = import_dia_nn_rows(
        tuple(
            DiaNnImportRow(
                precursor_id=row.precursor_id,
                peptide_sequence=row.peptide_sequence,
                charge=row.charge,
                q_value=row.q_value,
                quantity=row.precursor_quantity or 0.0,
                protein_group_id=row.protein_group_id,
            )
            for row in precursor_rows
        )
    )
    run_names = tuple(sorted({row.run_name for row in precursor_rows}))
    sample_names = tuple(sorted({row.sample_name for row in precursor_rows}))
    parameter_report = (
        None
        if config_path is None
        else parse_search_parameter_file(
            source_path=config_path,
            adapter_kind=SearchAdapterKind.DIANN,
        )
    )
    summary = DiaNnImportSummary(
        accepted_precursor_count=len(precursor_rows),
        rejected_precursor_count=len(normalization.parse_report.rejected_rows),
        protein_group_row_count=len(protein_group_rows),
        run_count=len(run_names),
        sample_count=len(sample_names),
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
        run_names=run_names,
        sample_names=sample_names,
    )
    return DiaNnBundleImportReport(
        normalization=normalization,
        precursor_rows=precursor_rows,
        protein_group_rows=protein_group_rows,
        summary=summary,
        dia_native_report=dia_native_report,
        parameter_report=parameter_report,
    )


def render_diann_summary_tsv(summary: DiaNnImportSummary) -> str:
    """Render the one-row DIA-NN summary as TSV."""
    header = (
        "accepted_precursor_count",
        "rejected_precursor_count",
        "protein_group_row_count",
        "run_count",
        "sample_count",
        "precursor_quantity_count",
        "protein_group_quantity_count",
        "target_precursor_count",
        "decoy_precursor_count",
        "run_names",
        "sample_names",
    )
    row = (
        str(summary.accepted_precursor_count),
        str(summary.rejected_precursor_count),
        str(summary.protein_group_row_count),
        str(summary.run_count),
        str(summary.sample_count),
        str(summary.precursor_quantity_count),
        str(summary.protein_group_quantity_count),
        str(summary.target_precursor_count),
        str(summary.decoy_precursor_count),
        ";".join(summary.run_names),
        ";".join(summary.sample_names),
    )
    return "\t".join(header) + "\n" + "\t".join(row) + "\n"


def render_diann_precursor_tsv(rows: tuple[DiaNnPrecursorReviewEntry, ...]) -> str:
    """Render reviewer-facing DIA-NN precursor rows as TSV."""
    lines = [
        "\t".join(
            (
                "precursor_id",
                "peptide_sequence",
                "modified_peptide",
                "canonical_peptide",
                "charge",
                "q_value",
                "protein_group_id",
                "protein_refs",
                "run_name",
                "sample_name",
                "precursor_quantity",
                "protein_group_quantity",
                "target_decoy_label",
            )
        )
    ]
    for row in rows:
        lines.append(
            "\t".join(
                (
                    row.precursor_id,
                    row.peptide_sequence,
                    row.modified_peptide,
                    row.canonical_peptide,
                    str(row.charge),
                    f"{row.q_value:.6g}",
                    row.protein_group_id,
                    ";".join(row.protein_refs),
                    row.run_name,
                    row.sample_name,
                    ""
                    if row.precursor_quantity is None
                    else f"{row.precursor_quantity:.6g}",
                    ""
                    if row.protein_group_quantity is None
                    else f"{row.protein_group_quantity:.6g}",
                    row.target_decoy_label.value,
                )
            )
        )
    return "\n".join(lines) + "\n"


def render_diann_protein_group_tsv(
    rows: tuple[DiaNnProteinGroupReviewEntry, ...],
) -> str:
    """Render reviewer-facing DIA-NN protein-group rows as TSV."""
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
            )
        )
    ]
    for row in rows:
        lines.append(
            "\t".join(
                (
                    row.protein_group_id,
                    ";".join(row.protein_refs),
                    row.run_name,
                    row.sample_name,
                    f"{row.q_value:.6g}",
                    ""
                    if row.protein_group_quantity is None
                    else f"{row.protein_group_quantity:.6g}",
                    str(row.source_precursor_count),
                    row.target_decoy_label.value,
                )
            )
        )
    return "\n".join(lines) + "\n"


def _build_diann_precursor_rows(
    normalization: SearchAdapterNormalizationReport,
) -> tuple[DiaNnPrecursorReviewEntry, ...]:
    rows: list[DiaNnPrecursorReviewEntry] = []
    for evidence_row in normalization.evidence_rows:
        if not evidence_row.accepted or evidence_row.normalized_record is None:
            continue
        record = evidence_row.normalized_record
        raw = evidence_row.raw_fields
        protein_group_id = _required_value(raw, "Protein.Group")
        run_name = _required_value(raw, "Run")
        sample_name = _required_value(raw, "Sample")
        rows.append(
            DiaNnPrecursorReviewEntry(
                precursor_id=record.spectrum_id,
                peptide_sequence=record.peptide,
                modified_peptide=raw.get("Modified.Sequence", "").strip()
                or record.canonical_peptide,
                canonical_peptide=record.canonical_peptide,
                charge=record.charge,
                q_value=record.q_value if record.q_value is not None else record.score,
                protein_group_id=protein_group_id,
                protein_refs=record.protein_refs,
                run_name=run_name,
                sample_name=sample_name,
                precursor_quantity=_optional_float(raw.get("Precursor.Quantity")),
                protein_group_quantity=_optional_float(raw.get("PG.Quantity")),
                target_decoy_label=record.target_decoy_label,
            )
        )
    return tuple(sorted(rows, key=lambda row: (row.q_value, row.precursor_id)))


def _build_diann_protein_group_rows(
    precursor_rows: tuple[DiaNnPrecursorReviewEntry, ...],
) -> tuple[DiaNnProteinGroupReviewEntry, ...]:
    grouped: dict[tuple[str, str, str], list[DiaNnPrecursorReviewEntry]] = {}
    for row in precursor_rows:
        grouped.setdefault(
            (row.protein_group_id, row.run_name, row.sample_name), []
        ).append(row)
    rows: list[DiaNnProteinGroupReviewEntry] = []
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
            DiaNnProteinGroupReviewEntry(
                protein_group_id=protein_group_id,
                protein_refs=protein_refs,
                run_name=run_name,
                sample_name=sample_name,
                q_value=min(entry.q_value for entry in entries),
                protein_group_quantity=quantity,
                source_precursor_count=len(entries),
                target_decoy_label=_combine_labels(entries),
            )
        )
    return tuple(rows)


def _combine_labels(entries: list[DiaNnPrecursorReviewEntry]) -> TargetDecoyLabel:
    labels = {entry.target_decoy_label for entry in entries}
    if labels == {TargetDecoyLabel.DECOY}:
        return TargetDecoyLabel.DECOY
    if labels == {TargetDecoyLabel.TARGET}:
        return TargetDecoyLabel.TARGET
    if not labels:
        return TargetDecoyLabel.UNKNOWN
    return TargetDecoyLabel.MIXED


def _required_value(row: dict[str, str], column: str) -> str:
    value = row.get(column, "").strip()
    if not value:
        raise ValueError(f"DIA-NN report is missing required {column!r} value")
    return value


def _optional_float(value: str | None) -> float | None:
    if value is None or not value.strip():
        return None
    return float(value.strip())

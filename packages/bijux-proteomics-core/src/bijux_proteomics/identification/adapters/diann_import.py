# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""DIA-NN report import over precursor and protein-group evidence."""

from __future__ import annotations

from pathlib import Path

from pydantic import ConfigDict, Field

from bijux_proteomics._scientific_tables import (
    ScientificTableRejectedRow,
    ScientificTableValidationError,
    ScientificTableValidationIssue,
    build_diann_report_schema,
    validate_scientific_table,
)
from bijux_proteomics._tabular import AcceptedDelimitedRow
from bijux_proteomics.dia import DiaNnImportReport, DiaNnImportRow, import_dia_nn_rows
from bijux_proteomics.domain.records import ImportedEvidenceProvenance
from bijux_proteomics.identification.contracts import TargetDecoyLabel
from bijux_proteomics.identification.rejected_evidence_table import (
    RejectedEvidenceTableEntry,
    build_rejected_evidence_rows_from_scientific_rows,
)
from bijux_proteomics.identification.search_adapters.contracts import (
    SearchAdapterKind,
    SearchAdapterNormalizationReport,
    SearchParameterReport,
)
from bijux_proteomics.identification.search_adapters.normalization import (
    normalize_search_results_with_adapter,
)
from bijux_proteomics.identification.search_adapters.parameter_review import (
    parse_search_parameter_file,
)
from bijux_proteomics.io.stable_outputs import sort_rows_by_fields, sort_strings
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
    provenance: ImportedEvidenceProvenance


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
    provenance: ImportedEvidenceProvenance


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


class DiaNnRejectedRowEntry(JsonModel):
    """One DIA-NN row rejected during governed import."""

    model_config = ConfigDict(extra="forbid")

    row_number: int = Field(..., ge=1)
    raw_values: dict[str, str] = Field(default_factory=dict)
    issues: tuple[ScientificTableValidationIssue, ...] = Field(default_factory=tuple)


class DiaNnBundleImportReport(JsonModel):
    """One governed DIA-NN report import packet."""

    model_config = ConfigDict(extra="forbid")

    normalization: SearchAdapterNormalizationReport | None = None
    precursor_rows: tuple[DiaNnPrecursorReviewEntry, ...] = Field(default_factory=tuple)
    protein_group_rows: tuple[DiaNnProteinGroupReviewEntry, ...] = Field(
        default_factory=tuple
    )
    rejected_rows: tuple[DiaNnRejectedRowEntry, ...] = Field(default_factory=tuple)
    rejected_evidence_rows: tuple[RejectedEvidenceTableEntry, ...] = Field(
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
    validation_report = validate_scientific_table(
        result_tsv_path,
        schema=build_diann_report_schema(),
    )
    if _has_structural_validation_failure(validation_report.rejected_rows):
        raise ScientificTableValidationError(validation_report)
    normalization = (
        None
        if validation_report.rejected_rows
        else normalize_search_results_with_adapter(
            source_path=result_tsv_path,
            adapter_kind=SearchAdapterKind.DIANN,
        )
    )
    precursor_rows = _build_diann_precursor_rows(
        validation_report.accepted_rows,
        source_path=result_tsv_path,
    )
    protein_group_rows = _build_diann_protein_group_rows(precursor_rows)
    rejected_rows = _build_diann_rejected_rows(validation_report.rejected_rows)
    dia_native_report = import_dia_nn_rows(
        tuple(
            DiaNnImportRow(
                precursor_id=row.precursor_id,
                peptide_sequence=row.peptide_sequence,
                modified_peptide=row.modified_peptide,
                charge=row.charge,
                q_value=row.q_value,
                precursor_quantity=row.precursor_quantity,
                protein_group_id=row.protein_group_id,
                protein_refs=row.protein_refs,
                run_name=row.run_name,
                sample_name=row.sample_name,
                protein_group_quantity=row.protein_group_quantity,
                provenance=row.provenance,
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
        rejected_precursor_count=len(rejected_rows),
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
        rejected_rows=rejected_rows,
        rejected_evidence_rows=build_rejected_evidence_rows_from_scientific_rows(
            validation_report.rejected_rows,
            source_file=result_tsv_path.name,
            entity_type="precursor",
            entity_id_columns=(
                "Precursor.Id",
                "Modified.Sequence",
                "Stripped.Sequence",
                "Protein.Group",
            ),
        ),
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
                    row.canonical_peptide,
                    str(row.charge),
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


def render_diann_protein_group_tsv(
    rows: tuple[DiaNnProteinGroupReviewEntry, ...],
) -> str:
    """Render reviewer-facing DIA-NN protein-group rows as TSV."""
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


def render_diann_rejected_row_tsv(rows: tuple[DiaNnRejectedRowEntry, ...]) -> str:
    """Render rejected DIA-NN rows and their validation evidence as TSV."""

    ordered_rows = sort_rows_by_fields(rows, "row_number")
    lines = [
        "\t".join(
            (
                "row_number",
                "precursor_id",
                "peptide_sequence",
                "modified_peptide",
                "charge",
                "q_value",
                "protein_group_id",
                "protein_refs",
                "run_name",
                "sample_name",
                "precursor_quantity",
                "protein_group_quantity",
                "decoy",
                "issue_codes",
                "issue_messages",
            )
        )
    ]
    for row in ordered_rows:
        lines.append(
            "\t".join(
                (
                    str(row.row_number),
                    row.raw_values.get("Precursor.Id", ""),
                    row.raw_values.get("Stripped.Sequence", ""),
                    row.raw_values.get("Modified.Sequence", ""),
                    row.raw_values.get("Precursor.Charge", ""),
                    row.raw_values.get("Q.Value", ""),
                    row.raw_values.get("Protein.Group", ""),
                    row.raw_values.get("Protein.Ids", ""),
                    row.raw_values.get("Run", ""),
                    row.raw_values.get("Sample", ""),
                    row.raw_values.get("Precursor.Quantity", ""),
                    row.raw_values.get("PG.Quantity", ""),
                    row.raw_values.get("Decoy", ""),
                    ";".join(issue.code for issue in row.issues),
                    " | ".join(issue.message for issue in row.issues),
                )
            )
        )
    return "\n".join(lines) + "\n"


def _build_diann_precursor_rows(
    accepted_rows: tuple[AcceptedDelimitedRow, ...],
    *,
    source_path: Path,
) -> tuple[DiaNnPrecursorReviewEntry, ...]:
    rows: list[DiaNnPrecursorReviewEntry] = []
    for accepted_row in accepted_rows:
        values = accepted_row.values
        raw = accepted_row.raw_values
        protein_group_id = _required_text(values, "protein_group_id")
        run_name = _required_text(values, "run_name")
        sample_name = _required_text(values, "sample_name")
        rows.append(
            DiaNnPrecursorReviewEntry(
                precursor_id=_required_text(values, "precursor_id"),
                peptide_sequence=_required_text(values, "peptide_sequence"),
                modified_peptide=_required_text(values, "modified_peptide"),
                canonical_peptide=_required_text(values, "peptide_sequence"),
                charge=_required_int(values, "charge"),
                q_value=_required_float(values, "q_value"),
                protein_group_id=protein_group_id,
                protein_refs=_split_protein_refs(
                    _required_text(values, "protein_refs")
                ),
                run_name=run_name,
                sample_name=sample_name,
                precursor_quantity=_optional_float_value(
                    values.get("precursor_quantity")
                ),
                protein_group_quantity=_optional_float_value(
                    values.get("protein_group_quantity")
                ),
                target_decoy_label=_parse_target_decoy_label(raw.get("Decoy")),
                provenance=ImportedEvidenceProvenance.from_single_row(
                    source_engine="diann",
                    source_file=str(source_path),
                    source_row_number=accepted_row.row_number,
                    original_identifiers={
                        "precursor_id": _required_text(values, "precursor_id"),
                        "protein_group_id": protein_group_id,
                        "run_name": run_name,
                        "sample_name": sample_name,
                    },
                ),
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


def _build_diann_rejected_rows(
    rejected_rows: tuple[ScientificTableRejectedRow, ...],
) -> tuple[DiaNnRejectedRowEntry, ...]:
    return tuple(
        DiaNnRejectedRowEntry(
            row_number=row.row_number,
            raw_values=row.raw_values,
            issues=row.issues,
        )
        for row in rejected_rows
    )


def _combine_labels(entries: list[DiaNnPrecursorReviewEntry]) -> TargetDecoyLabel:
    labels = {entry.target_decoy_label for entry in entries}
    if labels == {TargetDecoyLabel.DECOY}:
        return TargetDecoyLabel.DECOY
    if labels == {TargetDecoyLabel.TARGET}:
        return TargetDecoyLabel.TARGET
    if not labels:
        return TargetDecoyLabel.UNKNOWN
    return TargetDecoyLabel.MIXED


def _has_structural_validation_failure(
    rejected_rows: tuple[ScientificTableRejectedRow, ...],
) -> bool:
    return any(not row.raw_values for row in rejected_rows)


def _required_text(values: dict[str, str | int | float | bool | None], key: str) -> str:
    value = values.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"DIA-NN report is missing required {key!r} value")
    return value.strip()


def _required_int(values: dict[str, str | int | float | bool | None], key: str) -> int:
    value = values.get(key)
    if not isinstance(value, int):
        raise ValueError(f"DIA-NN report is missing required integer {key!r} value")
    return value


def _required_float(
    values: dict[str, str | int | float | bool | None],
    key: str,
) -> float:
    value = values.get(key)
    if not isinstance(value, float):
        raise ValueError(f"DIA-NN report is missing required numeric {key!r} value")
    return value


def _optional_float_value(value: str | int | float | bool | None) -> float | None:
    if value is None:
        return None
    if isinstance(value, int | float):
        return float(value)
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return None
        return float(stripped)
    raise ValueError("DIA-NN quantity values must be numeric or empty")


def _split_protein_refs(raw_protein_refs: str) -> tuple[str, ...]:
    return tuple(
        dict.fromkeys(
            protein_ref.strip()
            for protein_ref in raw_protein_refs.split(";")
            if protein_ref.strip()
        )
    )


def _parse_target_decoy_label(raw_decoy: str | None) -> TargetDecoyLabel:
    normalized = (raw_decoy or "").strip().lower()
    if normalized in {"1", "true", "yes", "y"}:
        return TargetDecoyLabel.DECOY
    if normalized in {"0", "false", "no", "n"}:
        return TargetDecoyLabel.TARGET
    return TargetDecoyLabel.UNKNOWN

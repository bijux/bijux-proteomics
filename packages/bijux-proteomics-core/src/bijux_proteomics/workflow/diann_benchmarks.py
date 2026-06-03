# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Benchmark surfaces for DIA-NN import and protein-matrix fidelity."""

from __future__ import annotations

import csv
from io import StringIO
from pathlib import Path

from pydantic import ConfigDict, Field

from bijux_proteomics.dia import (
    DiaPeptideRollupMethod,
    DiaPrecursorMatrixPolicy,
    DiaPrecursorMatrixReport,
    DiaProteinMatrixReport,
    DiaProteinMatrixTargetKind,
    DiaProteinRollupMethod,
    DiaSharedPeptidePolicy,
    build_dia_peptide_matrix_report,
    build_dia_precursor_matrix_report,
    build_dia_protein_matrix_report,
)
from bijux_proteomics.identification.contracts import TargetDecoyLabel
from bijux_proteomics.identification.diann_import import (
    DiaNnBundleImportReport,
    build_diann_import_report,
)
from bijux_proteomics_foundation import JsonModel


class DiannBenchmarkCountComparisonEntry(JsonModel):
    """One count comparison inside a DIA-NN benchmark report."""

    model_config = ConfigDict(extra="forbid")

    comparison_id: str = Field(..., min_length=1)
    source_count: int = Field(..., ge=0)
    imported_count: int = Field(..., ge=0)
    matched: bool
    note: str = Field(..., min_length=1)


class DiannBenchmarkProteinQuantityComparisonEntry(JsonModel):
    """One protein-group quantity comparison between source DIA-NN and Bijux."""

    model_config = ConfigDict(extra="forbid")

    entity_id: str = Field(..., min_length=1)
    sample_id: str = Field(..., min_length=1)
    source_quantity: float | None = Field(default=None, ge=0.0)
    imported_quantity: float | None = Field(default=None, ge=0.0)
    absolute_difference: float = Field(..., ge=0.0)
    exact_match: bool


class DiannBenchmarkSummary(JsonModel):
    """Compact summary over one DIA-NN benchmark."""

    model_config = ConfigDict(extra="forbid")

    source_precursor_count: int = Field(..., ge=0)
    imported_precursor_count: int = Field(..., ge=0)
    source_filtered_precursor_count: int = Field(..., ge=0)
    imported_filtered_precursor_count: int = Field(..., ge=0)
    source_protein_group_count: int = Field(..., ge=0)
    imported_protein_group_count: int = Field(..., ge=0)
    source_excluded_q_value_count: int = Field(..., ge=0)
    imported_excluded_q_value_count: int = Field(..., ge=0)
    source_decoy_count: int = Field(..., ge=0)
    imported_excluded_decoy_count: int = Field(..., ge=0)
    source_protein_quantity_count: int = Field(..., ge=0)
    imported_protein_quantity_count: int = Field(..., ge=0)
    exact_protein_quantity_match_count: int = Field(..., ge=0)
    max_protein_quantity_difference: float = Field(..., ge=0.0)
    precursor_count_matched: bool
    filtered_precursor_count_matched: bool
    protein_group_count_matched: bool
    q_value_filtering_matched: bool
    decoy_filtering_matched: bool
    protein_quantities_matched: bool


class DiannBenchmarkReport(JsonModel):
    """Owned benchmark report over one real DIA-NN report."""

    model_config = ConfigDict(extra="forbid")

    import_report: DiaNnBundleImportReport
    precursor_matrix_report: DiaPrecursorMatrixReport
    protein_matrix_report: DiaProteinMatrixReport
    count_comparisons: tuple[DiannBenchmarkCountComparisonEntry, ...] = Field(
        default_factory=tuple
    )
    protein_quantity_comparisons: tuple[
        DiannBenchmarkProteinQuantityComparisonEntry, ...
    ] = Field(default_factory=tuple)
    summary: DiannBenchmarkSummary
    note: str = Field(..., min_length=1)


def build_diann_benchmark_report(
    result_tsv_path: Path,
    *,
    config_path: Path | None = None,
    include_decoys: bool = False,
    max_q_value: float | None = 0.01,
    peptide_rollup_method: DiaPeptideRollupMethod = DiaPeptideRollupMethod.MAX,
    shared_peptide_policy: DiaSharedPeptidePolicy = DiaSharedPeptidePolicy.INCLUDE,
    protein_rollup_method: DiaProteinRollupMethod = DiaProteinRollupMethod.SUM,
) -> DiannBenchmarkReport:
    """Compare source DIA-NN report behavior against governed Bijux surfaces."""

    import_report = build_diann_import_report(result_tsv_path, config_path=config_path)
    source_rows = _read_source_rows(result_tsv_path)
    precursor_matrix_report = build_dia_precursor_matrix_report(
        import_report.precursor_rows,
        source_name="DIA-NN",
        policy=DiaPrecursorMatrixPolicy(
            include_decoys=include_decoys,
            max_q_value=max_q_value,
        ),
    )
    peptide_matrix_report = build_dia_peptide_matrix_report(
        precursor_matrix_report,
        rollup_method=peptide_rollup_method,
    )
    protein_matrix_report = build_dia_protein_matrix_report(
        peptide_matrix_report,
        target_kind=DiaProteinMatrixTargetKind.PROTEIN_GROUP,
        shared_peptide_policy=shared_peptide_policy,
        rollup_method=protein_rollup_method,
    )

    source_precursor_count = len(source_rows)
    source_decoy_count = sum(
        1 for row in source_rows if row.target_decoy_label is TargetDecoyLabel.DECOY
    )
    source_excluded_q_value_count = sum(
        1
        for row in source_rows
        if row.target_decoy_label is not TargetDecoyLabel.DECOY
        and max_q_value is not None
        and row.q_value > max_q_value
    )
    source_filtered_precursor_keys = _source_filtered_precursor_keys(
        source_rows,
        include_decoys=include_decoys,
        max_q_value=max_q_value,
    )
    source_protein_quantities = _source_protein_quantities(
        source_rows,
        include_decoys=include_decoys,
        max_q_value=max_q_value,
    )
    count_comparisons = (
        DiannBenchmarkCountComparisonEntry(
            comparison_id="precursor_rows",
            source_count=source_precursor_count,
            imported_count=import_report.summary.accepted_precursor_count,
            matched=source_precursor_count
            == import_report.summary.accepted_precursor_count,
            note="governed Bijux DIA-NN import should preserve the source precursor row count for the benchmark report",
        ),
        DiannBenchmarkCountComparisonEntry(
            comparison_id="filtered_precursor_rows",
            source_count=len(source_filtered_precursor_keys),
            imported_count=precursor_matrix_report.summary.precursor_row_count,
            matched=len(source_filtered_precursor_keys)
            == precursor_matrix_report.summary.precursor_row_count,
            note="filtered precursor-key count should match the governed precursor matrix row count under the active DIA-NN benchmark filter policy",
        ),
        DiannBenchmarkCountComparisonEntry(
            comparison_id="protein_group_rows",
            source_count=len({entity_id for entity_id, _ in source_protein_quantities}),
            imported_count=protein_matrix_report.summary.protein_row_count,
            matched=len({entity_id for entity_id, _ in source_protein_quantities})
            == protein_matrix_report.summary.protein_row_count,
            note="filtered source protein-group count should match the governed Bijux protein-matrix row count under protein-group rollup",
        ),
        DiannBenchmarkCountComparisonEntry(
            comparison_id="excluded_q_value_rows",
            source_count=source_excluded_q_value_count,
            imported_count=precursor_matrix_report.summary.excluded_q_value_count,
            matched=source_excluded_q_value_count
            == precursor_matrix_report.summary.excluded_q_value_count,
            note="q-value exclusions should match exactly between the source DIA-NN report and the governed Bijux precursor filter",
        ),
        DiannBenchmarkCountComparisonEntry(
            comparison_id="excluded_decoy_rows",
            source_count=0 if include_decoys else source_decoy_count,
            imported_count=precursor_matrix_report.summary.excluded_decoy_count,
            matched=(0 if include_decoys else source_decoy_count)
            == precursor_matrix_report.summary.excluded_decoy_count,
            note="decoy exclusions should match exactly between the source DIA-NN report and the governed Bijux precursor filter",
        ),
    )
    protein_quantity_comparisons = _build_protein_quantity_comparisons(
        source_quantities=source_protein_quantities,
        protein_matrix_report=protein_matrix_report,
    )
    return DiannBenchmarkReport(
        import_report=import_report,
        precursor_matrix_report=precursor_matrix_report,
        protein_matrix_report=protein_matrix_report,
        count_comparisons=count_comparisons,
        protein_quantity_comparisons=protein_quantity_comparisons,
        summary=DiannBenchmarkSummary(
            source_precursor_count=source_precursor_count,
            imported_precursor_count=import_report.summary.accepted_precursor_count,
            source_filtered_precursor_count=len(source_filtered_precursor_keys),
            imported_filtered_precursor_count=precursor_matrix_report.summary.precursor_row_count,
            source_protein_group_count=len(
                {entity_id for entity_id, _ in source_protein_quantities}
            ),
            imported_protein_group_count=protein_matrix_report.summary.protein_row_count,
            source_excluded_q_value_count=source_excluded_q_value_count,
            imported_excluded_q_value_count=precursor_matrix_report.summary.excluded_q_value_count,
            source_decoy_count=0 if include_decoys else source_decoy_count,
            imported_excluded_decoy_count=precursor_matrix_report.summary.excluded_decoy_count,
            source_protein_quantity_count=len(source_protein_quantities),
            imported_protein_quantity_count=len(protein_quantity_comparisons),
            exact_protein_quantity_match_count=sum(
                1 for entry in protein_quantity_comparisons if entry.exact_match
            ),
            max_protein_quantity_difference=max(
                (entry.absolute_difference for entry in protein_quantity_comparisons),
                default=0.0,
            ),
            precursor_count_matched=count_comparisons[0].matched,
            filtered_precursor_count_matched=count_comparisons[1].matched,
            protein_group_count_matched=count_comparisons[2].matched,
            q_value_filtering_matched=count_comparisons[3].matched,
            decoy_filtering_matched=count_comparisons[4].matched,
            protein_quantities_matched=all(
                entry.exact_match for entry in protein_quantity_comparisons
            ),
        ),
        note=(
            "DIA-NN benchmark compares source precursor coverage, q-value and decoy filtering, protein-group counts, and protein quantities against the governed Bijux import and protein-matrix surfaces"
        ),
    )


def render_diann_benchmark_summary_tsv(report: DiannBenchmarkReport) -> str:
    """Render one compact DIA-NN benchmark summary as TSV."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(("field", "value"))
    for field_name, value in (
        ("source_precursor_count", report.summary.source_precursor_count),
        ("imported_precursor_count", report.summary.imported_precursor_count),
        (
            "source_filtered_precursor_count",
            report.summary.source_filtered_precursor_count,
        ),
        (
            "imported_filtered_precursor_count",
            report.summary.imported_filtered_precursor_count,
        ),
        ("source_protein_group_count", report.summary.source_protein_group_count),
        ("imported_protein_group_count", report.summary.imported_protein_group_count),
        (
            "source_excluded_q_value_count",
            report.summary.source_excluded_q_value_count,
        ),
        (
            "imported_excluded_q_value_count",
            report.summary.imported_excluded_q_value_count,
        ),
        ("source_decoy_count", report.summary.source_decoy_count),
        (
            "imported_excluded_decoy_count",
            report.summary.imported_excluded_decoy_count,
        ),
        (
            "source_protein_quantity_count",
            report.summary.source_protein_quantity_count,
        ),
        (
            "imported_protein_quantity_count",
            report.summary.imported_protein_quantity_count,
        ),
        (
            "exact_protein_quantity_match_count",
            report.summary.exact_protein_quantity_match_count,
        ),
        (
            "max_protein_quantity_difference",
            f"{report.summary.max_protein_quantity_difference:g}",
        ),
        (
            "precursor_count_matched",
            str(report.summary.precursor_count_matched).lower(),
        ),
        (
            "filtered_precursor_count_matched",
            str(report.summary.filtered_precursor_count_matched).lower(),
        ),
        (
            "protein_group_count_matched",
            str(report.summary.protein_group_count_matched).lower(),
        ),
        (
            "q_value_filtering_matched",
            str(report.summary.q_value_filtering_matched).lower(),
        ),
        (
            "decoy_filtering_matched",
            str(report.summary.decoy_filtering_matched).lower(),
        ),
        (
            "protein_quantities_matched",
            str(report.summary.protein_quantities_matched).lower(),
        ),
        ("note", report.note),
    ):
        writer.writerow((field_name, value))
    return handle.getvalue()


def render_diann_benchmark_count_comparisons_tsv(
    report: DiannBenchmarkReport,
) -> str:
    """Render count comparisons inside one DIA-NN benchmark report."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(
        ("comparison_id", "source_count", "imported_count", "matched", "note")
    )
    for entry in report.count_comparisons:
        writer.writerow(
            (
                entry.comparison_id,
                entry.source_count,
                entry.imported_count,
                str(entry.matched).lower(),
                entry.note,
            )
        )
    return handle.getvalue()


def render_diann_benchmark_protein_quantities_tsv(
    report: DiannBenchmarkReport,
) -> str:
    """Render one DIA-NN protein quantity comparison ledger as TSV."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "entity_id",
            "sample_id",
            "source_quantity",
            "imported_quantity",
            "absolute_difference",
            "exact_match",
        )
    )
    for entry in report.protein_quantity_comparisons:
        writer.writerow(
            (
                entry.entity_id,
                entry.sample_id,
                "" if entry.source_quantity is None else f"{entry.source_quantity:g}",
                ""
                if entry.imported_quantity is None
                else f"{entry.imported_quantity:g}",
                f"{entry.absolute_difference:g}",
                str(entry.exact_match).lower(),
            )
        )
    return handle.getvalue()


class _SourceDiannRow(JsonModel):
    model_config = ConfigDict(extra="forbid")

    precursor_id: str
    peptide_sequence: str
    modified_peptide: str
    charge: int
    q_value: float
    protein_group_id: str
    sample_id: str
    precursor_quantity: float | None = None
    protein_group_quantity: float | None = None
    target_decoy_label: TargetDecoyLabel


def _read_source_rows(path: Path) -> tuple[_SourceDiannRow, ...]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames is None:
            raise ValueError("DIA-NN benchmark input must include a header row")
        rows: list[_SourceDiannRow] = []
        for row in reader:
            normalized = {key: (value or "").strip() for key, value in row.items()}
            rows.append(
                _SourceDiannRow(
                    precursor_id=normalized["Precursor.Id"],
                    peptide_sequence=normalized["Stripped.Sequence"],
                    modified_peptide=normalized["Modified.Sequence"],
                    charge=int(normalized["Precursor.Charge"]),
                    q_value=float(normalized["Q.Value"]),
                    protein_group_id=normalized["Protein.Group"],
                    sample_id=normalized["Sample"],
                    precursor_quantity=_parse_optional_float(
                        normalized.get("Precursor.Quantity", "")
                    ),
                    protein_group_quantity=_parse_optional_float(
                        normalized.get("PG.Quantity", "")
                    ),
                    target_decoy_label=(
                        TargetDecoyLabel.DECOY
                        if normalized.get("Decoy", "") in {"1", "true", "True"}
                        else TargetDecoyLabel.TARGET
                    ),
                )
            )
    return tuple(rows)


def _source_filtered_precursor_keys(
    rows: tuple[_SourceDiannRow, ...],
    *,
    include_decoys: bool,
    max_q_value: float | None,
) -> tuple[str, ...]:
    return tuple(
        sorted(
            {
                _build_precursor_key(row)
                for row in rows
                if _include_source_row(
                    row,
                    include_decoys=include_decoys,
                    max_q_value=max_q_value,
                )
            }
        )
    )


def _source_protein_quantities(
    rows: tuple[_SourceDiannRow, ...],
    *,
    include_decoys: bool,
    max_q_value: float | None,
) -> dict[tuple[str, str], float | None]:
    grouped: dict[tuple[str, str], list[float]] = {}
    for row in rows:
        if not _include_source_row(
            row,
            include_decoys=include_decoys,
            max_q_value=max_q_value,
        ):
            continue
        if row.protein_group_quantity is None:
            grouped.setdefault((row.protein_group_id, row.sample_id), [])
            continue
        grouped.setdefault((row.protein_group_id, row.sample_id), []).append(
            row.protein_group_quantity
        )
    return {key: (max(values) if values else None) for key, values in grouped.items()}


def _build_protein_quantity_comparisons(
    *,
    source_quantities: dict[tuple[str, str], float | None],
    protein_matrix_report: DiaProteinMatrixReport,
) -> tuple[DiannBenchmarkProteinQuantityComparisonEntry, ...]:
    comparisons: list[DiannBenchmarkProteinQuantityComparisonEntry] = []
    for row in sorted(protein_matrix_report.rows, key=lambda entry: entry.entity_id):
        for value in sorted(row.values, key=lambda entry: entry.sample_id):
            source_quantity = source_quantities[(row.entity_id, value.sample_id)]
            imported_quantity = value.abundance
            absolute_difference = abs(
                (source_quantity or 0.0) - (imported_quantity or 0.0)
            )
            comparisons.append(
                DiannBenchmarkProteinQuantityComparisonEntry(
                    entity_id=row.entity_id,
                    sample_id=value.sample_id,
                    source_quantity=source_quantity,
                    imported_quantity=imported_quantity,
                    absolute_difference=absolute_difference,
                    exact_match=source_quantity == imported_quantity,
                )
            )
    return tuple(comparisons)


def _include_source_row(
    row: _SourceDiannRow,
    *,
    include_decoys: bool,
    max_q_value: float | None,
) -> bool:
    if not include_decoys and row.target_decoy_label is TargetDecoyLabel.DECOY:
        return False
    return not (max_q_value is not None and row.q_value > max_q_value)


def _build_precursor_key(row: _SourceDiannRow) -> str:
    return (
        f"{row.peptide_sequence}|{row.modified_peptide}|{row.charge}|"
        f"{row.protein_group_id}"
    )


def _parse_optional_float(value: str) -> float | None:
    return None if not value else float(value)

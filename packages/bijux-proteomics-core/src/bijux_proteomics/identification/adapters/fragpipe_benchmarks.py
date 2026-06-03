# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Benchmark surfaces for FragPipe import fidelity against source bundle tables."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
import csv
from io import StringIO
from pathlib import Path

from pydantic import ConfigDict, Field

from bijux_proteomics.identification.adapters.fragpipe_import import (
    FragpipeImportReport,
    build_fragpipe_import_report,
)
from bijux_proteomics_foundation import JsonModel


class FragpipeCountComparisonEntry(JsonModel):
    """One source-versus-imported count comparison inside a FragPipe benchmark."""

    model_config = ConfigDict(extra="forbid")

    comparison_id: str = Field(..., min_length=1)
    source_count: int = Field(..., ge=0)
    imported_count: int = Field(..., ge=0)
    matched: bool
    note: str = Field(..., min_length=1)


class FragpipeProteinGroupComparison(JsonModel):
    """Protein-group identity comparison between a FragPipe source table and Bijux import."""

    model_config = ConfigDict(extra="forbid")

    source_protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    imported_protein_refs: tuple[str, ...] = Field(default_factory=tuple)
    missing_in_import: tuple[str, ...] = Field(default_factory=tuple)
    extra_in_import: tuple[str, ...] = Field(default_factory=tuple)
    matched: bool
    note: str = Field(..., min_length=1)


class FragpipeQValueComparisonEntry(JsonModel):
    """One q-value preservation row between a FragPipe source table and Bijux import."""

    model_config = ConfigDict(extra="forbid")

    entity_kind: str = Field(..., min_length=1)
    entity_id: str = Field(..., min_length=1)
    source_q_value: float = Field(..., ge=0.0)
    imported_q_value: float = Field(..., ge=0.0)
    absolute_difference: float = Field(..., ge=0.0)
    exact_match: bool


class FragpipeQValueBehaviorComparison(JsonModel):
    """Aggregate q-value behavior comparison between source FragPipe tables and Bijux import."""

    model_config = ConfigDict(extra="forbid")

    psm_entries: tuple[FragpipeQValueComparisonEntry, ...] = Field(default_factory=tuple)
    peptide_entries: tuple[FragpipeQValueComparisonEntry, ...] = Field(
        default_factory=tuple
    )
    source_psm_q_values_monotonic: bool
    imported_psm_q_values_monotonic: bool
    source_peptide_q_values_monotonic: bool
    imported_peptide_q_values_monotonic: bool
    max_psm_absolute_difference: float = Field(..., ge=0.0)
    max_peptide_absolute_difference: float = Field(..., ge=0.0)
    note: str = Field(..., min_length=1)


class FragpipeImportBenchmarkSummary(JsonModel):
    """Compact summary over one FragPipe import fidelity benchmark."""

    model_config = ConfigDict(extra="forbid")

    source_psm_count: int = Field(..., ge=0)
    imported_psm_count: int = Field(..., ge=0)
    source_peptide_count: int = Field(..., ge=0)
    imported_peptide_count: int = Field(..., ge=0)
    source_protein_group_count: int = Field(..., ge=0)
    imported_protein_group_count: int = Field(..., ge=0)
    source_q_value_psm_count: int = Field(..., ge=0)
    imported_q_value_psm_count: int = Field(..., ge=0)
    source_q_value_peptide_count: int = Field(..., ge=0)
    imported_q_value_peptide_count: int = Field(..., ge=0)
    protein_group_overlap_count: int = Field(..., ge=0)
    missing_protein_group_count: int = Field(..., ge=0)
    extra_protein_group_count: int = Field(..., ge=0)
    psm_count_matched: bool
    peptide_count_matched: bool
    protein_group_count_matched: bool
    q_value_behavior_matched: bool


class FragpipeImportBenchmarkReport(JsonModel):
    """Owned benchmark report over one real FragPipe result bundle."""

    model_config = ConfigDict(extra="forbid")

    import_report: FragpipeImportReport
    count_comparisons: tuple[FragpipeCountComparisonEntry, ...] = Field(
        default_factory=tuple
    )
    protein_group_comparison: FragpipeProteinGroupComparison
    q_value_behavior: FragpipeQValueBehaviorComparison
    summary: FragpipeImportBenchmarkSummary
    note: str = Field(..., min_length=1)


def build_fragpipe_import_benchmark_report(
    psm_tsv_path: Path,
    *,
    peptide_tsv_path: Path,
    protein_tsv_path: Path,
) -> FragpipeImportBenchmarkReport:
    """Compare Bijux FragPipe import behavior against one source FragPipe bundle."""

    import_report = build_fragpipe_import_report(
        psm_tsv_path,
        peptide_tsv_path=peptide_tsv_path,
        protein_tsv_path=protein_tsv_path,
    )
    source_psm_rows = _read_tsv_rows(psm_tsv_path)
    source_peptide_rows = _read_tsv_rows(peptide_tsv_path)
    source_protein_rows = _read_tsv_rows(protein_tsv_path)
    source_psm_q_values = _source_psm_q_values(source_psm_rows)
    source_peptide_q_values = _source_peptide_q_values(source_peptide_rows)
    imported_psm_q_values: Mapping[str, float] = {
        row.spectrum_id: row.q_value
        for row in import_report.psm_rows
        if row.q_value is not None
    }
    imported_peptide_q_values: Mapping[str, float] = {
        _peptide_entity_id(
            peptide=row.peptide,
            modified_peptide=row.modified_peptide,
            charge=row.charge,
        ): row.q_value
        for row in import_report.peptide_rows
        if row.q_value is not None
    }
    count_comparisons = (
        FragpipeCountComparisonEntry(
            comparison_id="psm_rows",
            source_count=len(source_psm_rows),
            imported_count=import_report.summary.accepted_psm_count,
            matched=len(source_psm_rows) == import_report.summary.accepted_psm_count,
            note="accepted Bijux FragPipe PSM rows should preserve the source PSM table row count for the governed benchmark bundle",
        ),
        FragpipeCountComparisonEntry(
            comparison_id="peptide_rows",
            source_count=len(source_peptide_rows),
            imported_count=import_report.summary.peptide_row_count,
            matched=len(source_peptide_rows) == import_report.summary.peptide_row_count,
            note="Bijux FragPipe peptide review rows should preserve the source peptide table row count for the governed benchmark bundle",
        ),
        FragpipeCountComparisonEntry(
            comparison_id="protein_rows",
            source_count=len(source_protein_rows),
            imported_count=import_report.summary.protein_row_count,
            matched=len(source_protein_rows) == import_report.summary.protein_row_count,
            note="Bijux FragPipe protein review rows should preserve the source protein table row count for the governed benchmark bundle",
        ),
        FragpipeCountComparisonEntry(
            comparison_id="psm_q_values",
            source_count=len(source_psm_q_values),
            imported_count=import_report.summary.q_value_psm_count,
            matched=len(source_psm_q_values) == import_report.summary.q_value_psm_count,
            note="count of source PSM q-values should match the governed Bijux import surface",
        ),
        FragpipeCountComparisonEntry(
            comparison_id="peptide_q_values",
            source_count=len(source_peptide_q_values),
            imported_count=import_report.summary.q_value_peptide_count,
            matched=len(source_peptide_q_values)
            == import_report.summary.q_value_peptide_count,
            note="count of source peptide q-values should match the governed Bijux import surface",
        ),
    )
    protein_group_comparison = _build_protein_group_comparison(
        source_protein_rows=source_protein_rows,
        import_report=import_report,
    )
    q_value_behavior = _build_q_value_behavior_comparison(
        source_psm_q_values=source_psm_q_values,
        source_peptide_q_values=source_peptide_q_values,
        imported_psm_q_values=imported_psm_q_values,
        imported_peptide_q_values=imported_peptide_q_values,
        source_psm_rows=source_psm_rows,
        source_peptide_rows=source_peptide_rows,
        import_report=import_report,
    )
    summary = FragpipeImportBenchmarkSummary(
        source_psm_count=len(source_psm_rows),
        imported_psm_count=import_report.summary.accepted_psm_count,
        source_peptide_count=len(source_peptide_rows),
        imported_peptide_count=import_report.summary.peptide_row_count,
        source_protein_group_count=len(source_protein_rows),
        imported_protein_group_count=import_report.summary.protein_row_count,
        source_q_value_psm_count=len(source_psm_q_values),
        imported_q_value_psm_count=import_report.summary.q_value_psm_count,
        source_q_value_peptide_count=len(source_peptide_q_values),
        imported_q_value_peptide_count=import_report.summary.q_value_peptide_count,
        protein_group_overlap_count=len(protein_group_comparison.source_protein_refs)
        - len(protein_group_comparison.missing_in_import),
        missing_protein_group_count=len(protein_group_comparison.missing_in_import),
        extra_protein_group_count=len(protein_group_comparison.extra_in_import),
        psm_count_matched=count_comparisons[0].matched,
        peptide_count_matched=count_comparisons[1].matched,
        protein_group_count_matched=count_comparisons[2].matched,
        q_value_behavior_matched=(
            q_value_behavior.max_psm_absolute_difference == 0.0
            and q_value_behavior.max_peptide_absolute_difference == 0.0
            and q_value_behavior.source_psm_q_values_monotonic
            and q_value_behavior.imported_psm_q_values_monotonic
            and q_value_behavior.source_peptide_q_values_monotonic
            and q_value_behavior.imported_peptide_q_values_monotonic
        ),
    )
    return FragpipeImportBenchmarkReport(
        import_report=import_report,
        count_comparisons=count_comparisons,
        protein_group_comparison=protein_group_comparison,
        q_value_behavior=q_value_behavior,
        summary=summary,
        note=(
            "FragPipe import benchmark compares governed Bijux review surfaces against the source FragPipe bundle for row counts, protein-group identity, and q-value preservation"
        ),
    )


def render_fragpipe_benchmark_summary_tsv(
    report: FragpipeImportBenchmarkReport,
) -> str:
    """Render one compact FragPipe benchmark summary as TSV."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(("field", "value"))
    for field_name, value in (
        ("source_psm_count", report.summary.source_psm_count),
        ("imported_psm_count", report.summary.imported_psm_count),
        ("source_peptide_count", report.summary.source_peptide_count),
        ("imported_peptide_count", report.summary.imported_peptide_count),
        ("source_protein_group_count", report.summary.source_protein_group_count),
        ("imported_protein_group_count", report.summary.imported_protein_group_count),
        ("source_q_value_psm_count", report.summary.source_q_value_psm_count),
        ("imported_q_value_psm_count", report.summary.imported_q_value_psm_count),
        ("source_q_value_peptide_count", report.summary.source_q_value_peptide_count),
        (
            "imported_q_value_peptide_count",
            report.summary.imported_q_value_peptide_count,
        ),
        ("protein_group_overlap_count", report.summary.protein_group_overlap_count),
        ("missing_protein_group_count", report.summary.missing_protein_group_count),
        ("extra_protein_group_count", report.summary.extra_protein_group_count),
        ("psm_count_matched", str(report.summary.psm_count_matched).lower()),
        ("peptide_count_matched", str(report.summary.peptide_count_matched).lower()),
        (
            "protein_group_count_matched",
            str(report.summary.protein_group_count_matched).lower(),
        ),
        (
            "q_value_behavior_matched",
            str(report.summary.q_value_behavior_matched).lower(),
        ),
        ("note", report.note),
    ):
        writer.writerow((field_name, value))
    return handle.getvalue()


def render_fragpipe_count_comparisons_tsv(
    report: FragpipeImportBenchmarkReport,
) -> str:
    """Render count comparisons inside one FragPipe benchmark report."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(("comparison_id", "source_count", "imported_count", "matched", "note"))
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


def render_fragpipe_protein_group_comparison_tsv(
    report: FragpipeImportBenchmarkReport,
) -> str:
    """Render protein-group identity comparison for one FragPipe benchmark report."""

    comparison = report.protein_group_comparison
    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "source_protein_refs",
            "imported_protein_refs",
            "missing_in_import",
            "extra_in_import",
            "matched",
            "note",
        )
    )
    writer.writerow(
        (
            ";".join(comparison.source_protein_refs),
            ";".join(comparison.imported_protein_refs),
            ";".join(comparison.missing_in_import),
            ";".join(comparison.extra_in_import),
            str(comparison.matched).lower(),
            comparison.note,
        )
    )
    return handle.getvalue()


def render_fragpipe_q_value_comparison_tsv(
    entries: tuple[FragpipeQValueComparisonEntry, ...],
) -> str:
    """Render one q-value comparison ledger as TSV."""

    handle = StringIO()
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(
        (
            "entity_kind",
            "entity_id",
            "source_q_value",
            "imported_q_value",
            "absolute_difference",
            "exact_match",
        )
    )
    for entry in entries:
        writer.writerow(
            (
                entry.entity_kind,
                entry.entity_id,
                f"{entry.source_q_value:g}",
                f"{entry.imported_q_value:g}",
                f"{entry.absolute_difference:g}",
                str(entry.exact_match).lower(),
            )
        )
    return handle.getvalue()


def _read_tsv_rows(path: Path) -> tuple[dict[str, str], ...]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames is None:
            raise ValueError("fragpipe benchmark input table must include a header row")
        return tuple({key: value or "" for key, value in row.items()} for row in reader)


def _source_psm_q_values(rows: tuple[dict[str, str], ...]) -> dict[str, float]:
    return {
        str(row["Spectrum"]).strip(): float(str(row["QValue"]).strip())
        for row in rows
        if str(row.get("QValue", "")).strip()
    }


def _source_peptide_q_values(rows: tuple[dict[str, str], ...]) -> dict[str, float]:
    return {
        _peptide_entity_id(
            peptide=str(row["Peptide"]).strip(),
            modified_peptide=str(row.get("Modified Peptide", "")).strip() or None,
            charge=int(str(row["Charge"]).strip())
            if str(row.get("Charge", "")).strip()
            else None,
        ): float(str(row["QValue"]).strip())
        for row in rows
        if str(row.get("QValue", "")).strip()
    }


def _peptide_entity_id(
    *, peptide: str, modified_peptide: str | None, charge: int | None
) -> str:
    modified_token = "" if modified_peptide is None else modified_peptide
    charge_token = "" if charge is None else str(charge)
    return f"{peptide}|{modified_token}|{charge_token}"


def _build_protein_group_comparison(
    *,
    source_protein_rows: tuple[dict[str, str], ...],
    import_report: FragpipeImportReport,
) -> FragpipeProteinGroupComparison:
    source_refs = tuple(sorted(str(row["Protein"]).strip() for row in source_protein_rows))
    imported_refs = tuple(sorted(row.protein_ref for row in import_report.protein_rows))
    source_set = set(source_refs)
    imported_set = set(imported_refs)
    missing = tuple(sorted(source_set - imported_set))
    extra = tuple(sorted(imported_set - source_set))
    return FragpipeProteinGroupComparison(
        source_protein_refs=source_refs,
        imported_protein_refs=imported_refs,
        missing_in_import=missing,
        extra_in_import=extra,
        matched=not missing and not extra,
        note=(
            "Bijux FragPipe import should preserve the source protein-group identity set exactly for the governed benchmark bundle"
        ),
    )


def _build_q_value_behavior_comparison(
    *,
    source_psm_q_values: dict[str, float],
    source_peptide_q_values: dict[str, float],
    imported_psm_q_values: Mapping[str, float],
    imported_peptide_q_values: Mapping[str, float],
    source_psm_rows: tuple[dict[str, str], ...],
    source_peptide_rows: tuple[dict[str, str], ...],
    import_report: FragpipeImportReport,
) -> FragpipeQValueBehaviorComparison:
    psm_entries = tuple(
        sorted(
            (
                FragpipeQValueComparisonEntry(
                    entity_kind="psm",
                    entity_id=spectrum_id,
                    source_q_value=source_q_value,
                    imported_q_value=imported_psm_q_values[spectrum_id],
                    absolute_difference=abs(
                        source_q_value - imported_psm_q_values[spectrum_id]
                    ),
                    exact_match=source_q_value == imported_psm_q_values[spectrum_id],
                )
                for spectrum_id, source_q_value in source_psm_q_values.items()
                if imported_psm_q_values.get(spectrum_id) is not None
            ),
            key=lambda entry: (entry.absolute_difference, entry.entity_id),
        )
    )
    peptide_entries = tuple(
        sorted(
            (
                FragpipeQValueComparisonEntry(
                    entity_kind="peptide",
                    entity_id=entity_id,
                    source_q_value=source_q_value,
                    imported_q_value=imported_peptide_q_values[entity_id],
                    absolute_difference=abs(
                        source_q_value - imported_peptide_q_values[entity_id]
                    ),
                    exact_match=source_q_value
                    == imported_peptide_q_values[entity_id],
                )
                for entity_id, source_q_value in source_peptide_q_values.items()
                if imported_peptide_q_values.get(entity_id) is not None
            ),
            key=lambda entry: (entry.absolute_difference, entry.entity_id),
        )
    )
    return FragpipeQValueBehaviorComparison(
        psm_entries=psm_entries,
        peptide_entries=peptide_entries,
        source_psm_q_values_monotonic=_q_values_monotonic(
            (
                float(str(row["QValue"]).strip())
                for row in sorted(
                    source_psm_rows,
                    key=lambda row: -float(str(row["Hyperscore"]).strip()),
                )
                if str(row.get("QValue", "")).strip()
            )
        ),
        imported_psm_q_values_monotonic=_q_values_monotonic(
            row.q_value
            for row in sorted(
                import_report.psm_rows,
                key=lambda row: -row.hyperscore,
            )
            if row.q_value is not None
        ),
        source_peptide_q_values_monotonic=_q_values_monotonic(
            (
                float(str(row["QValue"]).strip())
                for row in sorted(
                    source_peptide_rows,
                    key=lambda row: -float(str(row["Hyperscore"]).strip()),
                )
                if str(row.get("QValue", "")).strip()
            )
        ),
        imported_peptide_q_values_monotonic=_q_values_monotonic(
            row.q_value
            for row in sorted(
                import_report.peptide_rows,
                key=lambda row: -(row.hyperscore or 0.0),
            )
            if row.q_value is not None
        ),
        max_psm_absolute_difference=max(
            (entry.absolute_difference for entry in psm_entries),
            default=0.0,
        ),
        max_peptide_absolute_difference=max(
            (entry.absolute_difference for entry in peptide_entries),
            default=0.0,
        ),
        note=(
            "FragPipe benchmark keeps q-value count, exact preservation, and monotonic ordering explicit for both PSM and peptide review surfaces"
        ),
    )


def _q_values_monotonic(values: Iterable[float]) -> bool:
    q_values = tuple(float(value) for value in values)
    return all(left <= right for left, right in zip(q_values, q_values[1:], strict=False))


__all__ = [
    "FragpipeCountComparisonEntry",
    "FragpipeImportBenchmarkReport",
    "FragpipeImportBenchmarkSummary",
    "FragpipeProteinGroupComparison",
    "FragpipeQValueBehaviorComparison",
    "FragpipeQValueComparisonEntry",
    "build_fragpipe_import_benchmark_report",
    "render_fragpipe_benchmark_summary_tsv",
    "render_fragpipe_count_comparisons_tsv",
    "render_fragpipe_protein_group_comparison_tsv",
    "render_fragpipe_q_value_comparison_tsv",
]
